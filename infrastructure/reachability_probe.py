"""Bounded, disposable TCP/UDP nonce echo. No HTTP, file serving or forwarding.

Bind only an explicitly owned local address. Removes its listeners after at most
180 seconds. Run separately for IPv4/IPv6; do not change any firewall automatically.
"""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import selectors
import signal
import socket
import time


def probe(address, port, nonce, seconds, ready=lambda: None, stop=lambda: False):
    if not re.fullmatch(rb"[a-f0-9]{32}", nonce) or not 1 <= seconds <= 180 or not 1024 <= port <= 65535:
        raise ValueError("Invalid bounded probe parameters")
    ip = ipaddress.ip_address(address)
    family = socket.AF_INET6 if ip.version == 6 else socket.AF_INET
    counts = {"tcp": 0, "udp": 0, "rejected": 0}
    sockets = []
    with selectors.DefaultSelector() as selector:
        try:
            for kind, socktype in (("tcp", socket.SOCK_STREAM), ("udp", socket.SOCK_DGRAM)):
                s = socket.socket(family, socktype); sockets.append(s)
                if family == socket.AF_INET6: s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                s.bind((str(ip), port))
                if kind == "tcp": s.listen(4)
                s.setblocking(False); selector.register(s, selectors.EVENT_READ, kind)
            ready()
            until = time.monotonic() + seconds
            while time.monotonic() < until and not stop():
                for event, _ in selector.select(min(.2, max(0, until - time.monotonic()))):
                    if event.data == "tcp":
                        connection, _ = event.fileobj.accept()
                        with connection:
                            connection.settimeout(.2)
                            try:
                                data = b""
                                deadline = time.monotonic() + .2
                                while len(data) < 32 and time.monotonic() < deadline:
                                    chunk = connection.recv(33 - len(data))
                                    if not chunk: break
                                    data += chunk
                                if data == nonce:
                                    connection.sendall(nonce); counts["tcp"] += 1
                                else: counts["rejected"] += 1
                            except OSError: counts["rejected"] += 1
                    else:
                        data, peer = event.fileobj.recvfrom(33)
                        if data == nonce:
                            event.fileobj.sendto(nonce, peer); counts["udp"] += 1
                        else: counts["rejected"] += 1
                    # Bounded response work even if the temporary public port is flooded.
                    time.sleep(.01)
            return counts
        finally:
            for s in sockets: s.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--address", required=True)
    p.add_argument("--port", type=int, default=46381)
    p.add_argument("--nonce-file", required=True)
    p.add_argument("--seconds", type=int, default=120)
    args = p.parse_args()
    stopped = [False]
    def halt(*unused): stopped[0] = True
    signal.signal(signal.SIGTERM, halt); signal.signal(signal.SIGINT, halt)
    with Path(args.nonce_file).open("rb") as f:
        nonce = f.read(66).strip()
    counts = probe(args.address, args.port, nonce, args.seconds,
                   ready=lambda: print("Owned nonce probe ready", flush=True), stop=lambda: stopped[0])
    print(json.dumps(counts), flush=True)
