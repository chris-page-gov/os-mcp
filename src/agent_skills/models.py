from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SkillProperties:
    """Properties parsed from a skill's SKILL.md frontmatter.

    Mirrors the agentskills.io frontmatter fields.
    """

    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out: dict[str, object] = {"name": self.name, "description": self.description}
        if self.license is not None:
            out["license"] = self.license
        if self.compatibility is not None:
            out["compatibility"] = self.compatibility
        if self.allowed_tools is not None:
            out["allowed-tools"] = self.allowed_tools
        if self.metadata:
            out["metadata"] = dict(self.metadata)
        return out


@dataclass(frozen=True)
class SkillSummary:
    name: str
    description: str
    location: str
