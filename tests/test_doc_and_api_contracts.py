import ast
from pathlib import Path

import finhjb as fjb

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "finhjb"


def test_all_source_classes_and_functions_have_docstrings():
    missing: list[tuple[str, int, str]] = []
    for file_path in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in file_path.parts:
            continue
        tree = ast.parse(file_path.read_text())
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if ast.get_docstring(node) is None:
                    missing.append((str(file_path), node.lineno, f"class {node.name}"))
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if ast.get_docstring(method) is None:
                            missing.append(
                                (
                                    str(file_path),
                                    method.lineno,
                                    f"method {node.name}.{method.name}",
                                )
                            )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node) is None:
                    missing.append((str(file_path), node.lineno, f"func {node.name}"))

    assert not missing, f"Missing docstrings: {missing}"


def test_public_exports_are_importable():
    for symbol in fjb.__all__:
        assert hasattr(fjb, symbol), f"Missing export: {symbol}"


def test_bilingual_docs_mirror_expected_pages():
    pages = {
        "installation-and-environment.md",
        "index.md",
        "getting-started.md",
        "quickstart-library.md",
        "troubleshooting.md",
        "finhjb-model-coder.md",
        "finhjb-model-coder-overview.md",
        "finhjb-model-coder-inputs-and-readiness.md",
        "finhjb-model-coder-output-and-validation.md",
        "bcw2011-case-study.md",
        "bcw2011-liquidation-walkthrough.md",
        "bcw2011-refinancing-walkthrough.md",
        "bcw2011-hedging-walkthrough.md",
        "bcw2011-credit-line-walkthrough.md",
        "results-and-diagnostics.md",
        "modeling-guide.md",
        "adapting-bcw-to-your-model.md",
        "solver-guide.md",
        "api-reference.md",
        "faq.md",
    }
    en_pages = {p.name for p in (ROOT / "docs" / "en").glob("*.md")}
    zh_pages = {p.name for p in (ROOT / "docs" / "zh").glob("*.md")}

    assert pages <= en_pages
    assert pages <= zh_pages


def test_readme_points_to_existing_docs_entrypoints():
    readme_en = (ROOT / "README.md").read_text()
    readme_zh = (ROOT / "README.zh-CN.md").read_text()

    en_targets = [
        "./docs/en/index.md",
        "./docs/en/installation-and-environment.md",
        "./docs/en/getting-started.md",
        "./docs/en/quickstart-library.md",
        "./docs/en/finhjb-model-coder.md",
        "./docs/en/finhjb-model-coder-overview.md",
        "./docs/en/bcw2011-case-study.md",
        "./docs/en/adapting-bcw-to-your-model.md",
    ]
    zh_targets = [
        "./docs/zh/index.md",
        "./docs/zh/installation-and-environment.md",
        "./docs/zh/getting-started.md",
        "./docs/zh/quickstart-library.md",
        "./docs/zh/finhjb-model-coder.md",
        "./docs/zh/finhjb-model-coder-overview.md",
        "./docs/zh/bcw2011-case-study.md",
        "./docs/zh/adapting-bcw-to-your-model.md",
    ]

    for target in en_targets:
        assert target in readme_en
        assert (ROOT / target.removeprefix("./")).exists()

    for target in zh_targets:
        assert target in readme_zh
        assert (ROOT / target.removeprefix("./")).exists()


def test_readmes_keep_minimal_install_commands():
    readme_en = (ROOT / "README.md").read_text()
    readme_zh = (ROOT / "README.zh-CN.md").read_text()

    for readme in (readme_en, readme_zh):
        assert "uv add finhjb" in readme
        assert "pip install finhjb" in readme


def test_readmes_document_skill_installation():
    readme_en = (ROOT / "README.md").read_text()
    readme_zh = (ROOT / "README.zh-CN.md").read_text()

    for readme in (readme_en, readme_zh):
        assert "finhjb-model-coder" in readme
        assert "python scripts/install_skill.py" in readme


def test_public_api_names_are_documented():
    readme_en = (ROOT / "README.md").read_text()
    readme_zh = (ROOT / "README.zh-CN.md").read_text()
    api_en = (ROOT / "docs" / "en" / "api-reference.md").read_text()
    api_zh = (ROOT / "docs" / "zh" / "api-reference.md").read_text()

    for symbol in fjb.__all__:
        assert symbol in readme_en or symbol in api_en
        assert symbol in readme_zh or symbol in api_zh


def test_docs_root_contains_only_language_directories():
    docs_root = ROOT / "docs"
    files_in_root = [p for p in docs_root.iterdir() if p.is_file()]
    dirs_in_root = {p.name for p in docs_root.iterdir() if p.is_dir()}

    assert files_in_root == []
    assert dirs_in_root == {"en", "zh"}
