# First public release delivery acceptance

September 13, 2026, America/Chicago. **PROD P2: PASS WITH GATES.**

The public `v0.1.0-beta.1` release contains the unchanged P1B-qualified amd64
archive, SHA-256 `8e248491de55bff47dcfb00d4af59ceb2702772040491588132fd489f1865e72`.
Its internal package version remains `p1b-candidate-1`. All eight release asset
digests were compared with GitHub's API, and all eight exact source references
were resolved anonymously, including the embedded TagLib source relationship.

On the actual Ubuntu 26.04 headless server, the documented verifier and archive
were downloaded from GitHub over HTTPS. The expected checksum came separately
from the reviewed release record. Strict verification passed; modified bytes and
wrong-version metadata were rejected before installation. No source checkout,
compiler, LAN binary transfer or flash drive was required.

After a protected coherent backup, the supported same-version `upgrade --bundle`
path passed. Identity/PSK/device registry, owner capability, configuration,
infrastructure files/drop-ins, database counts and the database bytes immediately
after restart were unchanged. SQLite integrity was `ok`. Backup plus upgrade took
16.369 seconds in this one acceptance run; this is not an availability SLA.
Systemd remains enabled, services healthy, and Navidrome bound to loopback only.

The physical Galaxy S23+ refreshed its authenticated library, showed artwork,
streamed an uncached track and played an existing completed download with Wi-Fi
and mobile data disabled. Its active network agents showed no VPN transport.
Existing saved Aura pairing remained connected; no re-pair or account reset was
performed. Networking was restored and playback paused afterward. No personal
media, screenshots, private addresses or operator credentials accompany this record.

Validation: 9 release/archive tests; 45 infrastructure tests (44 as ordinary user,
the root-only privilege-drop test separately). GitHub Ubuntu 24.04 initially lacked
the newer OpenSSL `x509` date-setting flags used by one fixture. Commit
`40123434ceeb2889d670ecc6974a4a9b26548157` uses compatible `openssl ca` fixture
generation and retains the expired-certificate assertion. No runtime/certificate
implementation changed. The release tag remains immutable at its original
publication commit; this test-only correction is on `main`.

[The corrected CI run](https://github.com/xcoffeetommyx/aura-server/actions/runs/34771517942)
passed all tests and downloaded/verified the exact published archive. CI does not
claim to have produced the locally qualified binary.

Repository history/working-tree and release-text scans found no owner secrets to
publish. Upstream public test fixtures and attribution were preserved. Three home
address literals in private qualification test fixtures were anonymized before
the new public tooling branch was published; runtime bytes were unchanged.

Production signing/build attestation and final independent licensing/security
review remain gates. Unrelated physical ARM64 server, 16-KiB Android and Cast/Auto
qualifications are not promoted by publication. The operational legacy deployment
and Tailscale administration/rollback configuration remain preserved. P3 may be
planned separately; no operational retirement was performed here.
