# Personal pilot operations and acceptance

Aura's project owner operates these services and owns DNS, certificate alarms,
provider abuse response and billing. The home server owner retains all music,
Navidrome users/database, device trust and owner capability. Public services receive
none of that durable state. This is a bounded personal pilot, not Internet-scale
DoS protection or a commercial SLA.

## Exposure and privacy

| Host | Inbound | Outbound / state |
|---|---|---|
| DERP | TCP 443 TLS; UDP 3478 STUN; restricted administrator SSH | Responses on accepted flows; DNS and operator certificate/update HTTPS; binary/config/certificate only |
| Rendezvous | TCP 443 TLS; restricted administrator SSH | Responses to bounded polling/exchange requests; DNS/certificate/update HTTPS; mailbox RAM only |
| Home Aura Server | Existing private LAN pairing and owner TLS | Outbound DERP TLS/STUN, direct encrypted peer UDP, optional rendezvous HTTPS and narrowly scoped DNS-01; Navidrome stays 127.0.0.1:4533 |

Do not publish rendezvous's 127.0.0.1:4789 admin metrics. Do not publish Go profiling,
Docker, owner capability, raw Navidrome, port 4533 or a generic proxy. These units
do not automatically edit a machine-wide firewall. Before public exposure, apply
the exact provider/host rules with administrative recovery access preserved.

DERP terminates outer TLS and observes IPs, timing, node routing keys and packet
length/topology. WireGuard application traffic remains encrypted; relay operation
does not provide Navidrome credentials, decrypted music or library visibility.
Rendezvous sees temporary offers/IDs, timing, phases and opaque envelopes. It cannot
authorize a device, choose backend targets or decrypt the OPAQUE bootstrap. A
six-digit code remains authentication input to the existing protocol, not authority
conferred by the mailbox.

Preserve the T11 no-access/body/key-log policy. Unit journaling is rate limited;
bound host journal retention to 7 days / 16 MiB on dedicated hosts, subject to other
administrative log needs. Do not change shared-host global journal policy blindly.
Keep aggregate minute metrics 7 days and optional coarse capacity totals 30 days.
No per-device/source IDs in metric labels; provider full request/body logging off.
No routine packet capture, pairing-state dump or credential forwarding to analytics.

## Quotas, health and budgets

Existing compiled controls are unchanged:

- DERP: 64 live TLS sockets, 32/source; new connections 20/s burst 40; sender
  packet budget 2 MiB/s burst 2 MiB; STUN 200/s burst 400 with bounded input.
  The sender budget is shared by all relayed streams sent by one home server.
- Rendezvous: 8 simultaneous registrations total / 2 per source; at most 300s
  lifetime; 2 pending / 32 exchanges per registration; 64 in flight; 48 KiB
  envelopes / 32 KiB payload; 100 requests/s global / 10 per source, with existing
  bursts/source-map bounds. IPv6 source /64 normalization remains unchanged.
- DERP unit: 256 MiB, 2 CPU equivalent, 256 tasks/FDs. Rendezvous: 128 MiB,
  1 CPU equivalent, 128 tasks / 256 FDs. Provider limits must complement these.

Do not scale rendezvous using random active-active routing: each process owns its
ephemeral catalog. The eight-registration catalog is not a worldwide discovery
directory. Do not add a second unmeshed DERP node expecting transparent HA. One
stable DNS name and one explicit region/node preserve the qualified design.

External TLS health must use the real hostname, normal system trust and exact Host:

```
curl --fail --max-time 5 https://relay.DOMAIN/health
curl --fail --max-time 5 -H 'Content-Type: application/json' \
  --data '{"version":1}' https://pairing.DOMAIN/rendezvous/v1/candidates
```

First returns 204; the second returns a bounded catalog response and consumes an
existing catalog budget. Poll at most once/minute, without logging its body. Locally
scrape rendezvous `http://127.0.0.1:4789/health` for aggregate counters. Health alone
does not prove a paired service/media request; use a separately authorized test
profile and a small fixture for that synthetic check, never real credentials in
an infrastructure metric. Monitor STUN with the qualified binding probe as well.

