"""Disposable certificate fixtures; no CA account, issuance or production trust change."""
from pathlib import Path
import subprocess
import tempfile
import unittest

import renew


class IPCertificateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="aura-p1b-ip-tls-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.key = self.root / "key.pem"
        subprocess.run(["openssl", "genrsa", "-out", str(self.key), "2048"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.key.chmod(0o600)

    def certificate(self, address, days=6, kind="IP"):
        cert = self.root / "cert.pem"
        subprocess.run(["openssl", "req", "-x509", "-key", str(self.key), "-days", str(days),
                        "-subj", "/CN=owned fixture", "-addext", f"subjectAltName={kind}:{address}",
                        "-out", str(cert)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return cert

    def test_ipv4_six_day_ip_san(self):
        cert = self.certificate("8.8.8.8")
        renew.validate_pair(cert, self.key, "8.8.8.8", ca_file=cert, ip_identifier=True)

    def test_ipv6_six_day_ip_san_and_canonicalization(self):
        cert = self.certificate("2001:4860:4860::8888")
        renew.validate_pair(cert, self.key, "2001:4860:4860:0:0:0:0:8888", ca_file=cert, ip_identifier=True)

    def test_wrong_ip_rejected(self):
        cert = self.certificate("8.8.8.8")
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(cert, self.key, "1.1.1.1", ca_file=cert, ip_identifier=True)

    def test_dns_san_that_looks_like_ip_is_not_ip_identity(self):
        cert = self.certificate("8.8.8.8", kind="DNS")
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(cert, self.key, "8.8.8.8", ca_file=cert, ip_identifier=True)

    def test_less_than_two_days_rejected(self):
        cert = self.certificate("8.8.8.8", days=1)
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(cert, self.key, "8.8.8.8", ca_file=cert, ip_identifier=True)

    def test_untrusted_chain_rejected(self):
        cert = self.certificate("8.8.8.8")
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(cert, self.key, "8.8.8.8", ip_identifier=True)

    def test_nonpublic_or_ambiguous_identifiers_rejected(self):
        for value in ("127.0.0.1", "192.168.1.1", "100.64.0.1", "::1", "fe80::1", "fd00::1",
                      "ff02::1", "::ffff:8.8.8.8", "2001:4860::1%eth0", "[2001:4860::1]", "8.8.8.8:443"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                renew.public_ip(value)


if __name__ == "__main__":
    unittest.main()
