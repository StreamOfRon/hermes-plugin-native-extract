# Native Extract Plugin Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the `native_extract` tool from the hermes-agent dev branch into a standalone Hermes plugin, replacing the example template boilerplate.

**Architecture:** The native_extract tool is self-contained — it needs `requests` and `html-to-markdown` as required dependencies, with `certifi` optional for SSL. The plugin will replace all example boilerplate with native_extract schema, handler, skill, and tests. The `check_fn` pattern from core hermes (always returns True) maps to the plugin's `ctx.register_tool(check_fn=...)` parameter.

**Tech Stack:** Python 3.11+, requests, html-to-markdown (required), certifi (optional), pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `plugin/plugin.yaml` | Modify | Declare `native_extract` tool, remove example references |
| `plugin/schemas.py` | Replace | Define `NATIVE_EXTRACT_SCHEMA` |
| `plugin/tools.py` | Replace | Implement `native_extract_handler` |
| `plugin/__init__.py` | Replace | Register `native_extract` with `check_fn` |
| `skill/SKILL.md` | Replace | Skill for using native_extract |
| `pyproject.toml` | Modify | Rename package, add runtime deps |
| `tests/test_plugin.py` | Replace | Tests for native_extract plugin |
| `tests/test_skill.py` | Modify | Update for new skill |
| `README.md` | Replace | Plugin-specific documentation |
| `LICENSE` | Keep | Already MIT |
| `Makefile` | Modify | Update install targets |
| `AGENTS.md` | Keep | Good reference |

---

### Task 1: Update plugin manifest (plugin.yaml)

**Files:**
- Modify: `plugin/plugin.yaml`

- [ ] **Step 1: Replace plugin.yaml content**

Replace the entire file with:

```yaml
name: native_extract_plugin
version: 0.1.0
description: Extract web page content using native HTTP requests — no API key required
author: Your Name
provides_tools:
  - native_extract
provides_hooks:
  - post_tool_call
```

This declares only the `native_extract` tool (removes `example_tool`) and keeps the `post_tool_call` hook.

---

### Task 2: Define the native_extract schema

**Files:**
- Replace: `plugin/schemas.py`

- [ ] **Step 1: Write schemas.py**

```python
"""Tool schemas for the native_extract plugin."""

NATIVE_EXTRACT_SCHEMA = {
    "name": "native_extract",
    "description": (
        "Extract content from web pages using native HTTP requests. "
        "Converts HTML to markdown using html-to-markdown library if available, "
        "falls back to basic tag stripping. No API key required. "
        "Use this as a fallback when other extraction backends are unavailable "
        "or for simple content extraction tasks."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of URLs to extract content from (max 5 URLs per call)",
                "maxItems": 5,
            },
        },
        "required": ["urls"],
    },
}
```

---

### Task 3: Implement the native_extract handler

**Files:**
- Replace: `plugin/tools.py`

- [ ] **Step 1: Write tools.py**

