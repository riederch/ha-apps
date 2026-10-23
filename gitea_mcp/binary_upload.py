"""Safe binary uploads for the existing Home Assistant Gitea MCP bridge.

Native ChatGPT files are passed by openai/fileParams as short-lived URLs.
Only the requested file bytes are sent to the configured Gitea instance.
"""
import base64
import binascii
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request

TOOL_NAMES = frozenset(("upload_binary_file", "upload_binary_base64"))
BASE64_LIMIT = 2 * 1024 * 1024

FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "download_url": {"type": "string"},
        "file_id": {"type": "string"},
        "mime_type": {"type": "string"},
        "file_name": {"type": "string"},
    },
    "required": ["download_url", "file_id"],
    "additionalProperties": False,
}
COMMON_PROPERTIES = {
    "owner": {"type": "string", "description": "Gitea repository owner"},
    "repo": {"type": "string", "description": "Gitea repository name"},
    "path": {"type": "string", "description": "Relative destination path in repository"},
    "branch_name": {"type": "string", "description": "Branch; omit for repository default"},
    "message": {"type": "string", "description": "Git commit message"},
    "sha": {"type": "string", "description": "Current Git blob SHA for explicit replacement; omit to create only"},
    "expected_sha256": {"type": "string", "description": "Optional expected SHA-256 hex of original bytes"},
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "owner": {"type": "string"}, "repo": {"type": "string"},
        "path": {"type": "string"}, "size_bytes": {"type": "integer"},
        "sha256": {"type": "string"}, "blob_sha": {"type": "string"},
        "commit_sha": {"type": "string"}, "html_url": {"type": "string"},
    },
    "required": ["owner", "repo", "path", "size_bytes", "sha256", "blob_sha", "commit_sha"],
    "additionalProperties": False,
}


def read_only():
    return os.environ.get("GITEA_MCP_READ_ONLY", "false").lower() == "true"


def tool_definitions():
    if read_only():
        return []
    common = ["owner", "repo", "path", "message"]
    annotations = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
    return [
        {
            "name": "upload_binary_file",
            "description": "Commit the original bytes of a ChatGPT attachment to Gitea. Requires an explicit destination path; does not overwrite without sha.",
            "inputSchema": {
                "type": "object",
                "properties": {**COMMON_PROPERTIES, "file": FILE_SCHEMA},
                "required": [*common, "file"],
                "additionalProperties": False,
            },
            "outputSchema": OUTPUT_SCHEMA,
            "annotations": annotations,
            "_meta": {"openai/fileParams": ["file"]},
        },
        {
            "name": "upload_binary_base64",
            "description": "Commit up to 2 MiB of Base64-encoded original bytes to Gitea (non-ChatGPT clients or fallback). No silent overwrites.",
            "inputSchema": {
                "type": "object",
                "properties": {**COMMON_PROPERTIES, "content_base64": {"type": "string"}},
                "required": [*common, "content_base64"],
                "additionalProperties": False,
            },
            "outputSchema": OUTPUT_SCHEMA,
            "annotations": annotations,
        },
    ]


class UploadError(Exception):
    """Human-readable error with no credentials or signed URLs."""


def _required(value, field, max_length=255):
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise UploadError(f"Ungueltiger Parameter: {field}")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise UploadError(f"Ungueltiger Parameter: {field}")
    return value


def _repository_fields(args):
    if not isinstance(args, dict):
        raise UploadError("Argumente muessen ein Objekt sein")
    owner = _required(args.get("owner"), "owner", 100)
    repo = _required(args.get("repo"), "repo", 100)
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", name) and name not in (".", "..") for name in (owner, repo)):
        raise UploadError("Ungueltiger Repository-Name")
    path = _required(args.get("path"), "path", 2048)
    if ("\\" in path or any(segment in ("", ".", "..") for segment in path.split("/"))):
        raise UploadError("Ungueltiger Repository-Pfad")
    message = _required(args.get("message"), "message", 512)
    branch = args.get("branch_name")
    if branch is not None:
        _required(branch, "branch_name", 200)
        if branch.startswith("/") or ".." in branch or "\\" in branch:
            raise UploadError("Ungueltiger Branch")
    sha = args.get("sha")
    if sha is not None and (not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", sha)):
        raise UploadError("Ungueltige aktuelle Git-Blob-SHA")
    expected = args.get("expected_sha256")
    if expected is not None and (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected)):
        raise UploadError("Ungueltige erwartete SHA-256")
    return owner, repo, path, message, branch, sha, expected


