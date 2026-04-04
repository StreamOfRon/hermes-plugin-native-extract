"""Tests for plugin structure and tool handler contract.

These tests validate the plugin's own code without depending on
Hermes's internal PluginManager singleton or namespace package caching.
"""

import json
from pathlib import Path

import pytest
import yaml

PLUGIN_DIR = Path(__file__).parent.parent / "plugin"


class TestPluginYaml:
    """Validate plugin.yaml manifest."""

    def test_file_exists(self):
        assert (PLUGIN_DIR / "plugin.yaml").exists()

    def test_valid_yaml(self):
        data = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        assert isinstance(data, dict)

    def test_required_fields(self):
        data = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        assert "name" in data
        assert "version" in data
        assert "provides_tools" in data
        assert isinstance(data["provides_tools"], list)
        assert len(data["provides_tools"]) > 0

    def test_tool_names_match_schema(self):
        """Every tool in plugin.yaml should have a matching schema."""
        manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        from plugin.schemas import EXAMPLE_TOOL_SCHEMA

        for tool_name in manifest["provides_tools"]:
            assert EXAMPLE_TOOL_SCHEMA["name"] == tool_name


class TestPluginInit:
    """Validate __init__.py has the required register function."""

    def test_file_exists(self):
        assert (PLUGIN_DIR / "__init__.py").exists()

    def test_has_register_function(self):
        """__init__.py must expose a register() callable."""
        import plugin

        assert hasattr(plugin, "register")
        assert callable(plugin.register)


class TestToolSchemas:
    """Validate tool schema definitions."""

    def test_schema_has_name(self):
        from plugin.schemas import EXAMPLE_TOOL_SCHEMA

        assert "name" in EXAMPLE_TOOL_SCHEMA
        assert isinstance(EXAMPLE_TOOL_SCHEMA["name"], str)

    def test_schema_has_description(self):
        from plugin.schemas import EXAMPLE_TOOL_SCHEMA

        assert "description" in EXAMPLE_TOOL_SCHEMA

    def test_schema_has_parameters(self):
        from plugin.schemas import EXAMPLE_TOOL_SCHEMA

        assert "parameters" in EXAMPLE_TOOL_SCHEMA
        assert "type" in EXAMPLE_TOOL_SCHEMA["parameters"]
        assert "properties" in EXAMPLE_TOOL_SCHEMA["parameters"]

    def test_required_fields_are_strings(self):
        from plugin.schemas import EXAMPLE_TOOL_SCHEMA

        for field in EXAMPLE_TOOL_SCHEMA["parameters"].get("required", []):
            assert field in EXAMPLE_TOOL_SCHEMA["parameters"]["properties"]


class TestToolHandlers:
    """Validate tool handler implementations follow the contract."""

    def test_handler_returns_json_string(self):
        from plugin.tools import example_tool_handler

        result = example_tool_handler({"message": "hello"})
        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_handler_success_response(self):
        from plugin.tools import example_tool_handler

        result = example_tool_handler({"message": "hello world"})
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["message"] == "hello world"
        assert data["length"] == 11

    def test_handler_verbose_mode(self):
        from plugin.tools import example_tool_handler

        result = example_tool_handler({"message": "test", "verbose": True})
        data = json.loads(result)
        assert data["status"] == "success"
        assert "details" in data

    def test_handler_error_returns_json(self):
        """Handler must never raise; errors must be returned as JSON."""
        from plugin.tools import example_tool_handler

        # Even with missing keys, handler should not raise
        result = example_tool_handler({})
        data = json.loads(result)
        assert "status" in data

    def test_handler_does_not_raise(self):
        """Handler must catch all exceptions."""
        from plugin.tools import example_tool_handler

        try:
            result = example_tool_handler(None)
            data = json.loads(result)
            assert "status" in data
        except Exception:
            pytest.fail("Handler raised an exception instead of returning error JSON")
