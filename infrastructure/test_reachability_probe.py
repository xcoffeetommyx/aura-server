import socket
import threading
import unittest

from reachability_probe import probe


class ProbeTests(unittest.TestCase):
    def exercise(self, address, family):
        with socket.socket(family) as s:
            s.bind((address, 0)); port = s.getsockname()[1]
        ready, stop = threading.Event(), threading.Event()
        result = []; errors = []
        nonce = b"a" * 32
        def serve():
            try: result.append(probe(address, port, nonce, 2, ready.set, stop.is_set))
            except Exception as e: errors.append(e); ready.set()
        worker = threading.Thread(target=serve); worker.start()
        try:
            self.assertTrue(ready.wait(2)); self.assertFalse(errors)
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(1); s.connect((address, port)); s.sendall(nonce)
                self.assertEqual(s.recv(32), nonce)
            with socket.socket(family, socket.SOCK_DGRAM) as s:
                s.settimeout(1); s.sendto(nonce, (address, port))
                self.assertEqual(s.recv(32), nonce)
                s.settimeout(.1); s.sendto(b"not the nonce", (address, port))
                with self.assertRaises(socket.timeout): s.recv(32)
        finally:
            stop.set(); worker.join(3)
        self.assertFalse(worker.is_alive()); self.assertFalse(errors)
        self.assertEqual(result, [{"tcp": 1, "udp": 1, "rejected": 1}])
        with socket.socket(family) as s:
            s.settimeout(.2)
            self.assertNotEqual(s.connect_ex((address, port)), 0)

    def test_ipv4(self): self.exercise("127.0.0.1", socket.AF_INET)
    def test_ipv6(self): self.exercise("::1", socket.AF_INET6)


if __name__ == "__main__": unittest.main()
