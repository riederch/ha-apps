"""Guard against accidental automatic or off-main GHCR publication.

This test is deliberately source-only; it runs with no GitHub token or
registry access, and guards the release workflow's security boundaries.
"""
from pathlib import Path
import re
import unittest

WORKFLOW = (Path(__file__).resolve().parents[2]
            / ".github/workflows/vaultwarden-image.yaml")


def audit(text):
    errors = []

    def require(ok, msg):
        if not ok:
            errors.append(msg)

    require("workflow_dispatch:" in text and "default: false" in text
            and "type: boolean" in text and "publish:" in text,
            "Manual publish input must be a disabled-by-default Boolean")

    marker = "\n  build:\n"
    publisher_marker = "\n  publish:\n"
    require(marker in text and publisher_marker in text,
            "Build and publish must be separate jobs")
    if marker not in text or publisher_marker not in text:
        return errors

    build = text.split(marker, 1)[1].split(publisher_marker, 1)[0]
    publisher = text.split(publisher_marker, 1)[1]
    header = publisher.split("\n    steps:\n", 1)[0]

    require(bool(re.search(r"(?m)^\s+push:\s+false\s*$", build)),
            "PR/main build must never publish an image")
    require("docker/login-action" not in build,
            "PR/main build must not log in to the registry")
    require("packages: write" not in build,
            "PR/main build must not have package write permission")
    require("packages: write" not in text.split("\njobs:\n", 1)[0],
            "Root workflow token must not have package write permission")

    for required in [
        "github.event_name == 'workflow_dispatch'",
        "github.ref == 'refs/heads/main'",
        "inputs.publish == true",
        "needs: build",
        "environment: vaultwarden-release",
        "packages: write",
    ]:
        require(required in header,
                "Publisher must require " + required)

    require("docker/login-action" in publisher,
            "Only manual publisher may log in to GHCR")
    require(bool(re.search(r"(?m)^\s+push:\s+true\s*$", publisher)),
            "Explicit publisher must upload the validated image")

    return errors


class VaultwardenPublishPolicyTests(unittest.TestCase):
    def setUp(self):
        self.original = WORKFLOW.read_text(encoding="utf-8")

    def test_current_release_policy_is_safe(self):
        self.assertEqual(audit(self.original), [])

    def test_catches_automatic_push(self):
        broken = self.original.replace("push: false", "push: true", 1)
        self.assertIn("PR/main build must never publish an image", audit(broken))

    def test_catches_missing_main_branch_guard(self):
        broken = self.original.replace("github.ref == 'refs/heads/main'",
                                       "github.ref != 'refs/heads/main'", 1)
        self.assertTrue(any("github.ref" in e for e in audit(broken)))

    def test_catches_missing_manual_approval_switch(self):
        broken = self.original.replace("inputs.publish == true",
                                       "inputs.publish != true", 1)
        self.assertTrue(any("inputs.publish" in e for e in audit(broken)))

    def test_catches_unscoped_write_permission(self):
        broken = self.original.replace("permissions:\n  contents: read",
                                       "permissions:\n  contents: read\n  packages: write", 1)
        self.assertTrue(any("Root workflow token" in e for e in audit(broken)))

    def test_catches_missing_environment(self):
        broken = self.original.replace("environment: vaultwarden-release",
                                       "environment: other", 1)
        self.assertTrue(any("environment:" in e for e in audit(broken)))


if __name__ == "__main__":
    unittest.main()
