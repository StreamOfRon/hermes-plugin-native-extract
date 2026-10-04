# Hermes Native Extract Plugin

Extract web page content using native HTTP requests — no API key required.

## What it does

The `native_extract` tool fetches URLs and converts HTML to markdown:

- Requires no API key or configuration
- Fetches URLs with a browser-like User-Agent
- Converts HTML to markdown using `html-to-markdown`
- Passes through JSON and markdown responses unchanged
- Supports up to 5 URLs per call

## Installation & dependencies

The plugin declares its Python dependencies (`requests`, `html-to-markdown`)
in `pyproject.toml`. `hermes plugins install` asks you to consent to PM
installing them into Hermes's shared environment (dependencies are never
installed behind your back):

```bash
hermes plugins install <this-repo-url>

# Non-interactive (SSH automation, CI, Docker entrypoints):
hermes plugins install <this-repo-url> --yes-deps
```

**If the tool reports the libraries are missing:**

1. Run `hermes pm repair`, then **restart Hermes**. Discovery never installs
   dependencies — env sync happens through PM only.
2. If PM recorded the plugin without its dependencies (e.g. installed with
   `--no-deps`, or from before they were declared), reinstall with
   `--yes-deps` so PM re-admits the dependency graph.

Note: a bare `pip install html-to-markdown` does **not** fix this — Hermes
runs plugins inside its PM-managed venv, so plain pip targets the wrong
environment.

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
