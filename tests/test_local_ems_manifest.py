# SPDX-License-Identifier: GPL-3.0-or-later
"""Guard against hiding the EMS under the Home Assistant Helpers tab."""
import json
import unittest
from pathlib import Path

MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "local_ems"
    / "manifest.json"
)


class LocalEMSManifestTests(unittest.TestCase):
    def test_is_visible_as_integration_not_helper(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], "local_ems")
        self.assertEqual(manifest["integration_type"], "hub")
        self.assertTrue(manifest["config_flow"])

    def test_recorder_integration_and_version(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertIn("recorder", manifest["dependencies"])
        self.assertEqual(manifest["version"], "0.5.0b3")


if __name__ == "__main__":
    unittest.main()
