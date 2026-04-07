"""Tests for the native_extract plugin."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

PLUGIN_DIR = Path(__file__).parent.parent


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
        from schemas import NATIVE_EXTRACT_SCHEMA
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
        from __init__ import register
        assert callable(register), "register must be callable"


class TestToolSchemas:
    """Validate tool schema definitions."""

    def test_schema_has_name(self):
        from schemas import NATIVE_EXTRACT_SCHEMA
        assert NATIVE_EXTRACT_SCHEMA["name"] == "native_extract"

    def test_schema_has_description(self):
        from schemas import NATIVE_EXTRACT_SCHEMA
        desc = NATIVE_EXTRACT_SCHEMA["description"]
        assert len(desc) > 20, "Description should be detailed"
        assert "extract" in desc.lower()

    def test_schema_has_parameters(self):
        from schemas import NATIVE_EXTRACT_SCHEMA
        params = NATIVE_EXTRACT_SCHEMA["parameters"]
        assert params["type"] == "object"
        assert "urls" in params["properties"]
        assert "urls" in params["required"]

    def test_urls_property_schema(self):
        from schemas import NATIVE_EXTRACT_SCHEMA
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
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({"urls": ["https://example.com"]})
        assert isinstance(result, str)
        data = json.loads(result)  # Should not raise
        assert data["success"] is True

    def test_handler_success_single_url(self):
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert len(data["data"]) == 1
        assert data["data"][0]["url"] == "https://example.com"
        assert data["data"][0]["error"] is None

    def test_handler_multiple_urls(self):
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({
                "urls": ["https://a.com", "https://b.com", "https://c.com"]
            })
        data = json.loads(result)
        assert len(data["data"]) == 3

    def test_handler_respects_max_5_urls(self):
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response()
            result = native_extract_handler({
                "urls": [f"https://example.com/{i}" for i in range(10)]
            })
        data = json.loads(result)
        assert len(data["data"]) == 5

    def test_handler_no_urls_returns_error(self):
        from tools import native_extract_handler
        result = native_extract_handler({"urls": []})
        data = json.loads(result)
        assert "error" in data

    def test_handler_invalid_urls_returns_error(self):
        from tools import native_extract_handler
        result = native_extract_handler({"urls": "not-a-list"})
        data = json.loads(result)
        assert "error" in data

    def test_handler_json_passthrough(self):
        from tools import native_extract_handler
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
        from tools import native_extract_handler
        import requests
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.side_effect = requests.exceptions.SSLError("SSL error")
            result = native_extract_handler({"urls": ["https://bad-ssl.example.com"]})
        data = json.loads(result)
        assert data["success"] is True
        assert data["data"][0]["error"] is not None
        assert "SSL" in data["data"][0]["error"]

    def test_handler_http_error(self):
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
            mock_session.return_value.get.return_value = mock_resp
            result = native_extract_handler({"urls": ["https://example.com/missing"]})
        data = json.loads(result)
        assert data["success"] is True
        assert data["data"][0]["error"] is not None

    def test_handler_never_raises(self):
        from tools import native_extract_handler
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.side_effect = RuntimeError("unexpected")
            result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert "error" in data or data["success"] is True

    def test_handler_with_none_args(self):
        from tools import native_extract_handler
        result = native_extract_handler(None)
        data = json.loads(result)
        assert "error" in data

    def test_handler_with_empty_args(self):
        from tools import native_extract_handler
        result = native_extract_handler({})
        data = json.loads(result)
        assert "error" in data

    def test_handler_uses_html_to_markdown(self):
        from tools import native_extract_handler
        html = "<html><body><h1>Title</h1><p>Paragraph</p></body></html>"
        with patch("requests.Session") as mock_session:
            mock_session.return_value.get.return_value = self._make_mock_response(text=html)
            with patch.dict("sys.modules", {"html_to_markdown": MagicMock(convert=lambda x: "# Title\n\nParagraph")}):
                result = native_extract_handler({"urls": ["https://example.com"]})
        data = json.loads(result)
        assert "# Title" in data["data"][0]["content"]

    def test_handler_missing_html_to_markdown_returns_error(self):
        from tools import native_extract_handler
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
        from __init__ import _check_native_extract_available
        assert _check_native_extract_available() is True


class TestHookRegistration:
    """Test the post_tool_call hook."""

    def test_hook_tracks_calls(self):
        from __init__ import _on_post_tool_call, _call_log
        _call_log.clear()
        _on_post_tool_call("some_tool", {"arg": "val"}, '{"ok": true}', "task-1")
        assert len(_call_log) == 1
        assert _call_log[0]["tool"] == "some_tool"
        assert _call_log[0]["session"] == "task-1"

    def test_hook_caps_at_100(self):
        from __init__ import _on_post_tool_call, _call_log
        _call_log.clear()
        for i in range(150):
            _on_post_tool_call(f"tool_{i}", {}, "{}", f"task-{i}")
        assert len(_call_log) == 100
