# Hermes Native Extract Plugin

Extract web page content using native HTTP requests — no API key required.

## What it does

The `native_extract` tool fetches URLs and converts HTML to markdown. It's a
no-dependency-required fallback for web content extraction:

- Fetches URLs with a browser-like User-Agent
- Converts HTML to markdown using `html-to-markdown`
- Passes through JSON and markdown responses unchanged
- Supports up to 5 URLs per call

## Installation

### Local install

```bash
make install-local
```

This copies the plugin to `~/.hermes/plugins/native_extract_plugin/`.

### Via pip

```bash
pip install .
```

### Optional: enhanced SSL support

```bash
pip install ".[enhanced]"
```

This installs `certifi` for improved SSL certificate verification.

## Tool: `native_extract`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `urls` | `string[]` | Yes | List of URLs to extract (max 5) |

**Example usage:**

```json
{
  "urls": ["https://example.com/article", "https://example.com/docs"]
}
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "url": "https://example.com/article",
      "title": "",
      "content": "# Article Title\n\nArticle content in markdown...",
      "error": null
    }
  ]
}
```

## Skill

This plugin bundles a skill that provides AI agents with usage guidelines for
the `native_extract` tool. It's automatically installed to
`~/.hermes/skills/native_extract/` on first load.

## Development

```bash
# Install dev dependencies
make dev-install

# Run tests
make test

# Lint
make lint

# Clean
make clean
```

## License

MIT
