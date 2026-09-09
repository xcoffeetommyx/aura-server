# Upgrade, backup, rollback and reinstall

Fetch and verify a new release into a new directory using INSTALL.md. Confirm
the supported state/database format before upgrading or rolling back binaries.
Use the packaged lifecycle tool; do not copy an old registry into live state.

```sh
sudo python3 /opt/aura-server/current/aura-package.py backup /private/backups/pre-upgrade.tar.gz
# Coherent backup intentionally leaves the service stopped.
sudo python3 verified-release/aura-package.py upgrade --bundle verified-release
sudo python3 verified-release/aura-package.py status
```

The installer stages immutable software and atomically selects the release.
Persistent identity, PSK, approvals/tombstones, owner capability, Navidrome data
and music are outside software releases. A binary rollback uses the same upgrade
command with a compatible prior release and does not roll back state.

Backups contain secrets. Store encrypted, offline and owner-accessible; the
package's 0600 archive itself is not encryption. Restore authorization-sensitive
state offline. Historical approvals may be stale, even if every checksum matches.

```sh
sudo python3 verified-release/aura-package.py restore /private/backups/pre-upgrade.tar.gz
# RESTORE-QUARANTINE blocks admission and startup.
sudo python3 verified-release/aura-package.py repair-restored --revoke-all-historical-devices
sudo python3 verified-release/aura-package.py owner-bookmark /private/setup/new-owner-bookmark.txt
sudo python3 verified-release/aura-package.py start
```

This rotates owner access and requires explicit fresh device pairing. It is not
cryptographic rollback detection. Keep the original backup and the package's
retained previous state until recovery is independently verified.

`uninstall` removes software/service only. State, database, account, backups and
music remain. `reinstall --bundle verified-release` validates retained state
before restart. No distribution command destroys a music directory or silently
regenerates damaged security state.
