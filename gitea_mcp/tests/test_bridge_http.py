"""HTTP integration tests for the Gitea MCP compatibility bridge.

Runs against an isolated localhost JSON-RPC backend, without Gitea credentials,
external network calls, or a running production Gitea instance.
"""
import base64
import http.client
import json
import os
import pathlib
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import mcp_bridge as bridge


class MockMCPBackend(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        size = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(size))
        self.server.requests.append({
            "method": request.get("method"),
            "params": request.get("params"),
            "auth": self.headers.get("Authorization"),
            "path": self.path,
        })
        method = request.get("method")
        if method == "tools/list":
            result = {"tools": [
                {"name": "get_file_contents",
                 "inputSchema": {"type": "object", "properties": {}}},
                {"name": "get_me",
                 "inputSchema": {"type": "object", "properties": {}}},
            ]}
        elif method == "tools/call" and (request.get("params") or {}).get("name") == "get_file_contents":
            source = b"first\nsecond\nthird\n"
            result = {"content": [{
                "type": "text",
                "text": json.dumps({
                    "content": base64.b64encode(source).decode("ascii"),
                    "encoding": "base64", "sha": "sample-blob",
                }),
            }]}
        else:
            result = {"content": [{"type": "text", "text": "unmodified"}]}
        response = json.dumps({
            "jsonrpc": "2.0", "id": request.get("id"), "result": result,
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


class MCPBridgeHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = ThreadingHTTPServer(("127.0.0.1", 0), MockMCPBackend)
        cls.backend.requests = []
        cls.backend_thread = threading.Thread(
            target=cls.backend.serve_forever, daemon=True,
        )
        cls.backend_thread.start()
        cls.bridge = bridge.BridgeServer(
            ("127.0.0.1", 0), backend_port=cls.backend.server_port,
        )
        cls.bridge_thread = threading.Thread(
            target=cls.bridge.serve_forever, daemon=True,
        )
        cls.bridge_thread.start()

    @classmethod
    def tearDownClass(cls):
        for server, thread in ((cls.bridge, cls.bridge_thread),
                               (cls.backend, cls.backend_thread)):
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def setUp(self):
        self.backend.requests.clear()

    def call(self, method, params=None, token="Bearer test-only-token"):
        payload = json.dumps({
            "jsonrpc": "2.0", "id": 7, "method": method,
            "params": params or {},
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = token
        conn = http.client.HTTPConnection("127.0.0.1", self.bridge.server_port, timeout=5)
        try:
            conn.request("POST", "/mcp", body=payload, headers=headers)
            response = conn.getresponse()
            content = response.read()
            return response.status, json.loads(content)
        finally:
            conn.close()

    def test_tool_list_adds_structured_schema_and_upload_tools(self):
        with mock.patch.dict(os.environ, {"GITEA_MCP_READ_ONLY": "false"}):
            status, response = self.call("tools/list")
        self.assertEqual(status, 200)
        tools = {tool["name"]: tool for tool in response["result"]["tools"]}
        self.assertIn("outputSchema", tools["get_file_contents"])
        self.assertIn("start_line", tools["get_file_contents"]["inputSchema"]["properties"])
        self.assertIn("upload_binary_file", tools)
        self.assertIn("upload_binary_base64", tools)
        self.assertNotIn("outputSchema", tools["get_me"])
        self.assertEqual(self.backend.requests[-1]["auth"], "Bearer test-only-token")

    def test_file_chunk_is_structured_and_original_request_is_sanitized(self):
        status, response = self.call("tools/call", {
            "name": "get_file_contents",
            "arguments": {
                "owner": "example", "repo": "fixture",
                "path": "example.txt", "ref": "main",
                "start_line": 2, "end_line": 2, "max_bytes": 1024,
            },
        })
        self.assertEqual(status, 200)
        content = response["result"]["structuredContent"]
        self.assertEqual(content["content"], "second\n")
        self.assertEqual(content["sha"], "sample-blob")
        self.assertEqual(content["start_line"], 2)
        self.assertEqual(content["end_line"], 2)
        self.assertEqual(content["next_start_line"], 3)
        forwarded = self.backend.requests[-1]
        self.assertEqual(forwarded["auth"], "Bearer test-only-token")
        self.assertEqual(forwarded["path"], "/mcp")
        args = forwarded["params"]["arguments"]
        self.assertTrue(args["withLines"] is False)
        self.assertNotIn("start_line", args)
        self.assertNotIn("end_line", args)
        self.assertNotIn("max_bytes", args)

    def test_readonly_excludes_uploads_and_rejects_direct_call(self):
        with mock.patch.dict(os.environ, {"GITEA_MCP_READ_ONLY": "true"}):
            status, response = self.call("tools/list")
            names = {tool["name"] for tool in response["result"]["tools"]}
            self.assertNotIn("upload_binary_file", names)
            self.assertNotIn("upload_binary_base64", names)
            self.backend.requests.clear()
            status, response = self.call("tools/call", {
                "name": "upload_binary_base64",
                "arguments": {"content_base64": "AA=="},
            })
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["isError"])
        self.assertEqual(self.backend.requests, [])

    def test_binary_upload_without_token_fails_before_backend(self):
        status, response = self.call("tools/call", {
            "name": "upload_binary_file", "arguments": {},
        }, token=None)
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["isError"])
        self.assertEqual(self.backend.requests, [])

    def test_other_tool_payload_remains_unchanged(self):
        status, response = self.call("tools/call", {
            "name": "get_me", "arguments": {},
        })
        self.assertEqual(status, 200)
        self.assertEqual(response["result"]["content"][0]["text"], "unmodified")
        self.assertNotIn("structuredContent", response["result"])


if __name__ == "__main__":
    unittest.main()
