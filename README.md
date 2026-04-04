# Hermes Plugin Template

A boilerplate template for building [Hermes](https://github.com/NousResearch/hermes-agent) extensions. Provides scaffolding for all three Hermes extension layers: **Skills**, **Tools**, and **Plugins**.

## How to Use This Template

1. Click **"Use this template"** on GitHub (or fork this repository)
2. Clone your new repository locally
3. Customize the files (see [Quick Start](#quick-start))
4. Install into your Hermes instance

## Quick Start

```bash
# 1. Clone your repository
git clone git@github.com:your-org/your-hermes-plugin.git
cd your-hermes-plugin

# 2. Install dev dependencies
make dev-install

# 3. Install plugin to local Hermes
make install-local

# 4. Install skill to local Hermes
make install-skill

# 5. Verify
hermes
```

You should see `example_plugin: example_tool` in the banner's tool list.

Check plugin status:

```
/plugins
```

## Extension Layers

### Skill Layer (`skill/`)

Skills are Markdown files with YAML frontmatter that instruct AI agents on when and how to behave. They define slash commands, provide procedural knowledge, and reference external resources.

**Use when**: You want to add AI behavior instructions, slash commands, or procedural workflows.

```
skill/
└── SKILL.md        # Skill definition with frontmatter
```

### Tool Layer (`plugin/`)

Tools are Python functions exposed to the AI model as function-calling capabilities. Each tool has a schema (OpenAI format) and a handler implementation.

**Use when**: You want the AI to call your code — API integrations, data processing, external services.

```
plugin/
├── plugin.yaml     # Manifest (name, version, tools, hooks)
├── __init__.py     # register(ctx) entry point — wiring: schemas → handlers, register hooks
├── tools.py        # Handler implementations — the code that runs
└── schemas.py      # OpenAI-format schemas — what the LLM reads
```

### Plugin Layer (hooks)

Plugins can register lifecycle hooks that run at specific points in the Hermes session lifecycle (session start, tool calls, etc.).

**Use when**: You need to react to lifecycle events — logging, session setup, message preprocessing.

## Running Tests

```bash
# Run all tests
make test

# Or directly with pytest
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_plugin.py -v
python -m pytest tests/test_skill.py -v
```

## Distribution

### Via GitHub (recommended for teams)

1. Push your customized plugin to a GitHub repository
2. Users clone and run `make install-local`

### Via pip (recommended for public distribution)

```bash
# Build and install
pip install .

# Or install from PyPI (after publishing)
pip install your-hermes-plugin
```

The `pyproject.toml` is configured with the `hermes_agent.plugins` entry point for automatic discovery.

### Via Hermes Skills Hub

Publish your `SKILL.md` to the [Hermes Skills Hub](https://github.com/NousResearch/hermes-agent) for community discovery.

## Adding New Tools

See `AGENTS.md` for detailed instructions on adding tools, skills, and hooks.

Quick summary:
1. Add schema to `plugin/schemas.py`
2. Add handler to `plugin/tools.py`
3. Register in `plugin/__init__.py`
4. Update `plugin.yaml` `provides_tools` list

## Plugin Structure

```
~/.hermes/plugins/example_plugin/
├── plugin.yaml      # "I'm example_plugin, I provide tools and hooks"
├── __init__.py      # Wiring: schemas → handlers, register hooks
├── schemas.py       # What the LLM reads (descriptions + parameter specs)
└── tools.py         # What runs (handler functions)
```

Four files, clear separation:
- **Manifest** declares what the plugin is
- **Schemas** describe tools for the LLM
- **Handlers** implement the actual logic
- **Registration** connects everything

## What else can plugins do?

### Ship data files

Put any files in your plugin directory and read them at import time:

```python
# In tools.py or __init__.py
from pathlib import Path
_PLUGIN_DIR = Path(__file__).parent
_DATA_FILE = _PLUGIN_DIR / "data" / "config.yaml"
```

### Bundle a skill

Include a `skill.md` file and install it during registration:

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

### Gate on environment variables

If your plugin needs an API key:

```yaml
# plugin.yaml
requires_env:
  - MY_API_KEY
```

If `MY_API_KEY` isn't set, the plugin is disabled with a clear message.

### Conditional tool availability

For tools that depend on optional libraries:

```python
ctx.register_tool(
    name="my_tool",
    schema={...},
    handler=my_handler,
    check_fn=lambda: _has_optional_lib(),  # False = tool hidden from model
)
```

### Register multiple hooks

```python
def register(ctx):
    ctx.register_hook("pre_tool_call", before_any_tool)
    ctx.register_hook("post_tool_call", after_any_tool)
    ctx.register_hook("on_session_start", on_new_session)
    ctx.register_hook("on_session_end", on_session_end)
```

Available hooks:

| Hook | When | Arguments | Return |
|------|------|-----------|--------|
| `pre_tool_call` | Before any tool runs | `tool_name`, `args`, `task_id` | — |
| `post_tool_call` | After any tool returns | `tool_name`, `args`, `result`, `task_id` | — |
| `pre_llm_call` | Once per turn, before the LLM loop | `session_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`, `platform` | `{"context": "..."}` |
| `post_llm_call` | Once per turn, after the LLM loop | `session_id`, `user_message`, `assistant_response`, `conversation_history`, `model`, `platform` | — |
| `on_session_start` | New session created (first turn only) | `session_id`, `model`, `platform` | — |
| `on_session_end` | End of every `run_conversation` call | `session_id`, `completed`, `interrupted`, `model`, `platform` | — |

Most hooks are fire-and-forget observers. The exception is `pre_llm_call`: if a callback returns a dict with a `"context"` key (or a plain string), the value is appended to the ephemeral system prompt for the current turn.

If a hook crashes, it's logged and skipped; other hooks and the agent continue normally.

## Common mistakes

**Handler doesn't return JSON string:**
```python
# Wrong — returns a dict
def handler(args, **kwargs):
    return {"result": 42}

# Right — returns a JSON string
def handler(args, **kwargs):
    return json.dumps({"result": 42})
```

**Missing `**kwargs` in handler signature:**
```python
# Wrong — will break if Hermes passes extra context
def handler(args):
    ...

# Right
def handler(args, **kwargs):
    ...
```

**Handler raises exceptions:**
```python
# Wrong — exception propagates, tool call fails
def handler(args, **kwargs):
    result = 1 / int(args["value"])  # ZeroDivisionError!
    return json.dumps({"result": result})

# Right — catch and return error JSON
def handler(args, **kwargs):
    try:
        result = 1 / int(args.get("value", 0))
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**Schema description too vague:**
```python
# Bad — model doesn't know when to use it
"description": "Does stuff"

# Good — model knows exactly when and how
"description": "Evaluate a mathematical expression. Use for arithmetic, trig, logarithms. Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e."
```

## License

MIT — see [LICENSE](LICENSE)
