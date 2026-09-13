"""Default-deny host INPUT policy for the inventoried personal IPv4 layout.

LAN and the existing administration overlay remain independent operator trust
boundaries. Docker forwarding and unrelated nftables tables are not rewritten.
Outbound-created direct UDP flows retain normal conntrack return admission.
"""
import ipaddress
import owner_guard


def render(lan_address, lan_network, lan_ipv6, administration_udp):
    owner_guard.render(lan_address, lan_network)
    prefix = ipaddress.IPv6Network(lan_ipv6, strict=True)
    if prefix.prefixlen != 64 or not prefix.network_address.is_global:
        raise ValueError("Explicit observed global LAN /64 required")
    if type(administration_udp) is not int or not 1024 <= administration_udp <= 65535:
        raise ValueError("Inventoried administration UDP port required")
    return f"""destroy table inet aura_public_input
table inet aura_public_input {{
    chain input {{
        type filter hook input priority -4; policy drop;
        ct state invalid drop
        iifname "lo" accept
        ct state established,related accept
        iifname "tailscale0" accept
        ip saddr {lan_network} accept
        ip6 saddr {{ fe80::/10, {prefix} }} accept
        meta l4proto {{ icmp, ipv6-icmp }} accept
        udp sport 67 udp dport 68 accept
        udp sport 547 udp dport 546 accept
        ip daddr {lan_address} tcp dport {{ 80, 8443, 8444 }} accept
        ip daddr {lan_address} udp dport 3478 accept
        udp dport {administration_udp} accept
        counter drop
    }}
}}
"""


UNIT = """[Unit]
Description=Aura home host inbound firewall
Before=aura-server.service aura-derp.service aura-rendezvous.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/nft -f /etc/aura-infrastructure/host-guard.nft
RemainAfterExit=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
CapabilityBoundingSet=CAP_NET_ADMIN
# Stopping this service does not remove the firewall.

[Install]
WantedBy=multi-user.target
"""
DEPENDENCY = """[Unit]
Requires=aura-host-firewall.service
After=aura-host-firewall.service
"""
