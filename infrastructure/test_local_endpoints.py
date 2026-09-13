import unittest
import local_endpoints


class LocalEndpointTests(unittest.TestCase):
    def test_host_only_exact_services_preserve_tls_authority(self):
        text = local_endpoints.render("8.8.8.8", "192.168.1.10")
        self.assertIn("hook output priority dstnat", text)
        self.assertIn("ip daddr 8.8.8.8 tcp dport { 8443, 8444, 9443 }", text)
        self.assertIn("udp dport 3478", text)
        self.assertIn("dnat to 192.168.1.10", text)
        for prohibited in ("prerouting", "forward", "4533", "flush ruleset", "snat"):
            self.assertNotIn(prohibited, text)

    def test_unsafe_configuration_rejected(self):
        for public, lan in (("192.168.1.1", "192.168.1.10"), ("8.8.8.8", "8.8.4.4"), ("8.8.8.8; drop", "192.168.1.10")):
            with self.assertRaises(ValueError): local_endpoints.render(public, lan)
