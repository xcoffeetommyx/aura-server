#!/usr/bin/env python3
"""Deterministic package delivery; never executes downloaded code.

The expected SHA-256 must come from an authenticated independent release record.
TLS/checksums do not replace publisher authentication. No production signing key
or trust-on-first-use mechanism is embedded here.
"""
import argparse
import gzip
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import struct
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request

MAX_ARCHIVE = 512 * 1024 * 1024
MAX_EXPANDED = 1024 * 1024 * 1024
MAX_FILES = 256
REQUIRED = {"bin/aura-server", "bin/navidrome", "aura-package.py", "README.md"}


class InvalidRelease(ValueError):
    pass


class RegularTarInfo(tarfile.TarInfo):
    def _proc_member(self, archive):
        # Reject GNU/PAX extension headers before tarfile materializes their
        # metadata. Python 3.14 bypasses the public frombuf hook internally;
        # member processing is the shared boundary on supported Python versions.
        # The producer emits only bounded USTAR regular files.
        if self.type not in (tarfile.REGTYPE, tarfile.AREGTYPE):
            raise InvalidRelease("Only regular USTAR release members permitted")
        member_name(self.name)
        return super()._proc_member(archive)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidRelease("Duplicate manifest key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def member_name(name):
    path = PurePosixPath(name)
    if (not isinstance(name, str) or not name or len(name) > 240 or
            path.is_absolute() or str(path) != name or
            any(p in ("", ".", "..") for p in path.parts) or
            re.search(r"[^a-zA-Z0-9._/-]", name)):
        raise InvalidRelease("Unsafe archive member")
    return name


def lock():
    return read_json(Path(__file__).with_name("components.json").read_bytes())


def verify_bundle(root, version, arch):
    root = Path(root)
    if arch not in ("amd64", "arm64") or not re.fullmatch(r"[a-zA-Z0-9._-]{1,64}", version):
        raise InvalidRelease("Unsupported architecture/version")
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 128 * 1024:
        raise InvalidRelease("Invalid manifest")
    manifest = read_json(manifest_path.read_bytes())
    if manifest.get("format") != 1 or manifest.get("version") != version or manifest.get("arch") != arch:
        raise InvalidRelease("Release format/version/architecture mismatch")
    for field, expected in lock().items():
        if manifest.get(field) != expected:
            raise InvalidRelease("Component provenance mismatch: " + field)
    files = manifest.get("files")
    if not isinstance(files, dict) or not REQUIRED.issubset(files) or len(files) >= MAX_FILES:
        raise InvalidRelease("Incomplete file inventory")
    actual = set()
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise InvalidRelease("Release links/special files prohibited")
        if path.is_file():
            name = member_name(path.relative_to(root).as_posix())
            actual.add(name)
            total += path.stat().st_size
    if actual != set(files) | {"manifest.json"} or total > MAX_EXPANDED:
        raise InvalidRelease("Unexpected release content/size")
    for name, expected in files.items():
        member_name(name)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(root / name) != expected:
            raise InvalidRelease("Release file integrity mismatch")
    for name in ("bin/aura-server", "bin/navidrome"):
        with (root / name).open("rb") as f:
            header = f.read(20)
        if (len(header) != 20 or header[:6] != b"\x7fELF\x02\x01" or
                struct.unpack("<H", header[18:20])[0] != {"amd64": 62, "arm64": 183}[arch]):
            raise InvalidRelease("Executable architecture mismatch")
    return manifest


def pack(bundle, output, version, arch):
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    manifest = verify_bundle(bundle, version, arch)
    # New destinations only: interrupted delivery cannot replace an old release.
    with output.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
                for name in sorted(set(manifest["files"]) | {"manifest.json"}):
                    path = bundle / name
                    info = tarfile.TarInfo(name)
                    info.size = path.stat().st_size
                    info.mode = 0o755 if name in ("aura-package.py", "bin/aura-server", "bin/navidrome") else 0o644
                    info.mtime = 0
                    with path.open("rb") as f:
                        archive.addfile(info, f)
    if output.stat().st_size > MAX_ARCHIVE:
        raise InvalidRelease("Archive exceeds delivery budget")
    return digest(output)


def unpack(archive, destination, expected_sha, version, arch):
    archive, destination = Path(archive), Path(destination).absolute()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or archive.stat().st_size > MAX_ARCHIVE or digest(archive) != expected_sha:
        raise InvalidRelease("Archive checksum/size mismatch")
    if destination.exists() or destination.is_symlink():
        raise InvalidRelease("Destination already exists; nothing overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # All content is verified in a private sibling before publishing the directory.
    with tempfile.TemporaryDirectory(prefix=".aura-release-", dir=destination.parent) as temp:
        staging = Path(temp) / "verified"
        staging.mkdir(mode=0o700)
        seen, total = set(), 0
        with tarfile.open(archive, "r:gz", tarinfo=RegularTarInfo) as source:
            for member in source:
                name = member_name(member.name)
                if not member.isfile() or member.issparse() or member.pax_headers or name in seen:
                    raise InvalidRelease("Links, sparse, duplicate or special members prohibited")
                seen.add(name)
                total += member.size
                if member.size < 0 or total > MAX_EXPANDED or len(seen) > MAX_FILES:
                    raise InvalidRelease("Expanded archive budget exceeded")
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=65536)
                target.chmod(0o755 if name in ("aura-package.py", "bin/aura-server", "bin/navidrome") else 0o644)
        verify_bundle(staging, version, arch)
        # rename is atomic on the same filesystem; do not overwrite a destination.
        if destination.exists():
            raise InvalidRelease("Destination appeared during verification")
        staging.rename(destination)


class ReleaseRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, original_url):
        self.original = urllib.parse.urlsplit(original_url)
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        self.count += 1
        allowed = {self.original.hostname}
        # GitHub release delivery uses an HTTPS signed asset URL. Never forward
        # authorization headers: this consumer supports public artifacts only.
        if self.original.hostname == "github.com":
            allowed.add("release-assets.githubusercontent.com")
        if (self.count > 3 or self.original.scheme != "https" or target.scheme != "https" or
                target.hostname not in allowed or target.port not in (None, 443) or
                target.username or target.password or target.fragment):
            raise InvalidRelease("Release redirect outside the permitted HTTPS delivery hosts")
        return urllib.request.Request(newurl, headers={"Accept": "application/octet-stream"})


