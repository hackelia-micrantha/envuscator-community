#!/usr/bin/env python3
"""Public, synthetic-only illustration of a customer-runner adapter boundary.

This is NOT the commercial Envuscator adapter, engine, crypto or a native build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys

MAX_BYTES = 1024 * 1024
MAX_ENTRIES = 1024
MAX_VALUE = 16 * 1024
KEY_RE = re.compile(rb"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
BUILD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class DemoDenied(Exception):
    """Publicly safe, non-sensitive error category."""


def load_local_config(path: Path) -> dict[str, bytes]:
    # These checks illustrate the documented public parser boundary; they do
    # not certify behavior of the separate private engine.
    try:
        st = path.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077:
            raise DemoDenied("unsafe configuration file type or permissions")
        if st.st_uid not in (os.getuid(), 0) or st.st_size > MAX_BYTES:
            raise DemoDenied("unsafe configuration file owner or size")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            fst = os.fstat(stream.fileno())
            if ((fst.st_dev, fst.st_ino) != (st.st_dev, st.st_ino)
                or not stat.S_ISREG(fst.st_mode) or fst.st_mode & 0o077
                or fst.st_uid not in (os.getuid(), 0)):
                raise DemoDenied("configuration changed while opening")
            data = stream.read(MAX_BYTES + 1)
    except (OSError, ValueError) as error:
        raise DemoDenied("configuration unavailable") from error
    if len(data) > MAX_BYTES or len(data) != st.st_size:
        raise DemoDenied("configuration size changed or exceeds limit")
    result: dict[str, bytes] = {}
    if not data or not data.endswith(b"\n"):
        raise DemoDenied("invalid configuration record framing")
    if b"\r" in data:
        raise DemoDenied("invalid configuration record framing")
    lines = data.splitlines()
    if len(lines) > MAX_ENTRIES:
        raise DemoDenied("too many configuration records")
    for line in lines:
        if b"=" not in line:
            raise DemoDenied("invalid configuration record")
        raw_key, value = line.split(b"=", 1)
        if not KEY_RE.fullmatch(raw_key):
            raise DemoDenied("invalid configuration key")
        if not value or len(value) > MAX_VALUE or any(b < 32 or b == 127 for b in value):
            raise DemoDenied("invalid configuration value")
        try:
            key = raw_key.decode("ascii")
            value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DemoDenied("invalid configuration encoding") from error
        if key in result:
            raise DemoDenied("duplicate configuration key")
        result[key] = value
    return result


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def demonstrative_transform(value: bytes, build_id: str, key: str) -> str:
    """Reversible, publicly seeded XOR. An illustration, NOT secure encryption."""
    result = bytearray()
    for n in range(0, len(value), 32):
        block = hashlib.sha256(f"synthetic-demo-v1:{build_id}:{key}:{n // 32}".encode("ascii")).digest()
        result.extend(b ^ block[i] for i, b in enumerate(value[n:n + 32]))
    return bytes(result).hex()


def render(config: dict[str, bytes], build_id: str, platform: str, build_type: str) -> tuple[bytes, bytes, bytes]:
    artifact = canonical_json({
        "demo_schema": "synthetic-adapter.v1",
        "synthetic_only": True,
        "platform": platform,
        "build_type": build_type,
        "build_id": build_id,
        "encoded_configuration": [
            {"key": key, "encoded_hex": demonstrative_transform(config[key], build_id, key)}
            for key in sorted(config)
        ],
    })
    manifest = canonical_json({
        "demo_schema": "synthetic-manifest.v1",
        "synthetic_only": True,
        "artifact": "synthetic-artifact.json",
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "artifact_bytes": len(artifact),
    })
    evidence = canonical_json({
        "demo_schema": "synthetic-result.v1",
        "synthetic_only": True,
        "category": "success",
        "build_id": build_id,
        "platform": platform,
        "build_type": build_type,
        "artifacts": ["synthetic-artifact.json", "synthetic-manifest.json"],
    })
    return artifact, manifest, evidence


def execute(config: Path, output: Path, build_id: str, platform: str, build_type: str) -> None:
    if not BUILD_RE.fullmatch(build_id):
        raise DemoDenied("invalid build identifier")
    if platform not in ("android", "ios") or build_type not in ("Debug", "Release"):
        raise DemoDenied("unsupported platform or build type")
    data = load_local_config(config)
    blobs = render(data, build_id, platform, build_type)
    names = ("synthetic-artifact.json", "synthetic-manifest.json", "synthetic-result.json")
    # Avoid overwriting unrelated customer files or following a pre-existing
    # output-directory symlink. One new, private directory per demonstration.
    created = False
    try:
        output.mkdir(mode=0o700, parents=False, exist_ok=False)
        created = True
        for name, blob in zip(names, blobs):
            fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(blob)
    except OSError as error:
        if created:
            try:
                shutil.rmtree(output)
            except OSError as cleanup_error:
                raise DemoDenied("cannot clean up incomplete synthetic output") from cleanup_error
        raise DemoDenied("cannot create complete synthetic output") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic Envuscator adapter example; no native engine")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--platform", choices=("android", "ios"), required=True)
    parser.add_argument("--build-type", choices=("Debug", "Release"), required=True)
    args = parser.parse_args()
    try:
        execute(args.config, args.output, args.build_id, args.platform, args.build_type)
    except DemoDenied as error:
        print(f"denied: {error}", file=sys.stderr)
        return 2
    print("synthetic conformance demonstration completed (not a native build)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
