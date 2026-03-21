import re
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
STDLIB_BACKFILL = {"graphlib", "pathlib"}


def _dependency_name(requirement: str) -> str:
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        return requirement.strip().lower()
    return match.group(1).lower()


class DependencyGuardTests(unittest.TestCase):
    def test_pyproject_excludes_stdlib_backfill_packages(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
        dependencies = pyproject["project"]["dependencies"]
        dep_names = {_dependency_name(dep) for dep in dependencies}
        overlap = dep_names & STDLIB_BACKFILL
        self.assertEqual(
            overlap,
            set(),
            msg=f"Remove stdlib backfill packages from dependencies: {sorted(overlap)}",
        )

    def test_lockfile_excludes_stdlib_backfill_packages(self) -> None:
        lockfile = (ROOT / "uv.lock").read_text()
        for package in sorted(STDLIB_BACKFILL):
            self.assertNotIn(f'name = "{package}"', lockfile)


if __name__ == "__main__":
    unittest.main()
