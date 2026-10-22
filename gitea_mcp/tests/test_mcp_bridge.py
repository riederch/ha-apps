import base64
import json
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import mcp_bridge as bridge

class MCPBridgeTests(unittest.TestCase):
    def file_response(self, content):
        encoded = base64.b64encode(content).decode("ascii")
        return {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":json.dumps({"content":encoded,"encoding":"base64","sha":"abcdef"})}]}}
    def test_tool_schema(self):
        response = {"result":{"tools":[{"name":"get_file_contents","inputSchema":{"type":"object","properties":{}}},{"name":"get_me"}]}}
        out=bridge.transform(response,{"method":"tools/list"})
        self.assertIn("outputSchema",out["result"]["tools"][0])
        self.assertNotIn("outputSchema",out["result"]["tools"][1])
    def test_text_file(self):
        request={"method":"tools/call","params":{"name":"get_file_contents","arguments":{"path":"sample.csv","ref":"main"}}}
        out=bridge.transform(self.file_response(b"a;b\n1;2\n"),request)["result"]
        self.assertEqual(out["structuredContent"]["content"],"a;b\n1;2\n")
        self.assertEqual(out["structuredContent"]["sha"],"abcdef")
    def test_line_selection(self):
        result=bridge.adapt_file_result(self.file_response(b"a\nb\nc\n"),{"path":"file","start_line":2,"end_line":2})
        self.assertEqual(result["result"]["structuredContent"]["content"],"b\n")
    def test_large_chunk(self):
        data=("abcd;"*60+"\n").encode()*400
        r=bridge.adapt_file_result(self.file_response(data),{"path":"file","max_bytes":2048})
        c=r["result"]["structuredContent"]
        self.assertTrue(c["truncated"])
        self.assertGreater(c["next_start_line"],1)
    def test_binary(self):
        r=bridge.adapt_file_result(self.file_response(bytes([0,255,1])),{"path":"bin"})
        self.assertEqual(r["result"]["structuredContent"]["encoding"],"base64")
    def test_error_unchanged(self):
        msg={"result":{"isError":True,"content":[{"type":"text","text":"error"}]}}
        self.assertEqual(bridge.adapt_file_result(msg,{}),msg)
    def test_other_call_unchanged(self):
        msg={"result":{"content":[{"type":"text","text":"hello"}]}}
        self.assertEqual(bridge.transform(msg,{"method":"tools/call","params":{"name":"get_me"}}),msg)
    def test_unknown_payload_explicit(self):
        r=bridge.adapt_file_result({"result":{"content":[{"type":"text","text":"{}"}]}},{})
        self.assertTrue(r["result"]["isError"])
