from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda3._model_attempt_review import (
    build_month_day_bracket_summary,
    build_regime_performance_summary,
    enrich_predictions_with_brackets,
    write_onda3_model_attempt_review_artifacts,
)

runner = CliRunner()


def test_month_day_bracket_summary_uses_half_up_and_any_cp_metric():
    predictions = pl.DataFrame(
        {
            "date_local": [
                dt.date(2025, 1, 1),
                dt.date(2025, 1, 1),
                dt.date(2025, 1, 2),
                dt.date(2025, 1, 2),
            ],
            "cp": ["20:00", "23:00", "20:00", "23:00"],
            "actual": [15.0, 15.0, 16.0, 16.0],
            "prediction": [14.49, 14.50, 15.49, 15.49],
            "absolute_error": [0.51, 0.50, 0.51, 0.51],
            "model_name": ["ridge_challenger"] * 4,
            "production_status": ["EXPERIMENT_ONLY"] * 4,
        }
    )

    enriched = enrich_predictions_with_brackets(
        predictions,
        iteration_id="test_iteration",
        iteration_label="Test iteration",
    )
    monthly = build_month_day_bracket_summary(enriched).row(0, named=True)

    assert enriched["pred_bracket"].to_list() == [14, 15, 15, 15]
    assert enriched["actual_bracket"].to_list() == [15, 15, 16, 16]
    assert monthly["n_days"] == 2
    assert monthly["any_cp_exact_pct"] == 50.0
    assert monthly["cp23_exact_pct"] == 50.0


def test_regime_performance_summary_joins_assignments_and_reports_rates():
    predictions = pl.DataFrame(
        {
            "date_local": [
                dt.date(2025, 2, 1),
                dt.date(2025, 2, 1),
                dt.date(2025, 2, 2),
                dt.date(2025, 2, 2),
            ],
            "cp": ["20:00", "23:00", "20:00", "23:00"],
            "actual": [20.0, 20.0, 18.0, 18.0],
            "prediction": [20.1, 19.4, 16.9, 18.2],
            "absolute_error": [0.1, 0.6, 1.1, 0.2],
            "model_name": ["ridge_challenger"] * 4,
            "production_status": ["EXPERIMENT_ONLY"] * 4,
        }
    )
    assignments = pl.DataFrame(
        {
            "date_local": [
                dt.date(2025, 2, 1),
                dt.date(2025, 2, 1),
                dt.date(2025, 2, 2),
                dt.date(2025, 2, 2),
            ],
            "cp": ["20:00", "23:00", "20:00", "23:00"],
            "binary_macro_regime_label": [
                "macro_non_southerly",
                "macro_non_southerly",
                "macro_southerly_flow",
                "macro_southerly_flow",
            ],
        }
    )

    enriched = enrich_predictions_with_brackets(
        predictions,
        iteration_id="test_iteration",
        iteration_label="Test iteration",
        assignments=assignments,
    )
    regime = build_regime_performance_summary(enriched).sort(
        "binary_macro_regime_label"
    )

    non_southerly = regime.row(0, named=True)
    southerly = regime.row(1, named=True)
    assert non_southerly["n_cp_rows"] == 2
    assert non_southerly["exact_bracket_pct"] == 50.0
    assert southerly["n_cp_rows"] == 2
    assert southerly["exact_bracket_pct"] == 50.0


