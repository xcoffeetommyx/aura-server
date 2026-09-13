import unittest
import host_guard


class HostGuardTests(unittest.TestCase):
    def test_only_public_infrastructure_and_existing_administration(self):
        text = host_guard.render("192.168.1.10", "192.168.1.0/24", "2001:4860:1234:5678::/64", 41641)
        for expected in ("policy drop", "ct state established,related accept", 'iifname "lo" accept',
                         "tcp dport { 80, 8443, 8444 }", "udp dport 3478", "udp dport 41641"):
            self.assertIn(expected, text)
        for prohibited in ("4533", "9443", "flush ruleset", "hook forward", "hook output"):
            self.assertNotIn(prohibited, text)
        self.assertIn("Requires=aura-host-firewall.service", host_guard.DEPENDENCY)
    def test_unbounded_or_uninventoried_inputs_rejected(self):
        for prefix, port in (("::/0", 41641), ("fe80::/64", 41641), ("2600::/64", 22), ("2600::/64", True)):
            with self.assertRaises(ValueError):host_guard.render("192.168.1.10", "192.168.1.0/24", prefix, port)
