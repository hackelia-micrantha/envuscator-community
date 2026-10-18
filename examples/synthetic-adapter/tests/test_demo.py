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
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import demo  # noqa: E402


def tracked_public_files() -> set[str]:
    root = HERE.parents[1]
    tracked = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z", "--", "examples/synthetic-adapter"]
    )
    prefix = "examples/synthetic-adapter/"
    return {
        entry.decode("utf-8")[len(prefix):]
        for entry in tracked.split(bytes([0])) if entry
    }


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

    def test_partial_write_failure_keeps_destination_absent(self):
        destination = self.root / "incomplete"
        original_open = demo.os.open
        attempted = 0
        names = ("synthetic-artifact.json", "synthetic-manifest.json", "synthetic-result.json")

        def fail_second_staged_artifact(path, flags, mode=0o777, **kwargs):
            nonlocal attempted
            if Path(path).name in names:
                attempted += 1
                self.assertFalse(destination.exists(), "partial output must stay private")
                if attempted == 2:
                    raise OSError("synthetic disk failure")
            return original_open(path, flags, mode, **kwargs)

        with mock.patch.object(demo.os, "open", side_effect=fail_second_staged_artifact):
            with self.assertRaises(demo.DemoDenied):
                demo.execute(self.config, destination, "fixture-A", "android", "Debug")
        self.assertEqual(attempted, 2)
        self.assertFalse(destination.exists())
        self.output("incomplete")

    def test_concurrent_destination_creation_never_overwrites(self):
        destination = self.root / "raced"
        actual_publish = demo._publish_no_replace

        def competing_creator(staged, output):
            self.assertFalse(destination.exists())
            destination.mkdir()
            (destination / "unrelated.txt").write_text("keep")
            return actual_publish(staged, output)

        with mock.patch.object(demo, "_publish_no_replace", side_effect=competing_creator):
            with self.assertRaises(demo.DemoDenied):
                demo.execute(self.config, destination, "fixture-A", "android", "Debug")
        self.assertEqual((destination / "unrelated.txt").read_text(), "keep")
        self.assertEqual([p.name for p in destination.iterdir()], ["unrelated.txt"])

    def test_failure_never_unlinks_replacement_artifact(self):
        destination = self.root / "raced-files"
        original_open = demo.os.open
        mutated = False

        def adversarial_failure(path, flags, mode=0o777, **kwargs):
            nonlocal mutated
            if Path(path).name == "synthetic-manifest.json" and not mutated:
                mutated = True
                self.assertFalse(destination.exists())
                destination.mkdir()
                (destination / "synthetic-artifact.json").write_text("unrelated")
                raise OSError("injected staging failure")
            return original_open(path, flags, mode, **kwargs)

        with mock.patch.object(demo.os, "open", side_effect=adversarial_failure):
            with self.assertRaises(demo.DemoDenied):
                demo.execute(self.config, destination, "fixture-A", "android", "Debug")
        self.assertTrue(mutated)
        self.assertEqual((destination / "synthetic-artifact.json").read_text(), "unrelated")

    def test_reject_embedded_nul_without_truncated_publication(self):
        truncated_target = self.root / "victim"
        with self.assertRaises(demo.DemoDenied):
            demo.execute(self.config, self.root / ("victim" + chr(0) + "suffix"),
                         "fixture-A", "android", "Debug")
        self.assertFalse(truncated_target.exists())

    def test_close_error_after_atomic_publish_does_not_report_failure(self):
        destination = self.root / "committed"
        original_close = demo.os.close
        failed = False

        def close_after_commit(fd):
            nonlocal failed
            original_close(fd)
            if destination.exists() and not failed:
                failed = True
                raise OSError("simulated descriptor close failure")

        with mock.patch.object(demo.os, "close", side_effect=close_after_commit):
            demo.execute(self.config, destination, "fixture-A", "android", "Debug")
        self.assertTrue(failed)
        self.assertEqual(len(list(destination.iterdir())), 3)

    def test_temp_cleanup_error_after_atomic_publish_is_success(self):
        destination = self.root / "committed-cleanup-error"
        original_temporary_directory = demo.tempfile.TemporaryDirectory

        class CleanupFailure:
            def __init__(self, **kwargs):
                self.inner = original_temporary_directory(**kwargs)

            def __enter__(self):
                return self.inner.__enter__()

            def __exit__(self, *args):
                self.inner.__exit__(*args)
                raise OSError("simulated cleanup failure after publication")

        with mock.patch.object(demo.tempfile, "TemporaryDirectory", side_effect=CleanupFailure):
            demo.execute(self.config, destination, "fixture-A", "android", "Debug")
        self.assertEqual(len(list(destination.iterdir())), 3)

    def test_publication_allowlist(self):
        approved = {"README.md", "demo.py", "fixtures/sample.env", "tests/test_demo.py"}
        self.assertEqual(
            tracked_public_files(), approved,
            "unexpected tracked public example file; review its provenance before publishing",
        )

    def test_publication_allowlist_detects_tracked_bytecode(self):
        approved = {"README.md", "demo.py", "fixtures/sample.env", "tests/test_demo.py"}
        target = "examples/synthetic-adapter/__pycache__/demo.cpython-313.pyc"
        with mock.patch.object(subprocess, "check_output", return_value=target.encode() + bytes([0])):
            self.assertNotEqual(tracked_public_files(), approved)

    def test_fixture_has_only_public_data_and_no_private_artifacts(self):
        fixture = (HERE / "fixtures" / "sample.env").read_text()
        self.assertIn("https://example.invalid", fixture)
        self.assertNotIn("token=", fixture.lower())
        self.assertFalse(any((HERE / name).exists() for name in ("engine", "archive.tar.gz", "credentials.json", "release.statement.sig")))


if __name__ == "__main__":
    unittest.main()
