"""
build_agent_configs.py
───────────────────────────────────────────────────────────────────────────────
Renders the canonical agent command definitions in agent_config/commands/ into
every AI-client directory. ONE source of truth; N generated copies.

    python scripts/build_agent_configs.py           # write all client trees
    python scripts/build_agent_configs.py --check   # CI: fail if any tree drifted

Why this exists: the client trees (.claude/, .opencode/, cowork_plugin/) used
to be maintained as four hand-synced copies of the same files. In a project
whose whole point is zero drift, hand-synced prompt copies are drift waiting
to happen. Edit agent_config/commands/*.md, run this script, commit both.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL    = PROJECT_ROOT / "agent_config" / "commands"

# Every client directory that receives a copy of the canonical commands.
# Add new AI clients here — never by hand-copying files.
TARGETS = [
    PROJECT_ROOT / ".claude" / "commands",
    PROJECT_ROOT / ".opencode" / "commands",
    PROJECT_ROOT / "cowork_plugin" / "commands",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render canonical agent configs to client trees.")
    parser.add_argument("--check", action="store_true",
                        help="Verify the client trees match the canonical source (exit 1 on drift).")
    args = parser.parse_args()

    sources = sorted(CANONICAL.glob("*.md"))
    if not sources:
        print(f"❌ No canonical commands found in {CANONICAL}")
        return 1

    drifted: list[str] = []
    for target_dir in TARGETS:
        target_dir.mkdir(parents=True, exist_ok=True)
        for src in sources:
            dst = target_dir / src.name
            if args.check:
                if not dst.exists() or dst.read_text() != src.read_text():
                    drifted.append(str(dst.relative_to(PROJECT_ROOT)))
            else:
                dst.write_text(src.read_text())
        # Stale files in a client tree that no longer exist canonically
        for extra in target_dir.glob("*.md"):
            if not (CANONICAL / extra.name).exists():
                if args.check:
                    drifted.append(f"{extra.relative_to(PROJECT_ROOT)} (no canonical source)")
                else:
                    extra.unlink()
                    print(f"removed stale {extra.relative_to(PROJECT_ROOT)}")

    if args.check:
        if drifted:
            print("❌ Agent config drift — client trees don't match agent_config/commands/:")
            for d in drifted:
                print(f"   {d}")
            print("Fix with: python scripts/build_agent_configs.py")
            return 1
        print(f"✅ All {len(TARGETS)} client trees match the canonical source ({len(sources)} commands).")
        return 0

    print(f"✅ Rendered {len(sources)} commands to {len(TARGETS)} client trees.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
