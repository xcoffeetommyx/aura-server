import unittest
import owner_guard


class OwnerGuardTests(unittest.TestCase):
    def test_exact_lan_owner_only_preserves_other_rules(self):
        text = owner_guard.render("192.168.1.10", "192.168.1.0/24")
        self.assertIn("ip daddr 192.168.1.10 tcp dport 9443 ip saddr != 192.168.1.0/24 counter drop", text)
        self.assertNotIn("flush ruleset", text)
        self.assertNotIn("4533", text)
        self.assertIn("Requires=aura-home-firewall.service", owner_guard.DEPENDENCY)
        self.assertFalse(any(line.startswith("ExecStop=") for line in owner_guard.UNIT.splitlines()))

    def test_public_or_mismatched_network_rejected(self):
        for addr, net in (("192.168.1.1", "0.0.0.0/0"), ("192.168.1.1", "192.168.2.0/24"), ("8.8.8.8", "8.8.8.0/24")):
            with self.assertRaises(ValueError): owner_guard.render(addr, net)
