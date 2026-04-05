import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "finhjb-model-coder"
INSTALL_SCRIPT = ROOT / "scripts" / "install_skill.py"

EXPECTED_REFERENCES = {
    "clarification-checklist.md",
    "delivery-and-validation.md",
    "implementation-decision-rules.md",
    "math-to-finhjb-mapping.md",
    "model-spec-schema.md",
    "parameter-search-protocol.md",
    "readiness-and-scope.md",
}

EXPECTED_TEMPLATES = {
    "parameter-search-task.py",
    "single-control-fixed-boundary.py",
    "single-control-boundary-search.py",
    "multi-control-boundary-update.py",
    "multi-control-boundary-search.py",
}

EXPECTED_SCRIPTS = {
    "parameter_search_runner.py",
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
    scripts = {path.name for path in (SKILL_DIR / "scripts").glob("*.py")}

    assert EXPECTED_REFERENCES <= references
    assert EXPECTED_TEMPLATES <= templates
    assert EXPECTED_SCRIPTS <= scripts


def test_skill_workflow_mentions_environment_and_test_loop():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    schema_text = (SKILL_DIR / "references" / "model-spec-schema.md").read_text()
    checklist_text = (SKILL_DIR / "references" / "clarification-checklist.md").read_text()
    readiness_text = (SKILL_DIR / "references" / "readiness-and-scope.md").read_text()
    decision_text = (SKILL_DIR / "references" / "implementation-decision-rules.md").read_text()
    delivery_text = (SKILL_DIR / "references" / "delivery-and-validation.md").read_text()
    search_text = (SKILL_DIR / "references" / "parameter-search-protocol.md").read_text()

    assert "## Mission" in skill_text
    assert "## Use This Skill When" in skill_text
    assert "## Fast Routing" in skill_text
    assert "## Stage Protocol" in skill_text
    assert "## Output Rule" in skill_text
    assert "parameter-search rescue mode" in skill_text
    assert "hard constraints before soft preferences" in skill_text
    assert "`derivative_method`" in schema_text
    assert "no confirmed numeric calibration" in schema_text
    assert "`plot_requirements`" in schema_text
    assert "`project_layout`" in schema_text
    assert "`parameter_search.fixed_parameters`" in schema_text
    assert "## Stage 5: Parameter Search Rescue" in schema_text
    assert "`derivation_requirements`" in schema_text
    assert "## Stage 1: Delivery Context" in schema_text
    assert "## Stage 4: Solve Plan" in schema_text
    assert "target “shape” has not yet been translated into diagnostics" in schema_text
    assert "Ask Only When The Answer Changes The Build" in checklist_text
    assert "Rescue-Mode Questions" in checklist_text
    assert "fixed/search parameter split" in checklist_text
    assert "translate them into metrics" in checklist_text
    assert "`post_generation_tests`" in schema_text
    assert "## Hard Gate" in readiness_text
    assert "Final executable delivery is allowed only after a smoke test" in readiness_text
    assert "## Derivative Scheme" in decision_text
    assert "## Boundary Search Method" in decision_text
    assert "## Template Choice" in decision_text
    assert "## Project Layout" in decision_text
    assert "Rescue-Search Delivery Contract" in delivery_text
    assert "executed test-and-repair summary" in delivery_text
    assert "search runner plus task-adapter layout summary" in delivery_text
    assert "Activation Rule" in search_text
    assert "Translating Vague Preferences Into Diagnostics" in search_text


def test_docs_indexes_link_skill_page():
    docs_index_en = (ROOT / "docs" / "en" / "index.md").read_text()
    docs_index_zh = (ROOT / "docs" / "zh" / "index.md").read_text()

    assert "finhjb-model-coder" in docs_index_en
    assert "finhjb-model-coder" in docs_index_zh
    assert "actually run `finhjb`" in docs_index_en
    assert "真的运行 `finhjb`" in docs_index_zh


def test_docs_and_readme_describe_environment_numerics_and_test_loop():
    readme_en = (ROOT / "README.md").read_text()
    readme_zh = (ROOT / "README.zh-CN.md").read_text()
    skill_en = (ROOT / "docs" / "en" / "finhjb-model-coder.md").read_text()
    skill_zh = (ROOT / "docs" / "zh" / "finhjb-model-coder.md").read_text()
    install_en = (ROOT / "docs" / "en" / "installation-and-environment.md").read_text()
    install_zh = (ROOT / "docs" / "zh" / "installation-and-environment.md").read_text()
    solver_en = (ROOT / "docs" / "en" / "solver-guide.md").read_text()
    solver_zh = (ROOT / "docs" / "zh" / "solver-guide.md").read_text()

    assert "confirm that the target Python environment can actually run `finhjb`" in readme_en
    assert "先确认目标 Python 环境是否真的能运行 `finhjb`" in readme_zh
    assert "parameter-search rescue mode" in skill_en
    assert "parameter-search rescue mode" in skill_zh
    assert "`fixed_parameters`" in skill_en
    assert "`fixed_parameters`" in skill_zh
    assert "current one-dimensional FinHJB interface" in skill_en
    assert "当前一维 FinHJB 接口" in skill_zh
    assert "generate runnable FinHJB code" in skill_en
    assert "生成可运行的 FinHJB 代码" in skill_zh
    assert "post-generation test loop" in skill_en
    assert "生成后的测试修复闭环" in skill_zh
    assert "split the deliverable into solve, data, and plotting files" in readme_en
    assert "拆成求解、数据和绘图文件" in readme_zh
    assert "derivations" in readme_en
    assert "推导" in readme_zh
    assert "Before You Ask `finhjb-model-coder` For Runnable Code" in install_en
    assert "在要求 `finhjb-model-coder` 交付可运行代码之前" in install_zh
    assert "When Not To Use `central`" in solver_en
    assert "什么时候不该继续用 `central`" in solver_zh


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
