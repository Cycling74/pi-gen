"""Regressions for verification against fresh package-manager state."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class VerificationTests(unittest.TestCase):
    def verify(self, hold="hold", expected_version="1.4.6-9", audio=True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "os-release").write_text("VERSION_CODENAME=trixie\n")
            (root / "audio.conf").write_text(
                "@audio - rtprio 95\n@audio - memlock unlimited\n")
            commands = {
                "dpkg": "printf 'arm64\\n'",
                "dpkg-query": """case "$*" in
                    *'${Version}'*) printf '1.4.6-9' ;;
                    *'${db:Status-Want}'*) printf '%s' "$TEST_HOLD" ;;
                    *) exit 2 ;;
                esac""",
                # Reproduce the failure: apt-mark omits a package dpkg has held.
                "apt-mark": "exit 0",
                "id": '''printf '%s\\n' "$TEST_GROUPS"''',
            }
            for name, body in commands.items():
                command = root / name
                command.write_text("#!/bin/sh\n" + body + "\n")
                command.chmod(0o755)
            env = dict(os.environ, PATH=f"{temp}:{os.environ['PATH']}",
                       VERIFY_FIXTURE=temp, TEST_HOLD=hold,
                       TEST_GROUPS="pi audio" if audio else "pi",
                       RNBO_RUNNER_VERSION=expected_version, ARCH="arm64",
                       RELEASE="trixie", FIRST_USER_NAME="pi")
            # Execute the actual generated chroot script against fixture paths.
            harness = r'''
                on_chroot() {
                    sed -e "s|/etc/os-release|$VERIFY_FIXTURE/os-release|g" \
                        -e "s|/etc/security/limits.d/audio.conf|$VERIFY_FIXTURE/audio.conf|g" \
                        | bash -e "$@"
                }
                export -f on_chroot
                bash -e "$1"
            '''
            return subprocess.run(
                ["bash", "-c", harness, "--", str(Path(__file__).with_name("verify-image.sh"))],
                env=env, capture_output=True, text=True)

    def test_accepts_dpkg_hold_even_when_apt_mark_listing_is_empty(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RNBO package hold: expected [hold], found [hold]", result.stdout)

    def test_rejects_unheld_runner_with_diagnostic(self):
        result = self.verify(hold="install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Image verification failed: RNBO package hold", result.stderr)

    def test_rejects_wrong_version_with_diagnostic(self):
        result = self.verify(expected_version="1.4.5-9")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Image verification failed: RNBO runner version", result.stderr)

    def test_rejects_missing_audio_membership(self):
        result = self.verify(audio=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("user is not in the audio group", result.stderr)


if __name__ == "__main__":
    unittest.main()
