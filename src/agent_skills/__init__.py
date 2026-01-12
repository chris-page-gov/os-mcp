"""agentskills.io-compatible Skill discovery helpers.

This package provides lightweight utilities to discover and read Agent Skills
stored in the repository's `skills/` folder.

The format is based on https://agentskills.io and the `agentskills/agentskills`
specification:
- Skills are directories containing a `SKILL.md` (or `skill.md`) file
- The SKILL.md must start with YAML frontmatter containing at least:
  - name
  - description
"""

from .models import SkillProperties, SkillSummary
from .discovery import (
    find_skill_md,
    discover_skill_dirs,
    read_skill_properties,
    validate_skill_dir,
    skills_to_available_skills_xml,
)

__all__ = [
    "SkillProperties",
    "SkillSummary",
    "find_skill_md",
    "discover_skill_dirs",
    "read_skill_properties",
    "validate_skill_dir",
    "skills_to_available_skills_xml",
]