def max_file_bytes():
    try:
        mb = int(os.environ.get("GITEA_MCP_UPLOAD_MAX_MB", "16"))
    except ValueError:
        mb = 16
    return max(1, min(mb, 50)) * 1024 * 1024


def _allowed_host(host):
    hosts = os.environ.get("GITEA_MCP_UPLOAD_ALLOWED_HOSTS", "")
    for pattern in hosts.split(","):
        pattern = pattern.strip().lower().rstrip(".")
        if not pattern:
            continue
        if pattern.startswith("*.") and host.endswith(pattern[1:]) and host != pattern[2:]:
            return True
        if host == pattern:
            return True
    return False


def _validate_download_url(url):
    if not isinstance(url, str) or len(url) > 16384 or any(ord(c) < 33 for c in url):
        raise UploadError("Ungueltige Datei-Download-URL")
    try:
        parsed = urllib.parse.urlsplit(url)
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower().rstrip(".")
        port = parsed.port
    except (ValueError, UnicodeError):
        raise UploadError("Ungueltige Datei-Download-URL") from None
    if (parsed.scheme != "https" or not host or parsed.username or parsed.password
            or port not in (None, 443) or not re.fullmatch(r"[a-z0-9.-]+", host)):
        raise UploadError("Downloads erfordern HTTPS auf Port 443 ohne Benutzerinfo")
    try:
        ipaddress.ip_address(host)
        raise UploadError("Download von IP-Adressen ist gesperrt")
    except ValueError:
        pass
    if not _allowed_host(host):
        raise UploadError(f"Datei-Download-Host nicht freigegeben: {host}")
    return parsed, host


