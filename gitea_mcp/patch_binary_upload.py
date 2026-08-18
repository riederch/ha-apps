#!/usr/bin/env python3
from pathlib import Path

path = Path("/src/operation/repo/file.go")
text = path.read_text(encoding="utf-8")

schema_old = 'mcp.WithString("content", mcp.Required()),'
schema_new = '''mcp.WithString("content", mcp.Description("UTF-8 text content; mutually exclusive with content_base64")),\n\t\tmcp.WithString("content_base64", mcp.Description("raw file bytes encoded as standard base64; mutually exclusive with content")),'''
if schema_old not in text:
    raise SystemExit("binary upload patch: content schema marker not found")
text = text.replace(schema_old, schema_new, 1)

handler_old = 'content, _ := req.GetArguments()["content"].(string)'
handler_new = '''args := req.GetArguments()\n\tcontent, hasContent := args["content"].(string)\n\tcontentBase64, hasBase64 := args["content_base64"].(string)\n\tif hasContent == hasBase64 {\n\t\treturn to.ErrorResult(fmt.Errorf("exactly one of content or content_base64 is required"))\n\t}\n\tencodedContent := contentBase64\n\tif hasBase64 {\n\t\tif _, err := base64.StdEncoding.DecodeString(contentBase64); err != nil {\n\t\t\treturn to.ErrorResult(fmt.Errorf("content_base64 is not valid standard base64: %v", err))\n\t\t}\n\t} else {\n\t\tencodedContent = base64.StdEncoding.EncodeToString([]byte(content))\n\t}'''
if handler_old not in text:
    raise SystemExit("binary upload patch: handler content marker not found")
text = text.replace(handler_old, handler_new, 1)

encode_old = 'Content: base64.StdEncoding.EncodeToString([]byte(content)),'
count = text.count(encode_old)
if count < 1:
    raise SystemExit("binary upload patch: content encoding marker not found")
text = text.replace(encode_old, 'Content: encodedContent,')

path.write_text(text, encoding="utf-8")
print(f"binary upload patch applied; replaced {count} content encoding site(s)")
