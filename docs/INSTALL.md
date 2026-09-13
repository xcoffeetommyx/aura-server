# Install a verified prebuilt Aura Server

Supported host: Ubuntu 26.04, systemd, Linux amd64 or arm64, Python 3.11+,
CA certificates and ffmpeg. ARM64 build support does not establish physical
ARM64 server execution. This package is administered once, then operated
headlessly using its protected owner page.

Before downloading, obtain the release tool, `components.json`, exact version,
architecture and SHA-256 from an **authenticated release record**. A checksum
downloaded from the same compromised source is not publisher authentication.
The public repository is https://github.com/xcoffeetommyx/aura-server. The first
release is v0.1.0-beta.1; it intentionally retains the unchanged qualified internal
package version p1b-candidate-1. Production signing remains a gate. Review the
fixed release record and expected checksum through your authenticated GitHub
session or another trusted operator channel before fetching the binary.

```sh
curl --fail --proto '=https' --tlsv1.2 -o release.py https://raw.githubusercontent.com/xcoffeetommyx/aura-server/76cdcaf7459d64f700509abb4643951e1027615d/release.py
curl --fail --proto '=https' --tlsv1.2 -o components.json https://raw.githubusercontent.com/xcoffeetommyx/aura-server/76cdcaf7459d64f700509abb4643951e1027615d/components.json
python3 release.py fetch --url https://github.com/xcoffeetommyx/aura-server/releases/download/v0.1.0-beta.1/aura-server-p1b-candidate-1-linux-amd64.tar.gz \
  --sha256 8e248491de55bff47dcfb00d4af59ceb2702772040491588132fd489f1865e72 --output aura-server.tar.gz
python3 release.py verify --archive aura-server.tar.gz \
  --sha256 8e248491de55bff47dcfb00d4af59ceb2702772040491588132fd489f1865e72 \
  --version p1b-candidate-1 --arch amd64 --destination verified-release
```

Run in a new private directory (for example, umask 077 before creating it).
These URLs identify the first release's qualified verifier/lock and exact archive.
Also obtain the release's corresponding-source and third-party-notices assets;
they accompany binary distribution and must remain available to recipients.
Verification checks
the archive before extraction, exact version, component lock, internal inventory,
every file hash and both ELF architectures. Extraction refuses existing output
and unsafe entries. It executes nothing. Run as an ordinary user in a private
directory; use root only for the existing installer after verification.

Prepare the administrator inputs described by `verified-release/README.md`:
read-only music directory, exact logical library origin, private LAN pairing
address, trusted owner HTTPS certificate, operated DERP region and optional
rendezvous service. Do not replace certificates with trust-all settings or use
a universal owner capability. No private input belongs in the release archive.

```sh
sudo python3 verified-release/aura-package.py install --bundle verified-release \
  --config /private/setup/config.json --region /private/setup/region.json \
  --certificate /private/setup/owner.crt --key /private/setup/owner.key
sudo python3 verified-release/aura-package.py setup-account
sudo python3 verified-release/aura-package.py owner-bookmark /private/setup/owner-bookmark.txt
sudo python3 verified-release/aura-package.py start
```

For existing libraries follow MIGRATION.md; do not create/reset the old account.
Deliver the unique owner bookmark privately. Normal owner operation uses HTTPS
to open pairing, then Android discovers/selects the server and enters the code.
Navidrome authentication remains separate. Site/certificate provisioning and
operator infrastructure remain explicit responsibilities. For the no-domain home
deployment, follow [SELF-HOSTED.md](../infrastructure/SELF-HOSTED.md). The media
package does not overwrite an existing P1B infrastructure configuration.
