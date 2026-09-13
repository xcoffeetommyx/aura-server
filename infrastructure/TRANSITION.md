# Infrastructure transition and preserved identity

P1's domain/two-host preparation is historical. P1B qualified the personal
single-home-server public IPv4 layout in [SELF-HOSTED.md](SELF-HOSTED.md).
The original Docker Navidrome is stopped, preserved for rollback. The native
p1b-candidate-1 deployment is enabled. Do not start both database writers.

## Database and authorization continuity

Before activation, compare the live original database with its prior coherent
snapshot. P1B found changes, created another protected backup, and refreshed the
adopted database through the established procedure. Users, playlists, media and
the exact logical origin were preserved. Never replace the only backup.

Preserve server private key/PSK, installation ID, owner capability, active keys,
tombstones, database/music/configuration and logical origin. Infrastructure IP is
not library identity. Ordinary certificate renewal does not require re-pairing.

## Durable relay descriptors

Editing region.json alone cannot migrate an existing identity or Android profile.
Bridge commit 4abd8e8cd33853980826e20488c7f915fa971f7e supplies the qualified
offline reconfigure-ip-relay operation. Use its CLI help and the supported
package lifecycle: stop the runtime, back up protected state, provide a validated
public-IP region, perform the locked atomic transition, validate and restart.
It preserves identity/registry fields except relay metadata and rejects a running
instance, missing state or unsafe region. Never hand-edit phone secrets.

Deliver the changed descriptor through explicit owner-approved OPAQUE pairing
with a fresh client key. Android commit 310f8ee permits changed relay metadata
only after that verified flow matches the existing server fingerprint. Ordinary
restore still rejects changed descriptors. Atomic replacement checks the previous
key/descriptor to reject stale writes. Revoke the superseded key explicitly and
retain its tombstone; do not silently reapprove it.

P1B completed this transition on the S23+ over real cellular, preserving the
logical origin/account/download namespace. The old S23+ key was revoked. The
A14 was unplugged with its existing state preserved and has not been moved to
the new relay descriptor; it needs explicit pairing again when next used.

## Personal endpoint and address change

The ordinary signed Android build uses the existing operator parameter
-PauraPairingService=https://PUBLIC_IP:8444. It contains no private CA or secret.
The owner enters a pairing code, not an IP, in the normal phone flow. This is a
personal configured deployment, not a global six-digit locator or universal
discovery service. An arbitrary home server cannot be found from six digits alone.

The root-owned WAN observer quarantines a confirmed changed IP. Do not clear its
repair marker until the operator independently verifies the new address, issues
its trusted certificate, updates expected IP/firewall/local routing/owner identity,
and performs the offline relay transition. Explicitly re-pair affected phones;
they may need to return to LAN. Address stability over months is unmeasured.
No domain, VPS, cloud directory or automatic insecure descriptor refresh is used.

The owner TLS IP/port is separate from the logical Navidrome origin. Renewal
validates chain, IP SAN, expiry and key match before installing private material.
Owner management stays LAN-only behind the host guard; media uses the authenticated
Tailcat bridge, with Navidrome bound to loopback.

## Recovery

Preserve T14 and P1B backup roots. Software rollback must not restore stale
authorization state. Historical state restoration starts offline and requires
approval review/re-pairing where trust is uncertain. Restore original Docker
Navidrome only after stopping native Aura Server; preserve the matching database,
configuration and encryption material. No backup covers writes made afterward.

The old Tailscale configuration remains for rollback/unrelated administration.
The new phone media path was demonstrated with Wi-Fi/VPN/Tailscale disabled.
PROD P2 publication remains separately authorized; no source or release was pushed.
