import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "finhjb-model-coder"
INSTALL_SCRIPT = ROOT / "scripts" / "install_skill.py"

EXPECTED_REFERENCES = {
    "clarification-checklist.md",
    "environment-readiness.md",
    "math-to-finhjb-mapping.md",
    "model-spec-schema.md",
    "numerical-method-selection.md",
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


def test_skill_workflow_mentions_environment_and_test_loop():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    schema_text = (SKILL_DIR / "references" / "model-spec-schema.md").read_text()
    checklist_text = (SKILL_DIR / "references" / "clarification-checklist.md").read_text()
    env_text = (SKILL_DIR / "references" / "environment-readiness.md").read_text()
    numeric_text = (SKILL_DIR / "references" / "numerical-method-selection.md").read_text()
    output_text = (SKILL_DIR / "references" / "output-contract.md").read_text()

    assert "Environment readiness is a hard gate" in skill_text
    assert "missing economic parameter values as a hard blocker" in skill_text
    assert "unspecified plotting requirements as a blocker" in skill_text
    assert "sensitivity analysis with plotting" in skill_text
    assert "Run the post-generation test loop" in skill_text
    assert "`derivative_method`" in schema_text
    assert "no confirmed numeric calibration" in schema_text
    assert "`plot_requirements`" in schema_text
    assert "`project_layout`" in schema_text
    assert "ask before code generation instead of inventing a baseline" in checklist_text
    assert "ask before writing plotting code instead of guessing the figure layout" in checklist_text
    assert "default to a split file layout" in checklist_text
    assert "`post_generation_tests`" in schema_text
    assert "Final executable code delivery is allowed only after a smoke test" in env_text
    assert "Choose the finite-difference scheme" in numeric_text
    assert "produce four deliverables" in output_text


def test_docs_indexes_link_skill_page():
    docs_index_en = (ROOT / "docs" / "en" / "index.md").read_text()
    docs_index_zh = (ROOT / "docs" / "zh" / "index.md").read_text()

    assert "finhjb-model-coder" in docs_index_en
    assert "finhjb-model-coder" in docs_index_zh
    assert "runnable FinHJB environment" in docs_index_en
    assert "可运行环境" in docs_index_zh


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
    assert "Environment And Preconditions" in skill_en
    assert "运行环境与前置条件" in skill_zh
    assert "Choosing The Derivative Scheme" in skill_en
    assert "差分格式如何选" in skill_zh
    assert "Choosing The Boundary Search Method" in skill_en
    assert "边界搜索方法如何选" in skill_zh
    assert "post-generation test loop" in skill_en
    assert "生成后的测试修复闭环" in skill_zh
    assert "defines parameters but does not give the calibration" in skill_en
    assert "定义了参数，但没有给出数值校准" in skill_zh
    assert "what to plot when the user requests figures" in skill_en
    assert "要求画图但没有说明具体画什么" in skill_zh
    assert "File Layout For Sensitivity Analysis And Plotting" in skill_en
    assert "敏感性分析加作图时的文件结构" in skill_zh
    assert "split the deliverable into solve, data, and plotting files" in readme_en
    assert "默认拆成求解文件、数据保存文件、绘图文件" in readme_zh
    assert "If You Plan To Use `finhjb-model-coder`" in install_en
    assert "如果你打算使用 `finhjb-model-coder`" in install_zh
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
