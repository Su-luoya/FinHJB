#!/usr/bin/env python3
"""Install the `finhjb-model-coder` skill into a Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

SKILL_NAME = "finhjb-model-coder"
REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "skills" / SKILL_NAME


def default_skills_root() -> Path:
    """Return the default directory that stores installed Codex skills."""
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def resolve_install_target(dest: str | None) -> Path:
    """Resolve the install target from an optional destination override."""
    if dest is None:
        return default_skills_root() / SKILL_NAME

    raw_dest = Path(dest).expanduser()
    if raw_dest.name == SKILL_NAME:
        return raw_dest.resolve()
    return (raw_dest / SKILL_NAME).resolve()


def remove_existing_path(path: Path) -> None:
    """Remove an existing file, directory, or symlink."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def install_skill(target: Path, mode: str, force: bool, dry_run: bool) -> int:
    """Install the skill by copying or linking it into the target directory."""
    if not SOURCE_DIR.exists():
        print(f"Source skill directory not found: {SOURCE_DIR}", file=sys.stderr)
        return 1

    if target.exists():
        if not force:
            print(
                f"Target already exists: {target}\n"
                "Re-run with --force to replace the existing installation.",
                file=sys.stderr,
            )
            return 1
        if not dry_run:
            remove_existing_path(target)

    if dry_run:
        print(f"[dry-run] mode={mode} source={SOURCE_DIR} target={target}")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copytree(SOURCE_DIR, target)
    else:
        target.symlink_to(SOURCE_DIR, target_is_directory=True)

    print(f"Installed {SKILL_NAME} to {target} using mode={mode}")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Install the finhjb-model-coder skill into a Codex skills directory.",
    )
    parser.add_argument(
        "--dest",
        help=(
            "Destination skills root, or a full target path ending in "
            f"'{SKILL_NAME}'. Default: ${'{'}CODEX_HOME:-~/.codex{'}'}/skills"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("copy", "link"),
        default="copy",
        help="Install by copying the skill directory or by creating a symlink.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing installation at the target path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved install action without writing any files.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the skill installer CLI."""
    args = parse_args()
    target = resolve_install_target(args.dest)
    return install_skill(target=target, mode=args.mode, force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
