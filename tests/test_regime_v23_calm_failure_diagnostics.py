from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_v23_calm_failure_diagnostics import (
    build_regime_v23_calm_failure_diagnostics,
    write_regime_v23_calm_failure_diagnostics_artifacts,
)

runner = CliRunner()


def _assignments() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    macros = [
        "macro_calm_radiative",
        "macro_calm_radiative",
        "macro_nw_continuum",
        "macro_nw_continuum",
        "macro_southerly_flow",
        "macro_southerly_flow",
    ]
    cps = ["20:00", "21:00", "20:00", "21:00", "20:00", "21:00"]
    for idx, (macro, cp) in enumerate(zip(macros, cps, strict=True)):
        rows.append(
            {
                "candidate_version": "v2.2",
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "cp": cp,
                "macro_regime_label": macro,
                "candidate_regime_label": macro,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "calm_radiative_rule_score": 4 if macro == "macro_calm_radiative" else 0,
                "production_status": "NOT_PRODUCTION",
            }
        )
    return pl.DataFrame(rows)


def _r2_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "regime": "macro_calm_radiative",
                "hypothesis_id": "H-CALM-001",
                "feature_column": "cloud_base_transparency",
                "cp": "20:00",
                "passes": False,
                "n_days": 2,
                "status": "tested",
            },
            {
                "regime": "macro_calm_radiative",
                "hypothesis_id": "H-CALM-002",
                "feature_column": "nocturnal_plateau_flag",
                "cp": "21:00",
                "passes": False,
                "n_days": 2,
                "status": "tested",
            },
            {
                "regime": "macro_nw_continuum",
                "hypothesis_id": "H-NW-001",
                "feature_column": "foehn_score",
                "cp": "20:00",
                "passes": True,
                "n_days": 2,
                "status": "tested",
            },
            {
                "regime": "macro_southerly_flow",
                "hypothesis_id": "H-S-001",
                "feature_column": "precip_disruption",
                "cp": "20:00",
                "passes": True,
                "n_days": 2,
                "status": "tested",
            },
        ]
    )


def _features() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, cp in enumerate(["20:00", "21:00", "20:00", "21:00", "20:00", "21:00"]):
        rows.append(
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "cp": cp,
                "cloud_base_transparency": 0.2 + idx,
                "nocturnal_plateau_flag": idx % 2,
                "foehn_score": 50.0 + idx,
                "precip_disruption": idx % 3,
            }
        )
    return pl.DataFrame(rows)


def _labels() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(6):
        rows.append(
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "day_complete": True,
                "tmax_int": 20 + idx,
                "k_cp__cp_2000": 18 + idx,
                "k_cp__cp_2100": 19 + idx,
            }
        )
    return pl.DataFrame(rows)


def test_v23_diagnoses_calm_radiative_as_validation_target_gap():
    artifacts = build_regime_v23_calm_failure_diagnostics(
        assignments=_assignments(),
        r2_validation=_r2_validation(),
        features=_features(),
        labels=_labels(),
        min_assignment_rows=2,
        min_cp_rows=1,
    )

    diagnostics = artifacts["regime_calm_radiative_failure_diagnostics_v1"]
    next_experiments = artifacts["regime_v23_next_experiments"]

    calm = diagnostics.filter(
        pl.col("macro_regime_label") == "macro_calm_radiative"
    ).row(0, named=True)
    assert calm["assignment_rows"] == 2
    assert calm["r2_pass_rows"] == 0
    assert calm["r2_dead_status"] == "DEAD"
    assert calm["sample_support_status"] == "PASS"
    assert calm["feature_coverage_status"] == "PASS"
    assert calm["diagnosis"] == "CALM_RADIATIVE_VALIDATION_TARGET_GAP"
    assert "do not promote" in calm["recommended_next_action"].lower()
    assert calm["production_status"] == "EXPERIMENT_ONLY"

    assert next_experiments.height >= 2
    assert set(next_experiments["production_status"]) == {"EXPERIMENT_ONLY"}
    assert "CEXP-CALM-RADIATIVE-001" in set(next_experiments["experiment_id"])


def test_write_v23_calm_failure_diagnostics_artifacts(tmp_path: Path):
    artifacts = build_regime_v23_calm_failure_diagnostics(
        assignments=_assignments(),
        r2_validation=_r2_validation(),
        features=_features(),
        labels=_labels(),
        min_assignment_rows=2,
        min_cp_rows=1,
    )

    paths = write_regime_v23_calm_failure_diagnostics_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (
        tmp_path / "regime_calm_radiative_failure_diagnostics_v1.csv"
    ).exists()
    assert (tmp_path / "regime_v23_next_experiments.csv").exists()
    assert (
        tmp_path / "regime_calm_radiative_failure_diagnostics_v1.md"
    ).exists()
    report = paths["regime_calm_radiative_failure_diagnostics_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime v2.3 Calm/Radiative Failure Diagnostics - 2026-06-08" in report
    assert "not a production classifier" in report
    assert "CALM_RADIATIVE_VALIDATION_TARGET_GAP" in report


def test_regime_design_v23_calm_diagnostics_cli_writes_artifacts(tmp_path: Path):
    assignments_path = tmp_path / "regime_candidate_assignments_v2_2.csv"
    r2_path = tmp_path / "regime_candidate_r2_validation_v2_2.csv"
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    output_dir = tmp_path / "regime-design"

    _assignments().write_csv(assignments_path)
    _r2_validation().write_csv(r2_path)
    _features().write_parquet(features_path)
    _labels().write_parquet(labels_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v23-calm-diagnostics",
            "--assignments-v22-path",
            str(assignments_path),
            "--r2-v22-path",
            str(r2_path),
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
            "--min-assignment-rows",
            "2",
            "--min-cp-rows",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        output_dir / "regime_calm_radiative_failure_diagnostics_v1.csv"
    ).exists()
    assert (output_dir / "regime_v23_next_experiments.csv").exists()
    assert "CALM_RADIATIVE_VALIDATION_TARGET_GAP" in result.output
