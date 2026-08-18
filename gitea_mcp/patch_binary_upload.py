#!/usr/bin/env python3
from pathlib import Path

path = Path("/src/operation/repo/file.go")
text = path.read_text(encoding="utf-8")

# Patch CreateFileTool only. Keep the existing text input for backwards
# compatibility and add a mutually exclusive base64 input for raw bytes.
schema_old = 'mcp.WithString("content", mcp.Required(), mcp.Description("file content")),'
schema_new = '''mcp.WithString("content", mcp.Description("UTF-8 text content; mutually exclusive with content_base64")),
		mcp.WithString("content_base64", mcp.Description("raw file bytes encoded as standard base64; mutually exclusive with content")),'''
if schema_old not in text:
    raise SystemExit("binary upload patch: create_file content schema marker not found")
text = text.replace(schema_old, schema_new, 1)

handler_old = 'content, _ := req.GetArguments()["content"].(string)'
handler_new = '''args := req.GetArguments()
	content, hasContent := args["content"].(string)
	contentBase64, hasBase64 := args["content_base64"].(string)
	if hasContent == hasBase64 {
		return to.ErrorResult(fmt.Errorf("exactly one of content or content_base64 is required"))
	}
	encodedContent := contentBase64
	if hasBase64 {
		if _, err := base64.StdEncoding.DecodeString(contentBase64); err != nil {
			return to.ErrorResult(fmt.Errorf("content_base64 is not valid standard base64: %v", err))
		}
	} else {
		encodedContent = base64.StdEncoding.EncodeToString([]byte(content))
	}'''
if handler_old not in text:
    raise SystemExit("binary upload patch: create_file handler marker not found")
text = text.replace(handler_old, handler_new, 1)

encode_old = 'Content: base64.StdEncoding.EncodeToString([]byte(content)),'
if encode_old not in text:
    raise SystemExit("binary upload patch: create_file encoding marker not found")
text = text.replace(encode_old, 'Content: encodedContent,', 1)

path.write_text(text, encoding="utf-8")
print("binary upload patch applied to create_file")
