import json
import unittest

import self_hosted


class SelfHostedTests(unittest.TestCase):
    def config(self):
        return dict(version=1, publicIPv4="8.8.8.8", lanIPv4="192.168.1.10", regionId=9001, mediaRoot="/mnt/media")

    def test_nonconflicting_services_and_exact_host_ports(self):
        files = self_hosted.render(self.config())
        self.assertIn("-listen 192.168.1.10:8443 -host 8.8.8.8:8443", files["aura-derp.service"])
        self.assertIn("-listen 192.168.1.10:8444 -hosts 8.8.8.8:8444", files["aura-rendezvous.service"])
        for role in ("derp", "rendezvous"):
            unit = files[f"aura-{role}.service"]
            self.assertIn("tls/current/privkey.pem", unit)
            self.assertIn("InaccessiblePaths=-/mnt/media", unit)
            self.assertIn("DynamicUser=yes", unit)
            self.assertIn("LogNamespace=aura-infrastructure", unit)
            self.assertNotIn("CAP_NET_BIND_SERVICE", unit)
        node = json.loads(files["region.fresh-enrollment.json"])["Nodes"][0]
        self.assertEqual(node["HostName"], "8.8.8.8")
        self.assertEqual(node["DERPPort"], 8443)
        self.assertNotIn("InsecureForTests", node)
        self.assertIn("MaxRetentionSec=7day", files["journald@aura-infrastructure.conf"])
        self.assertIn("SystemMaxUse=32M", files["journald@aura-infrastructure.conf"])

    def test_no_owner_or_navidrome_exposure_and_hourly_renewal(self):
        files = self_hosted.render(self.config())
        review = json.loads(files["router-review.json"])
        self.assertEqual(review["tcp"], [80, 8443, 8444])
        self.assertEqual(review["udp"], [3478])
        self.assertIn("OnCalendar=hourly", files["aura-acme-renew.timer"])
        self.assertIn("--no-random-sleep-on-renew", files["aura-acme-renew.service"])
        self.assertNotIn("aura-server.service", files)

    def test_malformed_or_unsupported_inputs_rejected(self):
        for change in ({"publicIPv4": "127.0.0.1"}, {"publicIPv4": "2001:4860:4860::8888"},
                       {"lanIPv4": "8.8.8.8"}, {"mediaRoot": "/tmp/../etc"},
                       {"mediaRoot": "/mnt/media\nExecStart=bad"}, {"regionId": True}, {"version": True}):
            config = self.config(); config.update(change)
            with self.assertRaises(ValueError): self_hosted.render(config)


if __name__ == "__main__": unittest.main()