```python
"""Tool handlers for the native_extract plugin."""

import json
import logging
import re

logger = logging.getLogger(__name__)


def native_extract_handler(args: dict, **kwargs) -> str:
    """Extract web page content using native HTTP requests.

    Uses requests library to fetch content and html-to-markdown to convert
    HTML to markdown.

    Handler contract:
    1. Receive args (dict) — the parameters the LLM passed
    2. Do the work
    3. Return a JSON string — ALWAYS, even on error
    4. Accept **kwargs for forward compatibility
    """
    try:
        import requests
    except ImportError:
        return json.dumps({
            "error": "The 'requests' library is required but not installed. Run: pip install requests"
        })

    try:
        import html_to_markdown
    except ImportError:
        return json.dumps({
            "error": "The 'html-to-markdown' library is required but not installed. Run: pip install html-to-markdown"
        })

    urls = args.get("urls", [])
    if not isinstance(urls, list):
        return json.dumps({"error": "'urls' must be a list"})
    if not urls:
        return json.dumps({"error": "No URLs provided"})

    results = []
    for url in urls[:5]:  # Max 5 URLs
        try:
            session = requests.Session()
            try:
                import certifi as _certifi
                session.verify = _certifi.where()
            except ImportError:
                pass  # requests defaults to its own bundle

            resp = session.get(
                url,
                headers={
                    "Accept": "application/json, text/markdown;q=0.9, text/html;q=0.8",
                    "User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)",
                },
                timeout=30,
                allow_redirects=True,
            )
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "").lower()

            if "application/json" in ct or "text/markdown" in ct:
                content = resp.text
            else:
                content = html_to_markdown.convert(resp.text)

            results.append({
                "url": url,
                "title": "",
                "content": content,
                "error": None,
            })
        except requests.exceptions.SSLError as e:
            logger.warning("Native extract SSL error for %s: %s", url, e)
            results.append({
                "url": url,
                "title": "",
                "content": "",
                "error": (
                    f"SSL certificate verification failed for {url}. "
                    "This may be a Python SSL configuration issue. "
                    f"Details: {e}"
                ),
            })
        except Exception as e:
            logger.warning("Native extract failed for %s: %s", url, e)
            results.append({
                "url": url,
                "title": "",
                "content": "",
                "error": str(e),
            })

    return json.dumps({"success": True, "data": results}, ensure_ascii=False)
```

---

### Task 4: Write the plugin registration

**Files:**
- Replace: `plugin/__init__.py`

- [ ] **Step 1: Write __init__.py**

```python
"""Native extract plugin — registration."""

import logging
import shutil
from pathlib import Path

from .schemas import NATIVE_EXTRACT_SCHEMA
from .tools import native_extract_handler

logger = logging.getLogger(__name__)

_call_log = []


def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Hook: runs after every tool call (not just ours)."""
    _call_log.append({"tool": tool_name, "session": task_id})
    if len(_call_log) > 100:
        _call_log.pop(0)
    logger.debug("Tool called: %s (session %s)", tool_name, task_id)


def _check_native_extract_available() -> bool:
    """Native extract is always available (no API key needed)."""
    return True


def _install_skill():
    """Copy our skill to ~/.hermes/skills/ on first load."""
    try:
        from hermes_cli.config import get_hermes_home
        dest = get_hermes_home() / "skills" / "native_extract" / "SKILL.md"
    except Exception:
        dest = Path.home() / ".hermes" / "skills" / "native_extract" / "SKILL.md"
    if dest.exists():
        return  # don't overwrite user edits
    source = Path(__file__).parent.parent / "skill" / "SKILL.md"
    if source.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(dest))


def register(ctx):
    """Wire schemas to handlers and register hooks."""
    ctx.register_tool(
        name=NATIVE_EXTRACT_SCHEMA["name"],
        toolset="native_extract",
        schema=NATIVE_EXTRACT_SCHEMA,
        handler=native_extract_handler,
        check_fn=_check_native_extract_available,
    )
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    _install_skill()
```

---

### Task 5: Write the native_extract skill

**Files:**
- Replace: `skill/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: native-extract
description: Extract content from web pages using native HTTP requests — no API key required
author: Your Name
version: 0.1.0
tags: web, extraction, http, markdown
requires_tools:
  - native_extract
provides_commands:
  - /native-extract
---

## When to Use

- The user asks to extract, summarize, or analyze content from specific URLs
- Other extraction tools are unavailable or fail
- The user wants a no-API-key-required fallback for web content extraction
- Quick content extraction from public web pages

## Procedure

1. Call `native_extract` with the `urls` parameter (array of URLs, max 5)
2. Review the extracted markdown content
3. If the user asked for a summary, summarize the content
4. If extraction fails for some URLs, report which failed and why
5. For large content, focus on the most relevant sections

## Pitfalls

- **Max 5 URLs per call** — if the user provides more, process in batches
- **No JavaScript rendering** — this tool fetches raw HTML/JSON. SPA content may be incomplete
- **HTML-to-markdown optional** — if `html-to-markdown` isn't installed, falls back to basic tag stripping (less readable)
- **SSL errors** — may occur on some Python installations; suggest `pip install certifi`
- **Rate limiting** — some sites may block or rate-limit automated requests
- **Authentication required** — this tool cannot access pages requiring login
- **No retry logic** — transient failures are reported as errors; the user can retry

## Verification

- Extracted content should be readable markdown
- Each result includes `url`, `title`, `content`, and `error` fields
- If `error` is not null, the extraction failed for that URL
- Verify extracted content matches the expected page content
```

