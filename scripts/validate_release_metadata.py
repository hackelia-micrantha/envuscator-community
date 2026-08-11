#!/usr/bin/env python3
"""Validate the public metadata-only Envuscator release tree."""
from __future__ import annotations

import json
import re
import stat
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = ROOT / "web" / "releases" / "v1"

SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TARGETS = {
    "darwin-arm64",
    "darwin-x86_64",
    "linux-arm64",
    "linux-x86_64",
}
EXPECTED_FILES = {
    "release.statement.json",
    "release.statement.sig",
    "release.json",
}
FORBIDDEN_SUFFIXES = {
    ".tar",
    ".gz",
    ".tgz",
    ".zip",
    ".sha256",
    ".pem",
    ".key",
    ".p12",
    ".token",
}
MAX_STATEMENT_BYTES = 1024 * 1024
MAX_DESCRIPTOR_BYTES = 1024 * 1024
MIN_SIGNATURE_BYTES = 256
MAX_SIGNATURE_BYTES = 512


class ValidationError(RuntimeError):
    pass


def canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValidationError("invalid release metadata JSON") from error
    return (text + "\n").encode("utf-8")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError("duplicate release metadata field")
        value[key] = item
    return value


def reject_constant(_: str) -> object:
    raise ValidationError("invalid release metadata numeric constant")


def load_canonical_json(path: Path, *, max_bytes: int) -> dict[str, Any]:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValidationError(f"invalid release metadata file: {path.relative_to(ROOT)}")
    if metadata.st_size <= 0 or metadata.st_size > max_bytes:
        raise ValidationError(f"invalid release metadata size: {path.relative_to(ROOT)}")
    payload = path.read_bytes()
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except ValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid release metadata JSON: {path.relative_to(ROOT)}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"invalid release metadata shape: {path.relative_to(ROOT)}")
    if canonical_json(value) != payload:
        raise ValidationError(f"non-canonical release metadata JSON: {path.relative_to(ROOT)}")
    return value


def valid_semver(value: str) -> bool:
    match = SEMVER.fullmatch(value)
    if match is None:
        return False
    prerelease = match.group(4)
    if prerelease is None:
        return True
    return all(not (item.isdigit() and len(item) > 1 and item.startswith("0")) for item in prerelease.split("."))


def require_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValidationError(f"invalid {field}")
    return value


def require_sha256(value: object, *, field: str) -> str:
    result = require_string(value, field=field)
    if SHA256.fullmatch(result) is None:
        raise ValidationError(f"invalid {field}")
    return result


def require_positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"invalid {field}")
    return value


def validate_release_directory(path: Path, *, version: str, target: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ValidationError(f"invalid release target directory: {path.relative_to(ROOT)}")

    names = {entry.name for entry in path.iterdir()}
    if names != EXPECTED_FILES:
        raise ValidationError(
            f"release target must contain exactly {sorted(EXPECTED_FILES)}: {path.relative_to(ROOT)}"
        )
    for entry in path.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise ValidationError(f"invalid release metadata entry: {entry.relative_to(ROOT)}")
        lowered = entry.name.lower()
        if any(lowered.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            raise ValidationError(f"forbidden release payload: {entry.relative_to(ROOT)}")

    statement_path = path / "release.statement.json"
    signature_path = path / "release.statement.sig"
    descriptor_path = path / "release.json"

    statement = load_canonical_json(statement_path, max_bytes=MAX_STATEMENT_BYTES)
    descriptor = load_canonical_json(descriptor_path, max_bytes=MAX_DESCRIPTOR_BYTES)

    signature_metadata = signature_path.lstat()
    if (
        stat.S_ISLNK(signature_metadata.st_mode)
        or not stat.S_ISREG(signature_metadata.st_mode)
        or signature_metadata.st_size < MIN_SIGNATURE_BYTES
        or signature_metadata.st_size > MAX_SIGNATURE_BYTES
    ):
        raise ValidationError(f"invalid release signature file: {signature_path.relative_to(ROOT)}")

    if statement.get("schema_version") != "1":
        raise ValidationError("invalid release statement schema_version")
    if statement.get("signing_algorithm") != "RS256":
        raise ValidationError("invalid release signing algorithm")
    if require_string(statement.get("engine_version"), field="statement engine_version") != version:
        raise ValidationError("release statement version does not match path")
    if require_string(statement.get("target"), field="statement target") != target:
        raise ValidationError("release statement target does not match path")
    archive_digest = require_sha256(statement.get("archive_sha256"), field="statement archive_sha256")
    archive_size = require_positive_int(statement.get("archive_size"), field="statement archive_size")
    descriptor_digest = require_sha256(statement.get("descriptor_sha256"), field="statement descriptor_sha256")
    descriptor_size = require_positive_int(statement.get("descriptor_size"), field="statement descriptor_size")
    require_string(statement.get("signing_key_id"), field="statement signing_key_id")

    descriptor_bytes = descriptor_path.read_bytes()
    import hashlib

    if len(descriptor_bytes) != descriptor_size:
        raise ValidationError("release descriptor size does not match statement")
    if hashlib.sha256(descriptor_bytes).hexdigest() != descriptor_digest:
        raise ValidationError("release descriptor digest does not match statement")

    if descriptor.get("schema_version") != statement.get("descriptor_schema_version"):
        raise ValidationError("release descriptor schema does not match statement")
    if descriptor.get("engine_version") != version:
        raise ValidationError("release descriptor version does not match path")
    if descriptor.get("target") != target:
        raise ValidationError("release descriptor target does not match path")
    if descriptor.get("archive_sha256") != archive_digest:
        raise ValidationError("release descriptor archive digest does not match statement")
    if descriptor.get("archive_size") != archive_size:
        raise ValidationError("release descriptor archive size does not match statement")
    if descriptor.get("archive_filename") != statement.get("archive_filename"):
        raise ValidationError("release descriptor archive filename does not match statement")
    if descriptor.get("archive_format") != statement.get("archive_format"):
        raise ValidationError("release descriptor archive format does not match statement")
    if descriptor.get("source_revision") != statement.get("source_revision"):
        raise ValidationError("release descriptor revision does not match statement")
    if descriptor.get("required_entrypoints") != statement.get("required_entrypoints"):
        raise ValidationError("release descriptor entrypoints do not match statement")
    if descriptor.get("compatibility") != statement.get("compatibility"):
        raise ValidationError("release descriptor compatibility does not match statement")


def validate_tree() -> None:
    if not RELEASE_ROOT.exists():
        return
    if RELEASE_ROOT.is_symlink() or not RELEASE_ROOT.is_dir():
        raise ValidationError("invalid public release metadata root")

    for version_path in RELEASE_ROOT.iterdir():
        if version_path.is_symlink() or not version_path.is_dir() or not valid_semver(version_path.name):
            raise ValidationError(f"invalid release version path: {version_path.relative_to(ROOT)}")
        for target_path in version_path.iterdir():
            if target_path.name not in TARGETS:
                raise ValidationError(f"invalid release target path: {target_path.relative_to(ROOT)}")
            validate_release_directory(
                target_path,
                version=version_path.name,
                target=target_path.name,
            )


def main() -> int:
    try:
        validate_tree()
    except (OSError, ValidationError) as error:
        print(f"release metadata validation failed: {error}")
        return 1
    print("release metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
