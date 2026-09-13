"""Install the already-published IP certificate into the existing private owner state."""
import json
import os
from pathlib import Path
import pwd
import subprocess

import ip_deploy
import renew


def refresh(root, cert, key, public_ip, uid, gid, active, command=renew.run):
    # Read untrusted service-owned configuration only after dropping privileges.
    # The exact expected IP comes from the root-owned infrastructure configuration.
    def check_host():
        renew.private_regular(root / "config.json", uid)
        if (root / "config.json").stat().st_size > 65536:
            raise ValueError("Configuration too large")
        config = json.loads((root / "config.json").read_text())
        if config.get("ownerHost") != public_ip + ":9443":
            raise ValueError("Owner identity transition must be explicit")
    renew.as_owner(uid, gid, check_host)
    renew.validate_pair(cert, key, public_ip, ip_identifier=True)
    renew.owner_install(cert, key, root, uid, gid, active, command)


def main():
    if os.geteuid() != 0: raise ValueError("Root service required")
    config = Path("/etc/aura-infrastructure/ip-renewal.json")
    renew.private_regular(config, 0)
    if config.stat().st_size > 4096: raise ValueError("Configuration too large")
    value = ip_deploy.configuration(json.loads(config.read_text()))
    if not value.get("ownerEnabled", False): raise ValueError("Owner renewal not enabled")
    import fcntl
    lock = os.open("/run/lock/aura-owner-ip-tls.lock", os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock, "a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        user = pwd.getpwnam("aura-server")
        material = Path("/etc/aura-infrastructure/tls/current").resolve(strict=True)
        if material.parent != Path("/etc/aura-infrastructure/tls") or not material.name.startswith("pair-"):
            raise ValueError("Unexpected published certificate")
        cert, key = material / "fullchain.pem", material / "privkey.pem"
        for p in (cert, key): renew.private_regular(p, 0)
        active = subprocess.run(["systemctl", "is-active", "--quiet", "aura-server.service"], timeout=10).returncode == 0
        refresh(Path("/var/lib/aura-server"), cert, key, value["publicIP"], user.pw_uid, user.pw_gid, active)
    print("Owner IP certificate refreshed; transport identity and original service disposition preserved")


if __name__ == "__main__":
    try: main()
    except Exception:
        raise SystemExit("Owner certificate refresh needs repair; prior files remain in the private renewal backup on replacement failure")
