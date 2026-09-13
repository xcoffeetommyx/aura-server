"""Render a LAN-only owner guard without modifying unrelated host firewall rules."""
import ipaddress


def render(address, network):
    address = ipaddress.IPv4Address(address)
    network = ipaddress.IPv4Network(network, strict=True)
    private = tuple(ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
    if address not in network or not any(network.subnet_of(n) for n in private):
        raise ValueError("Owner LAN network must be explicit RFC1918")
    return f"""# Atomic replacement of this product-owned table only (nftables >= 1.0.9).
destroy table inet aura_home
table inet aura_home {{
    chain owner_input {{
        type filter hook input priority -5; policy accept;
        ip daddr {address} tcp dport 9443 ip saddr != {network} counter drop
    }}
}}
"""


UNIT = """[Unit]
Description=Aura private owner access guard
Before=aura-server.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/nft -f /etc/aura-infrastructure/owner-guard.nft
RemainAfterExit=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
CapabilityBoundingSet=CAP_NET_ADMIN
# No ExecStop: stopping this unit must not open owner access.

[Install]
WantedBy=multi-user.target
"""

DEPENDENCY = """[Unit]
Requires=aura-home-firewall.service
After=aura-home-firewall.service
"""
