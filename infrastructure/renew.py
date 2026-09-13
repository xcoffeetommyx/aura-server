"""Root Certbot deploy hook: verify first, refresh only the selected existing service.

Public services use systemd LoadCredential; keys never enter their images/environment.
The home owner service retains its existing private regular-file contract.
"""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shutil
import ssl
import stat
import subprocess
import tempfile

from prepare import hostname


def run(args):
    return subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)


def public_ip(value):
    address = ipaddress.ip_address(value)
    if not address.is_global or address.is_multicast or getattr(address, "ipv4_mapped", None) is not None or "%" in value:
        raise ValueError("A public unscoped IP identifier is required")
    return str(address)


def validate_pair(cert, key, host, *, ca_file=None, ip_identifier=False):
    if ip_identifier:
        host = public_ip(host)
    else:
        hostname(host)
    if cert.stat().st_size > 65536 or key.stat().st_size > 32768:
        raise ValueError("Certificate material exceeds budget")
    ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER).load_cert_chain(cert, key)
    # ca_file exists only for owned test callers. CLI always uses the system trust store.
    ca = ["-CAfile", str(ca_file)] if ca_file else []
    run(["openssl", "verify", *ca, "-purpose", "sslserver", "-verify_ip" if ip_identifier else "-verify_hostname", host,
         "-untrusted", str(cert), str(cert)])
    # IP certificates currently have a 160-hour lifetime. Keep the previous DNS
    # policy, but require at least 48 hours on a newly installed short-lived pair.
    run(["openssl", "x509", "-in", str(cert), "-noout", "-checkend", "172800" if ip_identifier else "1209600"])


def atomic_copy(source, destination, uid, gid):
    fd, name = tempfile.mkstemp(prefix=".tls-renew-", dir=destination.parent)
    try:
        os.fchmod(fd, 0o600)
        os.fchown(fd, uid, gid)
        with os.fdopen(fd, "wb") as out, source.open("rb") as inp:
            shutil.copyfileobj(inp, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, destination)
        directory = os.open(destination.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def private_regular(path, uid):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid != uid or s.st_mode & 0o077:
        raise ValueError("Unsafe private file")


def owner_files(cert_bytes, key_bytes, root, uid, gid):
    s = root.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != uid or s.st_mode & 0o077:
        raise ValueError("Unsafe owner state directory")
    for name in ("owner.crt", "owner.key"):
        private_regular(root / name, uid)
    # A crash between the two replacements leaves a stopped, mismatched pair that
    # package validation rejects. Never regenerate identity or remove quarantine.
    previous = root / ".owner-tls-before-renewal"
    previous.mkdir(mode=0o700, exist_ok=False)
    os.chown(previous, uid, gid)
    for name in ("owner.crt", "owner.key"):
        atomic_copy(root / name, previous / name, uid, gid)
    with tempfile.TemporaryDirectory(prefix=".tls-pair-", dir=root) as folder:
        for name, data in (("owner.crt", cert_bytes), ("owner.key", key_bytes)):
            staged = Path(folder) / name
            staged.write_bytes(data)
            staged.chmod(0o600)
            atomic_copy(staged, root / name, uid, gid)


def as_owner(uid, gid, operation):
    # All writes/reads in the service-owned tree happen without root privileges.
    # A compromised service account must not turn a path race into a root file read.
    child = os.fork()
    if child == 0:
        try:
            if os.geteuid() != uid:
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)
            operation()
        except BaseException:
            os._exit(1)
        os._exit(0)
    _, status = os.waitpid(child, 0)
    if status != 0:
        raise ValueError("Owner certificate file operation needs repair")


def owner_install(cert, key, root, uid, gid, active, command=run):
    cert_bytes, key_bytes = cert.read_bytes(), key.read_bytes()
    if active:
        command(["systemctl", "stop", "aura-server.service"])
    as_owner(uid, gid, lambda: owner_files(cert_bytes, key_bytes, root, uid, gid))
    command(["runuser", "-u", "aura-server", "--", "/opt/aura-server/current/bin/aura-server", "check", str(root)])
    if active:
        command(["systemctl", "start", "aura-server.service"])
        command(["systemctl", "is-active", "--quiet", "aura-server.service"])
    # Remove only these two task-owned rollback files after successful validation.
    def clean_previous():
        previous = root / ".owner-tls-before-renewal"
        for name in ("owner.crt", "owner.key"):
            (previous / name).unlink()
        previous.rmdir()
    as_owner(uid, gid, clean_previous)


def main():
    import fcntl
    import pwd
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    a = p.parse_args()
    if os.geteuid() != 0:
        raise ValueError("Run as root from the certificate deploy hook")
    config = Path(a.config)
    private_regular(config, 0)
    if not config.resolve().is_relative_to("/etc/aura-infrastructure"):
        raise ValueError("Use the private infrastructure configuration directory")
    for parent in config.resolve().parents:
        s = parent.stat()
        if s.st_uid != 0 or s.st_mode & 0o022:
            raise ValueError("Unsafe configuration parent")
    if config.stat().st_size > 4096:
        raise ValueError("Configuration exceeds budget")
    v = json.loads(config.read_text())
    if set(v) != {"version", "role", "hostname"} or type(v["version"]) is not int or v["version"] != 1 or v["role"] not in {"owner", "derp", "rendezvous"}:
        raise ValueError("Unsupported renewal configuration")
    host = hostname(v["hostname"])
    lineage = Path("/etc/letsencrypt/live") / host
    # A global Certbot hook must never install another lineage's certificate.
    if Path(os.environ.get("RENEWED_LINEAGE", "")).absolute() != lineage:
        raise ValueError("Unexpected certificate lineage")
    fd = os.open("/run/lock/aura-tls-renewal.lock", os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    s = os.fstat(fd)
    if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o077:
        os.close(fd)
        raise ValueError("Unsafe renewal lock")
    with os.fdopen(fd, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        paths = [(lineage / n).resolve(strict=True) for n in ("fullchain.pem", "privkey.pem")]
        for path in paths:
            if not path.is_relative_to("/etc/letsencrypt/archive") or path.stat().st_uid != 0:
                raise ValueError("Certificate must be from the root-owned Certbot archive")
        private_regular(paths[1], 0)
        # Validate a private stable snapshot, not files that renewal may replace.
        with tempfile.TemporaryDirectory(prefix="aura-tls-", dir="/run") as d:
            cert, key = Path(d) / "fullchain.pem", Path(d) / "privkey.pem"
            for source, target in zip(paths, (cert, key)):
                if source.stat().st_size > 65536:
                    raise ValueError("Certificate material exceeds budget")
                shutil.copyfile(source, target)
                target.chmod(0o600)
            validate_pair(cert, key, host)
            service = "aura-server.service" if v["role"] == "owner" else "aura-" + v["role"] + ".service"
            active = subprocess.run(["systemctl", "is-active", "--quiet", service], timeout=10).returncode == 0
            if v["role"] == "owner":
                user = pwd.getpwnam("aura-server")
                owner_install(cert, key, Path("/var/lib/aura-server"), user.pw_uid, user.pw_gid, active)
            elif active:
                run(["systemctl", "restart", service])
                run(["systemctl", "is-active", "--quiet", service])
    print("Aura certificate verified; existing service disposition preserved")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError, ssl.SSLError):
        raise SystemExit("Aura certificate deployment failed; inspect certificate/configuration/service health. No trust state was regenerated.")
