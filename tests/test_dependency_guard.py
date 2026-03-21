import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
STDLIB_BACKFILL = {"graphlib", "pathlib"}


def _dependency_name(requirement: str) -> str:
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        return requirement.strip().lower()
    return match.group(1).lower()


def test_pyproject_excludes_stdlib_backfill_packages() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]
    dep_names = {_dependency_name(dep) for dep in dependencies}
    overlap = dep_names & STDLIB_BACKFILL
    assert overlap == set(), (
        f"Remove stdlib backfill packages from dependencies: {sorted(overlap)}"
    )


def test_lockfile_excludes_stdlib_backfill_packages() -> None:
    lockfile = (ROOT / "uv.lock").read_text()
    for package in sorted(STDLIB_BACKFILL):
        assert f'name = "{package}"' not in lockfile
