"""Read-only BGW320 WAN observer for the personal no-domain deployment.

Never accepts a new address as trust. A confirmed change quarantines public
advertising until the operator provisions a new IP certificate and re-pairs.
No router authentication, mapping changes, external locator or account is used.
"""
import html.parser
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import urllib.request

import renew


class Rows(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row=[]
        elif tag in ("td", "th") and self.row is not None: self.cell=[]
    def handle_data(self, text):
        if self.cell is not None: self.cell.append(text)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split())); self.cell=None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row); self.row=None; self.cell=None


def observed_ipv4(data):
    if len(data) > 131072: raise ValueError("Router status exceeds budget")
    parser=Rows(); parser.feed(data.decode("utf-8", errors="strict"))
    values=[r[1] for r in parser.rows if len(r)==2 and r[0]=="Broadband IPv4 Address"]
    if len(values)!=1: raise ValueError("Unrecognized or ambiguous router status")
    address=renew.public_ip(values[0])
    if ipaddress.ip_address(address).version!=4: raise ValueError("Expected WAN IPv4")
    return address


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): raise ValueError("Router redirect rejected")


def observe(router):
    address=ipaddress.IPv4Address(router)
    if not any(address in ipaddress.ip_network(n) for n in ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16")):
        raise ValueError("Explicit LAN router IPv4 required")
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(f"http://{address}/cgi-bin/broadbandstatistics.ha",timeout=5) as response:
        if response.status!=200: raise ValueError("Router status unavailable")
        return observed_ipv4(response.read(131073))


SERVICES=("aura-server.service","aura-rendezvous.service","aura-derp.service")
def enforce(expected, observed, quarantine, command=renew.run):
    renew.public_ip(expected);renew.public_ip(observed)
    if expected==observed: return
    # Root-only fixed marker is written before stopping. Unit conditions prevent
    # a subsequent automatic restart, including after a physical reboot.
    with quarantine.open("w") as out:
        os.fchmod(out.fileno(),0o600)
        out.write("WAN address changed. Offline certificate/relay review and explicit fresh pairing required.\n")
        out.flush();os.fsync(out.fileno())
    directory=os.open(quarantine.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)
    # Non-blocking stop avoids waiting on this Before= prerequisite's own start
    # job when a mismatch is discovered during boot. The durable condition blocks
    # new starts; systemd completes the queued stops independently.
    for service in SERVICES:
        try:command(["systemctl","--no-block","stop",service])
        except Exception:pass  # Still attempt every stop; the durable guard remains.
    raise ValueError("Address change requires repair")


def main():
    if os.geteuid()!=0: raise ValueError("Root observer service required")
    root=Path("/etc/aura-infrastructure")
    config=root/"wan-observer.json";renew.private_regular(config,0)
    if config.stat().st_size>4096: raise ValueError("Configuration exceeds budget")
    value=json.loads(config.read_text())
    if set(value)!={"version","routerIPv4","expectedIPv4"} or type(value["version"]) is not int or value["version"]!=1:
        raise ValueError("Unsupported observer configuration")
    enforce(value["expectedIPv4"],observe(value["routerIPv4"]),root/"ADDRESS-REPAIR")
    print("Configured public IPv4 still matches router WAN; no trust change")


UNIT="""[Unit]
Description=Verify Aura public IP against home router WAN
Wants=network-online.target
After=network-online.target
Before=aura-server.service aura-derp.service aura-rendezvous.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/aura-infrastructure/current/wan_watch.py
TimeoutStartSec=30
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/etc/aura-infrastructure
CapabilityBoundingSet=
MemoryMax=64M
TasksMax=16
"""
TIMER="""[Unit]
Description=Watch Aura home public IP for changes
[Timer]
OnBootSec=60
OnUnitActiveSec=180
[Install]
WantedBy=timers.target
"""
DEPENDENCY="""[Unit]
Requires=aura-address-check.service
After=aura-address-check.service
ConditionPathExists=!/etc/aura-infrastructure/ADDRESS-REPAIR
"""

if __name__=="__main__":
    try:main()
    except Exception:raise SystemExit("WAN check unavailable or address changed; inspect local observer status and repair marker. No new endpoint was trusted.")
