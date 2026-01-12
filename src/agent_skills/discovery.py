from __future__ import annotations

import html
import os
import unicodedata
from pathlib import Path
from typing import Any, Optional

from agent_skills.models import SkillProperties, SkillSummary


class SkillError(Exception):
    pass


class SkillParseError(SkillError):
    pass


class SkillValidationError(SkillError):
    def __init__(self, message: str, errors: Optional[list[str]] = None):
        super().__init__(message)
        self.errors = errors if errors is not None else [message]


ALLOWED_FIELDS: set[str] = {
    "name",
    "description",
    "license",
    "compatibility",
    "allowed-tools",
    "metadata",
}

MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500


def find_skill_md(skill_dir: Path) -> Optional[Path]:
    for name in ("SKILL.md", "skill.md"):
        p = skill_dir / name
        if p.exists():
            return p
    return None


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---"):
        raise SkillParseError("SKILL.md must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise SkillParseError("SKILL.md frontmatter not properly closed with ---")

    frontmatter_str = parts[1]
    body = parts[2].lstrip("\r\n").rstrip()

    metadata = _parse_yaml_mapping(frontmatter_str)
    return metadata, body


def _parse_yaml_mapping(frontmatter: str) -> dict[str, Any]:
    """Very small YAML subset parser for agentskills frontmatter.

    Supports:
      - top-level `key: value` (single-line scalars)
      - a `metadata:` block with one-level indentation (two spaces)

    This avoids adding a YAML dependency to the runtime.
    """

    lines = [ln.rstrip("\n") for ln in frontmatter.splitlines()]
    out: dict[str, Any] = {}
    i = 0

    def parse_scalar(raw: str) -> str:
        v = raw.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        return v

    while i < len(lines):
        line = lines[i].rstrip()
        i += 1

        if not line.strip():
            continue

        if line.lstrip().startswith("#"):
            continue

        if line.endswith(":") and line.strip() == "metadata:":
            meta: dict[str, str] = {}
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    i += 1
                    continue
                if not nxt.startswith("  "):
                    break
                i += 1
                if ":" not in nxt:
                    raise SkillParseError("Invalid metadata mapping line in frontmatter")
                k, v = nxt.strip().split(":", 1)
                meta[k.strip()] = parse_scalar(v)
            out["metadata"] = meta
            continue

        if ":" not in line:
            raise SkillParseError("Invalid YAML in frontmatter: expected 'key: value'")

        key, value = line.split(":", 1)
        out[key.strip()] = parse_scalar(value)

    return out


def _validate_name(name: str, skill_dir: Optional[Path]) -> list[str]:
    errors: list[str] = []

    if not name or not isinstance(name, str) or not name.strip():
        errors.append("Field 'name' must be a non-empty string")
        return errors

    normalized = unicodedata.normalize("NFKC", name.strip())

    if len(normalized) > MAX_SKILL_NAME_LENGTH:
        errors.append(
            f"Skill name '{normalized}' exceeds {MAX_SKILL_NAME_LENGTH} character limit ({len(normalized)} chars)"
        )

    if normalized != normalized.lower():
        errors.append(f"Skill name '{normalized}' must be lowercase")

    if normalized.startswith("-") or normalized.endswith("-"):
        errors.append("Skill name cannot start or end with a hyphen")

    if "--" in normalized:
        errors.append("Skill name cannot contain consecutive hyphens")

    if not all(c.isalnum() or c == "-" for c in normalized):
        errors.append(
            f"Skill name '{normalized}' contains invalid characters. Only letters, digits, and hyphens are allowed."
        )

    if skill_dir is not None:
        dir_name = unicodedata.normalize("NFKC", skill_dir.name)
        if dir_name != normalized:
            errors.append(f"Directory name '{skill_dir.name}' must match skill name '{normalized}'")

    return errors


def _validate_description(description: str) -> list[str]:
    errors: list[str] = []

    if not description or not isinstance(description, str) or not description.strip():
        errors.append("Field 'description' must be a non-empty string")
        return errors

    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} character limit ({len(description)} chars)"
        )

    return errors


