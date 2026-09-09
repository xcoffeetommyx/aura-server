# Install a verified prebuilt Aura Server

Supported host: Ubuntu 26.04, systemd, Linux amd64 or arm64, Python 3.11+,
CA certificates and ffmpeg. ARM64 build support does not establish physical
ARM64 server execution. This package is administered once, then operated
headlessly using its protected owner page.

Before downloading, obtain the release tool, `components.json`, exact version,
architecture and SHA-256 from an **authenticated release record**. A checksum
downloaded from the same compromised source is not publisher authentication.
No public Aura Server repository or production signature is claimed yet.

```sh
python3 release.py fetch --url https://github.com/OWNER/REPOSITORY/releases/download/VERSION/ARTIFACT.tar.gz \
  --sha256 TRUSTED_SHA256 --output ARTIFACT.tar.gz
python3 release.py verify --archive ARTIFACT.tar.gz --sha256 TRUSTED_SHA256 \
  --version VERSION --arch amd64 --destination verified-release
```

These are placeholders, not working release URLs or hashes. Verification checks
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
final public release publication remain explicit operator responsibilities.
