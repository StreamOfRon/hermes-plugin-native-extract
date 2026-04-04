"""Tests for skill frontmatter parsing and structure validation.

Validates that SKILL.md files have correct frontmatter,
required fields, and field length constraints.
"""

import re
from pathlib import Path

import pytest

SKILL_PATH = Path(__file__).parent.parent / "skill" / "SKILL.md"


def parse_frontmatter(content: str) -> dict:
    """Extract and parse YAML frontmatter from a SKILL.md file."""
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "SKILL.md must have YAML frontmatter delimited by ---"

    return yaml.safe_load(match.group(1))


class TestSkillFrontmatter:
    """Test SKILL.md frontmatter parsing."""

    def test_frontmatter_exists(self):
        """SKILL.md must have YAML frontmatter."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)
        assert isinstance(frontmatter, dict)

    def test_required_field_name(self):
        """Frontmatter must include 'name' field."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)
        assert "name" in frontmatter
        assert isinstance(frontmatter["name"], str)
        assert len(frontmatter["name"]) > 0

    def test_required_field_description(self):
        """Frontmatter must include 'description' field."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)
        assert "description" in frontmatter
        assert isinstance(frontmatter["description"], str)
        assert len(frontmatter["description"]) > 0

    def test_name_length_constraint(self):
        """Name field should be under 50 characters."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)
        assert len(frontmatter["name"]) <= 50

    def test_description_length_constraint(self):
        """Description field should be under 200 characters."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)
        assert len(frontmatter["description"]) <= 200


class TestSkillStructure:
    """Test SKILL.md file structure."""

    def test_file_exists(self):
        """SKILL.md must exist in the skill directory."""
        assert SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}"

    def test_has_body_content(self):
        """SKILL.md must have content after frontmatter."""
        content = SKILL_PATH.read_text()
        parts = re.split(r"^---$", content, flags=re.MULTILINE)
        assert len(parts) >= 3, "SKILL.md must have content after frontmatter"

        body = parts[2].strip()
        assert len(body) > 0, "SKILL.md body must not be empty"

    def test_has_sections(self):
        """SKILL.md should have standard sections."""
        content = SKILL_PATH.read_text()
        # Check for at least one standard section header
        sections = [
            "## When to Use",
            "## Procedure",
            "## Pitfalls",
            "## Verification",
        ]
        found = [s for s in sections if s in content]
        assert len(found) >= 2, (
            f"SKILL.md should have at least 2 standard sections, found: {found}"
        )


class TestSkillOptionalFields:
    """Test optional frontmatter fields."""

    def test_optional_fields_types(self):
        """Optional fields should have correct types if present."""
        content = SKILL_PATH.read_text()
        frontmatter = parse_frontmatter(content)

        if "author" in frontmatter:
            assert isinstance(frontmatter["author"], str)

        if "version" in frontmatter:
            assert isinstance(frontmatter["version"], (str, int, float))

        if "tags" in frontmatter:
            assert isinstance(frontmatter["tags"], list)

        if "requires_tools" in frontmatter:
            assert isinstance(frontmatter["requires_tools"], list)

        if "provides_commands" in frontmatter:
            assert isinstance(frontmatter["provides_commands"], list)