def _validate_compatibility(compatibility: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(compatibility, str):
        errors.append("Field 'compatibility' must be a string")
        return errors

    if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        errors.append(
            f"Compatibility exceeds {MAX_COMPATIBILITY_LENGTH} character limit ({len(compatibility)} chars)"
        )

    return errors


def _validate_metadata_fields(metadata: dict[str, Any]) -> list[str]:
    extra = set(metadata.keys()) - ALLOWED_FIELDS
    if extra:
        return [
            f"Unexpected fields in frontmatter: {', '.join(sorted(extra))}. Only {sorted(ALLOWED_FIELDS)} are allowed."
        ]
    return []


def validate_skill_metadata(metadata: dict[str, Any], skill_dir: Optional[Path] = None) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_metadata_fields(metadata))

    if "name" not in metadata:
        errors.append("Missing required field in frontmatter: name")
    else:
        errors.extend(_validate_name(str(metadata["name"]), skill_dir))

    if "description" not in metadata:
        errors.append("Missing required field in frontmatter: description")
    else:
        errors.extend(_validate_description(str(metadata["description"])) )

    if "compatibility" in metadata:
        errors.extend(_validate_compatibility(metadata["compatibility"]))

    if "metadata" in metadata and not isinstance(metadata["metadata"], dict):
        errors.append("Field 'metadata' must be a mapping")

    return errors


def validate_skill_dir(skill_dir: Path) -> list[str]:
    if not skill_dir.exists():
        return [f"Path does not exist: {skill_dir}"]
    if not skill_dir.is_dir():
        return [f"Not a directory: {skill_dir}"]

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"]

    try:
        content = skill_md.read_text(encoding="utf-8")
        metadata, _ = _parse_frontmatter(content)
    except SkillParseError as e:
        return [str(e)]

    return validate_skill_metadata(metadata, skill_dir)


def read_skill_properties(skill_dir: Path) -> SkillProperties:
    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        raise SkillParseError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    metadata, _ = _parse_frontmatter(content)

    errors = validate_skill_metadata(metadata, skill_dir)
    if errors:
        raise SkillValidationError("Invalid SKILL.md frontmatter", errors=errors)

    name = unicodedata.normalize("NFKC", str(metadata["name"])).strip()
    description = str(metadata["description"]).strip()

    meta = metadata.get("metadata")
    meta_out: dict[str, str] = {}
    if isinstance(meta, dict):
        meta_out = {str(k): str(v) for k, v in meta.items()}

    return SkillProperties(
        name=name,
        description=description,
        license=metadata.get("license"),
        compatibility=metadata.get("compatibility"),
        allowed_tools=metadata.get("allowed-tools"),
        metadata=meta_out,
    )


def discover_skill_dirs(skill_roots: list[Path]) -> list[Path]:
    dirs: list[Path] = []
    for root in skill_roots:
        if not root.exists() or not root.is_dir():
            continue
        for child in root.iterdir():
            if not child.is_dir():
                continue
            if find_skill_md(child) is not None:
                dirs.append(child)
    return dirs


def _default_skill_roots() -> list[Path]:
    env = os.environ.get("OS_MCP_SKILLS_DIRS")
    if env:
        parts = [p.strip() for p in env.split(",") if p.strip()]
        return [Path(p) for p in parts]
    # Match VS Code Agent Skills auto-discovery locations, with a repo-root
    # `skills/` fallback for other clients.
    return [Path(".github/skills"), Path(".claude/skills"), Path("skills")]


def discover_skills(skill_roots: Optional[list[Path]] = None) -> list[SkillSummary]:
    roots = skill_roots if skill_roots is not None else _default_skill_roots()
    summaries: list[SkillSummary] = []

    for skill_dir in discover_skill_dirs(roots):
        try:
            props = read_skill_properties(skill_dir)
            skill_md = find_skill_md(skill_dir)
            if skill_md is None:
                continue
            summaries.append(
                SkillSummary(
                    name=props.name,
                    description=props.description,
                    location=str(skill_md.resolve()),
                )
            )
        except SkillError:
            # Ignore invalid skills for listing; callers can validate explicitly.
            continue

    summaries.sort(key=lambda s: s.name)
    return summaries


def skills_to_available_skills_xml(skill_dirs: list[Path]) -> str:
    """Generate the <available_skills> XML block (Anthropic-recommended format)."""
    if not skill_dirs:
        return "<available_skills>\n</available_skills>"

    lines: list[str] = ["<available_skills>"]

    for d in skill_dirs:
        props = read_skill_properties(d)
        skill_md = find_skill_md(d)
        if skill_md is None:
            continue

        lines.append("<skill>")
        lines.append("<name>")
        lines.append(html.escape(props.name))
        lines.append("</name>")
        lines.append("<description>")
        lines.append(html.escape(props.description))
        lines.append("</description>")
        lines.append("<location>")
        lines.append(html.escape(str(skill_md.resolve())))
        lines.append("</location>")
        lines.append("</skill>")

    lines.append("</available_skills>")
    return "\n".join(lines)
