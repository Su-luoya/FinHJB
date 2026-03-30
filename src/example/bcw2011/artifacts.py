"""Artifact helpers for BCW2011 example outputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .common import CASE_ARTIFACT_ROOT, DOCS_ASSET_ROOT_EN, DOCS_ASSET_ROOT_ZH


def case_output_dir(case_slug: str, output_dir: str | Path | None = None) -> Path:
    """Return the artifact directory for a BCW case."""
    path = CASE_ARTIFACT_ROOT / case_slug if output_dir is None else Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_summary_json(output_dir: str | Path, payload) -> Path:
    """Write a JSON summary payload."""
    output_path = Path(output_dir) / "summary.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def write_test_report(output_dir: str | Path, payload) -> Path:
    """Write a JSON test report payload."""
    output_path = Path(output_dir) / "test_report.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return output_path


def publish_docs_figure(source_path: str | Path, asset_name: str) -> dict[str, Path]:
    """Copy a generated figure into both docs asset directories."""
    source = Path(source_path)
    DOCS_ASSET_ROOT_EN.mkdir(parents=True, exist_ok=True)
    DOCS_ASSET_ROOT_ZH.mkdir(parents=True, exist_ok=True)
    target_en = DOCS_ASSET_ROOT_EN / asset_name
    target_zh = DOCS_ASSET_ROOT_ZH / asset_name
    shutil.copyfile(source, target_en)
    shutil.copyfile(source, target_zh)
    return {"en": target_en, "zh": target_zh}
