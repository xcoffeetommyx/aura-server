# Adopt an existing headless Navidrome library

Do not assume the development fixture is the user's existing library. Record
the actual host/OS/architecture, binary version, service configuration, data
directory, music path and logical origin privately. Do not print passwords,
JWTs, encryption keys or owner capabilities.

1. First qualify the candidate package on an owned development installation.
2. Preserve the working server and its administrative access. Stop Navidrome
   only for a coherent database/configuration backup; restart the original if
   migration cannot proceed. Back up its exact password-encryption configuration,
   database/users/playlists and service configuration. Back up music independently.
3. Verify the backup inventory/hashes and open a separate database copy for
   integrity/schema review. Preserve the original source directory unchanged.
4. Check T12 adoption compatibility: canonical Aura Navidrome database, Ubuntu
   26.04/systemd and reviewed supported settings. Other versions/settings require
   explicit compatibility investigation; never guess or drop them silently.
5. Retain the exact historical logical origin when adopting that same library.
   Transport moving from Tailscale to Tailcat does not change download identity.
   A different library requires explicit client selection, not rewritten cache keys.
6. Install using the verified bundle's documented `--adopt-data` and
   `--adopt-config` options. The installer copies source data and leaves music
   read-only; skip `setup-account` and authenticate with existing users.
7. Verify loopback-only Navidrome, protected owner controls, explicit pairing,
   authentication, library/playlist continuity, streaming, download/offline,
   revocation and physical host reboot before retiring any legacy route.

Supported imported application settings are documented by the exact pinned
package README. The original PasswordEncryptionKey must be retained. No transport
state is stored in Navidrome's database. The package's restore/quarantine policy
is separate from initial Navidrome adoption.

Rollback: stop the new service, preserve its new state separately, restore the
original service configuration and verified original application data at the
original paths, then start the original binary. Never run two Navidrome writers
against one database. Do not restore stale Aura authorization online. Do not
uninstall Tailscale if unrelated administration/services need it.

These instructions are a procedure, not evidence that the user's laptop was
migrated. The Android T14 results record actual execution and any blockers.
