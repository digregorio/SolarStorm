from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _write_nested_cli_inputs(
    *,
    features_path: Path,
    labels_path: Path,
    assignments_path: Path,
) -> None:
    features = []
    labels = []
    assignments = []
    for year in range(2020, 2025):
        for month in (1, 7):
            for day in range(1, 6):
                date = dt.date(year, month, day)
                labels.append({"date_local": date, "tmax_int": 15.0 + day / 2})
                for cp_index, cp in enumerate(("20:00", "21:00", "22:00", "23:00")):
                    macro = (
                        "macro_non_southerly"
                        if (day + cp_index) % 2 == 0
                        else "macro_southerly_flow"
                    )
                    features.append(
                        {
                            "date_local": date,
                            "cp": cp,
                            "k_cp": float(12 + day / 3 + cp_index / 5),
                            "foehn_score": float(day * 3 + cp_index),
                            "cloud_cover_suppression": float(7 - day),
                            "regime_label": "warm_nw"
                            if macro == "macro_non_southerly"
                            else "cool_s",
                            "regime_score_argmax": macro,
                            "day_sequence_pattern": "warming"
                            if day <= 2
                            else "cooling",
                        }
                    )
                    assignments.append(
                        {
                            "date_local": date,
                            "cp": cp,
                            "binary_macro_regime_label": macro,
                        }
                    )

    pl.DataFrame(features).write_parquet(features_path)
    pl.DataFrame(labels).unique("date_local").write_parquet(labels_path)
    pl.DataFrame(assignments).write_csv(assignments_path)


def test_onda3_nested_validation_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-nested-validation"
    _write_nested_cli_inputs(
        features_path=features_path,
        labels_path=labels_path,
        assignments_path=assignments_path,
    )

    result = runner.invoke(
        app,
        [
            "onda3-nested-validation",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
            "--train-start",
            "2020-01-01",
        ],
    )

    assert result.exit_code == 0
    expected_stems = {
        "onda3_nested_fold_scope_v1",
        "onda3_nested_model_results_v1",
        "onda3_nested_predictions_v1",
        "onda3_nested_metric_summary_v1",
        "onda3_nested_selection_v1",
        "onda3_nested_test_selected_summary_v1",
        "onda3_nested_by_month_v1",
        "onda3_nested_by_month_cp_v1",
        "onda3_nested_regime_performance_v1",
        "onda3_nested_decision_update_v1",
    }
    for stem in expected_stems:
        assert (output_dir / f"{stem}.csv").exists()
        assert (output_dir / f"{stem}.md").exists()

    report = (output_dir / "onda3_nested_validation_report_v1.md").read_text(
        encoding="utf-8"
    )
    decision = pl.read_csv(output_dir / "onda3_nested_decision_update_v1.csv")
    selection = pl.read_csv(output_dir / "onda3_nested_selection_v1.csv")

    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert selection["outer_test_year"].to_list() == [2024]
    assert "Open-Meteo forecast data is not integrated." in report
    assert "Open-Meteo forecast data is not integrated" in result.stdout


def test_onda3_nested_validation_cli_blocks_missing_assignments(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "missing_assignments.csv"
    output_dir = tmp_path / "onda3-nested-validation"
    populated_assignments_path = tmp_path / "assignments.csv"
    _write_nested_cli_inputs(
        features_path=features_path,
        labels_path=labels_path,
        assignments_path=populated_assignments_path,
    )

    result = runner.invoke(
        app,
        [
            "onda3-nested-validation",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
            "--train-start",
            "2020-01-01",
        ],
    )

    assert result.exit_code == 2
    assert "missing binary assignments path" in result.stdout
