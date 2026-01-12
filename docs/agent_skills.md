# Agent Skills (agentskills.io)

This repository supports the **agentskills.io** format.

VS Code (v1.108+) automatically detects skills from `.github/skills/` (or `.claude/skills/` for backwards compatibility). This repo follows that convention.

A skill is a directory containing at minimum a `SKILL.md` file with YAML frontmatter.

## Directory layout

```
.github/skills/
  <skill-name>/
    SKILL.md
    scripts/        (optional)
    references/     (optional)
    assets/         (optional)
```

## SKILL.md frontmatter

Required fields:
- `name`
- `description`

Optional fields:
- `license`
- `compatibility`
- `metadata` (string->string mapping)
- `allowed-tools` (experimental)

## Adding a new skill
1. Create a folder: `.github/skills/<your-skill-name>/`
2. Add `SKILL.md` with matching `name: <your-skill-name>`
3. Keep the description concise and keyword-rich.

## MCP integration (read-only tools)
This MCP server exposes read-only tools so tool-based agents can discover and load skills:
- `list_agent_skills` – lists available skills (name, description, location)
- `get_agent_skill` – returns the full `SKILL.md` for a named skill

Skill discovery roots:
- Default: `.github/skills/`, `.claude/skills/`, then `skills/` (fallback)
- Override: set `OS_MCP_SKILLS_DIRS` to a comma-separated list of directories.
