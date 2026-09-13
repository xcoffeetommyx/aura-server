"""Render operator deployment inputs; never deploy, issue certificates or edit trust."""
import argparse
import ipaddress
import json
from pathlib import Path
import re


def hostname(value):
    if not isinstance(value, str) or len(value) > 253 or value != value.lower():
        raise ValueError("Use a lowercase DNS hostname")
    labels = value.split(".")
    if len(labels) < 2 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x) for x in labels):
        raise ValueError("Invalid DNS hostname")
    if labels[-1] in {"invalid", "localhost", "local", "test"} or value.endswith(".ts.net"):
        raise ValueError("A permanent non-Tailscale DNS hostname is required")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return value
    raise ValueError("A hostname, not an IP address, is required")


def unit(role, host):
    derp = role == "derp"
    args = f"-listen 0.0.0.0:443 {'-host' if derp else '-hosts'} {host} -tls-cert %d/tls.crt -tls-key %d/tls.key"
    args += " -stun 0.0.0.0:3478" if derp else " -admin 127.0.0.1:4789"
    return f"""[Unit]
Description=Aura public {role} infrastructure
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
Type=simple
DynamicUser=yes
ExecStart=/opt/aura-infrastructure/current/aura-{role} {args}
LoadCredential=tls.crt:/etc/letsencrypt/live/{host}/fullchain.pem
LoadCredential=tls.key:/etc/letsencrypt/live/{host}/privkey.pem
Restart=on-failure
RestartSec=5
TimeoutStopSec=10
UMask=0077
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
ProtectClock=yes
RestrictSUIDSGID=yes
LockPersonality=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
MemoryMax={'256M' if derp else '128M'}
CPUQuota={'200%' if derp else '100%'}
TasksMax={'256' if derp else '128'}
LimitNOFILE=256
StandardOutput=journal
StandardError=journal
LogRateLimitIntervalSec=30s
LogRateLimitBurst=20

[Install]
WantedBy=multi-user.target
"""


def render(config):
    required = {"version", "domain", "serverId", "derpIPv4", "rendezvousIPv4", "ownerLANIPv4", "regionId"}
    if set(config) != required or type(config["version"]) is not int or config["version"] != 1:
        raise ValueError("Unsupported configuration fields/version")
    domain = hostname(config["domain"])
    if not re.fullmatch(r"[0-9a-f]{32}", config["serverId"]):
        raise ValueError("Use an opaque 128-bit server label; never a user/account name")
    for field in ("derpIPv4", "rendezvousIPv4"):
        address = ipaddress.IPv4Address(config[field])
        if not address.is_global or address.is_multicast:
            raise ValueError("Reviewed public IPv4 addresses are required")
    if config["derpIPv4"] == config["rendezvousIPv4"]:
        raise ValueError("This layout uses separate service IPs on TCP 443")
    lan = ipaddress.IPv4Address(config["ownerLANIPv4"])
    if not any(lan in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("Owner listener must use a private LAN IPv4 address")
    if type(config["regionId"]) is not int or not 1 <= config["regionId"] <= 65535:
        raise ValueError("Invalid explicit relay region")
    hosts = {"derp": hostname("relay." + domain), "rendezvous": hostname("pairing." + domain),
             "owner": hostname(config["serverId"] + ".server." + domain)}
    result = {}
    for role, host in hosts.items():
        result[role + "/renewal.json"] = json.dumps({"version": 1, "role": role, "hostname": host}, indent=2) + "\n"
        if role != "owner":
            result[role + "/aura-" + role + ".service"] = unit(role, host)
    region = {"RegionID": config["regionId"], "RegionCode": "aura", "RegionName": "Aura operated relay",
              "Nodes": [{"Name": "aura-1", "RegionID": config["regionId"], "HostName": hosts["derp"], "DERPPort": 443, "STUNPort": 3478}]}
    # Fresh provisioning input only. Existing identities and descriptors carry their own relay state.
    result["region.fresh-install.json"] = json.dumps(region, indent=2) + "\n"
    result["owner/config-review.json"] = json.dumps({"ownerAddress": str(lan) + ":9443", "ownerHost": hosts["owner"] + ":9443",
                                                  "rendezvous": "https://" + hosts["rendezvous"]}, indent=2) + "\n"
    result["dns-review.json"] = json.dumps({hosts["derp"]: config["derpIPv4"], hosts["rendezvous"]: config["rendezvousIPv4"],
                                           hosts["owner"]: {"LAN-only resolution": str(lan)}}, indent=2) + "\n"
    result["android-build-setting.txt"] = "-PauraPairingService=https://" + hosts["rendezvous"] + "\n"
    return result


def write(config, destination):
    files = render(config)
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, content in files.items():
        p = destination / name
        p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with p.open("x", encoding="utf-8", newline="\n") as f:
            f.write(content)
        p.chmod(0o600)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    try:
        raw = Path(a.config).read_bytes()
        if len(raw) > 4096:
            raise ValueError("Configuration exceeds its budget")
        write(json.loads(raw), a.output)
    except (ValueError, OSError, TypeError):
        raise SystemExit("Preparation failed: check schema, owned DNS/public IPs and a new private output directory")
    print("Operator inputs prepared; no services or authorization state changed")
