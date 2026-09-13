# Preserved T14 candidate: infrastructure transition boundary

The original Docker Navidrome is active; the native candidate is stopped/disabled.
Do not restart it with the removed temporary relay. T14's verified backups remain
authoritative recovery material. P1 preparation did not acquire new SSH access,
touch either database, alter either phone, or replace trust state.

## Required inputs and continuity checks

Obtain actual owner DNS/certificate, public relay health and rendezvous endpoint
before mutation. Compare any new source-database activity with the stopped candidate.
Only if it changed is another coherent refresh needed; do not replay migration
solely to reproduce T14. Never run two writers on one database.

Preserve exact logical origin, database/music/configuration, server private key/PSK,
installation ID, owner capability, approved keys and tombstones except explicit
owner-directed revocations/enrollments. Record non-secret equality results privately;
never print the raw identity document.

Owner hostname/certificate changes are separate from relay bootstrap. Update only
ownerAddress/ownerHost and configured rendezvous in the package config, keeping
the complete existing config and exact logicalOrigin. Install the validated
certificate pair under the existing private-file contract, run the package check
and health against the new exact hostname, then configure renewal. Normal renewal
with the same name needs no re-pairing or cache change.

## Relay descriptors are durable, not a live global map

Pinned source: `internal/tailcatadapter/identity.go` stores Relay inside Identity;
`serverpackage.Initialize` reads region.json only for initial identity creation.
Every Android encrypted profile has its own authenticated descriptor/bootstrap.
Therefore **editing region.json alone does not migrate an existing bridge/client**.
The old descriptor also carries the old explicit address/hostname/port; a new
domain's DNS cannot silently repair it. Do not replace Identity with a newly
generated one or hand-edit secrets as a normal installation step.

The one-time switch requires a reviewed offline adapter operation that changes
only validated relay metadata while preserving the exact server key/PSK/registry,
plus explicit delivery of a new authenticated descriptor to each phone. The current
package does not expose a general relay-migration command. **This operation remains
to be implemented/qualified against the actual selected endpoints before activation;
P1 preparation does not pretend it already happened.** It is a narrow infrastructure
configuration task, not permission to redesign pairing or trust.

The existing owner-approved Pair this device again flow can supply a fresh descriptor
with a fresh client key. Revoke the exact superseded key through the owner workflow;
retain its tombstone. Verify the unchanged server fingerprint and logical library,
preserved local downloads and survivor access. Do not make certificate renewal
trigger this one-time relay transition, and do not silently reapprove revoked keys.

Android already supports the operator endpoint through Gradle
`-PauraPairingService=https://pairing.DOMAIN`; server configuration has `rendezvous`.
The T14 APK has no permanent endpoint configured. Set the existing build parameter
once the actual hostname is known, build an ordinary signed in-place upgrade, and
run focused remote-enrollment validation. No app protocol or hardcoded personal
server name is needed. A coordinator cannot supply an arbitrary backend target.

After these scoped operations, execute OPERATIONS.md's real cellular, relay-failure
and rendezvous-independence matrix. Until then leave the original server/backup path
intact and classify P1 BLOCKED. Temporary test relays are not permanent substitutes.
