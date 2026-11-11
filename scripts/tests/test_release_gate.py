"""Adversarial tests for the always-running Home Assistant app release gate.

Each test modifies a single file *in memory* and verifies that the validator
fails closed. Production YAML, Dockerfiles and the working tree are untouched.
"""
import contextlib
import io
import pathlib
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from scripts import verify_ha_app_versions as gate


class ReleaseGateTests(unittest.TestCase):
    def run_gate(self, target=None, pattern=None, replacement=None):
        original_read = gate.read
        applied = []

        def fake_read(path):
            value = original_read(path)
            if path == target:
                updated, count = re.subn(pattern, replacement, value, count=1, flags=re.MULTILINE)
                self.assertEqual(count, 1, "Test mutation anchor not found in " + path)
                applied.append(path)
                return updated
            return value

        stderr = io.StringIO()
        stdout = io.StringIO()
        with mock.patch.object(gate, "read", side_effect=fake_read):
            with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                code = gate.main()
        if target:
            self.assertEqual(applied, [target])
        return code, stderr.getvalue(), stdout.getvalue()

    def expect_rejected(self, path, pattern, replacement, error_fragment):
        code, stderr, stdout = self.run_gate(path, pattern, replacement)
        self.assertEqual(code, 1, stdout)
        self.assertIn("HA app release gate FAILED", stderr)
        self.assertIn(error_fragment, stderr)

    def test_actual_repo_versions_pass(self):
        code, stderr, stdout = self.run_gate()
        self.assertEqual(code, 0, stderr)
        self.assertIn("HA app release gate OK", stdout)

    def test_mcp_image_drift_fails(self):
        self.expect_rejected(
            "gitea_mcp/Dockerfile",
            r"^FROM docker\\.gitea\\.com/gitea-mcp-server:[0-9.]+ AS upstream$",
            "FROM docker.gitea.com/gitea-mcp-server:9.9.9 AS upstream",
            "gitea_mcp: app version",
        )

    def test_runner_build_label_drift_fails(self):
        self.expect_rejected(
            "gitea_runner/Dockerfile",
            r"^ARG BUILD_VERSION=[0-9A-Za-z.+-]+$",
            "ARG BUILD_VERSION=0.0.0-rch1",
            "Gitea Runner BUILD_VERSION",
        )

    def test_runner_banner_drift_fails(self):
        self.expect_rejected(
            "gitea_runner/run.sh",
            r"Starting Gitea Runner [0-9.]+",
            "Starting Gitea Runner 0.0.0",
            "Gitea Runner startup banner",
        )

    def test_cloudflared_app_version_drift_fails(self):
        self.expect_rejected(
            "cloudflared_auth/config.yaml",
            r'^version: "[0-9.]+-rch[0-9]+"$',
            'version: "0.0.0-rch1"',
            "cloudflared_auth: app version",
        )

    def test_vaultwarden_backup_version_drift_fails(self):
        self.expect_rejected(
            "vaultwarden/rootfs/etc/s6-overlay/s6-rc.d/vaultwarden/run",
            r'local migration_version="[0-9.]+"',
            'local migration_version="0.0.0"',
            "Vaultwarden rollback snapshot",
        )

    def test_missing_app_version_fails(self):
        self.expect_rejected(
            "gitea_mcp/config.yaml",
            r'^version: ["\']?[0-9][A-Za-z0-9.+-]*["\']?$',
            "# intentionally removed",
            "gitea_mcp manifest version",
        )

    def test_readme_drift_fails(self):
        self.expect_rejected(
            "README.md",
            r"^- Vaultwarden: `[0-9.]+`",
            "- Vaultwarden: `0.0.0`",
            "README Vaultwarden",
        )

    def test_state_resets_after_failed_check(self):
        with mock.patch.object(gate, "read", side_effect=lambda path: (
            "invalid" if path == "gitea_mcp/config.yaml" else
            (gate.ROOT / path).read_text(encoding="utf-8")
        )):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(gate.main(), 1)
        code, stderr, _ = self.run_gate()
        self.assertEqual(code, 0, stderr)


if __name__ == "__main__":
    unittest.main()
