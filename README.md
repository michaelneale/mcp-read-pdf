# mcp-unlock-pdf

MCP server to give client the ability read protected (or un-unprotected) PDF
Works with large PDFs by extracting text to temp file.

Forked from the excellent upstream project https://github.com/algonacci/mcp-unlock-pdf

Published to pypi.

# Test

```sh
uv run python main.py --test
```

# Usage from source

## Running from cli (Goose, or to try it)

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

### Building and Publishing

1. Update version in `pyproject.toml`:

```toml
[project]
version = "x.y.z"  # Update this
```

2. Build the package:

```bash
# Clean previous builds
rm -rf dist/*


# Or build in a clean environment using uv
uv venv .venv
source .venv/bin/activate
uv pip install build
python -m build
```

3. Publish to PyPI:

```bash
# Install twine if needed
uv pip install twine

# Upload to PyPI
python -m twine upload dist/*
```