Inspect `systemctl show SERVICE -p MainPID -p NRestarts -p MemoryCurrent -p CPUUsageNSec`
and cgroup/socket counts. Warn at 75% memory/CPU, 48 sockets, 6 rendezvous slots,
5% rejected requests for five minutes, TLS <14 days and 70% bandwidth budget.
Critical: service down, repeated restarts, unexpected proxy/media paths or TLS <7
days. Detect within two minutes; target restart within five minutes/manual recovery
within thirty. These are operator objectives, not measured public guarantees.

DERP media egress GB/month estimate:
`users * hours/day * 30 * 3600 * bitrate_bits/sec / 8 / 1e9 * relay_fraction * overhead`.
For one user at 2h/day and all-relayed: 320 kbps is 8.64 GB payload/month; 1.72 Mbps
is 46.44 GB. An illustrative 1.25 framing/retransmission factor gives 10.8/58.05 GB.
For 100 users at 20% relayed, the same examples become 216/1,161 GB including that
illustrative factor. These are estimates, not forecasts or prices. Provider-billed
ingress can roughly add another payload traversal. Actual carrier loss changes this.

Monthly cost = two small instances + IP/DNS costs + egress/ingress charges + monitoring.
Set billing alarms and a reviewed network throughput ceiling (initial pilot proposal
100 Mb/s, 50 GiB/day egress alarm), then measure before increasing capacity. An open
relay can be abused even without Aura admission. Provider packet/SYN/UDP policing
and incident response are required; do not claim a private paid relay or billing
admission exists. Closing public ingress safely is preferable to weakening approval.

## Restart, update, rollback, certificates and incidents

`systemctl restart aura-derp` drops relay connections; direct flows may survive,
but fresh Tailcat bootstrap requires DERP. `systemctl restart aura-rendezvous`
discards incomplete pairing; open a new owner-approved session. Already paired
clients must never depend on rendezvous. No mailbox backup/restore is supported.

For updates: verify the new immutable binary/hash/source graph, retain old binary,
switch the root-owned current symlink, restart, check TLS and real service access.
Rollback binaries/config only; never restore home authorization state as part of a
public service rollback. Dependency changes need separate qualification, not an
automatic nightly latest build. DNS/IP changes can take TTL/cache time; stable names
do not guarantee existing sockets migrate instantly.

TLS.md specifies renewal and failure handling. Back up protected ACME/DNS recovery
configuration and binaries/manifests. No public-host backup should contain home
server identity/PSK, owner capability, music or Navidrome data. On compromise isolate
the affected ingress, rotate its credentials/certificate, review aggregate evidence
and notify the owner. Preserve established transport authorization; never empty an
allowlist or convert an unavailable paired profile to Direct.

## Required public/physical acceptance after provisioning

Run only after verified DNS/TLS, service startup/reboot and source/hashes are checked:

1. Confirm wrong/expired certificate and wrong Host rejection; intended public ports
   only; unauthenticated home owner management denied; no exposed Navidrome/proxy.
2. Activate the preserved home candidate according to TRANSITION.md. Qualify local
   discovery, explicit remote endpoint, OPAQUE enrollment and separate Navidrome login.
3. On a physical phone, disable Tailscale/VPN, prove Wi-Fi API/artwork/media, then
   disable Wi-Fi and verify cellular is the active default. Make fresh API/library,
   artwork, MP3/seek, FLAC and download requests. Record actual direct/DERP telemetry;
   a successful bootstrap/probe is not sustained-flow route attribution.
4. Interrupt DERP during cellular playback: record whether direct survives, otherwise
   bounded failure; restart and prove recovery without re-pairing. Restore Wi-Fi and
   prove recovery. Do not change routing policy to force permanent relay use.
5. Stop rendezvous; paired API/media/download/reconstruction must continue. Restore
   it and separately prove fresh enrollment, single-use/expired replay rejection and
   quota behavior using owned sessions. Do not run an Internet-scale flood.
6. Capture idle/load CPU/RSS/FD/sockets, bandwidth, resource enforcement, restart and
   actual public-host reboot. Verify certificate renewal on the real provider.

Keep the T14 rollback and compare live original Navidrome changes before activation.
P1 cannot pass without real cellular access. Missing resources are BLOCKED, not
PASS WITH GATES. No P2 publication is performed by these instructions.
