# P1B — single home server, no purchased domain

September 13, 2026: public IPv4 TCP/UDP cellular reachability, trusted IP issuance,
renewal rehearsal, remote OPAQUE pairing, cellular media/downloads and physical
host reboot have been demonstrated. Full evidence/final disposition is in Aura
Android's native/tailcat/results/PROD-P1B-SELF-HOSTED.md. This is a personal operated
deployment, not universal zero-configuration discovery or an Internet-scale claim.
P1's two-public-host/domain deployment is superseded by this owner requirement.
Its hardened systemd and certificate helpers remain reusable; its topology is
not a prerequisite. T14 engineering/physical evidence remains authoritative.

## Reachability before installation

Inventory the actual home router WAN, independent outward address observations,
laptop IPv4/IPv6 and default routes before changing rules. A Tailscale interface's
100.64/10 or fd7a address is not evidence of ISP CGNAT. A global IPv6 lease and
outbound access do not prove inbound reachability. Short router-advertisement/DHCP
lifetimes do not by themselves mean a public prefix changes every lease interval.

Use `reachability_probe.py` only on explicitly owned addresses. It runs a small
TCP/UDP nonce echo for at most 180 seconds, serves no files, forwards nothing,
rejects other payloads and reports aggregate counts without remote addresses.
It never changes firewall/router rules. Store a random 32-lowercase-hex nonce in
a private temporary file; run the listener on an unused high port and compare
exact returned bytes from a cellular phone with Wi-Fi/VPN disabled. Repeat per
family. Stop/delete fixtures and any temporary exact-port rules afterward.

Successful LAN controls and cellular probes, plus explicit router/firewall evidence,
are required to distinguish the categories A/B/C/D. A blocked port behind an
unconfigured stateful firewall is not an ISP-impossibility finding. No automatic
UPnP/NAT-PMP, tunnels, VPS or fallback domain purchase is permitted by this plan.

## Trusted IP TLS

Current primary documentation confirms Let's Encrypt supports IPv4 and IPv6 IP
SAN certificates under its 160-hour shortlived profile. HTTP-01 uses inbound TCP
80; TLS-ALPN-01 uses 443 with an appropriately supporting client. DNS-01 cannot
validate an IP identifier. Certbot 5.3 introduced IP identifiers; 5.4 adds webroot.
Certbot's standalone/webroot path uses HTTP-01. The inspected development Ubuntu
package index offered 4.0; it is insufficient and was not installed as a substitute.
The actual laptop also lacked a suitable client. A dedicated Certbot 5.4.0
environment is installed. Public IPv4 issuance and staging renewal rehearsal
succeeded; no private CA or ordinary Android trust modification was used.

References:

- https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability
- https://letsencrypt.org/2026/03/11/shorter-certs-certbot
- https://letsencrypt.org/docs/challenge-types/

The reused `renew.validate_pair(..., ip_identifier=True)` explicitly verifies an
IP SAN with OpenSSL `-verify_ip`, a trusted chain, key-pair match and at least 48
hours remaining on newly installed material. A DNS SAN that merely looks like an
IP is rejected. Private/link-local/scoped/mapped/multicast identifiers are rejected.
The existing DNS policy remains 14 days; no trust-all CLI switch was added.
These are disposable-fixture validation tests, not public certificate issuance or
physical carrier/MTU evidence. The historical v1 deploy-hook CLI still targets DNS.
The new `ip_deploy.py` reuses its validator for IP issuance and publishes immutable
certificate/key generations through one atomic link. It retains current/previous,
restores the previous link after a failed restart, and never implicitly starts a
stopped service. The root-only configuration fixes the expected IP and ACME lineage.
Wrong lineage, untrusted/mismatched material and unsafe filesystem state fail closed.

`self_hosted.py` renders this separate single-machine layout without mutating
trust/router state. Its hourly systemd renewal timer provides the scheduling jitter;
Certbot's additional random sleep is disabled to fit the bounded service timeout.
Certbot retains its standard renewal due-date policy for short-lived certificates.
The live deploy hook and both post-restart local health checks passed. Public-IP
change detection and the owner certificate transition are described below.

## Qualified single-machine layout

After inbound access and socket conflict checks, use separate TLS
ports for DERP and rendezvous (8443/8444), UDP 3478 STUN and a minimal
ACME-only port-80 challenge listener. No general web/content proxy is needed.
Owner management remains LAN-only; never forward Navidrome 4533 or arbitrary
bridge traffic. Each public process must use its own unprivileged identity and
systemd credential access, with no permission to home music/database/owner trust.

