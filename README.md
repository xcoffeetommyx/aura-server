# Aura Server

Self-host your Aura music server. Music, accounts and the Navidrome database stay
on your own machine. Start with the verified prebuilt
[v0.1.0-beta.1 release](https://github.com/xcoffeetommyx/aura-server/releases/tag/v0.1.0-beta.1)
and [installation guide](docs/INSTALL.md), not component source builds.

This is an initial **beta for an operator-managed deployment**, not universal
plug-and-play hosting. The qualified no-domain topology requires reachable public
IPv4 and explicit router port forwarding. Dynamic public-IP changes require
operator certificate/endpoint repair and explicit re-pairing. No purchased domain,
VPS or Aura cloud account is required. CGNAT without usable inbound connectivity
cannot host these public endpoints. See [requirements](infrastructure/SELF-HOSTED.md).

Component source stays in separate repositories. This repository owns the exact
component lock, reproducible archive and verified delivery tools. The first public
release distributes the unchanged physically qualified P1B archive; its internal
package version remains p1b-candidate-1. No old candidate is retroactively called
a previous public release.

The supported server remains the T12 native Ubuntu 26.04/systemd package: separate
Aura bridge/owner and canonical Navidrome processes, loopback-only backend,
private persistent state, fixed Tailcat service, explicit approval/revocation.
DERP and rendezvous retain separate process/trust boundaries. The P1B personal
deployment co-locates them on the home laptop using its reachable public IPv4 and
trusted IP certificate. No purchased domain, VPS, consumer Go, Git/source checkout,
Docker or Tailscale requirement for Aura operation.

* [Installation](docs/INSTALL.md)
* [Upgrade and recovery](docs/UPGRADE.md)
* [Existing Navidrome migration](docs/MIGRATION.md)
* [Release production, provenance and trust](docs/RELEASE.md)
* [Narrow distribution threat model](docs/SECURITY.md)
* [P1B self-hosted infrastructure](infrastructure/SELF-HOSTED.md) — public IPv4,
  IP certificate renewal, isolated DERP/rendezvous and operational recovery
* [Historical P1 preparation](infrastructure/README.md) — superseded domain/two-host pilot

`components.json` fixes the bridge, Navidrome, Tailcat, Aura Tailscale and Go
revisions. `release.py` rejects packages with a different graph. It wraps the
existing package; it never copies or rewrites authorization state, pairing,
Navidrome configuration or Android data.

Maintainer validation: `python3 -m unittest -v test_release`.
The generated artifacts belong in ignored `build/`, never Git. Release operator:
Aura project owner. No external repository, release, certificate or signing
identity is created by these tools.

The release currently provides Linux amd64. ARM64 server execution, physical
16-KiB Android, Cast/Auto, independent security/legal review and production signing
remain explicit qualifications. GitHub Actions checks tooling and optional asset
integrity; it does not rebuild the locally qualified CGO/Navidrome executable or
claim to attest a build it did not perform.

Component source: [bridge/DERP](https://github.com/xcoffeetommyx/aura-tailcat-bridge),
[rendezvous](https://github.com/xcoffeetommyx/aura-rendezvous),
[Aura Navidrome fork](https://github.com/xcoffeetommyx/aura-navidrome),
[Aura Tailscale fork](https://github.com/xcoffeetommyx/aura-tailscale).
Exact revisions and source/license boundaries are in [release provenance](docs/RELEASE.md).
