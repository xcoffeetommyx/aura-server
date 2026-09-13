# Release assembly and provenance

The Aura operator owns release review and publication. The canonical product
repository is https://github.com/xcoffeetommyx/aura-server.

## First public prerelease

`v0.1.0-beta.1` distributes the **unchanged** physically qualified
`aura-server-p1b-candidate-1-linux-amd64.tar.gz`. The public tag is a distribution
version; the internal package version remains `p1b-candidate-1`. Do not rename
the internal manifest or rebuild these binaries merely to change a release label.
`releases/v0.1.0-beta.1.json` records the exact archive and individual binary hashes.
The bridge was built with Go 1.27.1; the canonical Navidrome binary was built with
Go 1.26.0 and CGO/FTS5. The package's Go field identifies the bridge toolchain.
Navidrome has no embedded VCS revision: its source attribution relies on the
qualified producer record, not a cryptographic build attestation.

The release includes the archive, checksums, component/provenance manifests and
supplemental notices/source inventory. Download the supplemental material too;
the original package's historical notices are retained byte-for-byte.

The GitHub workflow tests the distribution/infrastructure tooling and can verify
the fixed published asset. It does **not** build a substitute CGO binary or claim
to attest the original local build. Future releases must qualify their actual
producer environment before replacing the approved bytes.

## Producing a subsequent candidate

1. Check out exact clean component revisions in `components.json`.
2. Build the canonical Navidrome binary, including UI and required CGO/FTS5 tags,
   in the previously qualified Linux toolchain. Record commands, compiler/native
   library versions, source revision and binary hash. The bridge package builder
   checks source cleanliness/ELF architecture; it does not independently attest
   an arbitrary supplied Navidrome binary's origin.
3. Run the existing bridge `packaging/build-bundle.py` with that executable,
   exact source, new version and target architecture. Its source verifier imports
   the checksummed Aura Tailscale Git bundle onto the exact official base. No
   mutable third-party PR branch is consulted.
4. Run the native/bridge/GSO/package and affected Android qualification recorded
   in T14. Audit the bundle for source/test/private-state contamination.
5. Create the deterministic delivery archive:

```sh
python3 release.py pack --bundle /build/qualified-bundle --version VERSION \
  --arch amd64 --output build/aura-server-VERSION-linux-amd64.tar.gz
```

The archive uses sorted entries, normalized ownership/modes and zero tar/gzip
timestamps. Repeating packing of identical qualified bundle bytes produces the
same hash. This is archive reproducibility; it is not a claim that independently
rebuilding all CGO/UI dependencies has already produced identical binary bytes.

`manifest.json` identifies version, architecture, bridge/Navidrome/Tailcat/
Tailscale revisions, Go version and every shipped file hash. `components.json`
must be reviewed and deliberately updated for future component qualifications.
Artifacts contain no server state. The source SHA identifies the software, never
a user's logical server or a device credential.

## Publisher authentication and GitHub

P2 authorizes public server-component publication. This does not authorize making
the existing private Android repository public. Restrict repository/release write
access to the operator and review exact commits and assets before upload.

Recommended release authentication is GitHub OIDC/Sigstore artifact attestation
bound to the exact approved repository/workflow/source revision, with consumer
verification before the package executes. No locally invented production signing
key is generated. This local tool does **not** claim an attestation it has not
received or verified. The first release uses HTTPS GitHub delivery and a checksum
obtained from the reviewed exact source commit or another authenticated operator
channel. A checksum supplied by the same compromised publisher cannot defend
against that publisher. Production signing/build attestation remains a gate.

GitHub documentation: [artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations),
[release asset downloads](https://docs.github.com/en/rest/releases/assets),
[offline attestation verification](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/verify-attestations-offline).
The downloader allows bounded HTTPS redirects to the original host and, for
github.com releases, release-assets.githubusercontent.com. It forwards no auth
headers and supports public assets only. Private GitHub token handling is not
silently added. Loopback HTTP is a separate explicit controlled-test flag.

## Corresponding source and notices

The release record maps exact revisions to these component repositories:

- https://github.com/xcoffeetommyx/aura-tailcat-bridge (bridge, package builder,
  systemd/install tooling, dependency bundle and lock)
- https://github.com/xcoffeetommyx/aura-navidrome (GPL Navidrome fork, UI source,
  module/package locks and build scripts)
- https://github.com/xcoffeetommyx/aura-rendezvous (separate pairing infrastructure)
- https://github.com/xcoffeetommyx/aura-tailscale (qualified Aura fork, original
  upstream author history and BSD notices)
- https://github.com/tailscale/tailcat (exact official Tailcat source)

Use the locked source commits, not a moving default branch, to reconstruct the
release. The Navidrome component README may advance independently of its frozen
production source revision. The Aura fork is not official Tailscale and no
Tailscale sponsorship is claimed. Supplemental license/source inventory does not
constitute an independent legal opinion; final licensing review remains a gate.
