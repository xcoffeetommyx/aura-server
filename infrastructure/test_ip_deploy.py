import os
from pathlib import Path
import tempfile
import unittest

import ip_deploy


class IPDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.root.chmod(0o700)
        self.cert = self.root / "cert"; self.cert.write_text("validated fixture certificate")
        self.key = self.root / "key"; self.key.write_text("fixture private data")
        self.published = self.root / "published"

    def test_stopped_services_not_started_and_atomic_pair(self):
        commands = []
        ip_deploy.publish(self.cert, self.key, self.published, [], commands.append)
        self.assertEqual(commands, [])
        self.assertTrue((self.published / "current").is_symlink())
        self.assertEqual((self.published / "current/privkey.pem").read_bytes(), self.key.read_bytes())
        self.assertEqual((self.published / "current/privkey.pem").stat().st_mode & 0o777, 0o600)

    def test_failed_restart_restores_previous_pair(self):
        ip_deploy.publish(self.cert, self.key, self.published, [])
        before = os.readlink(self.published / "current")
        self.cert.write_text("next certificate")
        def fail(command): raise RuntimeError("owned injected restart failure")
        with self.assertRaises(RuntimeError):
            ip_deploy.publish(self.cert, self.key, self.published, [ip_deploy.SERVICES[0]], fail)
        self.assertEqual(os.readlink(self.published / "current"), before)
        self.assertEqual((self.published / "current/fullchain.pem").read_text(), "validated fixture certificate")

    def test_rotation_bounded_to_current_and_previous(self):
        for _ in range(4): ip_deploy.publish(self.cert, self.key, self.published, [])
        self.assertEqual(len(list(self.published.glob("pair-*"))), 2)

    def test_no_unrelated_service_or_unsafe_lineage(self):
        with self.assertRaises(ValueError):
            ip_deploy.publish(self.cert, self.key, self.published, ["navidrome.service"])
        for extra in ({"certName": "../other"}, {"publicIP": "192.168.1.1"}, {"version": True}):
            c = dict(version=1, publicIP="8.8.8.8", certName="aura-home-ip"); c.update(extra)
            with self.assertRaises(ValueError): ip_deploy.configuration(c)

    def test_unsafe_publication_directory_fails_closed(self):
        self.published.mkdir(); self.published.chmod(0o755)
        with self.assertRaises(ValueError): ip_deploy.publish(self.cert, self.key, self.published, [])


if __name__ == "__main__": unittest.main()
