# PROD P1 operator infrastructure

**Historical two-public-host pilot; superseded by the owner's P1B requirement.**
The owner requires a single self-hosted home laptop, without a purchased domain,
VPS or cloud tunnel. See [SELF-HOSTED.md](SELF-HOSTED.md) for the qualified personal deployment.
The original preparation below is retained as history and reusable tooling, not
the required final deployment.

**Prepared and locally exercised; not publicly deployed.** No owned domain, DNS
automation or public hosts were identified at P1 preparation. Public cellular
acceptance is blocked until those resources exist. This directory does not install
cloud services on the home music server, change paired profiles or publish anything.

## Resource contract

For the first personal deployment, supply:

1. One operator-controlled domain and permission to create DNS records and automate
   DNS-01 challenges. No marketing/content website is needed.
2. Two independently reachable Linux/systemd hosts, typically two small VMs:
   one DERP and one rendezvous. Each needs a static public IPv4; TCP 443 on both,
   UDP 3478 on DERP. The supplied units each bind all IPv4 interfaces on port 443;
   they must run on separate hosts. This is service separation, not high availability.
3. Verified administrator access, provider traffic/billing limits and monitoring.
   Starting allocation: 1 vCPU, 1 GiB RAM and 10 GiB disk per VM, expanded for
   measured relay load. These are operator planning values, not provider quotes.
4. Existing headless server LAN administration and a physical phone with cellular
   service, for the controlled final activation/acceptance window.

No public host/account was fabricated or purchased. A GitHub source connector is
not a cloud/DNS account. The existing server/bridge/rendezvous repositories have no
configured remotes or infrastructure Actions workflows. No Actions secret values
were read. Public release distribution remains separate PROD P2 work.

## Topology and identity

```
phone -- OPAQUE pairing messages --> pairing.DOMAIN:443 (ephemeral mailbox)
phone <====== encrypted Tailcat direct path ======> private home Aura Server
phone <== encrypted fallback ==> relay.DOMAIN:443 <==> home Aura Server
                                                     -> loopback Navidrome
owner browser on home LAN --> SERVER_ID.server.DOMAIN:9443
```

Use an opaque 128-bit `SERVER_ID` (32 lowercase hex characters), assigned to the
installation hostname. It may refer to the existing installation ID, but is not
authorization or the logical Navidrome origin. No friendly name, account or public
IP becomes the cryptographic identity. Keep the exact old logical origin/download
namespace during infrastructure changes for the same adopted library.

The operator can own `server.DOMAIN` for future customers, so they need not purchase
individual domains. **P1 only prepares a personal deployment.** A scalable issuance
broker, installation authorization, quota and DNS lifecycle service is not already
implemented. Do not issue arbitrary server certificates based on an unauthenticated
server-id claim. Do not put a wildcard key or broad operator DNS credential on home
servers. A domain model is not a completed consumer issuance system.

Owner DNS must resolve the hostname to the correct private LAN address on that LAN.
Use managed LAN DNS/DHCP reservation; verify DNS-rebinding protection behavior rather
than globally disabling it. DNS-01 itself does not require a public A record for
the owner name. No public owner proxy, Navidrome exposure or router port forwarding
is required. Browser access to the owner page from arbitrary cellular networks is
not promised; remote pairing is opened by an authenticated owner in the supported
owner workflow, not by an unauthenticated rendezvous caller.

## Prepare, build and install

Copy `site.example.json` into a private operator directory and replace its dummy
domain/IPs. The supplied example is intentionally rejected. The renderer refuses
unknown fields, private public-service addresses, shared service IPs, invalid names,
Tailscale names, public owner addresses and existing output directories.

```
python3 infrastructure/prepare.py --config /private/site.json --output /private/p1-plan
```

Review DNS records and generated units. `owner/config-review.json` is a **partial
review input, not a replacement config**. `region.fresh-install.json` is for a new
installation only; it must not overwrite a restored identity. Read TRANSITION.md.

Build on the maintainer machine, not the home server/public VMs, from clean pinned
component sources using their existing scripts:

```
# in the qualified bridge repository
sh deployment/build-derp.sh
# in the qualified rendezvous repository
sh deployment/build.sh
```

Retain exact source revisions, Go 1.27.1, DERP's verified Aura Tailscale source
55d7fa798eed422c58486968bd2ecec0514915e2, build flags and SHA-256 for each binary.
Tailcat remains 7a50a1abd8bca63432afbcc5c04dd278c7029e31; OPAQUE remains v0.18.0.
DERP does not import the bridge/OPAQUE/Navidrome entry points; rendezvous is its
existing standard-library Go module. Do not infer an unqualified graph from an
old binary left in `bin/`: P1 rebuilt both from the clean current revisions.

Deliver verified prebuilt binaries through authenticated administrator access.
On each appropriate VM, install only its binary, root-owned mode 0755, under
`/opt/aura-infrastructure/releases/VERSION/`; select it through the root-owned
`/opt/aura-infrastructure/current` symlink. Parent paths are root-owned 0755.
Never place home-server state, private keys or Navidrome here. Record/check the
independently authenticated SHA-256 before running it; no GitHub publisher
authentication has been invented by this preparation.

After DNS-01 certificate issuance (TLS.md), install the matching generated unit
as `/etc/systemd/system/aura-derp.service` or `aura-rendezvous.service`, root 0644.
Install `prepare.py` and `renew.py` as root-owned 0644 files under
`/opt/aura-infrastructure/tools/`, and the role's renewal.json as root 0600 under
`/etc/aura-infrastructure/`. Then:

```
sudo systemd-analyze verify /etc/systemd/system/aura-derp.service
sudo systemctl daemon-reload
sudo systemctl enable --now aura-derp.service
# Use aura-rendezvous.service on the other VM.
```

systemd supplies private read-only credential snapshots to DynamicUser processes.
The only ambient capability is binding privileged port 443. Root filesystem is
read-only, home/devices protected, PIDs/FDs/CPU/memory bounded; no media state or
writeable application volume. No Docker runtime/image is required for this P1
operator path. The existing T11 container option remains separate and unchanged.
Do not claim its unavailable Docker-engine checks were newly executed by P1.

Public ingress must be direct TCP/TLS, preserving real source identity. Do not
front DERP with an HTTP CDN that breaks its upgraded stream. Do not add a proxy
that makes rendezvous trust arbitrary Forwarded/X-Forwarded-For headers. Public
IPv6 is deferred until an actual address, DNS AAAA, listeners and reachability are
tested together. Never publish an unreachable AAAA merely for apparent dual stack.

See OPERATIONS.md for health, ports, quotas and acceptance; TLS.md for renewal;
TRANSITION.md for preserved-server activation. Unit preparation does not claim a
domain was issued, a public endpoint exists or a phone worked over cellular.