def test_model_attempt_review_writer_exports_markdown_and_csv(tmp_path: Path):
    artifacts = {
        "onda3_model_attempt_scope_v1": pl.DataFrame(
            {
                "iteration_id": ["onda3_a"],
                "iteration_label": ["Onda 3A"],
                "split_type": ["fixed_holdout"],
                "train_period": ["2009-04-23 to 2024-12-31"],
                "validation_period": ["none"],
                "test_period": ["2025-01-01 to 2026-06-03"],
                "row_unit": ["all_cp_rows"],
                "n_train_reported": [19748],
                "n_test_reported": [2076],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "onda3_model_iteration_summary_v1": pl.DataFrame(
            {
                "iteration_id": ["onda3_a"],
                "iteration_label": ["Onda 3A"],
                "weighted_null_mae": [2.8],
                "weighted_challenger_mae": [1.4],
                "weighted_mae_lift": [1.4],
                "all_challenger_rows_beat_null": [True],
                "has_line_level_predictions": [False],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "onda3_model_result_rows_v1": pl.DataFrame(
            {
                "iteration_id": ["onda3_a"],
                "iteration_label": ["Onda 3A"],
                "test_year": [None],
                "cp": ["ALL"],
                "model_name": ["ridge_challenger"],
                "n_train": [19748],
                "n_test": [2076],
                "mae": [1.4],
                "beats_train_mean_null": [True],
                "production_status": ["EXPERIMENT_ONLY"],
            }
        ),
        "onda3_bracket_overall_v1": pl.DataFrame(),
        "onda3_bracket_by_month_day_v1": pl.DataFrame(),
        "onda3_bracket_by_month_cp_v1": pl.DataFrame(),
        "onda3_regime_performance_v1": pl.DataFrame(),
        "onda3_regime_by_cp_v1": pl.DataFrame(),
        "onda3_regime_comparison_v1": pl.DataFrame(),
        "onda3_onda4_gate_review_v1": pl.DataFrame(),
    }

    paths = write_onda3_model_attempt_review_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    assert paths["onda3_model_attempt_review_md"].exists()
    assert paths["onda3_model_iteration_summary_csv"].exists()
    report = paths["onda3_model_attempt_review_md"].read_text(encoding="utf-8")
    assert "Onda 3 Model Attempt Review" in report
    assert "Open-Meteo forecast data is not integrated" in report


def test_onda3_model_attempt_review_cli_writes_report_from_existing_artifacts(
    tmp_path: Path,
):
    reports_dir = tmp_path / "reports"
    onda3_dir = reports_dir / "onda3"
    next_dir = reports_dir / "onda3-next"
    regime_dir = reports_dir / "regime-design"
    output_dir = reports_dir / "onda3-model-review"
    for directory in (onda3_dir, next_dir, regime_dir):
        directory.mkdir(parents=True)

    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    pl.DataFrame(
        {
            "date_local": [
                dt.date(2024, 12, 31),
                dt.date(2025, 1, 1),
                dt.date(2025, 1, 2),
            ],
            "cp": ["23:00", "20:00", "23:00"],
            "k_cp": [14.0, 15.0, 16.0],
        }
    ).write_parquet(features_path)
    pl.DataFrame(
        {
            "date_local": [
                dt.date(2024, 12, 31),
                dt.date(2025, 1, 1),
                dt.date(2025, 1, 2),
            ],
            "tmax_int": [14, 15, 16],
        }
    ).write_parquet(labels_path)

    pl.DataFrame(
        {
            "model_name": ["train_mean_null"],
            "cp": ["ALL"],
            "n_train": [1],
            "n_test": [2],
            "mae": [2.0],
            "beats_train_mean_null": [False],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3_dir / "onda3_baseline_results_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["ridge_challenger"],
            "cp": ["ALL"],
            "n_train": [1],
            "n_test": [2],
            "mae": [1.0],
            "beats_train_mean_null": [True],
            "production_status": ["EXPERIMENT_ONLY"],
        }
    ).write_csv(onda3_dir / "onda3_challenger_results_v1.csv")
    pl.DataFrame(
        {
            "model_name": ["train_mean_null", "ridge_challenger"],
            "cp": ["23:00", "23:00"],
            "n_train": [1, 1],
            "n_test": [2, 2],
            "mae": [2.0, 0.5],
            "beats_train_mean_null": [False, True],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(next_dir / "onda3_next_model_results_v1.csv")
    pl.DataFrame(
        {
            "date_local": [dt.date(2025, 1, 1), dt.date(2025, 1, 2)],
            "cp": ["23:00", "23:00"],
            "actual": [15.0, 16.0],
            "prediction": [14.5, 15.1],
            "absolute_error": [0.5, 0.9],
            "model_name": ["ridge_challenger", "ridge_challenger"],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    ).write_csv(next_dir / "onda3_next_predictions_v1.csv")
    pl.DataFrame(
        {
            "date_local": [dt.date(2025, 1, 1), dt.date(2025, 1, 2)],
            "cp": ["23:00", "23:00"],
            "binary_macro_regime_label": [
                "macro_non_southerly",
                "macro_southerly_flow",
            ],
        }
    ).write_csv(regime_dir / "regime_binary_macro_assignments_v1.csv")

    result = runner.invoke(
        app,
        [
            "onda3-model-attempt-review",
            "--reports-dir",
            str(reports_dir),
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "onda3_model_attempt_review_v1.md").exists()
    assert "Onda 3 model attempt review complete" in result.stdout
