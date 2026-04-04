"""Example Hermes plugin — register entry point.

This module is the entry point for the Hermes plugin system.
The `register(ctx)` function is called by the PluginManager
when the plugin is discovered and loaded.
"""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)

# Track tool usage via hooks
_call_log = []


def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Hook: runs after every tool call (not just ours)."""
    _call_log.append({"tool": tool_name, "session": task_id})
    if len(_call_log) > 100:
        _call_log.pop(0)
    logger.debug("Tool called: %s (session %s)", tool_name, task_id)


def register(ctx):
    """Register all tools and hooks with the plugin context.

    Args:
        ctx: Plugin registration context provided by Hermes.
             Provides register_tool() and register_hook() methods.
    """
    # Register example tool
    ctx.register_tool(
        name=EXAMPLE_TOOL_SCHEMA["name"],
        toolset="example_plugin",
        schema=EXAMPLE_TOOL_SCHEMA,
        handler=tools.example_tool_handler,
    )

    # Register a lifecycle hook — fires for ALL tool calls, not just ours
    ctx.register_hook("post_tool_call", _on_post_tool_call)
