from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def test_onda3_pooled_cli_writes_full_artifact_surface(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-pooled"

    features = []
    labels = []
    assignments = []
    for cp in ("20:00", "21:00", "22:00", "23:00"):
        for year in (2022, 2023, 2024):
            for month in (1, 6, 11):
                for day in range(1, 4):
                    date = dt.date(year, month, day)
                    macro = (
                        "macro_non_southerly"
                        if day % 2
                        else "macro_southerly_flow"
                    )
                    k_cp = float(12 + day + month / 10)
                    features.append(
                        {
                            "date_local": date,
                            "cp": cp,
                            "k_cp": k_cp,
                            "foehn_score": float(day * 7),
                            "cloud_cover_suppression": float(4 - day),
                            "regime_label": "warm_nw" if day % 2 else "cool_s",
                            "regime_score_argmax": macro,
                            "day_sequence_pattern": (
                                "warming" if day % 2 else "cooling"
                            ),
                        }
                    )
                    labels.append(
                        {
                            "date_local": date,
                            "tmax_int": k_cp
                            + (0.7 if macro == "macro_non_southerly" else -0.3),
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

    result = runner.invoke(
        app,
        [
            "onda3-pooled-model-iteration",
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
        ],
    )

    assert result.exit_code == 0
    expected_stems = {
        "onda3_pooled_feature_audit_v1",
        "onda3_pooled_model_results_v1",
        "onda3_pooled_predictions_v1",
        "onda3_pooled_bracket_overall_v1",
        "onda3_pooled_bracket_by_month_day_v1",
        "onda3_pooled_bracket_by_month_cp_v1",
        "onda3_pooled_regime_performance_v1",
        "onda3_pooled_regime_by_cp_v1",
        "onda3_pooled_slice_diagnostics_v1",
        "onda3_pooled_uncertainty_abstention_v1",
        "onda3_pooled_temporal_diagnostics_v1",
        "onda3_pooled_decision_update_v1",
    }
    for stem in expected_stems:
        assert (output_dir / f"{stem}.csv").exists()
        assert (output_dir / f"{stem}.md").exists()

    report = (output_dir / "onda3_pooled_model_report_v1.md").read_text(
        encoding="utf-8"
    )
    results = pl.read_csv(output_dir / "onda3_pooled_model_results_v1.csv")
    predictions = pl.read_csv(output_dir / "onda3_pooled_predictions_v1.csv")

    assert set(results["cp"].to_list()) == {"ALL"}
    assert set(predictions["cp"].unique().to_list()) == {
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    }
    assert "Open-Meteo forecast data is not integrated." in report
    assert "Open-Meteo forecast data is not integrated" in result.stdout


def test_onda3_pooled_cli_joins_assignments_when_feature_cp_is_time(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "assignments.csv"
    output_dir = tmp_path / "onda3-pooled"

    cp_pairs = (
        (dt.time(20, 0), "20:00"),
        (dt.time(21, 0), "21:00"),
        (dt.time(22, 0), "22:00"),
        (dt.time(23, 0), "23:00"),
    )
    features = []
    labels = []
    assignments = []
    for cp_time, cp_text in cp_pairs:
        for year in (2022, 2023, 2024):
            for month in (1, 7):
                for day in range(1, 4):
                    date = dt.date(year, month, day)
                    macro = (
                        "macro_non_southerly"
                        if day % 2
                        else "macro_southerly_flow"
                    )
                    k_cp = float(10 + day + month / 10)
                    features.append(
                        {
                            "date_local": date,
                            "cp": cp_time,
                            "k_cp": k_cp,
                            "foehn_score": float(day * 4),
                            "cloud_cover_suppression": float(5 - day),
                        }
                    )
                    labels.append({"date_local": date, "tmax_int": k_cp})
                    assignments.append(
                        {
                            "date_local": date,
                            "cp": cp_text,
                            "binary_macro_regime_label": macro,
                        }
                    )

    pl.DataFrame(features).write_parquet(features_path)
    pl.DataFrame(labels).unique("date_local").write_parquet(labels_path)
    pl.DataFrame(assignments).write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "onda3-pooled-model-iteration",
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
        ],
    )

    assert result.exit_code == 0
    predictions = pl.read_csv(output_dir / "onda3_pooled_predictions_v1.csv")
    regime = pl.read_csv(output_dir / "onda3_pooled_regime_performance_v1.csv")

    assert set(predictions["cp"].unique().to_list()) == {
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    }
    assert "binary_macro_regime_label" in predictions.columns
    assert not predictions["binary_macro_regime_label"].null_count()
    assert set(regime["binary_macro_regime_label"].to_list()) == {
        "macro_non_southerly",
        "macro_southerly_flow",
    }
