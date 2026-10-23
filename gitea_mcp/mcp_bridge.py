#!/usr/bin/env python3
"""Stateless compatibility bridge for Gitea MCP file responses.

The Gitea MCP binary handles authentication and all repository operations.
This bridge adds structuredContent and chunked reads for get_file_contents.
No credentials, file content or request paths are logged or persisted.
"""
import base64
import binary_upload
import binascii
import http.client
import json
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8081
LISTEN_PORT = 8080
MAX_BODY = 16 * 1024 * 1024
MAX_OUTPUT_BYTES = 65536
HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "content-length",
    "content-encoding",
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "encoding": {"type": "string", "enum": ["utf-8", "base64"]},
        "path": {"type": "string"},
        "ref": {"type": "string"},
        "sha": {"type": "string"},
        "size_bytes": {"type": "integer", "minimum": 0},
        "start_line": {"type": "integer", "minimum": 1},
        "end_line": {"type": "integer", "minimum": 0},
        "total_lines": {"type": "integer", "minimum": 0},
        "next_start_line": {"type": "integer", "minimum": 1},
        "start_byte": {"type": "integer", "minimum": 0},
        "next_start_byte": {"type": "integer", "minimum": 0},
        "truncated": {"type": "boolean"},
    },
    "required": ["content", "encoding", "truncated"],
    "additionalProperties": False,
}


def bounded_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (ValueError, TypeError, OverflowError):
        return default
    return max(minimum, min(maximum, number))


def request_args(request):
    if not isinstance(request, dict):
        return {}
    params = request.get("params") or {}
    arguments = params.get("arguments") or {}
    return arguments if isinstance(arguments, dict) else {}


def is_file_call(request):
    return (
        isinstance(request, dict)
        and request.get("method") == "tools/call"
        and (request.get("params") or {}).get("name") == "get_file_contents"
    )


def adapt_tool_list(message):
    result = message.get("result")
    if not isinstance(result, dict):
        return message
    for tool in result.get("tools", []):
        if tool.get("name") != "get_file_contents":
            continue
        tool["outputSchema"] = OUTPUT_SCHEMA
        props = tool.setdefault("inputSchema", {"type": "object"}).setdefault(
            "properties", {}
        )
        props["start_line"] = {
            "type": "integer", "minimum": 1,
            "description": "First 1-based line to read; default 1.",
        }
        props["end_line"] = {
            "type": "integer", "minimum": 1,
            "description": "Optional inclusive last line.",
        }
        props["start_byte"] = {
            "type": "integer", "minimum": 0,
            "description": "Optional byte offset for binary files.",
        }
        props["max_bytes"] = {
            "type": "integer", "minimum": 1024, "maximum": MAX_OUTPUT_BYTES,
            "description": "Maximum UTF-8 bytes per response; default 65536.",
        }
    result.setdefault("tools", []).extend(binary_upload.tool_definitions())
    return message


def decode_upstream(result):
    blocks = result.get("content", [])
    if not isinstance(blocks, list):
        return None
    text = next(
        (b.get("text") for b in blocks if isinstance(b, dict)
         and b.get("type") == "text" and isinstance(b.get("text"), str)),
        None,
    )
    if text is None:
        return None
    try:
        meta = json.loads(text)
    except (TypeError, ValueError):
        return text.encode("utf-8"), {}
    if isinstance(meta, str):
        return meta.encode("utf-8"), {}
    if not isinstance(meta, dict) or not isinstance(meta.get("content"), str):
        return None
    if meta.get("encoding") == "base64":
        try:
            data = base64.b64decode(meta["content"], validate=False)
        except (ValueError, binascii.Error):
            return None
    else:
        data = meta["content"].encode("utf-8")
    return data, meta


