#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_release_metadata as validator  # noqa: E402


class ReleaseMetadataSurfaceTests(unittest.TestCase):
    VERSION = "1.2.3"
    TARGET = "linux-x86_64"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.release_root = self.root / "web" / "releases" / "v1"
        self.old_root = validator.ROOT
        self.old_release_root = validator.RELEASE_ROOT
        validator.ROOT = self.root
        validator.RELEASE_ROOT = self.release_root
        self.addCleanup(self._restore_globals)

    def _restore_globals(self) -> None:
        validator.ROOT = self.old_root
        validator.RELEASE_ROOT = self.old_release_root

    def _canonical(self, value: object) -> bytes:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")

    def _descriptor(self) -> dict[str, object]:
        archive_name = f"envuscator-engine-{self.VERSION}-{self.TARGET}.tar.gz"
        return {
            "schema_version": "1",
            "engine_version": self.VERSION,
            "source_revision": "a" * 40,
            "target": self.TARGET,
            "archive_url": f"https://private-store.example/{archive_name}",
            "archive_filename": archive_name,
            "archive_format": "tar.gz",
            "archive_sha256": "b" * 64,
            "archive_size": 4096,
            "required_entrypoints": ["scripts/run_execution.py"],
            "configuration_schema_version": "1",
            "artifact_schema_version": "1",
            "execution_result_schema_version": "1",
            "compatibility": {"adapter_contract_version": "1"},
            "entitlement_contract_version": "1",
            "entitlement_verifier_sha256": "c" * 64,
            "trusted_key_bundle_sha256": "d" * 64,
            "entitlement_issuer": "https://license.example.com",
            "entitlement_audience": "envuscator-engine",
            "supported_entitlement_modes": ["disabled", "observe", "required"],
        }

    def _statement(self, descriptor_bytes: bytes, descriptor: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "1",
            "signed_at": 1_786_000_000,
            "signing_key_id": "release-key-2026-01",
            "signing_algorithm": "RS256",
            "engine_version": self.VERSION,
            "source_revision": descriptor["source_revision"],
            "target": self.TARGET,
            "archive_filename": descriptor["archive_filename"],
            "archive_format": descriptor["archive_format"],
            "archive_sha256": descriptor["archive_sha256"],
            "archive_size": descriptor["archive_size"],
            "checksum_filename": str(descriptor["archive_filename"]) + ".sha256",
            "checksum_sha256": "e" * 64,
            "checksum_size": 96,
            "descriptor_filename": f"envuscator-engine-{self.VERSION}-{self.TARGET}.release.json",
            "descriptor_sha256": hashlib.sha256(descriptor_bytes).hexdigest(),
            "descriptor_size": len(descriptor_bytes),
            "descriptor_schema_version": descriptor["schema_version"],
            "required_entrypoints": descriptor["required_entrypoints"],
            "compatibility": descriptor["compatibility"],
        }

    def _write_release(
        self,
        *,
        version: str | None = None,
        target: str | None = None,
        descriptor: dict[str, object] | None = None,
        statement_overrides: dict[str, object] | None = None,
    ) -> Path:
        version = version or self.VERSION
        target = target or self.TARGET
        path = self.release_root / version / target
        path.mkdir(parents=True)
        descriptor_value = descriptor or self._descriptor()
        descriptor_bytes = self._canonical(descriptor_value)
        statement = self._statement(descriptor_bytes, descriptor_value)
        if statement_overrides:
            statement.update(statement_overrides)
        (path / "release.json").write_bytes(descriptor_bytes)
        (path / "release.statement.json").write_bytes(self._canonical(statement))
        (path / "release.statement.sig").write_bytes(b"s" * 384)
        return path

    def test_absent_release_tree_is_valid_until_production_publication(self) -> None:
        validator.validate_tree()

    def test_valid_complete_metadata_tree_passes(self) -> None:
        self._write_release()
        validator.validate_tree()

    def test_archive_or_private_key_injection_is_rejected(self) -> None:
        for name in ("engine.tar.gz", "release-key.pem"):
            with self.subTest(name=name):
                path = self._write_release()
                (path / name).write_bytes(b"forbidden")
                with self.assertRaises(validator.ValidationError):
                    validator.validate_tree()
                (path / name).unlink()

    def test_invalid_version_or_target_path_is_rejected(self) -> None:
        for version, target in (("01.2.3", self.TARGET), (self.VERSION, "windows-x86_64")):
            with self.subTest(version=version, target=target):
                self._write_release(version=version, target=target)
                with self.assertRaises(validator.ValidationError):
                    validator.validate_tree()
                import shutil
                shutil.rmtree(self.release_root)

    def test_noncanonical_descriptor_is_rejected(self) -> None:
        path = self._write_release()
        value = json.loads((path / "release.json").read_text(encoding="utf-8"))
        (path / "release.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "non-canonical"):
            validator.validate_tree()

    def test_statement_version_must_match_public_path(self) -> None:
        self._write_release(statement_overrides={"engine_version": "9.9.9"})
        with self.assertRaisesRegex(validator.ValidationError, "version does not match path"):
            validator.validate_tree()

    def test_descriptor_digest_binding_is_required(self) -> None:
        path = self._write_release()
        payload = bytearray((path / "release.json").read_bytes())
        payload[-2] ^= 1
        (path / "release.json").write_bytes(bytes(payload))
        with self.assertRaises(validator.ValidationError):
            validator.validate_tree()

    def test_descriptor_identity_must_match_statement_even_when_descriptor_digest_is_updated(self) -> None:
        descriptor = self._descriptor()
        statement_archive_digest = descriptor["archive_sha256"]
        descriptor["archive_sha256"] = "f" * 64
        descriptor_bytes = self._canonical(descriptor)
        self._write_release(
            descriptor=descriptor,
            statement_overrides={
                "archive_sha256": statement_archive_digest,
                "descriptor_sha256": hashlib.sha256(descriptor_bytes).hexdigest(),
                "descriptor_size": len(descriptor_bytes),
            },
        )
        with self.assertRaisesRegex(validator.ValidationError, "archive digest does not match statement"):
            validator.validate_tree()


if __name__ == "__main__":
    unittest.main()
