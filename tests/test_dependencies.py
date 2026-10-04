"""Dependency smoke tests — run against the declared runtime environment.

Unlike the mock-based handler tests, these import the real libraries the
handler relies on, so a broken install or missing `pip_dependencies`
declaration fails CI immediately instead of blowing up a user's session.
Requires the environment active when running tests to have the plugin's
runtime dependencies installed (Hermes: `hermes pm repair`; CI: the
lockfile-synced venv `uv run` provides).
"""

import importlib


class TestRuntimeDepsPresent:
    """The declared runtime deps must actually import where tests run."""

    def test_requests_importable(self):
        requests = importlib.import_module("requests")
        assert hasattr(requests, "Session")

    def test_html_to_markdown_importable(self):
        html_to_markdown = importlib.import_module("html_to_markdown")
        assert callable(html_to_markdown.convert)

    def test_html_to_markdown_conversion_matches_handler_contract(self):
        """convert() must yield text the handler can JSON-serialize."""
        import json

        html_to_markdown = importlib.import_module("html_to_markdown")
        converted = html_to_markdown.convert("<h1>Title</h1><p>Body</p>")
        content = converted.content if hasattr(converted, "content") else converted
        assert isinstance(content, str)
        assert content  # non-empty markdown
        json.dumps({"content": content})  # serializable
