from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_repair_diagnostics import (
    build_regime_repair_diagnostics,
    write_regime_repair_diagnostics_artifacts,
)

runner = CliRunner()


def test_build_regime_repair_diagnostics_flags_dead_and_underpowered_families():
    assignments = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "candidate_regime_family": "candidate_maritime_cloudy",
                "candidate_regime_label": "candidate_maritime_cloudy",
                "assignment_confidence": 0.8,
                "distance_to_candidate": 1.5,
            },
            {
                "date_local": dt.date(2025, 2, 1),
                "cp": "21:00",
                "candidate_regime_family": None,
                "candidate_regime_label": "candidate_maritime_cloudy",
                "assignment_confidence": 0.6,
                "distance_to_candidate": 2.5,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "22:00",
                "candidate_regime_family": "candidate_mixed_or_transition",
                "candidate_regime_label": "candidate_mixed_or_transition",
                "assignment_confidence": 0.4,
                "distance_to_candidate": 3.0,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "19:00",
                "candidate_regime_family": "candidate_mixed_or_transition",
                "candidate_regime_label": "candidate_mixed_or_transition",
                "assignment_confidence": 0.9,
                "distance_to_candidate": 1.0,
            },
        ]
    )
    r2_validation = pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "cp": "20:00",
                "passes": "false",
            },
            {
                "regime": "candidate_mixed_or_transition",
                "cp": "22:00",
                "passes": "TRUE",
            },
            {
                "regime": "candidate_mixed_or_transition",
                "cp": "19:00",
                "passes": True,
            },
        ]
    )

    artifacts = build_regime_repair_diagnostics(
        pl.DataFrame(),
        assignments,
        r2_validation,
        min_support_rows=2,
    )

    diagnostics = artifacts["regime_repair_diagnostics"]
    assert diagnostics.columns == [
        "candidate_regime_family",
        "assignment_rows",
        "cp_count",
        "month_count",
        "mean_assignment_confidence",
        "min_assignment_confidence",
        "mean_distance_to_candidate",
        "r2_rows",
        "r2_pass_rows",
        "r2_dead_status",
        "power_status",
        "recommended_repair",
        "production_status",
    ]
    rows = {row["candidate_regime_family"]: row for row in diagnostics.iter_rows(named=True)}
    assert rows["candidate_maritime_cloudy"]["assignment_rows"] == 2
    assert rows["candidate_maritime_cloudy"]["cp_count"] == 2
    assert rows["candidate_maritime_cloudy"]["month_count"] == 2
    assert rows["candidate_maritime_cloudy"]["r2_rows"] == 1
    assert rows["candidate_maritime_cloudy"]["r2_pass_rows"] == 0
    assert rows["candidate_maritime_cloudy"]["r2_dead_status"] == "DEAD"
    assert rows["candidate_maritime_cloudy"]["power_status"] == "OK"
    assert rows["candidate_maritime_cloudy"]["production_status"] == "NOT_PRODUCTION"
    assert rows["candidate_mixed_or_transition"]["assignment_rows"] == 1
    assert rows["candidate_mixed_or_transition"]["r2_rows"] == 1
    assert rows["candidate_mixed_or_transition"]["r2_pass_rows"] == 1
    assert rows["candidate_mixed_or_transition"]["r2_dead_status"] == "PASS"
    assert rows["candidate_mixed_or_transition"]["power_status"] == "UNDERPOWERED"


def test_write_regime_repair_diagnostics_artifacts_uses_regime_design_filenames(tmp_path: Path):
    diagnostics = pl.DataFrame(
        [
            {
                "candidate_regime_family": "candidate_maritime_cloudy",
                "assignment_rows": 2,
                "cp_count": 2,
                "month_count": 2,
                "mean_assignment_confidence": 0.7,
                "min_assignment_confidence": 0.6,
                "mean_distance_to_candidate": 2.0,
                "r2_rows": 1,
                "r2_pass_rows": 0,
                "r2_dead_status": "DEAD",
                "power_status": "OK",
                "recommended_repair": "repair candidate family before production promotion",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_regime_family": "candidate_mixed_or_transition",
                "assignment_rows": 1,
                "cp_count": 1,
                "month_count": 1,
                "mean_assignment_confidence": 0.4,
                "min_assignment_confidence": 0.4,
                "mean_distance_to_candidate": 3.0,
                "r2_rows": 1,
                "r2_pass_rows": 1,
                "r2_dead_status": "PASS",
                "power_status": "UNDERPOWERED",
                "recommended_repair": "collect more support before production promotion",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )

    paths = write_regime_repair_diagnostics_artifacts(
        {"regime_repair_diagnostics": diagnostics},
        tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert paths["regime_repair_diagnostics_csv"] == tmp_path / "regime_repair_diagnostics_v1.csv"
    assert paths["regime_repair_diagnostics_md"] == tmp_path / "regime_repair_diagnostics_v1.md"
    assert paths["regime_repair_diagnostics_csv"].exists()
    report = paths["regime_repair_diagnostics_md"].read_text(encoding="utf-8")
    assert "# Regime Repair Diagnostics v1 - 2026-06-07" in report
    assert "NOT_PRODUCTION" in report
    assert "candidate_maritime_cloudy" in report
    assert "candidate_mixed_or_transition" in report


def test_regime_repair_diagnostics_cli_writes_artifacts(tmp_path: Path):
    candidate_path = tmp_path / "regime_design_candidate_v1.csv"
    assignments_path = tmp_path / "regime_candidate_assignments_v1.csv"
    r2_path = tmp_path / "regime_candidate_r2_validation.csv"
    output_dir = tmp_path / "regime-design"
    pl.DataFrame(
        [{"candidate_id": "RDC-V1-MONTH-1-C04", "production_status": "NOT_PRODUCTION"}]
    ).write_csv(candidate_path)
    pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "candidate_regime_family": "candidate_maritime_cloudy",
                "candidate_regime_label": "candidate_maritime_cloudy",
                "assignment_confidence": 0.8,
                "distance_to_candidate": 1.5,
                "production_status": "NOT_PRODUCTION",
            }
        ]
    ).write_csv(assignments_path)
    pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "cp": "20:00",
                "passes": False,
            }
        ]
    ).write_csv(r2_path)

    result = runner.invoke(
        app,
        [
            "regime-repair-diagnostics",
            "--candidate-path",
            str(candidate_path),
            "--assignments-path",
            str(assignments_path),
            "--r2-path",
            str(r2_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--min-support-rows",
            "30",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_repair_diagnostics_v1.csv").exists()
    assert (output_dir / "regime_repair_diagnostics_v1.md").exists()
