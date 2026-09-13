"""Render the personal IPv4/no-domain layout. Does not open ports or change trust."""
import argparse
import ipaddress
import json
from pathlib import Path
import re

import prepare
import renew


def render(v):
    if set(v) != {"version", "publicIPv4", "lanIPv4", "regionId", "mediaRoot"} or type(v["version"]) is not int or v["version"] != 1:
        raise ValueError("Unsupported self-hosted configuration")
    public = renew.public_ip(v["publicIPv4"])
    if ipaddress.ip_address(public).version != 4: raise ValueError("This qualified layout uses IPv4")
    lan = ipaddress.IPv4Address(v["lanIPv4"])
    if not any(lan in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("Private LAN IPv4 required")
    if type(v["regionId"]) is not int or not 1 <= v["regionId"] <= 65535: raise ValueError("Invalid region")
    media = v["mediaRoot"]
    if not isinstance(media, str) or not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+", media):
        raise ValueError("Use an explicit supported media-root path")
    result = {}
    for role, port in (("derp", 8443), ("rendezvous", 8444)):
        authority = f"{public}:{port}"
        unit = prepare.unit(role, authority)
        unit = unit.replace("-listen 0.0.0.0:443", f"-listen {lan}:{port}")
        unit = unit.replace("-stun 0.0.0.0:3478", f"-stun {lan}:3478")
        unit = unit.replace(f"/etc/letsencrypt/live/{authority}/", "/etc/aura-infrastructure/tls/current/")
        unit = unit.replace("CapabilityBoundingSet=CAP_NET_BIND_SERVICE", "CapabilityBoundingSet=")
        unit = unit.replace("AmbientCapabilities=CAP_NET_BIND_SERVICE", "AmbientCapabilities=")
        unit += f"\n[Service]\nLogNamespace=aura-infrastructure\nInaccessiblePaths=-{media} -/var/lib/aura-server -/var/lib/docker -/var/backups -/opt/aura-server -/etc/letsencrypt\n"
        result[f"aura-{role}.service"] = unit
    result["ip-renewal.json"] = json.dumps(dict(version=1, publicIP=public, certName="aura-home-ip"), indent=2) + "\n"
    result["region.fresh-enrollment.json"] = json.dumps({
        "RegionID": v["regionId"], "RegionCode": "aura", "RegionName": "Aura home relay",
        "Nodes": [{"Name": "aura-home", "RegionID": v["regionId"], "HostName": public,
                   "IPv4": public, "IPv6": "none", "DERPPort": 8443, "STUNPort": 3478}]}, indent=2) + "\n"
    result["journald@aura-infrastructure.conf"] = "[Journal]\nStorage=persistent\nSystemMaxUse=32M\nRuntimeMaxUse=16M\nMaxRetentionSec=7day\n"
    result["aura-acme-renew.service"] = """[Unit]
Description=Renew and validate Aura home IP certificate
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
UMask=0077
ExecStart=/opt/aura-infrastructure/acme-venv/bin/certbot renew --cert-name aura-home-ip --non-interactive --quiet --no-random-sleep-on-renew --deploy-hook "/usr/bin/python3 /opt/aura-infrastructure/current/ip_deploy.py --config /etc/aura-infrastructure/ip-renewal.json"
TimeoutStartSec=300
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/etc/letsencrypt /var/lib/letsencrypt /var/log/letsencrypt /etc/aura-infrastructure /run
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
MemoryMax=256M
TasksMax=64
"""
    result["aura-acme-renew.timer"] = """[Unit]
Description=Check short-lived Aura IP certificate every hour

[Timer]
OnCalendar=hourly
RandomizedDelaySec=300
Persistent=true

[Install]
WantedBy=timers.target
"""
    result["aura-owner-tls-refresh.service"] = """[Unit]
Description=Refresh existing private Aura owner IP certificate
After=aura-home-firewall.service
Requires=aura-home-firewall.service

[Service]
Type=oneshot
UMask=0077
ExecStart=/usr/bin/python3 /opt/aura-infrastructure/current/owner_ip_refresh.py
TimeoutStartSec=120
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/aura-server /run/lock
CapabilityBoundingSet=CAP_SETUID CAP_SETGID CAP_CHOWN CAP_DAC_READ_SEARCH
MemoryMax=256M
TasksMax=64
"""
    result["router-review.json"] = json.dumps({"destination": str(lan), "tcp": [80, 8443, 8444], "udp": [3478],
        "owner": "not publicly admitted; separate LAN-only host firewall and hairpin qualification required",
        "neverForward": [4533, 4534, 4789, 22]}, indent=2) + "\n"
    result["android-build-setting.txt"] = f"-PauraPairingService=https://{public}:8444\n"
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True); p.add_argument("--output", required=True)
    a = p.parse_args()
    raw = Path(a.config).read_bytes()
    if len(raw) > 4096: raise ValueError("Oversized configuration")
    files = render(json.loads(raw))
    root = Path(a.output); root.mkdir(mode=0o700, exist_ok=False)
    for name, data in files.items():
        with (root / name).open("x", encoding="utf-8", newline="\n") as f: f.write(data)
        (root / name).chmod(0o600)
    print("Self-hosted inputs prepared; no services, ports or trust state changed")


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, TypeError, KeyError):
        raise SystemExit("Preparation failed: review explicit public/LAN addresses and a new output directory")