The package binds owner TLS to private IPv4 but uses the public-IP authority on
TCP 9443. Router loopback preserves a usable LAN URL; owner_guard.py drops non-LAN
sources before the listener. Actual LAN TLS without owner capability returned
403; cellular access timed out and incremented the nftables drop counter. The
router source translation was measured; revalidate it before adapting this to
another router. No trust bypass or public owner authorization was introduced.

Approved mappings are TCP 80, 8443/8444, UDP 3478 and guarded TCP 9443. Local and
cellular DERP health returns 204; rendezvous catalog returns 200 with ordinary
certificate/IP verification. Wrong DERP Host returns 400.
Actual namespace/user checks deny both services access to music, Aura state,
Docker state and backups. Real public Tailcat media is recorded in P1B results.
Router rules must target only the laptop's reviewed infrastructure sockets, preserve
unrelated administration, and survive reboot. Existing NAT/default-server settings
must be inventoried; do not replace somebody else's mappings blindly.

## Address changes and paired identity

Public addresses remain network endpoints, not server/library identity. A new public
IP needs a new correctly validated certificate. Old certificates and descriptors
must not be advertised as valid for a new address. Stable key/PSK/installation ID,
approved devices/tombstones, logical origin and cache namespaces must be preserved.
Prefer explicit owner-approved re-pair over adding an unreviewed remote metadata
protocol. Certificate renewal for the same IP alone does not require re-pairing.