def extract_file_chunk(data, arguments, metadata):
    path = str(arguments.get("path", ""))
    ref = str(arguments.get("ref", ""))
    limit = bounded_int(
        arguments.get("max_bytes"), MAX_OUTPUT_BYTES, 1024, MAX_OUTPUT_BYTES
    )
    common = {"path": path, "ref": ref, "size_bytes": len(data)}
    if metadata.get("sha"):
        common["sha"] = str(metadata["sha"])
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        offset = bounded_int(arguments.get("start_byte"), 0, 0, len(data))
        end = min(len(data), offset + limit)
        result = {
            **common, "encoding": "base64",
            "content": base64.b64encode(data[offset:end]).decode("ascii"),
            "start_byte": offset, "truncated": end < len(data),
        }
        if end < len(data):
            result["next_start_byte"] = end
        return result

    lines = content.splitlines(keepends=True)
    total = len(lines)
    start = bounded_int(arguments.get("start_line"), 1, 1, max(1, total + 1))
    end_limit = bounded_int(
        arguments.get("end_line"), total, 1, max(1, total)
    )
    end_limit = max(start - 1, end_limit)
    pieces = []
    size = 0
    index = start - 1
    while index < min(total, end_limit):
        line = lines[index]
        line_size = len(line.encode("utf-8"))
        if line_size > limit and not pieces:
            raise ValueError(
                "File line exceeds max_bytes; split the source line before reading"
            )
        if size + line_size > limit:
            break
        pieces.append(line)
        size += line_size
        index += 1
    next_line = index + 1
    result = {
        **common, "encoding": "utf-8", "content": "".join(pieces),
        "start_line": start, "end_line": index, "total_lines": total,
        "truncated": index < min(total, end_limit)
        or (index < total and arguments.get("end_line") is None),
    }
    if index < total:
        result["next_start_line"] = next_line
    return result


def adapt_file_result(message, arguments):
    result = message.get("result")
    if not isinstance(result, dict) or result.get("isError"):
        return message
    if isinstance(result.get("structuredContent"), dict) and (
        "content" in result["structuredContent"]
    ):
        return message
    decoded = decode_upstream(result)
    if decoded is None:
        result["isError"] = True
        result.pop("structuredContent", None)
        result["content"] = [{
            "type": "text",
            "text": "Unsupported Gitea MCP file payload; expected text ContentsResponse",
        }]
        return message
    data, metadata = decoded
    try:
        structured = extract_file_chunk(data, arguments, metadata)
    except ValueError as exc:
        result["isError"] = True
        result.pop("structuredContent", None)
        result["content"] = [{"type": "text", "text": str(exc)}]
        return message
    result["structuredContent"] = structured
    result["content"] = [{
        "type": "text", "text": json.dumps(structured, ensure_ascii=False)
    }]
    return message


def transform(message, request):
    if not isinstance(message, dict) or not isinstance(request, dict):
        return message
    if request.get("method") == "tools/list":
        return adapt_tool_list(message)
    if is_file_call(request):
        return adapt_file_result(message, request_args(request))
    return message


class BridgeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *_args):
        # Avoid logging request paths or credentials.
        pass

    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def do_DELETE(self):
        self.forward()

    def do_OPTIONS(self):
        self.forward()

    def forward(self):
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self.send_error(400, "Invalid request length")
            return
        if length < 0 or length > MAX_BODY:
            self.send_error(413, "MCP request too large")
            return
        if self.headers.get("Transfer-Encoding"):
            self.send_error(501, "Chunked requests are unsupported")
            return

        body = self.rfile.read(length) if length else None
        request = None
        if body and self.path.split("?", 1)[0] == "/mcp":
            try:
                request = json.loads(body)
            except (ValueError, TypeError):
                pass

        if request and request.get("method") == "tools/call":
            name = (request.get("params") or {}).get("name")
            if name in binary_upload.TOOL_NAMES:
                auth = self.headers.get("Authorization", "")
                payload = json.dumps(binary_upload.handle_tool(request, auth), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True
                return

        backend_body = body
        if is_file_call(request):
            upstream_request = json.loads(body)
            arguments = upstream_request["params"].get("arguments") or {}
            for key in ("start_line", "end_line", "start_byte", "max_bytes"):
                arguments.pop(key, None)
            arguments["withLines"] = False
            upstream_request["params"]["arguments"] = arguments
            backend_body = json.dumps(upstream_request).encode("utf-8")

        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in HOP_HEADERS and k.lower() != "host"
        }
        headers["Accept-Encoding"] = "identity"
        conn = http.client.HTTPConnection(
            BACKEND_HOST, self.server.backend_port, timeout=60
        )
        sent_headers = False
        try:
            conn.request(self.command, self.path, body=backend_body, headers=headers)
            response = conn.getresponse()
            content_type = response.getheader("Content-Type", "")
            if content_type.lower().startswith("text/event-stream"):
                self.send_response(response.status, response.reason)
                for key, val in response.getheaders():
                    if key.lower() not in HOP_HEADERS:
                        self.send_header(key, val)
                self.send_header("Connection", "close")
                self.end_headers()
                sent_headers = True
                self.forward_sse(response, request)
            else:
                payload = response.read(MAX_BODY + 1)
                if len(payload) > MAX_BODY:
                    raise ValueError("Upstream response exceeded safe size limit")
                if request and "json" in content_type.lower():
                    try:
                        parsed = json.loads(payload)
                        payload = json.dumps(
                            transform(parsed, request), ensure_ascii=False
                        ).encode("utf-8")
                    except (ValueError, TypeError):
                        pass
                self.send_response(response.status, response.reason)
                for key, val in response.getheaders():
                    if key.lower() not in HOP_HEADERS:
                        self.send_header(key, val)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                sent_headers = True
                self.wfile.write(payload)
        except (OSError, ValueError, http.client.HTTPException) as exc:
            print("MCP bridge upstream error:", type(exc).__name__, file=sys.stderr)
            if not sent_headers:
                try:
                    self.send_error(502, "MCP upstream temporarily unavailable")
                except OSError:
                    pass
        finally:
            conn.close()
            self.close_connection = True

    def forward_sse(self, response, request):
        pending = []
        event_size = 0
        while True:
            part = response.readline(MAX_BODY + 1)
            if not part:
                if pending:
                    self.wfile.write(b"".join(pending))
                return
            event_size += len(part)
            if event_size > MAX_BODY:
                raise ValueError("MCP SSE event exceeded safe size limit")
            pending.append(part)
            if part.strip():
                continue
            event_bytes = b"".join(pending)
            pending = []
            event_size = 0
            if request:
                lines = event_bytes.splitlines(keepends=True)
                data = b"".join(
                    line[5:].strip() for line in lines
                    if line.startswith(b"data:")
                )
                if data:
                    try:
                        parsed = json.loads(data)
                        transformed = json.dumps(
                            transform(parsed, request), ensure_ascii=False
                        ).encode("utf-8")
                        event_bytes = b"".join(
                            line for line in lines
                            if not line.startswith(b"data:")
                        ).rstrip(b"\r\n") + b"\ndata: " + transformed + b"\n\n"
                    except (ValueError, TypeError):
                        pass
            self.wfile.write(event_bytes)
            self.wfile.flush()


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, backend_port=BACKEND_PORT):
        super().__init__(address, BridgeHandler)
        self.backend_port = backend_port


def main():
    if len(sys.argv) < 2:
        sys.exit("Missing Gitea MCP upstream command")
    upstream = subprocess.Popen(sys.argv[1:])
    server = BridgeServer(("0.0.0.0", LISTEN_PORT))
    print(
        f"Gitea MCP bridge :{LISTEN_PORT} -> 127.0.0.1:{BACKEND_PORT}",
        flush=True,
    )

    def stop(_signum=None, _frame=None):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def watch_upstream():
        upstream.wait()
        stop()

    threading.Thread(target=watch_upstream, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        if upstream.poll() is None:
            upstream.terminate()
            try:
                upstream.wait(timeout=5)
            except subprocess.TimeoutExpired:
                upstream.kill()
                upstream.wait()


if __name__ == "__main__":
    main()
