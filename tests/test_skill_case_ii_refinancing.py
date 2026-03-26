import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_TEST_DIR = ROOT / "skills" / "finhjb-model-coder" / "tests"
FIXTURE_FILE = SKILL_TEST_DIR / "BCWrefinancing.py"

EXPECTED_TRACKED_FILES = {
    "README.md",
    "case_ii_refinancing_prompt.md",
    "case_ii_refinancing_live_transcript.md",
    "case_ii_refinancing_scripted_protocol.md",
    "case_ii_refinancing_confirmed_spec.md",
    "BCWrefinancing.py",
}


def load_fixture_module():
    spec = importlib.util.spec_from_file_location("bcw_refinancing_fixture", FIXTURE_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_skill_local_refinancing_bundle_exists():
    assert SKILL_TEST_DIR.exists()
    tracked = {path.name for path in SKILL_TEST_DIR.iterdir() if path.is_file()}
    assert EXPECTED_TRACKED_FILES <= tracked
    assert (SKILL_TEST_DIR / "artifacts" / ".gitignore").exists()


def test_interaction_docs_capture_model_confirmation():
    live = (SKILL_TEST_DIR / "case_ii_refinancing_live_transcript.md").read_text()
    protocol = (SKILL_TEST_DIR / "case_ii_refinancing_scripted_protocol.md").read_text()
    spec = (SKILL_TEST_DIR / "case_ii_refinancing_confirmed_spec.md").read_text()

    assert "one-dimensional" in live
    assert "not the hedging extension" in live
    assert "repo-backed FinHJB task" in live
    assert 'uv run python -c "import finhjb"' in live
    assert "phi = 1%" in protocol
    assert "phi = 0" in protocol
    assert "post-generation solve loop" in protocol
    assert "Eq. (19)" in spec
    assert "Eq. (20)" in spec
    assert "derivative method: `central`" in spec
    assert "final search method in the archived fixture: `hybr`" in spec


def test_refinancing_fixture_runs_and_matches_bcq_targets(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    module = load_fixture_module()

    bundle = module.run_fixture(output_dir=tmp_path, number=1000)
    fixed = bundle["fixed-cost"]
    no_fixed = bundle["no-fixed-cost"]

    fixed_summary = fixed["summary"]
    no_fixed_summary = no_fixed["summary"]

    assert abs(fixed_summary["payout_boundary"] - 0.19) <= 0.03
    assert abs(fixed_summary["return_cash_ratio"] - 0.06) <= 0.02
    assert fixed_summary["p0_above_l"]
    assert abs(fixed_summary["dv_at_m"] - 1.06) <= 0.05
    assert 0.08 <= fixed_summary["investment_at_payout"] <= 0.14

    assert abs(no_fixed_summary["payout_boundary"] - 0.14) <= 0.03
    assert abs(no_fixed_summary["return_cash_ratio"] - 0.0) <= 0.02

    assert fixed_summary["derivative_method"] == "central"
    assert fixed_summary["boundary_search_method"] == "hybr"
    assert fixed_summary["is_value_increasing"]
    assert fixed_summary["is_dv_decreasing"]
    assert fixed_summary["is_investment_increasing"]

    figure_path = bundle["artifact_paths"]["figure"]
    summary_path = bundle["artifact_paths"]["summary"]
    test_report_path = bundle["artifact_paths"]["test_report"]
    assert figure_path.exists()
    assert summary_path.exists()
    assert test_report_path.exists()

    report = test_report_path.read_text()
    assert "repo-backed" in report
    assert "target_default" in report
    assert "bisection" in report
    assert "final_boundary_search_method" in report
    assert "hybr" in report


def test_refinancing_fixture_stays_single_control():
    text = FIXTURE_FILE.read_text()
    assert "psi" not in text
    assert "sigma_m" not in text
    assert "epsilon" not in text
    assert "rho" not in text
    assert 'DEFAULT_DERIVATIVE_METHOD = "central"' in text
    assert 'DEFAULT_SEARCH_METHOD = "hybr"' in text