There is no magic way for a phone that knows only obsolete IP A to discover new IP B
using the same unreachable mailbox. Without an external locator, address change can
require returning to LAN discovery/owner-approved re-pair. No seamless arbitrary-IP
churn promise is made. Current relay metadata is durable, and package region.json
edits alone do not update paired clients (see TRANSITION.md's source findings).

Fresh cellular-only enrollment also needs a previously provisioned trusted mailbox
location; a six-digit code alone cannot locate one arbitrary home among all Internet
addresses. The existing operator endpoint build setting can serve a personal stable
deployment; generalized per-home remote discovery is not invented in this stage.
Neither issue justifies silently introducing an external directory or network account.

## Operations and recovery

The candidate, DERP/rendezvous and timers are enabled under systemd. The original
Docker Navidrome is stopped, with data/image/backups preserved. Never run duplicate
writers/listeners on 4533. No public GitHub/fork publication or PROD P2 is included.

See the implementation contracts in self_hosted.py, ip_deploy.py, owner_guard.py,
owner_ip_refresh.py, local_endpoints.py, host_guard.py and wan_watch.py. Install
them under a root-owned versioned /opt/aura-infrastructure directory. Configuration
belongs under root-only /etc/aura-infrastructure (0700, files 0600). Infrastructure
services need no source checkout/Go compiler on the headless server.

1. Inventory/reserve the LAN address, actual WAN address, LAN IPv6 prefix and
   existing administration. Render version-1 publicIPv4/lanIPv4/regionId/mediaRoot
   configuration with self_hosted.py. Review before installation.
2. Issue with the dedicated Certbot: certonly --standalone --preferred-challenges
   http --required-profile shortlived --ip-address PUBLIC_IP --cert-name aura-home-ip.
   PUBLIC_IP is an operator placeholder. Choose ACME contact/terms explicitly.
3. Install the generated units, root renewal JSON, exact-lineage deploy hook and
   firewall/routing dependencies. Set ownerEnabled=true only after the explicit
   ownerHost/IP certificate transition and owner guard verification.
4. Run systemd-analyze verify, bounded trusted health checks, then enable services
   and renewal/address-check timers. Never treat Type=simple activation as health.

The owner refresh uses a separate bounded service. It verifies root-authorized IP
against ownerHost, drops to the Aura UID before touching service-owned paths,
stops Aura if active, keeps a private previous pair, validates package state and
restarts. A crash between file replacements leaves a stopped repair condition.
Do not delete the prior pair or regenerate trust to conceal a renewal failure.

The home router dropped new loopback connections to its public relay address
while older connections remained. Captures showed SYNs leaving but not arriving;
direct LAN TLS still worked. local_endpoints.py corrects this with OUTPUT-only
DNAT for this host's public-IP TCP 8443/8444/9443 and UDP 3478 to the local service
address. It does not intercept forwarded/phone traffic or change URL/TLS authority.
Three consecutive generated-identity reconstructions passed normal and race with
the actual relay afterward. No Tailcat retry/revocation implementation changed.

host_guard.py supplies default-deny INPUT while preserving loopback, established
return flows, explicitly trusted LAN /24 and IPv6 /64, ICMP/DHCP, public infrastructure
ports and inventoried administration (existing tailscale0/UDP 41641). That overlay
exception preserves unrelated administration; Aura does not depend on it. Docker
forwarding/unrelated tables are untouched. Use a timed rollback deleting only the
new table until fresh SSH and cellular TLS succeed. Outbound-created direct UDP
retains normal conntrack return admission; no permanent forced-DERP setting exists.

wan_watch.py checks the bounded router WAN status every three minutes and before
startup, without redirects/proxies. It never accepts a newly observed IP as trust.
A confirmed mismatch fsyncs ADDRESS-REPAIR before queuing all service stops; unit
conditions block restart across reboot. One failed stop does not skip others.
An unreadable router fails the check; already-running services are not stopped
solely for an unknown observation. The observer's LAN HTTP input can cause denial
of service if the trusted LAN is compromised, but cannot authorize a new IP.

On ISP address change: keep services offline, back up, independently verify the
new WAN/inbound route, issue its certificate, update root expected IP/ownerHost/
local routing/region explicitly, run reconfigure-ip-relay offline and package
checks, then clear the repair marker and explicitly re-pair. Preserve exact server
key/PSK/installation/registry/logical origin. Certificate renewal at the same IP
does not require this procedure. Do not promise seamless arbitrary IP churn.

Operator/project owner monitors service health, certificate expiry, failed timers,
repair marker, resource/rejection counters and relay bandwidth. Alarm on renewal
failure; fewer than 48 hours remaining requires intervention. Back up ACME account,
certificate/configuration and Aura state as secrets; rendezvous sessions are
ephemeral and must not become durable restored authorization.

DERP budgets: 64 connections, 32/source, 20 admissions/s burst 40, per-client
2 MiB/s/burst 2 MiB, five-second write deadline, 256 MiB/two-core quota. Rendezvous
retains T10/T11 protocol/map/source budgets with 128 MiB/one-core quota. This does
not establish Internet-scale abuse resistance. Relay uses home upload bandwidth;
costs are ISP/electricity/hardware, not a domain/VPS. One host/ISP is a single
failure domain; no availability SLA is invented.

DERP observes addresses/public node identities/timing/encrypted sizes, not
decrypted media or Navidrome credentials. Rendezvous observes bounded coordination
metadata, not OPAQUE secrets/bootstrap plaintext or media. Logs omit payloads,
codes/descriptors/keys/capabilities; retain bounded startup/aggregate journaling.
Do not export raw personal inventories. Existing unrelated LAN/overlay services
remain separate operator trust boundaries, not a claim of whole-laptop hardening.

Use systemctl status/list-timers/show Result for aura-* units, check absence of
ADDRESS-REPAIR, run the package status command and inspect ss -lntup. Restart
infrastructure with systemctl and Aura through the package lifecycle. Prolonged
outage can exhaust Android's existing retry budget: Connect saved Aura Server
grants an explicit attempt without re-pairing. A stale setup error may remain
beside later Connected status; verify a real authenticated service request.

Upgrade verified binaries/configuration into a new root-owned version directory,
check, switch the link and restart. Software rollback never rolls authorization
state back. Restore old backups OFFLINE, reconcile stale approvals and re-pair
if trust is uncertain. Preserve T14/P1B recovery material and never blindly expose
an old allowlist.

Infrastructure logs use the dedicated aura-infrastructure journal namespace:
install journald@aura-infrastructure.conf under /etc/systemd, retain at most 32 MiB
persistent / 16 MiB runtime with seven-day retention, and query with
journalctl --namespace=aura-infrastructure -u aura-derp -u aura-rendezvous.
Both units retained the namespace through the final physical reboot. Existing
system journals from earlier testing are not retroactively relabeled. Log rate
limits remain 20 events per 30 seconds. No packet/pairing payload capture belongs
in routine operations.

Outbound requirements are ordinary CA HTTPS (443) and its supporting DNS when
renewing, DERP TLS 8443/rendezvous TLS 8444 for the configured endpoint, STUN UDP
3478 and peer UDP for direct candidates. No restrictive outbound firewall is
installed by P1B. Public ACME TCP 80 serves only the short-lived challenge listener;
it is not a website. Certificate private keys/ACME account, configuration and
server backups remain root/private; do not put them into release archives.

For installation on another owned laptop, inventory first rather than copying
this household's addresses. Render with self_hosted.py --config PRIVATE_JSON
--output NEW_PRIVATE_DIRECTORY. Install qualified binaries at the paths defined
by prepare.unit, root-owned Python helpers under /opt/aura-infrastructure/current,
and the generated units/configuration under /etc. Obtain a public IP certificate
using the pinned Certbot HTTP-01 flow before starting listeners. Install the
owner/default-deny/local-endpoint guards and their Requires/After drop-ins before
activating router mappings; validate with nft --check and systemd-analyze verify.
Install the generated journald configuration under /etc/systemd. Use a bounded
rollback timer for first firewall activation and verify fresh administrative access.
This remains an operator provisioning procedure, not a new consumer installer.
Do not enable owner renewal until the explicit protected owner IP transition passes.
