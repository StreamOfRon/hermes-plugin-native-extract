# AGENTS.md — Instructions for AI Coding Agents

This project is a **Hermes plugin template** created from `hermes-plugin-template`.
It provides boilerplate for all three Hermes extension layers: **Skills**, **Tools**, and **Plugins**.

## Project Structure

```
├── plugin/                 # PLUGIN LAYER — Python code + manifest
│   ├── plugin.yaml         # Plugin manifest (name, version, tools, hooks)
│   ├── __init__.py         # register(ctx) entry point
│   ├── tools.py            # Tool handler implementations
│   └── schemas.py          # OpenAI-format tool schema definitions
│
├── skill/                  # SKILL LAYER — Markdown instructions for AI
│   └── SKILL.md            # Skill definition with YAML frontmatter
│
├── tests/                  # TEST SCAFFOLDING
│   ├── test_plugin.py      # Plugin loading + tool registration tests
│   └── test_skill.py       # Skill frontmatter + structure tests
│
├── pyproject.toml          # Pip distribution config
├── Makefile                # Convenience targets
└── AGENTS.md               # This file
```

## How to Add a New Tool

1. **Define the schema** in `plugin/schemas.py`:
   ```python
   MY_TOOL_SCHEMA = {
       "name": "my_tool",
       "description": "What this tool does — be specific so the LLM knows when to use it",
       "parameters": {
           "type": "object",
           "properties": {
               "param_name": {"type": "string", "description": "..."},
           },
           "required": ["param_name"],
       },
   }
   ```

2. **Implement the handler** in `plugin/tools.py`:
   ```python
   def my_tool_handler(args: dict, **kwargs) -> str:
       try:
           # Process args, return json.dumps(result)
           return json.dumps({"status": "success", "data": ...})
       except Exception as e:
           return json.dumps({"error": str(e)})
   ```

3. **Register in `plugin/__init__.py`**:
   ```python
   from .schemas import MY_TOOL_SCHEMA
   from .tools import my_tool_handler

   def register(ctx):
       ctx.register_tool(
           name=MY_TOOL_SCHEMA["name"],
           toolset="my_plugin",        # plugin name, NOT tool name
           schema=MY_TOOL_SCHEMA,
           handler=my_tool_handler,
       )
   ```

4. **Update `plugin/plugin.yaml`**:
   ```yaml
   provides_tools:
     - my_tool
   ```

## How to Add a New Skill

1. Create a directory under `~/.hermes/skills/<skill-name>/`
2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What this skill does
   ---
   ```
3. Required frontmatter fields: `name`, `description`
4. Optional fields: `author`, `version`, `tags`, `requires_tools`, `provides_commands`
5. Standard sections: `## When to Use`, `## Procedure`, `## Pitfalls`, `## Verification`
6. Field constraints: `name` ≤ 50 chars, `description` ≤ 200 chars

### Bundle a skill with your plugin

Include a `skill.md` (or `SKILL.md`) in your plugin directory and install it during registration:

```python
import shutil
from pathlib import Path

def _install_skill():
    """Copy our skill to ~/.hermes/skills/ on first load."""
    try:
        from hermes_cli.config import get_hermes_home
        dest = get_hermes_home() / "skills" / "my-plugin" / "SKILL.md"
    except Exception:
        dest = Path.home() / ".hermes" / "skills" / "my-plugin" / "SKILL.md"
    if dest.exists():
        return  # don't overwrite user edits
    source = Path(__file__).parent / "skill.md"
    if source.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

def register(ctx):
    ctx.register_tool(...)
    _install_skill()
```

## How to Add Lifecycle Hooks

In `plugin/__init__.py`:

```python
import logging
logger = logging.getLogger(__name__)

def on_session_start(session_id, model, platform, **kwargs):
    logger.info("Session started: %s", session_id)

def register(ctx):
    # ... tool registration ...
    ctx.register_hook("on_session_start", on_session_start)
```

Available hooks:

| Hook | When | Arguments | Return |
|------|------|-----------|--------|
| `pre_tool_call` | Before any tool runs | `tool_name`, `args`, `task_id` | — |
| `post_tool_call` | After any tool returns | `tool_name`, `args`, `result`, `task_id` | — |
| `pre_llm_call` | Once per turn, before LLM loop | `session_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`, `platform` | `{"context": "..."}` |
| `post_llm_call` | Once per turn, after LLM loop | `session_id`, `user_message`, `assistant_response`, `conversation_history`, `model`, `platform` | — |
| `on_session_start` | New session created | `session_id`, `model`, `platform` | — |
| `on_session_end` | End of session | `session_id`, `completed`, `interrupted`, `model`, `platform` | — |

The `pre_llm_call` hook can inject context: return a dict with `"context"` key to append to the system prompt.
If a hook crashes, it's logged and skipped; other hooks and the agent continue normally.

## Handler Contract

- **Signature**: `def handler(args: dict, **kwargs) -> str`
- **Return**: MUST return a JSON-encoded string (`json.dumps(...)`)
- **Errors**: MUST NOT raise exceptions; catch and return error JSON
- **args**: Dict of parameters matching the schema definition
- **kwargs**: Accept `**kwargs` for forward compatibility

## Testing Patterns

- Use `tmp_path` fixture for temporary directories
- Monkeypatch `HERMES_HOME` to avoid affecting real installation
- Create `PluginManager()` directly (not global singleton)
- Test: discovery, loading, tool registration, tool execution, hook invocation

```python
@pytest.fixture
def hermes_home(tmp_path, monkeypatch):
    hermes = tmp_path / ".hermes"
    hermes.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes))
    return hermes
```

## Common Pitfalls

- **Hardcoded `~/.hermes`**: Never hardcode paths; use `HERMES_HOME` env var
- **Missing `name` in schema**: Every tool schema MUST have a `name` field
- **Raising in handlers**: Handlers must catch all exceptions and return error JSON
- **Non-JSON returns**: Handlers MUST return `json.dumps(...)`, not raw strings/dicts
- **Duplicate tool names**: Tool names must be unique across all loaded plugins
- **Missing frontmatter delimiters**: SKILL.md must start and end frontmatter with `---`
- **Using tool name as toolset**: `toolset` should be the plugin name, not the tool name
- **Missing `**kwargs`**: Handlers must accept `**kwargs` for forward compatibility
- **Vague schema descriptions**: Be specific so the LLM knows when to use your tool

## Key Hermes Source Files (for reference)

When implementing advanced patterns, reference the Hermes agent source:
- Plugin loading: `hermes_cli/plugins.py`
- Plugin context: `PluginContext` class in `hermes_cli/plugins.py`
- Skill loading: `hermes_cli/skills_config.py`
- Hook system: `invoke_hook()` in `hermes_cli/plugins.py`
