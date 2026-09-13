# Distribution boundary

Threats: modified download, wrong build/architecture, archive traversal/link or
resource attack, stale trust-state rollback, forged publisher identity and secret
contamination. This addition cannot authorize a Tailcat peer or modify pairing.

Controls: out-of-band authenticated expected SHA-256; normal HTTPS certificate
verification; three bounded HTTPS redirects within permitted delivery hosts;
no ambient proxy or forwarded authorization; 20-second socket timeout and bounded
download duration; 512-MiB compressed / 1-GiB expanded / 256-file budgets; no
links/sparse/special/duplicate members; private staging; exact inventory/hash,
version/revision and ELF checks before publishing a new extraction directory.
The tools never execute downloaded code, elevate privileges, overwrite existing
destinations, open archives of live server state or print remote response bodies.

Use a private administrator-owned working directory; an attacker with write
access to that directory can replace files after verification. Root or an owner
who replaces the verifier and its trusted component lock is outside this boundary.
The installer remains a separate explicit action after review. A malicious archive
with a mismatching authenticated hash is rejected before any decompression.

Checksums do not authenticate an attacker-controlled release record. Verify the
publisher is `xcoffeetommyx/aura-server` and obtain the expected hash from a reviewed
exact commit or independent authenticated operator channel. Initial publication
uses GitHub HTTPS and exact source/checksum records; signed build provenance is
not claimed and remains a gate. No private release key is stored or generated. No arbitrary historical
state rollback is declared safe. Restore uses T12 offline quarantine and fresh
approval, independently of software delivery.