---

### Task 6: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update package metadata and dependencies**

Replace the entire `[project]` section with:

```toml
[project]
name = "hermes-plugin-native-extract"
version = "0.1.0"
description = "Hermes plugin for native web content extraction — no API key required"
requires-python = ">= 3.11"
dependencies = [
    "requests>=2.28",
    "html-to-markdown",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pyyaml",
    "hermes-agent",
]
enhanced = [
    "certifi",
]

[project.entry-points."hermes_agent.plugins"]
native_extract_plugin = "plugin"
```

---

### Task 7: Write plugin tests

**Files:**
- Replace: `tests/test_plugin.py`

- [ ] **Step 1: Write test_plugin.py**

```python
"""Tests for the native_extract plugin."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PLUGIN_DIR = Path(__file__).parent.parent / "plugin"


class TestPluginYaml:
    """Validate plugin.yaml structure."""

    def test_plugin_yaml_exists(self):
        yaml_path = PLUGIN_DIR / "plugin.yaml"
        assert yaml_path.exists(), "plugin.yaml must exist"

    def test_plugin_yaml_is_valid(self):
        import yaml
        yaml_path = PLUGIN_DIR / "plugin.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert "name" in data, "plugin.yaml must have 'name'"
        assert "version" in data, "plugin.yaml must have 'version'"
        assert "provides_tools" in data, "plugin.yaml must have 'provides_tools'"
        assert isinstance(data["provides_tools"], list)
        assert "native_extract" in data["provides_tools"]

    def test_tool_names_match_schemas(self):
        import yaml
        yaml_path = PLUGIN_DIR / "plugin.yaml"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        from plugin.schemas import NATIVE_EXTRACT_SCHEMA
        yaml_tools = set(data["provides_tools"])
        schema_tools = {NATIVE_EXTRACT_SCHEMA["name"]}
        assert yaml_tools == schema_tools, (
            f"plugin.yaml tools {yaml_tools} must match schemas {schema_tools}"
        )


class TestPluginInit:
    """Validate __init__.py structure."""

    def test_init_exists(self):
        init_path = PLUGIN_DIR / "__init__.py"
        assert init_path.exists(), "__init__.py must exist"

    def test_register_is_callable(self):
        from plugin import register
        assert callable(register), "register must be callable"


class TestToolSchemas:
    """Validate tool schema definitions."""

    def test_schema_has_name(self):
        from plugin.schemas import NATIVE_EXTRACT_SCHEMA
        assert NATIVE_EXTRACT_SCHEMA["name"] == "native_extract"

    def test_schema_has_description(self):
        from plugin.schemas import NATIVE_EXTRACT_SCHEMA
        desc = NATIVE_EXTRACT_SCHEMA["description"]
        assert len(desc) > 20, "Description should be detailed"
        assert "extract" in desc.lower()

    def test_schema_has_parameters(self):
        from plugin.schemas import NATIVE_EXTRACT_SCHEMA
        params = NATIVE_EXTRACT_SCHEMA["parameters"]
        assert params["type"] == "object"
        assert "urls" in params["properties"]
        assert "urls" in params["required"]

    def test_urls_property_schema(self):
        from plugin.schemas import NATIVE_EXTRACT_SCHEMA
        urls_prop = NATIVE_EXTRACT_SCHEMA["parameters"]["properties"]["urls"]
        assert urls_prop["type"] == "array"
        assert urls_prop["items"]["type"] == "string"
        assert urls_prop["maxItems"] == 5


class TestToolHandlers:
    """Test native_extract handler behavior."""

    def _make_mock_response(self, text="<html><body><h1>Test</h1><p>Content here</p></body></html>",
                            headers=None):
        mock = MagicMock()
        mock.text = text
        mock.headers = headers or {"Content-Type": "text/html; charset=utf-8"}
        mock.raise_for_status = MagicMock()
        return mock

    def test_handler_returns_json_string(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({"urls": ["https://example.com"]})
        assert isinstance(result, str)
        data = json.loads(result)  # Should not raise
        assert data["success"] is True

    def test_handler_success_single_url(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert len(data["data"]) == 1
        assert data["data"][0]["url"] == "https://example.com"
        assert data["data"][0]["error"] is None

    def test_handler_multiple_urls(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({
                "urls": ["https://a.com", "https://b.com", "https://c.com"]
            })
        data = json.loads(result)
        assert len(data["data"]) == 3

    def test_handler_respects_max_5_urls(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({
                "urls": [f"https://example.com/{i}" for i in range(10)]
            })
        data = json.loads(result)
        assert len(data["data"]) == 5

    def test_handler_no_urls_returns_error(self):
        from plugin.tools import native_extract_handler
        result = native_extract_handler({"urls": []})
        data = json.loads(result)
        assert "error" in data

    def test_handler_invalid_urls_returns_error(self):
        from plugin.tools import native_extract_handler
        result = native_extract_handler({"urls": "not-a-list"})
        data = json.loads(result)
        assert "error" in data

    def test_handler_json_passthrough(self):
        from plugin.tools import native_extract_handler
        mock_resp = self._make_mock_response(
            text='{"key": "value"}',
            headers={"Content-Type": "application/json"}
        )
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = mock_resp
            result = native_extract_handler({"urls": ["https://api.example.com/data"]})
        data = json.loads(result)
        assert data["data"][0]["content"] == '{"key": "value"}'

    def test_handler_ssl_error(self):
        from plugin.tools import native_extract_handler
        import requests
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.side_effect = requests.exceptions.SSLError("SSL error")
            result = native_extract_handler({"urls": ["https://bad-ssl.example.com"]})
        data = json.loads(result)
        assert data["success"] is True
        assert data["data"][0]["error"] is not None
        assert "SSL" in data["data"][0]["error"]

    def test_handler_http_error(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
            mock_session.return_value.get.return_value = mock_resp
            result = native_extract_handler({"urls": ["https://example.com/missing"]})
        data = json.loads(result)
        assert data["success"] is True
        assert data["data"][0]["error"] is not None

    def test_handler_never_raises(self):
        from plugin.tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.side_effect = RuntimeError("unexpected")
            result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert "error" in data or data["success"] is True

    def test_handler_with_none_args(self):
        from plugin.tools import native_extract_handler
        result = native_extract_handler(None)
        data = json.loads(result)
        assert "error" in data

    def test_handler_with_empty_args(self):
        from plugin.tools import native_extract_handler
        result = native_extract_handler({})
        data = json.loads(result)
        assert "error" in data

    def test_handler_uses_html_to_markdown(self):
        from plugin.tools import native_extract_handler
        html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response(text=html)
            with patch.dict("sys.modules", {"html_to_markdown": MagicMock(convert=lambda x: "# Title\n\nParagraph")}):
                result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert "# Title" in data["data"][0]["content"]

    def test_handler_missing_html_to_markdown_returns_error(self):
        from plugin.tools import native_extract_handler
        import sys
        original = sys.modules.get("html_to_markdown")
        try:
            sys.modules["html_to_markdown"] = None
            result = native_extract_handler({"urls": ["https://example.com"]})
            data = json.loads(result)
            assert "error" in data
            assert "html-to-markdown" in data["error"].lower()
        finally:
            if original is not None:
                sys.modules["html_to_markdown"] = original
            else:
                sys.modules.pop("html_to_markdown", None)


class TestCheckFunction:
    """Test the availability check function."""

    def test_check_always_returns_true(self):
        from plugin import _check_native_extract_available
        assert _check_native_extract_available() is True


class TestHookRegistration:
    """Test the post_tool_call hook."""

    def test_hook_tracks_calls(self):
        from plugin import _on_post_tool_call, _call_log
        _call_log.clear()
        _on_post_tool_call("some_tool", {"arg": "val"}, '{"ok": true}', "task-1")
        assert len(_call_log) == 1
        assert _call_log[0]["tool"] == "some_tool"
        assert _call_log[0]["session"] == "task-1"

    def test_hook_caps_at_100(self):
        from plugin import _on_post_tool_call, _call_log
        _call_log.clear()
        for i in range(150):
            _on_post_tool_call(f"tool_{i}", {}, "{}", f"task-{i}")
        assert len(_call_log) == 100
```