def fetch(url, output, expected_sha, controlled_http=False):
    parsed = urllib.parse.urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise InvalidRelease("Invalid release URL")
    local = False
    try:
        local = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        pass
    if parsed.scheme != "https" and not (controlled_http and parsed.scheme == "http" and local):
        raise InvalidRelease("HTTPS required; controlled HTTP is literal loopback only")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise InvalidRelease("Trusted expected SHA-256 required")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise InvalidRelease("Download destination already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), ReleaseRedirect(url))
    with tempfile.TemporaryDirectory(prefix=".aura-download-", dir=output.parent) as temp:
        pending = Path(temp) / "artifact"
        deadline = time.monotonic() + 300
        with opener.open(url, timeout=20) as response, pending.open("xb") as f:
            if response.status != 200:
                raise InvalidRelease("Release server did not return 200")
            size = 0
            while data := response.read(65536):
                size += len(data)
                if size > MAX_ARCHIVE or time.monotonic() > deadline:
                    raise InvalidRelease("Download budget exceeded")
                f.write(data)
        if digest(pending) != expected_sha:
            raise InvalidRelease("Downloaded artifact checksum mismatch")
        if output.exists():
            raise InvalidRelease("Download destination appeared")
        pending.rename(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--bundle", required=True)
    p.add_argument("--output", required=True)
    for p in (p, sub.add_parser("verify")):
        p.add_argument("--version", required=True)
        p.add_argument("--arch", choices=("amd64", "arm64"), required=True)
    p.add_argument("--archive", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--sha256", required=True)
    p = sub.add_parser("fetch")
    p.add_argument("--url", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--controlled-http", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "pack":
            print(pack(args.bundle, args.output, args.version, args.arch))
        elif args.command == "verify":
            actual_arch = {"x86_64": "amd64", "AMD64": "amd64", "aarch64": "arm64", "ARM64": "arm64"}.get(platform.machine())
            if args.arch != actual_arch:
                raise InvalidRelease("Selected artifact is not for this host")
            unpack(args.archive, args.destination, args.sha256, args.version, args.arch)
            print("Release verified; no service or downloaded program was executed")
        else:
            fetch(args.url, args.output, args.sha256, args.controlled_http)
            print("Release downloaded and checksum verified")
    except (ValueError, OSError, tarfile.TarError) as error:
        # Remote URLs/response bodies and raw server errors never reach logs.
        parser.exit(1, "Release rejected: " + (str(error) if isinstance(error, InvalidRelease) else type(error).__name__) + "\n")


if __name__ == "__main__":
    main()
