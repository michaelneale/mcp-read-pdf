# mcp-unlock-pdf

MCP server to give client the ability read protected (or un-unprotected) PDF
Works with large PDFs by extracting text to temp file.

Forked from the excellent upstream project https://github.com/algonacci/mcp-unlock-pdf

Published to pypi.

# Test

```sh
uv run python main.py --test
```

# Usage

## Running from cli

```sh
uv --directory /Users/micn/Documents/code/extractorb-py/mcp-unlock-pdf run python main.py
```

## in Claude

For this MCP server to work, add the following configuration to your MCP config file for claude:

```json
{
  "mcpServers": {
    "unlock_pdf": {
      "command": "uv",
      "args": [
        "--directory",
        "%USERPROFILE%/THIS_DIR",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```
