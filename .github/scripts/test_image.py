"""Exercise packaging without building a multi-gigabyte Raspberry Pi image."""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import image


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "stage2").mkdir()
        (self.root / "deploy").mkdir()
        env = patch.dict(os.environ, {
            "RNBO_RUNNER_VERSION": "1.4.6-9",
            "IMAGE_RELEASE": "trixie", "IMAGE_BITS": "64",
            "FIRST_USER_PASS": "spaces ' quotes $(false) `false` $HOME\nnewline",
        })
        env.start()
        self.addCleanup(env.stop)
        git = patch.object(image.subprocess, "check_output", return_value="abc123\n")
        git.start()
        self.addCleanup(git.stop)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def test_both_targets_and_metadata(self):
        payload = bytes(range(256)) * 100
        for release, bits in (("trixie", "64"), ("bookworm", "32")):
            with self.subTest(release=release):
                os.environ.update(IMAGE_RELEASE=release, IMAGE_BITS=bits)
                image.configure(self.root)
                name = image.settings()[3]
                archive = self.root / "deploy" / (name + ".img.zip")
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
                    zipped.writestr(name + ".img", payload)
                image.metadata(self.root)
                entry = json.loads((self.root / "deploy/repo-entry.json").read_text())
                self.assertEqual(entry["extract_sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(entry["extract_size"], len(payload))
                self.assertEqual(entry["image_download_size"], archive.stat().st_size)
                self.assertTrue(entry["url"].endswith(archive.name))
                self.assertEqual(entry["name"], f"RNBO 1.4.6 ({release.title()}, {bits}-bit)")
                self.assertEqual(entry["devices"], [f"pi{n}-{bits}bit" for n in (5, 4, 3)])
                sha = (self.root / "deploy" / (archive.name + ".sha256")).read_text().split()[0]
                self.assertEqual(sha, hashlib.sha256(archive.read_bytes()).hexdigest())
                for path in (self.root / "deploy").iterdir():
                    path.unlink()

    def test_config_round_trips_shell_metacharacters(self):
        image.configure(self.root)
        result = subprocess.run(
            ["bash", "-eu", "-c", f"source {shlex.quote(str(self.root / 'config'))}; printf '%s' \"$FIRST_USER_PASS\""],
            capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, os.environ["FIRST_USER_PASS"])
        self.assertEqual((self.root / "stage2/EXPORT_IMAGE").read_text(), 'IMG_SUFFIX=""\n')
        self.assertTrue(os.access(self.root / "stage2/99-rnbo-verify/00-run.sh", os.X_OK))

    def test_rejects_invalid_versions_and_targets(self):
        for value in ("", "1.4.6", "1.4.6-9\n", "1.4.6-9; touch /tmp/bad", "$(false)"):
            with self.subTest(version=value), patch.dict(os.environ, RNBO_RUNNER_VERSION=value):
                with self.assertRaises(ValueError):
                    image.configure(self.root)
        with patch.dict(os.environ, IMAGE_BITS="32"):
            with self.assertRaises(ValueError):
                image.configure(self.root)
        self.assertFalse((self.root / "config").exists())

    def test_rejects_stale_builds(self):
        (self.root / "work").mkdir()
        (self.root / "work/stale").touch()
        with self.assertRaises(ValueError):
            image.configure(self.root)

    def test_rejects_wrong_archive_contents(self):
        image.configure(self.root)
        archive = self.root / "deploy" / (image.settings()[3] + ".img.zip")
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("old-name.img", b"image")
        with self.assertRaises(ValueError):
            image.metadata(self.root)
        self.assertFalse((self.root / "deploy/repo-entry.json").exists())

    def test_rejects_corrupt_zip(self):
        image.configure(self.root)
        name = image.settings()[3]
        archive = self.root / "deploy" / (name + ".img.zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as zipped:
            zipped.writestr(name + ".img", b"unique payload")
        archive.write_bytes(archive.read_bytes().replace(b"unique payload", b"broken payload"))
        with self.assertRaises(zipfile.BadZipFile):
            image.metadata(self.root)


if __name__ == "__main__":
    unittest.main()
