from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_onda3_train_start_sensitivity_cli_writes_report(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-train-start-sensitivity"
    interactions_dir = tmp_path / "onda3-interactions"
    interactions_dir.mkdir()
    sentinel = interactions_dir / "onda3_interaction_predictions_v1.csv"
    sentinel.write_text("existing interaction artifact\n", encoding="utf-8")

    features = []
    labels = []
    assignments = []
    for cp in ("20:00", "21:00"):
        for year in (2010, 2011, 2012, 2013, 2022, 2023):
            for day in range(1, 5):
                date = dt.date(year, 1, day)
                macro = "macro_non_southerly" if day % 2 else "macro_southerly_flow"
                features.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "k_cp": float(day + year - 2000),
                        "foehn_score": float(day * 10),
                        "cloud_cover_suppression": float(5 - day),
                    }
                )
                labels.append({"date_local": date, "tmax_int": float(day + year - 1999)})
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

    result = runner.invoke(
        app,
        [
            "onda3-train-start-sensitivity",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--binary-assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2023",
        ],
    )

    assert result.exit_code == 0
    expected_stems = {
        "onda3_train_start_scope_v1",
        "onda3_train_start_model_results_v1",
        "onda3_train_start_predictions_v1",
        "onda3_train_start_bracket_overall_v1",
        "onda3_train_start_bracket_by_month_day_v1",
        "onda3_train_start_bracket_by_month_cp_v1",
        "onda3_train_start_regime_performance_v1",
        "onda3_train_start_regime_by_cp_v1",
        "onda3_train_start_comparison_v1",
        "onda3_train_start_decision_update_v1",
    }
    for stem in expected_stems:
        assert (output_dir / f"{stem}.csv").exists()
        assert (output_dir / f"{stem}.md").exists()

    report = (output_dir / "onda3_train_start_sensitivity_report_v1.md").read_text(
        encoding="utf-8"
    )
    comparison = pl.read_csv(output_dir / "onda3_train_start_comparison_v1.csv")
    decision = pl.read_csv(output_dir / "onda3_train_start_decision_update_v1.csv")

    assert set(comparison["variant_id"].to_list()) == {
        "legacy_2009_start",
        "continuous_2012_start",
    }
    assert set(decision["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert "Open-Meteo forecast data is not integrated." in report
    assert sentinel.read_text(encoding="utf-8") == "existing interaction artifact\n"
    assert "Onda 3E train-start sensitivity complete" in result.stdout
