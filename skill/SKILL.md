---
name: example-skill
description: An example skill demonstrating Hermes skill structure and frontmatter
author: Your Name
version: 0.1.0
tags:
  - example
  - template
  - demonstration
requires_tools: []
provides_commands:
  - /example-skill
---

# Example Skill

## When to Use

Use this skill when you need a reference for how Hermes skills are structured,
or when you want to demonstrate the skill loading mechanism.

This skill serves as a template showing:
- YAML frontmatter with all optional fields
- Required sections and their purpose
- Directory patterns for references and templates

## Procedure

1. **Understand the frontmatter** — The YAML block at the top defines metadata
   that Hermes uses to register and display the skill.

2. **Review the sections** — Skills should have clear sections:
   - When to Use: Conditions that trigger this skill
   - Procedure: Step-by-step instructions
   - Pitfalls: Common mistakes to avoid
   - Verification: How to confirm correct behavior

3. **Reference external resources** — Use the `references/` directory pattern:
   ```
   skill/
   ├── SKILL.md
   └── references/
       └── api-docs.md    # Supporting documentation
   ```

4. **Use templates** — Use the `templates/` directory pattern:
   ```
   skill/
   ├── SKILL.md
   └── templates/
       └── output.md.j2   # Jinja2 template for output
   ```

## Pitfalls

- **Missing frontmatter**: Skills without `---` delimited YAML frontmatter
  will not be discovered by Hermes.
- **Missing required fields**: `name` and `description` are required in frontmatter.
- **Field length limits**: Keep `name` under 50 characters, `description` under 200.
- **Incorrect directory structure**: Skills must be in `~/.hermes/skills/<name>/SKILL.md`.
- **Duplicate names**: Two skills with the same `name` will conflict.

## Verification

To verify this skill is loaded correctly:

1. Copy the `skill/` directory to `~/.hermes/skills/example/`
2. Run `hermes` and check that `/example-skill` appears in slash commands
3. Trigger the skill and confirm it responds with the expected behavior
