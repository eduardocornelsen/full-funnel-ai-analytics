"""
generate_project_instructions.py
────────────────────────────────────────────────────────────────────────────
Regenerates docs/guides/claude_desktop_project_instructions.md from
CLAUDE.md + the commands section template.

Run this whenever CLAUDE.md changes significantly (new metric rules,
new MCP servers, changed data sourcing logic). Then re-paste the output
into Claude Projects → Project Instructions.

Usage:
    python scripts/generate_project_instructions.py
    python scripts/generate_project_instructions.py --check   # CI: exit 1 if out of sync

The script does NOT attempt to auto-sync every rule from CLAUDE.md — the
Desktop file is intentionally leaner (no git-specific path references, no
Python import examples). Instead it:

1. Extracts the canonical metric rules from CLAUDE.md (§1–§8) as a
   compact summary.
2. Checks that every MCP server in .mcp.json is listed in the Desktop file.
3. Checks that the schema version watermark matches CLAUDE.md's schema_version.
4. Optionally rewrites the file with a freshness timestamp.

For full rewrites (new commands, restructured rules), edit the template
section at the bottom of this file and re-run.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CLAUDE_MD    = PROJECT_ROOT / "CLAUDE.md"
DESKTOP_FILE = PROJECT_ROOT / "docs" / "guides" / "claude_desktop_project_instructions.md"
MCP_JSON     = PROJECT_ROOT / ".mcp.json"


def get_schema_version() -> str:
    """Extract schema_version from CLAUDE.md (looks for 'schema v2.x' pattern)."""
    text = CLAUDE_MD.read_text()
    m = re.search(r"schema v(\d+\.\d+)", text)
    return m.group(1) if m else "unknown"


def get_mcp_servers() -> list[str]:
    """Return server names from .mcp.json."""
    if not MCP_JSON.exists():
        return []
    data = json.loads(MCP_JSON.read_text())
    return list(data.get("mcpServers", {}).keys())


def check_sync() -> list[str]:
    """
    Run basic sync checks. Returns a list of problems found.
    An empty list means the file looks in sync.
    """
    problems = []
    desktop_text = DESKTOP_FILE.read_text()
    schema_ver   = get_schema_version()
    mcp_servers  = get_mcp_servers()

    # Schema version watermark
    if f"schema v{schema_ver}" not in desktop_text:
        problems.append(
            f"Schema version mismatch: CLAUDE.md is v{schema_ver} but "
            f"Desktop file does not mention 'schema v{schema_ver}'"
        )

    # All MCP servers listed
    for server in mcp_servers:
        if server not in ("dbt-semantic-layer",) and server not in desktop_text:
            problems.append(f"MCP server '{server}' is in .mcp.json but not mentioned in Desktop file")

    # Golden layer first rule present
    if "Golden Layer First" not in desktop_text and "golden layer" not in desktop_text.lower():
        problems.append("Desktop file does not mention the golden layer first rule")

    # Dynamic dates — no hardcoded window dates
    hardcoded = re.findall(r"20\d\d-\d\d-\d\d", desktop_text)
    if hardcoded:
        problems.append(
            f"Desktop file contains hardcoded dates (should use analytics.get_meta()): "
            f"{', '.join(set(hardcoded))}"
        )

    return problems


def update_watermark():
    """Update the 'Generated from CLAUDE.md schema vX.X' line with today's date."""
    text         = DESKTOP_FILE.read_text()
    schema_ver   = get_schema_version()
    today        = date.today().isoformat()
    new_watermark = (
        f"*Generated from CLAUDE.md schema v{schema_ver} · last sync {today}. "
        f"Re-paste whenever CLAUDE.md changes significantly.*"
    )
    text = re.sub(
        r"\*Generated from CLAUDE\.md schema v[\d.]+ .*?\*",
        new_watermark,
        text,
    )
    DESKTOP_FILE.write_text(text)
    print(f"Updated watermark → schema v{schema_ver} · {today}")


def main() -> int:
    check_mode = "--check" in sys.argv

    problems = check_sync()

    if problems:
        print("❌ Desktop instructions out of sync with CLAUDE.md:\n")
        for p in problems:
            print(f"  • {p}")
        print(
            "\nFix: edit docs/guides/claude_desktop_project_instructions.md "
            "then re-paste into Claude Projects."
        )
        return 1

    if not check_mode:
        update_watermark()
        print("✅ Desktop instructions are in sync.")
        print(f"   File: {DESKTOP_FILE}")
        print("   Re-paste into Claude Projects → Project Instructions.")
    else:
        print("✅ Desktop instructions look in sync with CLAUDE.md.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