---

### Task 8: Update skill tests

**Files:**
- Modify: `tests/test_skill.py`

- [ ] **Step 1: Update skill tests to reference the new skill name**

The existing `test_skill.py` tests are generic enough they should work as-is (they check frontmatter structure, not specific names). Verify they pass. No changes needed unless they reference "example" explicitly.

---

### Task 9: Update README.md

**Files:**
- Replace: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Hermes Native Extract Plugin

Extract web page content using native HTTP requests — no API key required.

## What it does

The `native_extract` tool fetches URLs and converts HTML to markdown. It's a
no-dependency-required fallback for web content extraction:

- Fetches URLs with a browser-like User-Agent
- Converts HTML to markdown using `html-to-markdown` if available
- Falls back to basic tag stripping if not
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
```

---

### Task 10: Update Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Update install targets**

Replace `install-local` and `install-skill` targets:

```makefile
install-local:
	@echo "Installing native_extract plugin locally..."
	@mkdir -p $(HOME)/.hermes/plugins/native_extract_plugin
	@cp plugin/plugin.yaml $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp plugin/__init__.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp plugin/schemas.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@cp plugin/tools.py $(HOME)/.hermes/plugins/native_extract_plugin/
	@echo "Done. Restart Hermes to load the plugin."

install-skill:
	@echo "Installing native_extract skill..."
	@mkdir -p $(HOME)/.hermes/skills/native_extract
	@cp skill/SKILL.md $(HOME)/.hermes/skills/native_extract/
	@echo "Done."