def _public_addresses(host):
    try:
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        raise UploadError("Download-Host konnte nicht aufgeloest werden") from None
    addresses = list(dict.fromkeys(item[4][0] for item in answers))
    if not addresses or not all(ipaddress.ip_address(ip).is_global for ip in addresses):
        raise UploadError("Download-Host hat eine nicht-oeffentliche IP-Adresse")
    return addresses


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, 443, timeout=20, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, self.port), timeout=self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def download_file(url, limit):
    # No HTTP proxy, no DNS re-resolution, no private IPs or unverified redirects.
    for _ in range(4):
        parsed, host = _validate_download_url(url)
        address = _public_addresses(host)[0]
        conn = _PinnedHTTPSConnection(host, address)
        try:
            target = parsed.path or "/"
            if parsed.query:
                target += "?" + parsed.query
            conn.request("GET", target, headers={"Accept-Encoding": "identity", "Connection": "close"})
            response = conn.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise UploadError("Download-Weiterleitung ohne Ziel")
                url = urllib.parse.urljoin(url, location)
                continue
            if response.status != 200:
                raise UploadError(f"Datei-Download fehlgeschlagen (HTTP {response.status})")
            if response.getheader("Content-Encoding", "identity").lower() not in ("identity", ""):
                raise UploadError("Komprimierte Download-Antwort nicht unterstuetzt")
            if int(response.getheader("Content-Length") or "0") > limit:
                raise UploadError("Datei ueberschreitet das Upload-Limit")
            data = response.read(limit + 1)
            if len(data) > limit:
                raise UploadError("Datei ueberschreitet das Upload-Limit")
            return data
        except (OSError, ssl.SSLError, http.client.HTTPException):
            raise UploadError("Datei-Download konnte nicht sicher abgeschlossen werden") from None
        finally:
            conn.close()
    raise UploadError("Zu viele Datei-Weiterleitungen")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _commit_to_gitea(owner, repo, path, message, branch, sha, data, authorization):
    host = os.environ.get("GITEA_HOST", "").rstrip("/")
    parsed_host = urllib.parse.urlsplit(host)
    if parsed_host.scheme not in ("https", "http") or not parsed_host.hostname or parsed_host.username or parsed_host.password:
        raise UploadError("Gitea-Host ist nicht konfiguriert")
    api_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    endpoint = host + "/api/v1/repos/" + urllib.parse.quote(owner, safe="") + "/" + urllib.parse.quote(repo, safe="") + "/contents/" + api_path
    payload = {"content": base64.b64encode(data).decode("ascii"), "message": message}
    if branch:
        payload["branch"] = branch
    if sha:
        payload["sha"] = sha
    request = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": authorization, "Content-Type": "application/json", "Accept": "application/json"},
        method="PUT" if sha else "POST",
    )
    context = ssl._create_unverified_context() if os.environ.get("GITEA_INSECURE", "false").lower() == "true" else ssl.create_default_context()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect(), urllib.request.HTTPSHandler(context=context))
    try:
        with opener.open(request, timeout=30) as response:
            result = json.loads(response.read(65537))
    except urllib.error.HTTPError as error:
        raise UploadError(f"Gitea hat den Commit abgelehnt (HTTP {error.code}); existierende Dateien nur mit aktueller sha ersetzen") from None
    except (ValueError, urllib.error.URLError, TimeoutError, OSError):
        raise UploadError("Gitea-Commit fehlgeschlagen") from None
    if not isinstance(result, dict):
        raise UploadError("Gitea lieferte keine gueltige Commit-Antwort")
    content = result.get("content") or {}
    commit = result.get("commit") or {}
    blob_sha = content.get("sha")
    commit_sha = commit.get("sha")
    if not isinstance(blob_sha, str) or not isinstance(commit_sha, str):
        raise UploadError("Gitea-Commit-Antwort enthaelt keine SHAs")
    output = {"owner": owner, "repo": repo, "path": path,
              "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
              "blob_sha": blob_sha, "commit_sha": commit_sha}
    if isinstance(content.get("html_url"), str):
        output["html_url"] = content["html_url"]
    return output


def handle_tool(request, authorization):
    """Return one JSON-RPC response. Never leak signed URLs or bearer tokens."""
    try:
        if read_only():
            raise UploadError("Upload im Read-only-Modus deaktiviert")
        if not isinstance(authorization, str) or not authorization.lower().startswith("bearer ") or not authorization[7:].strip():
            raise UploadError("Gitea-Bearer-Token fehlt")
        args = request.get("params", {}).get("arguments", {})
        owner, repo, path, message, branch, sha, expected = _repository_fields(args)
        name = request["params"]["name"]
        if name == "upload_binary_file":
            file_object = args.get("file")
            if not isinstance(file_object, dict) or not isinstance(file_object.get("file_id"), str) or not file_object["file_id"]:
                raise UploadError("ChatGPT-Dateiobjekt fehlt")
            data = download_file(file_object.get("download_url"), max_file_bytes())
        elif name == "upload_binary_base64":
            value = args.get("content_base64")
            if not isinstance(value, str) or len(value) > (BASE64_LIMIT + 2) * 4 // 3 + 8:
                raise UploadError("Base64-Upload-Limit ueberschritten")
            try:
                data = base64.b64decode(value, validate=True)
            except (ValueError, binascii.Error):
                raise UploadError("Ungueltiges Base64") from None
            if len(data) > BASE64_LIMIT:
                raise UploadError("Base64-Upload-Limit ueberschritten")
        else:
            raise UploadError("Unbekanntes Upload-Tool")
        if expected and hashlib.sha256(data).hexdigest() != expected.lower():
            raise UploadError("SHA-256 der Quelldatei stimmt nicht ueberein")
        result = _commit_to_gitea(owner, repo, path, message, branch, sha, data, authorization)
        body = {"structuredContent": result, "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
    except UploadError as error:
        body = {"isError": True, "content": [{"type": "text", "text": str(error)}]}
    except Exception:
        body = {"isError": True, "content": [{"type": "text", "text": "Unerwarteter Upload-Fehler"}]}
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": body}
