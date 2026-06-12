from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _prediction_rows(
    *,
    iteration_id: str,
    iteration_label: str,
    offset: float,
) -> list[dict[str, object]]:
    rows = []
    for day in range(1, 5):
        date = dt.date(2024, 1, day)
        macro = "macro_non_southerly" if day % 2 else "macro_southerly_flow"
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            actual = 16 + day % 2
            rows.append(
                {
                    "iteration_id": iteration_id,
                    "iteration_label": iteration_label,
                    "date_local": date,
                    "calendar_year": date.year,
                    "test_year": 2024,
                    "month": date.strftime("%Y-%m"),
                    "cp": cp,
                    "actual": actual,
                    "prediction": actual + offset,
                    "absolute_error": offset,
                    "actual_bracket": actual,
                    "pred_bracket": actual,
                    "exact_bracket": True,
                    "binary_macro_regime_label": macro,
                    "model_name": "ridge_challenger",
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return rows


def _write_cli_inputs(reports_dir: Path, features_path: Path) -> None:
    (reports_dir / "onda3-interactions").mkdir(parents=True)
    (reports_dir / "onda3-train-start-sensitivity").mkdir(parents=True)
    (reports_dir / "onda3-pooled").mkdir(parents=True)
    (reports_dir / "regime-design").mkdir(parents=True)

    d_rows = []
    assignments = []
    features = []
    for day in range(1, 5):
        date = dt.date(2024, 1, day)
        macro = "macro_non_southerly" if day % 2 else "macro_southerly_flow"
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            actual = 16 + day % 2
            d_rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "actual": actual,
                    "prediction": actual + 0.45,
                    "absolute_error": 0.45,
                    "model_name": "ridge_challenger",
                    "production_status": "EXPERIMENT_ONLY",
                    "test_year": 2024,
                }
            )
            assignments.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "binary_macro_regime_label": macro,
                }
            )
            features.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "regime_label": "calm_radiative" if day == 1 else "other",
                    "foehn_score": float(day * 12),
                    "cloud_cover_suppression": float(80 - day),
                }
            )

    e_rows = [
        {
            **row,
            "variant_id": "legacy_2009_start",
            "train_start": "2009-04-23",
        }
        for row in _prediction_rows(
            iteration_id="legacy_2009_start",
            iteration_label="Onda 3E legacy 2009-start",
            offset=0.44,
        )
    ] + [
        {
            **row,
            "variant_id": "continuous_2012_start",
            "train_start": "2012-01-01",
        }
        for row in _prediction_rows(
            iteration_id="continuous_2012_start",
            iteration_label="Onda 3E continuous 2012-start",
            offset=0.43,
        )
    ]
    f_rows = _prediction_rows(
        iteration_id="onda3_f_pooled_temporal_regime",
        iteration_label="Onda 3F pooled temporal/regime",
        offset=0.25,
    )

    pl.DataFrame(d_rows).write_csv(
        reports_dir / "onda3-interactions" / "onda3_interaction_predictions_v1.csv"
    )
    pl.DataFrame(e_rows).write_csv(
        reports_dir
        / "onda3-train-start-sensitivity"
        / "onda3_train_start_predictions_v1.csv"
    )
    pl.DataFrame(f_rows).write_csv(
        reports_dir / "onda3-pooled" / "onda3_pooled_predictions_v1.csv"
    )
    pl.DataFrame(assignments).write_csv(
        reports_dir / "regime-design" / "regime_binary_macro_assignments_v1.csv"
    )
    pl.DataFrame(features).write_parquet(features_path)


def test_onda3_audit_comparison_cli_writes_artifacts(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    features_path = tmp_path / "features.parquet"
    output_dir = tmp_path / "onda3-audit-comparison"
    _write_cli_inputs(reports_dir, features_path)

    result = runner.invoke(
        app,
        [
            "onda3-audit-comparison",
            "--reports-dir",
            str(reports_dir),
            "--features-path",
            str(features_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    expected_stems = {
        "onda3_audit_model_summary_v1",
        "onda3_audit_pairwise_delta_v1",
        "onda3_audit_by_year_v1",
        "onda3_audit_by_month_v1",
        "onda3_audit_by_month_cp_v1",
        "onda3_audit_regime_performance_v1",
        "onda3_audit_regime_winner_v1",
        "onda3_audit_feature_slice_v1",
        "onda3_audit_decision_update_v1",
    }
    for stem in expected_stems:
        assert (output_dir / f"{stem}.csv").exists()
        assert (output_dir / f"{stem}.md").exists()

    summary = pl.read_csv(output_dir / "onda3_audit_model_summary_v1.csv")
    decision = pl.read_csv(output_dir / "onda3_audit_decision_update_v1.csv")
    report = (output_dir / "onda3_audit_comparison_report_v1.md").read_text(
        encoding="utf-8"
    )

    assert set(summary["iteration_id"].to_list()) == {
        "onda3_d_binary_macro_interactions",
        "onda3_e_legacy_2009_start",
        "onda3_e_continuous_2012_start",
        "onda3_f_pooled_temporal_regime",
    }
    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert "Open-Meteo forecast data is not integrated." in report
    assert "Open-Meteo forecast data is not integrated" in result.stdout


def test_onda3_audit_comparison_cli_blocks_incomplete_canonical_inputs(
    tmp_path: Path,
):
    reports_dir = tmp_path / "reports"
    features_path = tmp_path / "features.parquet"
    output_dir = tmp_path / "onda3-audit-comparison"
    _write_cli_inputs(reports_dir, features_path)
    (
        reports_dir
        / "onda3-train-start-sensitivity"
        / "onda3_train_start_predictions_v1.csv"
    ).unlink()

    result = runner.invoke(
        app,
        [
            "onda3-audit-comparison",
            "--reports-dir",
            str(reports_dir),
            "--features-path",
            str(features_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 2
    assert "missing canonical Onda 3 audit models" in result.stdout
