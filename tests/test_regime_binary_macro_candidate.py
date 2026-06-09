"""Tests for the experiment-only binary macro regime candidate."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_binary_macro_candidate import (
    build_regime_binary_macro_candidate_artifacts,
    write_regime_binary_macro_candidate_artifacts,
)

runner = CliRunner()


def _assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "20:00",
                "macro_regime_label": "macro_calm_radiative",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_binary_macro_candidate_collapses_non_southerly_without_production_mutation():
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    candidate = artifacts["regime_binary_macro_candidate_v1"]
    assignments = artifacts["regime_binary_macro_assignments_v1"]
    audit = artifacts["regime_binary_macro_assignment_audit_v1"]

    assert set(candidate["macro_regime_label"].to_list()) == {
        "macro_southerly_flow",
        "macro_non_southerly",
    }
    assert set(assignments["binary_macro_regime_label"].to_list()) == {
        "macro_southerly_flow",
        "macro_non_southerly",
    }
    calm = assignments.filter(pl.col("source_macro_regime_label") == "macro_calm_radiative").row(
        0, named=True
    )
    assert calm["binary_macro_regime_label"] == "macro_non_southerly"
    assert set(assignments["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert (
        audit.filter(pl.col("audit_item") == "source_production_status").row(0, named=True)["status"]
        == "PASS"
    )


def test_southerly_assignments_stay_southerly():
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    assignments = artifacts["regime_binary_macro_assignments_v1"]
    southerly = assignments.filter(pl.col("source_macro_regime_label") == "macro_southerly_flow").row(
        0, named=True
    )
    assert southerly["binary_macro_regime_label"] == "macro_southerly_flow"


def test_nw_continuum_collapses_to_non_southerly():
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    assignments = artifacts["regime_binary_macro_assignments_v1"]
    nw = assignments.filter(pl.col("source_macro_regime_label") == "macro_nw_continuum").row(0, named=True)
    assert nw["binary_macro_regime_label"] == "macro_non_southerly"


def test_rejects_production_assignments():
    bad = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "production_status": "PRODUCTION",
            }
        ],
        strict=False,
    )
    with pytest.raises(ValueError, match="NOT_PRODUCTION"):
        build_regime_binary_macro_candidate_artifacts(bad)


def test_candidate_version_is_binary_v1():
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    candidate = artifacts["regime_binary_macro_candidate_v1"]
    assert all(v == "binary_v1" for v in candidate["candidate_version"].to_list())


def test_binary_macro_writer_and_cli(tmp_path: Path):
    artifacts = build_regime_binary_macro_candidate_artifacts(_assignments())
    paths = write_regime_binary_macro_candidate_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )
    assert (tmp_path / "regime_binary_macro_candidate_v1.csv").exists()
    assert (tmp_path / "regime_binary_macro_candidate_v1.md").exists()
    assert (tmp_path / "regime_binary_macro_assignments_v1.csv").exists()
    assert "experiment-only" in paths["regime_binary_macro_candidate_md"].read_text(encoding="utf-8")

    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "cli"
    _assignments().write_csv(assignments_path)
    result = runner.invoke(
        app,
        [
            "regime-binary-macro-candidate",
            "--assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_binary_macro_assignments_v1.csv").exists()
    assert "macro_non_southerly" in result.output
