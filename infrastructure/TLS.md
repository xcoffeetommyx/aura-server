# DNS-01 certificates and renewal

Issue three independent exact-name certificates: relay.DOMAIN, pairing.DOMAIN,
and SERVER_ID.server.DOMAIN. The private owner key is generated on the home server;
relay/rendezvous keys stay on their respective hosts. No shared wildcard key.

Use a maintained Certbot DNS authenticator supported by the selected DNS provider.
**A provider has not been selected; DNS API access is an external prerequisite.**
Install its supported plugin through the host's reviewed package mechanism. Do not
download an unreviewed root shell installer or mix arbitrary plugin versions into
the qualified Go/application graph. Record the chosen ACME client/plugin versions
when actually deployed.

Prefer a delegated challenge zone per exact owner hostname with credentials that
can change only its TXT record. DNS-01 permits CNAME or NS delegation, but not all
provider plugins follow a CNAME when updating records. Verify the chosen plugin
against the actual delegation in the ACME staging environment. An RFC2136-capable
DNS operator can grant a unique TSIG key only the specific challenge TXT owner;
do not grant zone-wide update rights. Never place the operator's domain-wide API
token on a home server. Protect credentials root:root 0600 outside Git/images,
and restrict DNS API access at the provider where supported.

Each host registers its own ACME account and obtains its certificate using DNS-01;
this needs outbound HTTPS to the CA/DNS API and ordinary DNS resolution, not
inbound port 80 or a public owner/Navidrome web listener. Review account terms and
contact identity with the owner. Do not include passwords/tokens in command lines.
Use certificate name equal to the exact hostname so the hook's paths match.

Example command shape (replace the bracketed provider-specific option group from
that plugin's official documentation; it is not an executable generic plugin):

```
sudo certbot certonly [DNS AUTHENTICATOR AND PRIVATE CREDENTIAL-FILE OPTIONS] \
  --cert-name HOSTNAME -d HOSTNAME
```

First validate staging issuance, DNS cleanup, renewal and least-privilege denial of
an unrelated TXT name. A staging certificate must never be installed on the real
Aura owner service/Android trust store. Then obtain a production-chain certificate.
Validate the existing package against its exact ownerHost and keep owner capability
in the established fragment/header workflow, never a query parameter.

## Deploy hook

Configure a **per-lineage** deploy hook, not a global hook for unrelated certificates:

```
python3 /opt/aura-infrastructure/tools/renew.py --config /etc/aura-infrastructure/renewal.json
```

Certbot supplies RENEWED_LINEAGE. The root-owned private config names only role and
exact hostname. The hook rejects unrelated lineages, non-root/unsafe credentials,
malformed/mismatched key pairs, untrusted/expired/wrong-host certificates and less
than 14 days remaining. Its CLI uses the system trust store; no trust-all/private-CA
production switch is supplied. Tests inject a private CA only into the internal
verification function, using disposable generated fixtures.

For public services, restart reloads systemd credentials. For the existing owner
package, the hook stops an active service, copies the certificate pair as the
unprivileged service account into the existing private regular-file paths, validates
the package as that user, then starts only if it was previously active. A deliberately
stopped candidate stays stopped. No key/PSK/registry/logical origin is generated or
rewritten. Certificate renewal alone requires no client re-pairing.

The two existing owner files cannot be atomically renamed as one. The service is
stopped first; a crash/mismatched pair fails package validation. Previous TLS files
remain in `.owner-tls-before-renewal` on a failed operation. A stale directory is a
repair condition, not silently overwritten. Review it offline, restore only the
previous TLS pair if appropriate, validate and explicitly restart. Never restore
the authorization registry merely to undo a TLS renewal. Root filesystem actions
are limited to trusted config/Certbot inputs; service-owned path operations drop
root privileges, preventing path races from granting root file access.

After initial issuance, use the matching RENEWED_LINEAGE environment explicitly
for a first hook check, then configure Certbot's persisted per-lineage deploy hook.
Enable/inspect the supported Certbot renewal timer (typically twice daily with
jitter). A failed renewal leaves the old in-memory certificate running until expiry;
a failed owner install leaves the package safely stopped. Alert on either failure.
Check actual service TLS after renewal; a process-active flag alone is insufficient.
Certbot dry-run normally skips deploy hooks; running hooks with staging certificates
is expected to be rejected. Test the hook separately with the valid live lineage.

Alert at 30 days remaining, escalate at 14 and critical at 7. Rotate a compromised
DNS credential and revoke/reissue affected certificates; inspect DNS changes and
owner access. A CA/DNS compromise does not replace OPAQUE/device authorization, but
is a serious infrastructure incident. Back up ACME account/config and recovery
credentials securely; never back up rendezvous mailboxes as identity state.

Official references (reviewed during P1):

- [Let's Encrypt DNS-01 and challenge delegation](https://letsencrypt.org/docs/challenge-types/)
- [Certbot renewal and deploy hooks](https://eff-certbot.readthedocs.io/en/latest/using.html)

Public issuance, delegated DNS permissions and unattended renewal remain unexecuted
until the owner supplies the domain/provider access. Local certificate tests are not
production CA issuance evidence.
