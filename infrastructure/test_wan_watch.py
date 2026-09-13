from pathlib import Path
import tempfile
import unittest
import wan_watch

class WANWatchTests(unittest.TestCase):
    def row(self, value):return f"<table><tr><th>Broadband IPv4 Address</th><td>{value}</td></tr></table>".encode()
    def test_exact_bounded_public_row(self):
        self.assertEqual(wan_watch.observed_ipv4(self.row("8.8.8.8")),"8.8.8.8")
        for data in (self.row("192.168.1.1"),self.row("100.64.0.1"),self.row("8.8.8.8")*2,b"login required",b"x"*131073):
            with self.assertRaises(ValueError):wan_watch.observed_ipv4(data)
    def test_same_address_does_not_mutate_services(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/"repair";commands=[]
            wan_watch.enforce("8.8.8.8","8.8.8.8",marker,commands.append)
            self.assertEqual(commands,[]);self.assertFalse(marker.exists())
    def test_changed_address_quarantines_before_any_stop(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/"repair";commands=[]
            def command(value):self.assertTrue(marker.exists());commands.append(value)
            with self.assertRaises(ValueError):wan_watch.enforce("8.8.8.8","1.1.1.1",marker,command)
            self.assertEqual([c[3] for c in commands],list(wan_watch.SERVICES))
            self.assertNotIn("1.1.1.1",marker.read_text())
            self.assertEqual(marker.stat().st_mode & 0o777,0o600)
    def test_one_failed_stop_does_not_skip_other_services(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/"repair";commands=[]
            def command(value):
                commands.append(value)
                if len(commands)==1:raise RuntimeError("fixture stop failure")
            with self.assertRaises(ValueError):wan_watch.enforce("8.8.8.8","1.1.1.1",marker,command)
            self.assertEqual(len(commands),3);self.assertTrue(marker.exists())
