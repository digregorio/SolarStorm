"""Tests for the regime deadlock pivot decision and audit-demotion artifacts."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_deadlock_pivot import (
    build_regime_deadlock_pivot_artifacts,
    write_regime_deadlock_pivot_artifacts,
)

runner = CliRunner()


def _r2_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"regime": "macro_calm_radiative", "passes": False, "n_days": 27, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "n_days": 210, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "n_days": 110, "cp": "20:00"},
        ],
        strict=False,
    )


def _cloud_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "experiment_id": "CEXP-CALM-RADIATIVE-002B",
                "feature_column": "cloud_cover_suppression",
                "validation_decision": "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN",
                "controlled_slope": -1.75,
                "controlled_slope_retention": 0.605,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )


def test_deadlock_pivot_marks_old_path_superseded_and_calm_audit_only():
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=_cloud_validation(),
        source_report_path="reports/onda2e/regime_deadlock_diagnosis_v1.md",
    )

    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    demotions = artifacts["regime_audit_demotions_v1"]
    superseded = artifacts["regime_deadlock_superseded_path_v1"]

    assert decision["decision_status"] == "PIVOT_ACCEPTED"
    assert decision["active_path"] == "OPTION_C_AUDIT_DEMOTION_PLUS_OPTION_A_BINARY_EXPERIMENT"
    assert decision["production_status"] == "EXPERIMENT_ONLY"
    assert "v2.4" in decision["blocked_next_actions"]
    assert set(demotions["macro_regime_label"].to_list()) == {
        "macro_calm_radiative",
        "macro_nw_continuum",
        "macro_southerly_flow",
    }
    calm = demotions.filter(pl.col("macro_regime_label") == "macro_calm_radiative").row(0, named=True)
    assert calm["gate_role"] == "AUDIT_ONLY"
    assert calm["blocks_production_gate"] is False
    assert calm["known_signal"] == "cloud_cover_suppression"
    assert superseded.filter(pl.col("superseded_status") == "SUPERSEDED_ACTIVE_UNLOCK_PATH").height >= 1


def test_production_macros_still_block():
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=_cloud_validation(),
    )
    demotions = artifacts["regime_audit_demotions_v1"]
    for regime in ("macro_nw_continuum", "macro_southerly_flow"):
        row = demotions.filter(pl.col("macro_regime_label") == regime).row(0, named=True)
        assert row["gate_role"] == "PRODUCTION_BLOCKING"
        assert row["blocks_production_gate"] is True


def test_empty_cloud_validation_does_not_crash():
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=pl.DataFrame(),
    )
    calm = (
        artifacts["regime_audit_demotions_v1"]
        .filter(pl.col("macro_regime_label") == "macro_calm_radiative")
        .row(0, named=True)
    )
    assert calm["known_signal"] == ""


def test_superseded_path_blocks_v24():
    artifacts = build_regime_deadlock_pivot_artifacts(r2_validation=_r2_validation())
    superseded = artifacts["regime_deadlock_superseded_path_v1"]
    v24 = superseded.filter(pl.col("path_item") == "v2.4_threshold_tuning").row(0, named=True)
    assert v24["superseded_status"] == "BLOCKED_BY_DECISION"


def test_deadlock_pivot_writer_and_cli(tmp_path: Path):
    artifacts = build_regime_deadlock_pivot_artifacts(
        r2_validation=_r2_validation(),
        cloud_validation=_cloud_validation(),
        source_report_path="reports/onda2e/regime_deadlock_diagnosis_v1.md",
    )
    paths = write_regime_deadlock_pivot_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_deadlock_pivot_decision_v1.csv").exists()
    assert (tmp_path / "regime_deadlock_pivot_decision_v1.md").exists()
    assert (tmp_path / "regime_deadlock_superseded_path_v1.csv").exists()
    assert (tmp_path / "regime_audit_demotions_v1.csv").exists()
    assert (tmp_path / "regime_audit_demotions_v1.md").exists()
    md_text = paths["regime_deadlock_pivot_decision_md"].read_text(encoding="utf-8")
    assert "not a production classifier" in md_text

    r2_path = tmp_path / "r2.csv"
    cloud_path = tmp_path / "cloud.csv"
    output_dir = tmp_path / "cli"
    _r2_validation().write_csv(r2_path)
    _cloud_validation().write_csv(cloud_path)

    result = runner.invoke(
        app,
        [
            "regime-deadlock-pivot",
            "--r2-validation-path",
            str(r2_path),
            "--cloud-validation-path",
            str(cloud_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_deadlock_pivot_decision_v1.csv").exists()
    assert "PIVOT_ACCEPTED" in result.output
