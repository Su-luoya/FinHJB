import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "finhjb-model-coder"
INSTALL_SCRIPT = ROOT / "scripts" / "install_skill.py"

EXPECTED_REFERENCES = {
    "clarification-checklist.md",
    "math-to-finhjb-mapping.md",
    "model-spec-schema.md",
    "output-contract.md",
    "template-selection.md",
    "unsupported-models.md",
    "validation-checklist.md",
}

EXPECTED_TEMPLATES = {
    "single-control-fixed-boundary.py",
    "single-control-boundary-search.py",
    "multi-control-boundary-update.py",
    "multi-control-boundary-search.py",
}


def extract_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match is not None, "SKILL.md is missing YAML frontmatter"

    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def test_skill_frontmatter_and_openai_metadata():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    frontmatter = extract_frontmatter(skill_text)

    assert frontmatter["name"] == "finhjb-model-coder"
    assert "one-dimensional FinHJB implementations" in frontmatter["description"]

    openai_yaml = (SKILL_DIR / "agents" / "openai.yaml").read_text()
    assert 'display_name: "FinHJB Model Coder"' in openai_yaml
    assert 'short_description: "Convert finance models into FinHJB code"' in openai_yaml
    assert "$finhjb-model-coder" in openai_yaml


def test_skill_resources_exist():
    references = {path.name for path in (SKILL_DIR / "references").glob("*.md")}
    templates = {path.name for path in (SKILL_DIR / "assets" / "templates").glob("*.py")}

    assert EXPECTED_REFERENCES <= references
    assert EXPECTED_TEMPLATES <= templates


def test_docs_indexes_link_skill_page():
    docs_index_en = (ROOT / "docs" / "en" / "index.md").read_text()
    docs_index_zh = (ROOT / "docs" / "zh" / "index.md").read_text()

    assert "finhjb-model-coder" in docs_index_en
    assert "finhjb-model-coder" in docs_index_zh


def test_install_script_dry_run_does_not_write(tmp_path):
    dest_root = tmp_path / "skills-root"
    result = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), "--dest", str(dest_root), "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "dry-run" in result.stdout
    assert not (dest_root / "finhjb-model-coder").exists()


def test_install_script_copy_and_force(tmp_path):
    dest_root = tmp_path / "skills-root"
    target = dest_root / "finhjb-model-coder"

    first_run = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), "--dest", str(dest_root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first_run.returncode == 0
    assert target.exists()
    assert (target / "SKILL.md").exists()

    marker = target / "stale.txt"
    marker.write_text("stale")

    second_run = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), "--dest", str(dest_root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert second_run.returncode != 0
    assert marker.exists()

    force_run = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), "--dest", str(dest_root), "--force"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert force_run.returncode == 0
    assert target.exists()
    assert not marker.exists()
