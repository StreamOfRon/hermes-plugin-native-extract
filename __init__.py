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
    source = Path(__file__).parent / "skill" / "SKILL.md"
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
