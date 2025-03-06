# mcp-unlock-pdf

MCP server to give client the ability read protected (or un-unprotected) PDF

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
