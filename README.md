# mcp-unlock-pdf

MCP server to give client the ability read protected (or un-unprotected) PDF
Works with large PDFs by extracting text to temp file.

Forked from the excellent upstream project https://github.com/algonacci/mcp-unlock-pdf

Published to pypi.

# Usage

For this MCP server to work, add the following configuration to your MCP config file:

```json
{
  "mcpServers": {
    "unlock_pdf": {
      "command": "uv",
      "args": [
        "--directory",
        "%USERPROFILE%/Documents/GitHub/mcp-unlock-pdf",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```
