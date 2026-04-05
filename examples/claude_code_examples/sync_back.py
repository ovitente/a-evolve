#!/usr/bin/env python3
"""Sync evolved workspace back to ~/.claude/agents/.

Shows a diff before applying. Does not overwrite without confirmation.

Usage:
    python examples/claude_code_examples/sync_back.py \
        --workspace evolution_workdir/architect \
        --role architect \
        --target ~/.claude/agents/
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def show_diff(old_path: Path, new_path: Path, label: str) -> bool:
    """Show unified diff between two files. Returns True if they differ."""
    old = old_path.read_text() if old_path.exists() else ""
    new = new_path.read_text() if new_path.exists() else ""

    if old == new:
        return False

    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"original/{label}",
        tofile=f"evolved/{label}",
    )
    print(f"\n--- Diff: {label} ---")
    sys.stdout.writelines(diff)
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync evolved agent back to dotfiles")
    parser.add_argument("--workspace", required=True, help="Evolved workspace path")
    parser.add_argument("--role", required=True, help="Agent role name")
    parser.add_argument("--target", default=str(Path.home() / ".claude" / "agents"),
                        help="Target agents directory")
    parser.add_argument("--dry-run", action="store_true", help="Show diff only, don't copy")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    target = Path(args.target)

    if not workspace.exists():
        print(f"Error: workspace not found: {workspace}")
        sys.exit(1)

    # 1. System prompt -> agent .md file
    evolved_prompt = workspace / "prompts" / "system.md"
    target_prompt = target / f"{args.role}.md"

    has_changes = False

    if evolved_prompt.exists():
        if show_diff(target_prompt, evolved_prompt, f"{args.role}.md"):
            has_changes = True

    # 2. Skills
    skills_dir = workspace / "skills"
    target_skills = target / "skills"

    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            # Read skill content and inject target_agents
            content = skill_file.read_text()
            if "target_agents:" not in content:
                # Add target_agents to frontmatter
                content = content.replace(
                    "---\n",
                    f"---\ntarget_agents:\n  - {args.role.upper()}\n",
                    1,  # only first occurrence (closing ---)
                )

            target_skill = target_skills / f"{skill_dir.name}.md"
            old_content = target_skill.read_text() if target_skill.exists() else ""

            if content != old_content:
                has_changes = True
                print(f"\n--- New skill: {skill_dir.name} ---")
                print(content[:500])
                if len(content) > 500:
                    print(f"... ({len(content)} chars total)")

    if not has_changes:
        print("No changes to apply.")
        return

    if args.dry_run:
        print("\n[dry-run] No files modified.")
        return

    # Confirm
    answer = input("\nApply these changes? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    # Apply prompt
    if evolved_prompt.exists():
        shutil.copy2(evolved_prompt, target_prompt)
        print(f"Copied: {target_prompt}")

    # Apply skills
    if skills_dir.exists():
        target_skills.mkdir(parents=True, exist_ok=True)
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            content = skill_file.read_text()
            if "target_agents:" not in content:
                content = content.replace(
                    "---\n",
                    f"---\ntarget_agents:\n  - {args.role.upper()}\n",
                    1,
                )

            target_skill = target_skills / f"{skill_dir.name}.md"
            target_skill.write_text(content)
            print(f"Copied skill: {target_skill}")

    print("\nDone. Run /dev to test with evolved agents.")


if __name__ == "__main__":
    main()
