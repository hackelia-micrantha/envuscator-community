"""Synthetic contract and negative tests; do not require a private engine."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import demo  # noqa: E402


class SyntheticContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "config.env"
        self.config.write_bytes((HERE / "fixtures" / "sample.env").read_bytes())
        self.config.chmod(0o600)

    def output(self, name: str, build: str = "fixture-build-A", platform: str = "android", build_type: str = "Debug"):
        folder = self.root / name
        demo.execute(self.config, folder, build, platform, build_type)
        return {path.name: path.read_bytes() for path in folder.iterdir()}

    def test_deterministic_provenance_and_build_specific_difference(self):
        first = self.output("first")
        replay = self.output("replay")
        second = self.output("second", build="fixture-build-B")
        self.assertEqual(first, replay)
        self.assertNotEqual(first["synthetic-artifact.json"], second["synthetic-artifact.json"])
        manifest = json.loads(first["synthetic-manifest.json"])
        self.assertEqual(manifest["artifact_sha256"], hashlib.sha256(first["synthetic-artifact.json"]).hexdigest())
        self.assertEqual(manifest["artifact_bytes"], len(first["synthetic-artifact.json"]))
        artifact = json.loads(first["synthetic-artifact.json"])
        self.assertEqual([x["key"] for x in artifact["encoded_configuration"]], ["DISPLAY_LABEL", "PUBLIC_ENDPOINT"])
        self.assertTrue(artifact["synthetic_only"])
        self.assertEqual(json.loads(first["synthetic-result.json"])["category"], "success")

    def test_no_plaintext_in_simulated_public_outputs(self):
        self.config.write_bytes(b"SYNTHETIC_CANARY=SAFE_DEMO_VALUE_NOT_SECRET_012345\n")
        output = self.output("private-result")
        for blob in output.values():
            self.assertNotIn(b"SAFE_DEMO_VALUE_NOT_SECRET_012345", blob)
            self.assertNotIn(b"https://example.invalid/api", blob)
            self.assertNotIn(str(self.root).encode(), blob)
        directory = self.root / "private-result"
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for name in output:
            self.assertEqual(stat.S_IMODE((directory / name).stat().st_mode) & 0o077, 0)

    def test_deny_duplicate_malformed_and_unsafe_config(self):
        cases = [
            b"DUP=one\nDUP=two\n", b"BAD-NAME=value\n", b"MISSING_EQUALS\n",
            b"EMPTY=\n", b"X=tab\tvalue\n", b"X=invalid\xff\n", b"X=oops",
            b"X=a\r\n", b"X=" + b"a" * (16 * 1024 + 1) + b"\n",
            b"X=ok\n" * 1025, b"X=ok\n" + b" " * (1024 * 1024),
        ]
        for index, raw in enumerate(cases):
            with self.subTest(index=index):
                self.config.write_bytes(raw)
                with self.assertRaises(demo.DemoDenied):
                    demo.execute(self.config, self.root / f"invalid-{index}", "fixture-A", "android", "Debug")
                self.assertFalse((self.root / f"invalid-{index}").exists())

    def test_deny_symlink_and_world_readable_config(self):
        self.config.chmod(0o644)
        with self.assertRaises(demo.DemoDenied):
            demo.execute(self.config, self.root / "out1", "fixture-A", "android", "Debug")
        self.config.chmod(0o600)
        link = self.root / "link.env"
        link.symlink_to(self.config)
        with self.assertRaises(demo.DemoDenied):
            demo.execute(link, self.root / "out2", "fixture-A", "android", "Debug")

    def test_deny_symlink_output_without_overwriting_target(self):
        sentinel = self.root / "unchanged"
        sentinel.mkdir()
        (sentinel / "marker.txt").write_text("original")
        link = self.root / "output-link"
        link.symlink_to(sentinel, target_is_directory=True)
        with self.assertRaises(demo.DemoDenied):
            demo.execute(self.config, link, "fixture-A", "android", "Debug")
        self.assertEqual((sentinel / "marker.txt").read_text(), "original")

    def test_deny_existing_output_and_bad_selectors(self):
        self.output("created")
        with self.assertRaises(demo.DemoDenied):
            demo.execute(self.config, self.root / "created", "fixture-A", "android", "Debug")
        for build_id, platform, typ in [
            ("../traversal", "android", "Debug"), ("fixture-A", "server", "Debug"),
            ("fixture-A", "ios", "Production"), ("", "android", "Debug")
        ]:
            with self.subTest(build_id=build_id, platform=platform, typ=typ):
                with self.assertRaises(demo.DemoDenied):
                    demo.execute(self.config, self.root / "invalid-selector", build_id, platform, typ)

    def test_cli_denial_is_generic_and_no_config_value_in_logs(self):
        self.config.write_bytes(b"X=SAFE_DEMO_VALUE_NOT_SECRET_012345\nX=bad\n")
        run = subprocess.run([sys.executable, str(HERE / "demo.py"), "--config", str(self.config), "--output", str(self.root / "out"),
                              "--build-id", "example", "--platform", "android", "--build-type", "Debug"],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertNotIn("SAFE_DEMO_VALUE_NOT_SECRET_012345", run.stderr + run.stdout)
        self.assertFalse((self.root / "out").exists())

    def test_ios_is_only_synthetic_label(self):
        output = self.output("ios-fixture", "fixture-build-A", "ios", "Release")
        artifact = json.loads(output["synthetic-artifact.json"])
        self.assertTrue(artifact["synthetic_only"])
        self.assertEqual((artifact["platform"], artifact["build_type"]), ("ios", "Release"))
        self.assertNotIn("XCFramework", str(artifact))

    def test_publication_allowlist(self):
        approved = {"README.md", "demo.py", "fixtures/sample.env", "tests/test_demo.py"}
        actual = {
            path.relative_to(HERE).as_posix() for path in HERE.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, approved, "unexpected public example file; review its provenance before publishing")

    def test_fixture_has_only_public_data_and_no_private_artifacts(self):
        fixture = (HERE / "fixtures" / "sample.env").read_text()
        self.assertIn("https://example.invalid", fixture)
        self.assertNotIn("token=", fixture.lower())
        self.assertFalse(any((HERE / name).exists() for name in ("engine", "archive.tar.gz", "credentials.json", "release.statement.sig")))


if __name__ == "__main__":
    unittest.main()
