"""Host-originated access to co-located public-IP services without router hairpin.

The original URL, IP SAN verification and HTTP authority are unchanged. This
does not intercept forwarded/LAN/client traffic or expose an additional port.
"""
import ipaddress
import renew


def render(public, lan):
    public = renew.public_ip(public)
    if ipaddress.ip_address(public).version != 4:
        raise ValueError("Qualified IPv4 layout required")
    lan = ipaddress.IPv4Address(lan)
    if not any(lan in ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("Explicit private service address required")
    return f"""# Only this product-owned table is replaced atomically.
destroy table ip aura_local_endpoints
table ip aura_local_endpoints {{
    chain output {{
        type nat hook output priority dstnat; policy accept;
        ip daddr {public} tcp dport {{ 8443, 8444, 9443 }} counter dnat to {lan}
        ip daddr {public} udp dport 3478 counter dnat to {lan}
    }}
}}
"""


UNIT = """[Unit]
Description=Aura co-located public IP service routing
Before=aura-server.service aura-derp.service aura-rendezvous.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/nft -f /etc/aura-infrastructure/local-endpoints.nft
RemainAfterExit=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
CapabilityBoundingSet=CAP_NET_ADMIN

[Install]
WantedBy=multi-user.target
"""

DEPENDENCY = """[Unit]
Requires=aura-local-endpoints.service
After=aura-local-endpoints.service
"""
