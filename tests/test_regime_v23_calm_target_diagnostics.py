from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_v23_calm_target_diagnostics import (
    build_regime_calm_radiative_target_diagnostics,
    write_regime_calm_radiative_target_diagnostics_artifacts,
)

runner = CliRunner()


def _assignments() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    specs = [
        (dt.date(2025, 1, 1), "20:00", "macro_calm_radiative"),
        (dt.date(2025, 1, 2), "20:00", "macro_calm_radiative"),
        (dt.date(2025, 1, 3), "20:00", "macro_nw_continuum"),
        (dt.date(2025, 1, 4), "20:00", "macro_nw_continuum"),
        (dt.date(2025, 2, 1), "21:00", "macro_calm_radiative"),
        (dt.date(2026, 1, 1), "20:00", "macro_calm_radiative"),
    ]
    for idx, (day, cp, macro) in enumerate(specs):
        rows.append(
            {
                "candidate_version": "v2.2",
                "date_local": day,
                "cp": cp,
                "macro_regime_label": macro,
                "candidate_regime_label": macro,
                "production_status": "NOT_PRODUCTION",
                "assignment_confidence": 0.8,
                "reassigned_to_calm_radiative": macro == "macro_calm_radiative",
                "source_candidate_id": f"RDC-{idx:02d}",
            }
        )
    return pl.DataFrame(rows)


def _labels() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "day_complete": True,
                "tmax_int": 20,
                "tmax_hour": 11,
                "k_cp__cp_2000": 16,
                "k_cp__cp_2100": 17,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "day_complete": True,
                "tmax_int": 22,
                "tmax_hour": 14,
                "k_cp__cp_2000": 18,
                "k_cp__cp_2100": 19,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "day_complete": True,
                "tmax_int": 25,
                "tmax_hour": 17,
                "k_cp__cp_2000": 20,
                "k_cp__cp_2100": 21,
            },
            {
                "date_local": dt.date(2025, 1, 4),
                "day_complete": True,
                "tmax_int": 27,
                "tmax_hour": 19,
                "k_cp__cp_2000": 22,
                "k_cp__cp_2100": 23,
            },
            {
                "date_local": dt.date(2025, 2, 1),
                "day_complete": True,
                "tmax_int": 18,
                "tmax_hour": 10,
                "k_cp__cp_2000": 14,
                "k_cp__cp_2100": 15,
            },
            {
                "date_local": dt.date(2026, 1, 1),
                "day_complete": True,
                "tmax_int": 30,
                "tmax_hour": 18,
                "k_cp__cp_2000": 10,
                "k_cp__cp_2100": 11,
            },
        ]
    )


def test_calm_target_diagnostics_are_train_only_by_macro_month_cp():
    artifacts = build_regime_calm_radiative_target_diagnostics(
        assignments=_assignments(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        min_cell_rows=2,
    )

    diagnostics = artifacts["regime_calm_radiative_target_diagnostics_v1"]
    calm_jan = diagnostics.filter(
        (pl.col("macro_regime_label") == "macro_calm_radiative")
        & (pl.col("month") == 1)
        & (pl.col("cp") == "20:00")
    ).row(0, named=True)

    assert calm_jan["experiment_id"] == "CEXP-CALM-RADIATIVE-001"
    assert calm_jan["n_assignment_rows"] == 2
    assert calm_jan["n_unique_days"] == 2
    assert calm_jan["remaining_warming_p50"] == 4.0
    assert calm_jan["remaining_warming_p90"] == 4.0
    assert calm_jan["tmax_hour_p50"] == 14.0
    assert calm_jan["tmax_hour_before_13_share"] == 0.5
    assert calm_jan["underpowered_n_lt_min_cell"] is False
    assert calm_jan["causal_role"] == "FULL_DAY_TARGET_AUDIT_ONLY"
    assert calm_jan["production_status"] == "EXPERIMENT_ONLY"

    assert diagnostics.filter(pl.col("date_window_end") == "2026-01-01").height == 0


def test_calm_target_diagnostics_writer_outputs_csv_and_markdown(tmp_path: Path):
    artifacts = build_regime_calm_radiative_target_diagnostics(
        assignments=_assignments(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        min_cell_rows=2,
    )

    paths = write_regime_calm_radiative_target_diagnostics_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (
        tmp_path / "regime_calm_radiative_target_diagnostics_v1.csv"
    ).exists()
    assert (
        tmp_path / "regime_calm_radiative_target_diagnostics_v1.md"
    ).exists()
    report = paths["regime_calm_radiative_target_diagnostics_md"].read_text(
        encoding="utf-8"
    )
    assert "CEXP-CALM-RADIATIVE-001 Target Diagnostics - 2026-06-08" in report
    assert "FULL_DAY_TARGET_AUDIT_ONLY" in report
    assert "not a production classifier" in report


def test_calm_target_diagnostics_cli_writes_artifacts(tmp_path: Path):
    assignments_path = tmp_path / "regime_candidate_assignments_v2_2.csv"
    labels_path = tmp_path / "labels.parquet"
    output_dir = tmp_path / "regime-design"
    _assignments().write_csv(assignments_path)
    _labels().write_parquet(labels_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v23-calm-target-diagnostics",
            "--assignments-v22-path",
            str(assignments_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2025-12-31",
            "--min-cell-rows",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        output_dir / "regime_calm_radiative_target_diagnostics_v1.csv"
    ).exists()
    assert "CEXP-CALM-RADIATIVE-001" in result.output
