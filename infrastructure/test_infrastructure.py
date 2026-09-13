import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import prepare
import renew


class PreparationTests(unittest.TestCase):
    def config(self):
        # Inert renderer-only inputs: no DNS or network operation occurs.
        return dict(version=1, domain="operator.example.org", serverId="1" * 32,
                    derpIPv4="8.8.8.8", rendezvousIPv4="1.1.1.1", ownerLANIPv4="192.168.1.10", regionId=9001)

    def test_fixed_services_and_identity_separation(self):
        files = prepare.render(self.config())
        self.assertEqual(len(files), 9)
        region = json.loads(files["region.fresh-install.json"])
        self.assertEqual(len(region["Nodes"]), 1)
        self.assertNotIn("IPv4", region["Nodes"][0])
        self.assertNotIn("InsecureForTests", region["Nodes"][0])
        review = json.loads(files["owner/config-review.json"])
        self.assertNotIn("logicalOrigin", review)
        self.assertNotIn("privateKey", "".join(files.values()))
        self.assertNotIn("navidrome", files["derp/aura-derp.service"])

    def test_constraints_and_no_proxy(self):
        files = prepare.render(self.config())
        for role in ("derp", "rendezvous"):
            text = files[f"{role}/aura-{role}.service"]
            for expected in ("DynamicUser=yes", "ProtectSystem=strict", "LoadCredential=tls.key:", "MemoryMax=", "LimitNOFILE=256", "Restart=on-failure"):
                self.assertIn(expected, text)
            self.assertNotIn("--privileged", text)
        self.assertIn("-admin 127.0.0.1:4789", files["rendezvous/aura-rendezvous.service"])

    def test_invalid_configuration_rejected(self):
        variants = [{"domain": x} for x in ("example.invalid", "a.ts.net", "x\nExecStart=bad", "127.0.0.1", "https://example.org", "*.example.org")]
        variants += [{"derpIPv4": "192.168.1.1"}, {"ownerLANIPv4": "8.8.8.8"}, {"regionId": True}, {"rendezvousIPv4": "8.8.8.8"}, {"token": "not-a-real-token"}]
        for variant in variants:
            with self.subTest(variant=variant):
                value = self.config(); value.update(variant)
                with self.assertRaises(ValueError): prepare.render(value)

    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "prepared"
            prepare.write(self.config(), out)
            before = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
            with self.assertRaises(FileExistsError): prepare.write(self.config(), out)
            self.assertTrue(all(p.read_bytes() == data for p, data in before.items()))


@unittest.skipUnless(shutil.which("openssl"), "Requires an owned OpenSSL fixture")
class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="aura-p1-cert-tests-")
        cls.root = Path(cls.temp.name)
        cls.cert = cls.root / "cert.pem"; cls.key = cls.root / "key.pem"
        cls.host = "owner.operator.example.org"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30",
                        "-subj", "/CN=" + cls.host, "-addext", "subjectAltName=DNS:" + cls.host,
                        "-keyout", str(cls.key), "-out", str(cls.cert)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.key.chmod(0o600)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_valid_exact_host_and_pair(self):
        renew.validate_pair(self.cert, self.key, self.host, ca_file=self.cert)

    def test_wrong_host_rejected(self):
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(self.cert, self.key, "wrong.operator.example.org", ca_file=self.cert)

    def test_untrusted_chain_rejected(self):
        with self.assertRaises(subprocess.CalledProcessError):
            renew.validate_pair(self.cert, self.key, self.host)

    def test_malformed_key_rejected_before_install(self):
        bad = self.root / "bad.key"; bad.write_text("not a private key")
        with self.assertRaises(Exception): renew.validate_pair(self.cert, bad, self.host, ca_file=self.cert)

    def test_short_lifetime_rejected(self):
        short = self.root / "short.pem"
        subprocess.run(["openssl", "req", "-x509", "-key", str(self.key), "-days", "1", "-subj", "/CN=" + self.host,
                        "-addext", "subjectAltName=DNS:" + self.host, "-out", str(short)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.assertRaises(subprocess.CalledProcessError): renew.validate_pair(short, self.key, self.host, ca_file=short)

    def test_expired_certificate_rejected(self):
        expired = self.root / "expired.pem"
        subprocess.run(["openssl", "x509", "-in", str(self.cert), "-signkey", str(self.key),
                        "-not_before", "20200101000000Z", "-not_after", "20200102000000Z", "-out", str(expired)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.assertRaises(subprocess.CalledProcessError): renew.validate_pair(expired, self.key, self.host, ca_file=expired)

    def test_different_private_key_rejected(self):
        other = self.root / "other.key"
        subprocess.run(["openssl", "genrsa", "-out", str(other), "2048"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.assertRaises(Exception): renew.validate_pair(self.cert, other, self.host, ca_file=self.cert)

    @unittest.skipUnless(hasattr(os, "geteuid") and os.geteuid() == 0, "Root-only privilege-drop regression")
    def test_owner_file_operation_really_drops_root(self):
        import pwd
        user = pwd.getpwnam("nobody")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); os.chown(root, user.pw_uid, user.pw_gid)
            proof = root / "uid"
            renew.as_owner(user.pw_uid, user.pw_gid, lambda: proof.write_text(str(os.geteuid())))
            self.assertEqual(proof.read_text(), str(user.pw_uid))

    @unittest.skipUnless(hasattr(os, "fork"), "Linux owner filesystem contract")
    def test_stopped_owner_stays_stopped_and_identity_unchanged(self):
        self.owner_case(False)

    @unittest.skipUnless(hasattr(os, "fork"), "Linux owner filesystem contract")
    def test_active_owner_stop_check_start(self):
        self.owner_case(True)

    def owner_case(self, active):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); root.chmod(0o700)
            for name, data in (("owner.crt", b"previous certificate"), ("owner.key", b"previous key"), ("identity.json", b"unchanged trust")):
                (root / name).write_bytes(data); (root / name).chmod(0o600)
            commands = []
            renew.owner_install(self.cert, self.key, root, os.getuid(), os.getgid(), active, commands.append)
            self.assertEqual((root / "identity.json").read_bytes(), b"unchanged trust")
            self.assertEqual((root / "owner.crt").read_bytes(), self.cert.read_bytes())
            self.assertEqual((root / "owner.key").stat().st_mode & 0o777, 0o600)
            self.assertFalse((root / ".owner-tls-before-renewal").exists())
            self.assertEqual([c[1] for c in commands if c[0] == "systemctl"], ["stop", "start", "is-active"] if active else [])

    @unittest.skipUnless(hasattr(os, "fork"), "Linux owner filesystem contract")
    def test_failed_package_check_keeps_service_stopped_and_previous_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); root.chmod(0o700)
            for n in ("owner.crt", "owner.key"):
                (root / n).write_text("previous"); (root / n).chmod(0o600)
            commands = []
            def command(args):
                commands.append(args)
                if args[0] == "runuser": raise ValueError("fixture package rejection")
            with self.assertRaises(ValueError): renew.owner_install(self.cert, self.key, root, os.getuid(), os.getgid(), True, command)
            self.assertFalse(any(c[:2] == ["systemctl", "start"] for c in commands))
            self.assertEqual((root / ".owner-tls-before-renewal/owner.key").read_text(), "previous")


if __name__ == "__main__": unittest.main()
