"""Root-only deploy hook for one home IP certificate; never changes Aura trust.

Reuse the existing chain/IP/key/lifetime validator. Publish immutable pairs through
one atomic link, so failed renewal cannot replace a working pair with half a pair.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile

import renew

SERVICES = ("aura-derp.service", "aura-rendezvous.service")


def configuration(value):
    if set(value) not in ({"version", "publicIP", "certName"}, {"version", "publicIP", "certName", "ownerEnabled"}) or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Unsupported IP certificate configuration")
    if "ownerEnabled" in value and type(value["ownerEnabled"]) is not bool:
        raise ValueError("Owner renewal must be explicitly enabled")
    renew.public_ip(value["publicIP"])
    if not isinstance(value["certName"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value["certName"]):
        raise ValueError("Invalid certificate lineage name")
    return value


def sync_directory(root):
    fd = os.open(root, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def point(root, name):
    link = root / ".current-next"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(name)
    os.replace(link, root / "current")
    sync_directory(root)


def publish(cert, key, root, active, command=renew.run):
    """Inputs are already validated snapshots; root is exclusively root-owned.

    Called under the deploy lock. Keep a prior generation for crash recovery.
    A failed restart restores the previous pair and attempts to restore services.
    No service that was stopped is started implicitly.
    """
    if any(s not in SERVICES for s in active): raise ValueError("Invalid service")
    root.mkdir(mode=0o700, exist_ok=True)
    s = root.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid != os.geteuid() or s.st_mode & 0o077:
        raise ValueError("Unsafe certificate publication directory")
    previous = None
    current = root / "current"
    if current.is_symlink():
        previous = os.readlink(current)
        if not re.fullmatch(r"pair-[a-zA-Z0-9_-]+", previous) or not (root / previous).is_dir():
            raise ValueError("Invalid previous certificate generation")
    elif current.exists():
        raise ValueError("Unexpected current certificate object")
    generation = Path(tempfile.mkdtemp(prefix="pair-", dir=root))
    for source, name in ((cert, "fullchain.pem"), (key, "privkey.pem")):
        with source.open("rb") as inp, (generation / name).open("xb") as out:
            os.fchmod(out.fileno(), 0o600)
            shutil.copyfileobj(inp, out)
            out.flush(); os.fsync(out.fileno())
    sync_directory(generation)
    point(root, generation.name)
    try:
        for service in active:
            command(["systemctl", "restart", service])
            command(["systemctl", "is-active", "--quiet", service])
    except Exception:
        if previous:
            point(root, previous)
            for service in active:
                try: command(["systemctl", "restart", service])
                except Exception: pass
        else:
            current.unlink(); sync_directory(root)
            for service in active:
                try: command(["systemctl", "stop", service])
                except Exception: pass
        raise
    # Only remove our own complete older generations. Retain current + previous;
    # incomplete/stale staging remains private for operator review after a crash.
    for old in root.glob("pair-*"):
        if old.name in {generation.name, previous} or old.is_symlink() or not old.is_dir(): continue
        if {p.name for p in old.iterdir()} == {"fullchain.pem", "privkey.pem"}:
            for name in ("fullchain.pem", "privkey.pem"): (old / name).unlink()
            old.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    a = p.parse_args()
    if os.geteuid() != 0: raise ValueError("Root deploy hook required")
    config = Path(a.config)
    renew.private_regular(config, 0)
    if not config.resolve().is_relative_to("/etc/aura-infrastructure") or config.stat().st_size > 4096:
        raise ValueError("Unsafe configuration location/size")
    for parent in config.resolve().parents:
        s = parent.stat()
        if s.st_uid != 0 or s.st_mode & 0o022: raise ValueError("Unsafe configuration parent")
    value = configuration(json.loads(config.read_text()))
    lineage = Path("/etc/letsencrypt/live") / value["certName"]
    if Path(os.environ.get("RENEWED_LINEAGE", "")).absolute() != lineage:
        raise ValueError("Unexpected certificate lineage")
    fd = os.open("/run/lock/aura-ip-tls.lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    s = os.fstat(fd)
    if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o077:
        os.close(fd); raise ValueError("Unsafe deploy lock")
    with os.fdopen(fd, "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sources = [(lineage / n).resolve(strict=True) for n in ("fullchain.pem", "privkey.pem")]
        for source in sources:
            s = source.stat()
            if not source.is_relative_to(Path("/etc/letsencrypt/archive") / value["certName"]) or not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or s.st_size > 65536:
                raise ValueError("Unsafe certificate archive")
        renew.private_regular(sources[1], 0)
        with tempfile.TemporaryDirectory(prefix="aura-ip-tls-", dir="/run") as folder:
            cert, key = (Path(folder) / n for n in ("fullchain.pem", "privkey.pem"))
            for source, target in zip(sources, (cert, key)):
                shutil.copyfile(source, target); target.chmod(0o600)
            renew.validate_pair(cert, key, value["publicIP"], ip_identifier=True)
            active = [s for s in SERVICES if subprocess.run(["systemctl", "is-active", "--quiet", s], timeout=10).returncode == 0]
            publish(cert, key, Path("/etc/aura-infrastructure/tls"), active)
            if value.get("ownerEnabled", False):
                renew.run(["systemctl", "start", "aura-owner-tls-refresh.service"])
    print("IP certificate validated and published; stopped services remain stopped")


if __name__ == "__main__":
    try: main()
    except Exception:
        raise SystemExit("IP certificate deployment failed; previous material preserved. Inspect local service health.")
