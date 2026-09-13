"""Owned Linux/systemd fixture for generated units. Never targets a public host.

Usage (root): python3 smoke_systemd.py --derp BIN --rendezvous BIN --output NEW_JSON
Requires Python 3.11+, OpenSSL and systemd with LoadCredential/DynamicUser.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import tempfile
import time

from prepare import unit


def command(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=20).strip()


def freeport():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--derp", required=True); p.add_argument("--rendezvous", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    assert os.geteuid() == 0
    output = Path(a.output)
    if output.exists(): raise ValueError("Evidence output already exists")
    created = []
    records = {}
    with tempfile.TemporaryDirectory(prefix="aura-p1-systemd-", dir="/opt") as folder:
        root = Path(folder); root.chmod(0o755)
        cert, key = root / "cert.pem", root / "key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30",
                        "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost",
                        "-keyout", str(key), "-out", str(cert)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key.chmod(0o600)
        context = ssl.create_default_context(cafile=cert)
        try:
            for role in ("derp", "rendezvous"):
                port, admin, stun = freeport(), freeport(), freeport()
                name = f"aura-p1-test-{role}-{os.getpid()}.service"
                path = Path("/run/systemd/system") / name
                binary = root / ("aura-" + role)
                shutil.copyfile(Path(getattr(a, role)).resolve(strict=True), binary); binary.chmod(0o755)
                text = unit(role, f"localhost:{port}").replace("/opt/aura-infrastructure/current/aura-" + role, str(binary))
                text = text.replace("0.0.0.0:443", f"127.0.0.1:{port}").replace("0.0.0.0:3478", f"127.0.0.1:{stun}").replace("127.0.0.1:4789", f"127.0.0.1:{admin}")
                text = text.replace(f"/etc/letsencrypt/live/localhost:{port}/fullchain.pem", str(cert)).replace(f"/etc/letsencrypt/live/localhost:{port}/privkey.pem", str(key))
                with path.open("x") as f: f.write(text)
                created.append((name, path))
                command("systemd-analyze", "verify", str(path))
                command("systemctl", "daemon-reload"); command("systemctl", "start", name)

                def request(host=None):
                    c = http.client.HTTPSConnection("localhost", port, context=context, timeout=2)
                    if role == "derp": c.request("GET", "/health", headers={"Host": host or f"localhost:{port}"})
                    else: c.request("POST", "/rendezvous/v1/candidates", '{"version":1}', {"Host": host or f"localhost:{port}", "Content-Type": "application/json"})
                    r = c.getresponse(); data = r.read(65537); c.close()
                    assert len(data) <= 65536
                    return r.status

                def ready():
                    until = time.monotonic() + 15
                    while time.monotonic() < until:
                        try:
                            if request() in (200, 204): return
                        except OSError: pass
                        time.sleep(.1)
                    raise ValueError("Owned service did not become ready")

                ready(); assert request("wrong.invalid") >= 400
                pid = int(command("systemctl", "show", "-p", "MainPID", "--value", name))
                status = Path(f"/proc/{pid}/status").read_text()
                fields = {l.split(":", 1)[0]: l.split(":", 1)[1].strip() for l in status.splitlines() if ":" in l}
                assert int(fields["Uid"].split()[0]) != 0
                assert int(fields["CapEff"], 16) & ~1024 == 0
                before = int(command("systemctl", "show", "-p", "CPUUsageNSec", "--value", name))
                time.sleep(2)
                after = int(command("systemctl", "show", "-p", "CPUUsageNSec", "--value", name))
                records[role] = {"uidNonRoot": True, "rssKiB": int(fields["VmRSS"].split()[0]),
                                 "threads": int(fields["Threads"]), "fdCount": len(list(Path(f"/proc/{pid}/fd").iterdir())),
                                 "idleCPUPercentTwoSeconds": round((after - before) / 2e9 * 100, 3),
                                 "wrongHostRejected": True, "verifiedFixtureTLS": True,
                                 "memoryMaxBytes": command("systemctl", "show", "-p", "MemoryMax", "--value", name)}
                at = time.monotonic()
                command("systemctl", "kill", "--kill-whom=main", "--signal=KILL", name)
                ready()
                assert int(command("systemctl", "show", "-p", "MainPID", "--value", name)) != pid
                records[role]["crashRecoverySeconds"] = round(time.monotonic() - at, 3)
                command("systemctl", "stop", name)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(records, indent=2) + "\n")
            print(json.dumps(records))
        finally:
            for name, path in reversed(created):
                subprocess.run(["systemctl", "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                path.unlink(missing_ok=True)
            command("systemctl", "daemon-reload")


if __name__ == "__main__": main()
