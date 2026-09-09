# Release assembly and provenance

The Aura operator owns release review and publication. No repository has been
created remotely and no release is published by this local project.

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

Public-release publication needs separate owner authorization, a chosen GitHub
repository, protected release permissions and reviewed corresponding source.
Do not publish existing private repositories automatically.

Recommended release authentication is GitHub OIDC/Sigstore artifact attestation
bound to the exact approved repository/workflow/source revision, with consumer
verification before the package executes. No locally invented production signing
key is generated. This local tool does **not** claim an attestation it has not
received or verified. The expected archive hash must arrive through an
authenticated operator channel until that publication/verification exists.

GitHub documentation: [artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations),
[release asset downloads](https://docs.github.com/en/rest/releases/assets),
[offline attestation verification](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/verify-attestations-offline).
The downloader allows bounded HTTPS redirects to the original host and, for
github.com releases, release-assets.githubusercontent.com. It forwards no auth
headers and supports public assets only. Private GitHub token handling is not
silently added. Loopback HTTP is a separate explicit controlled-test flag.

## Corresponding source and notices

Navidrome GPL source: https://github.com/xcoffeetommyx/aura-navidrome at the exact
locked SHA. Tailcat official source: https://github.com/tailscale/tailcat at its
locked SHA. Aura Tailscale source is reproducible from the committed bridge
dependency bundle/lock plus the exact official base. Its original BSD notices
and upstream author history are retained. Bridge and Aura Tailscale repositories
currently exist locally; do not imply their prospective GitHub URLs are published.

Before distribution, provide the exact bridge source/build material and full
required corresponding Navidrome source, dependency/license inventory and notices.
An upstream URL or a binary ELF check alone is not a complete corresponding-source
or legal packaging review. No Tailscale sponsorship is claimed. The package's
historical SOURCE.txt bridge URL is prospective; publication remains blocked until
the referenced source is actually supplied through an authorized channel.