```

---

### Task 11: Run tests and fix any failures

**Files:**
- All modified files

- [ ] **Step 1: Install test dependencies**

Run: `uv pip install pytest pyyaml requests`

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`

Expected: All tests pass. If any fail, fix the implementation (not the tests).

- [ ] **Step 3: Verify no example references remain**

Run: `rg -i "example_tool\|example_plugin\|example-skill" plugin/ tests/ --files-with-matches`

Expected: No matches.

---

### Task 12: Template improvements (optional but recommended)

After the migration is complete, review the template for issues that would make
it hard to rapidly create new plugins. Potential improvements to propose:

1. **`pyproject.toml` has no `[tool.pytest]` section** — tests use `Path(__file__).parent.parent / "plugin"` which works but could be cleaner
2. **Tests import `plugin` module directly** — this works because the plugin directory is importable, but a proper package structure would be more robust
3. **No `__init__.py` in `plugin/`** as a Python package — it exists but is also the Hermes entry point, which is fine
4. **Makefile `install-local` copies files individually** — could use `cp -r plugin/*` but the current approach is more explicit
5. **No pre-commit hooks configured** — could add ruff, black, etc.
6. **The template's `AGENTS.md` references `example_plugin` in places** — should be parameterized

Document any proposed template changes separately for review.
