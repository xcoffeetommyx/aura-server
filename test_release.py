import hashlib
import http.server
import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import threading
import unittest
import urllib.request
from unittest.mock import patch

import release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        (self.bundle / "bin").mkdir(parents=True)
        for name in ("bin/aura-server", "bin/navidrome"):
            (self.bundle / name).write_bytes(b"\x7fELF\x02\x01" + bytes(12) + struct.pack("<H", 62) + b"fake executable")
        (self.bundle / "aura-package.py").write_text("# TEST ONLY; never execute\n")
        (self.bundle / "README.md").write_text("Fixture\n")
        self.manifest = dict(release.lock(), version="test-1", arch="amd64", files={
            p.relative_to(self.bundle).as_posix(): release.digest(p)
            for p in self.bundle.rglob("*") if p.is_file()
        })
        self.save_manifest()

    def save_manifest(self):
        (self.bundle / "manifest.json").write_text(json.dumps(self.manifest, sort_keys=True))

    def packed(self, name="release.tar.gz"):
        path = self.root / name
        sha = release.pack(self.bundle, path, "test-1", "amd64")
        return path, sha

    def test_deterministic_archive_and_verified_extraction(self):
        one, sha = self.packed()
        two, other = self.packed("second.tar.gz")
        self.assertEqual(sha, other)
        for p in self.bundle.rglob("*"):
            if p.is_file():
                import os
                os.utime(p, (2000, 2000))
        _, changed_time = self.packed("third.tar.gz")
        self.assertEqual(sha, changed_time)
        destination = self.root / "installed"
        release.unpack(one, destination, sha, "test-1", "amd64")
        self.assertEqual(release.verify_bundle(destination, "test-1", "amd64"), self.manifest)
        with self.assertRaises(release.InvalidRelease):
            release.unpack(two, destination, sha, "test-1", "amd64")

    def test_corrupt_archive_never_publishes(self):
        path, sha = self.packed()
        path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaises(release.InvalidRelease):
            release.unpack(path, self.root / "out", sha, "test-1", "amd64")
        self.assertFalse((self.root / "out").exists())

    def test_wrong_version_architecture_and_revision(self):
        path, sha = self.packed()
        for version, arch in (("other", "amd64"), ("test-1", "arm64")):
            with self.subTest(version=version, arch=arch), self.assertRaises(release.InvalidRelease):
                release.unpack(path, self.root / "out", sha, version, arch)
            self.assertFalse((self.root / "out").exists())
        self.manifest["tailscaleRevision"] = "0" * 40
        self.save_manifest()
        with self.assertRaises(release.InvalidRelease):
            self.packed("wrong-source.tar.gz")

    def test_inventory_hashes_and_executable_machine(self):
        (self.bundle / "secret.key").write_text("FAKE-DO-NOT-SHIP")
        with self.assertRaises(release.InvalidRelease):
            self.packed()
        (self.bundle / "secret.key").unlink()
        (self.bundle / "bin/navidrome").write_bytes(b"wrong machine")
        self.manifest["files"]["bin/navidrome"] = release.digest(self.bundle / "bin/navidrome")
        self.save_manifest()
        with self.assertRaises(release.InvalidRelease):
            self.packed()

    def test_duplicate_json_rejected(self):
        with self.assertRaises(release.InvalidRelease):
            release.read_json('{"version":"good","version":"evil"}')

    def test_hostile_archive_members(self):
        cases = [("../escape", tarfile.REGTYPE), ("/absolute", tarfile.REGTYPE),
                 ("C:/drive", tarfile.REGTYPE), ("a\\b", tarfile.REGTYPE),
                 ("linked", tarfile.SYMTYPE), ("hard", tarfile.LNKTYPE),
                 ("fifo", tarfile.FIFOTYPE), ("pax", tarfile.XHDTYPE),
                 ("long", tarfile.GNUTYPE_LONGNAME)]
        for index, (name, kind) in enumerate(cases):
            with self.subTest(name=name):
                path = self.root / (str(index) + ".tar.gz")
                with tarfile.open(path, "w:gz") as archive:
                    info = tarfile.TarInfo(name)
                    info.type, info.linkname = kind, "../outside"
                    info.size = 1 if kind == tarfile.REGTYPE else 0
                    archive.addfile(info, io.BytesIO(b"x"))
                with self.assertRaises(release.InvalidRelease):
                    release.unpack(path, self.root / "out", release.digest(path), "test-1", "amd64")
                self.assertFalse((self.root / "out").exists())

    def test_duplicate_and_expanded_budget(self):
        path = self.root / "duplicate.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for _ in range(2):
                info = tarfile.TarInfo("duplicate")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(release.InvalidRelease):
            release.unpack(path, self.root / "out", release.digest(path), "test-1", "amd64")
        path, sha = self.packed()
        with patch.object(release, "MAX_EXPANDED", 10), self.assertRaises(release.InvalidRelease):
            release.unpack(path, self.root / "out", sha, "test-1", "amd64")

    def test_controlled_http_delivery_and_corrupt_response(self):
        path, sha = self.packed()
        content = path.read_bytes()
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "http://127.0.0.1:1/unrelated")
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(content)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = "http://127.0.0.1:" + str(server.server_port)
            output = self.root / "download.tar.gz"
            release.fetch(url + "/artifact", output, sha, True)
            self.assertEqual(release.digest(output), sha)
            for path, expected, control in (("/artifact", "0" * 64, True), ("/artifact", sha, False), ("/redirect", sha, True)):
                with self.subTest(path=path, expected=expected, control=control), self.assertRaises(release.InvalidRelease):
                    release.fetch(url + path, self.root / "bad", expected, control)
                self.assertFalse((self.root / "bad").exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_release_redirect_scope_and_no_authorization_forwarding(self):
        original = "https://github.com/owner/repo/releases/download/v1/artifact.tar.gz"
        handler = release.ReleaseRedirect(original)
        request = urllib.request.Request(original, headers={"Authorization": "FAKE-NOT-A-LIVE-TOKEN"})
        redirected = handler.redirect_request(request, None, 302, "", {},
            "https://release-assets.githubusercontent.com/asset?signature=FAKE")
        self.assertIsNone(redirected.get_header("Authorization"))
        for url in ("http://release-assets.githubusercontent.com/asset", "https://127.0.0.1/secret",
                    "https://github.com.evil.invalid/file", "https://user:secret@github.com/file"):
            with self.subTest(url=url), self.assertRaises(release.InvalidRelease):
                handler.redirect_request(request, None, 302, "", {}, url)


if __name__ == "__main__":
    unittest.main()
