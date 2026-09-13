# Aura Server distribution

Local T14 product/distribution repository. **Not published and not a production
release.** Component source stays in its existing repositories; this repository
owns the exact component lock, reproducible archive and verified delivery tools.

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
