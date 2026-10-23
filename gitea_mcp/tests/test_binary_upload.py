"""Tests for binary upload extension."""
import base64
import hashlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import binary_upload as upload

PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n%%EOF\n\x00\xff"

class UploadTests(unittest.TestCase):
    def setUp(self):
        self.env = dict(os.environ)
        os.environ["GITEA_MCP_READ_ONLY"] = "false"
        os.environ["GITEA_MCP_UPLOAD_ALLOWED_HOSTS"] = "files.oaiusercontent.com"
    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
    def _req(self, name, args):
        return {"id": 1, "params": {"name": name, "arguments": {
            "owner": "riederch", "repo": "test", "path": "source.pdf",
            "message": "Add PDF", **args}}}
    def test_fileparams_schema(self):
        native, fallback = upload.tool_definitions()
        self.assertEqual(native["_meta"]["openai/fileParams"], ["file"])
        self.assertNotIn("_meta", fallback)
    def test_binary_integrity(self):
        with mock.patch.object(upload, "_commit_to_gitea", return_value={"sha256": hashlib.sha256(PDF).hexdigest()}) as commit:
            result = upload.handle_tool(self._req("upload_binary_base64", {"content_base64": base64.b64encode(PDF).decode()}), "Bearer sample")
            self.assertNotIn("isError", result["result"])
            self.assertEqual(commit.call_args.args[6], PDF)
    def test_read_only(self):
        os.environ["GITEA_MCP_READ_ONLY"] = "true"
        self.assertEqual(upload.tool_definitions(), [])
        result = upload.handle_tool(self._req("upload_binary_base64", {"content_base64": "AA=="}), "Bearer sample")
        self.assertTrue(result["result"]["isError"])
    def test_ssrf(self):
        for url in ["http://files.oaiusercontent.com/file", "https://127.0.0.1/file", "https://localhost/file", "https://evil.com/file"]:
            with self.assertRaises(upload.UploadError):
                upload._validate_download_url(url)
    def test_path_traversal(self):
        for path in ["../secret", "/absolute", "a//b", "a/./b", "a\\b"]:
            with self.assertRaises(upload.UploadError):
                upload._repository_fields(self._req("upload_binary_base64", {"path": path, "content_base64": "AA=="})["params"]["arguments"])
    def test_bad_base64_and_sha_mismatch(self):
        for extra in [{"content_base64": "%%%"}, {"content_base64": "AA==", "expected_sha256": "a" * 64}]:
            r = upload.handle_tool(self._req("upload_binary_base64", extra), "Bearer sample")
            self.assertTrue(r["result"]["isError"])
    def test_signed_url_never_returned(self):
        r = upload.handle_tool(self._req("upload_binary_file", {"file": {"file_id": "test", "download_url": "https://evil.com/?secret=12345"}}), "Bearer sample")
        self.assertNotIn("12345", str(r))

if __name__ == "__main__":
    unittest.main()
