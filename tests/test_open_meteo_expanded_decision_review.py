from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_open_meteo_expanded_decision_review_artifacts,
    write_open_meteo_expanded_decision_review_artifacts,
)


def _prediction_rows(
    *,
    augmented_error: float,
    season_error: float,
    recent_error: float,
    year: int,
    regime: str,
    cp: str = "23:00",
    actual: float = 20.0,
) -> list[dict[str, object]]:
    date_local = dt.date(year, 1 if regime == "macro_non_southerly" else 2, 1)
    rows: list[dict[str, object]] = []
    for candidate_id, error in [
        ("open_meteo_augmented_onda3f", augmented_error),
        ("om_family_season_bias_corrected", season_error),
        ("om_family_recent_bias_corrected", recent_error),
    ]:
        prediction = actual + error
        rows.append(
            {
                "date_local": date_local,
                "cp": cp,
                "stage": "test",
                "outer_test_year": year,
                "evaluation_year": year,
                "candidate_id": candidate_id,
                "candidate_label": candidate_id,
                "actual": actual,
                "prediction": prediction,
                "absolute_error": abs(actual - prediction),
                "actual_bracket": int(actual + 0.5),
                "pred_bracket": int(prediction + 0.5),
                "exact_bracket": int(actual + 0.5) == int(prediction + 0.5),
                "month": date_local.strftime("%Y-%m"),
                "calendar_year": year,
                "binary_macro_regime_label": regime,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return rows


def _selection() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "outer_test_year": 2024,
                "validation_year": 2023,
                "selected_candidate_id": "om_family_season_bias_corrected",
                "selection_rule": "test_rule",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "outer_test_year": 2025,
                "validation_year": 2024,
                "selected_candidate_id": "om_family_recent_bias_corrected",
                "selection_rule": "test_rule",
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )


def _promotable_predictions() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    rows.extend(
        _prediction_rows(
            augmented_error=1.2,
            season_error=0.2,
            recent_error=0.8,
            year=2024,
            regime="macro_non_southerly",
        )
    )
    rows.extend(
        _prediction_rows(
            augmented_error=1.0,
            season_error=0.1,
            recent_error=0.7,
            year=2024,
            regime="macro_southerly_flow",
            cp="20:00",
            actual=16.0,
        )
    )
    rows.extend(
        _prediction_rows(
            augmented_error=1.1,
            season_error=0.7,
            recent_error=0.2,
            year=2025,
            regime="macro_non_southerly",
        )
    )
    rows.extend(
        _prediction_rows(
            augmented_error=1.0,
            season_error=0.8,
            recent_error=0.1,
            year=2025,
            regime="macro_southerly_flow",
            cp="20:00",
            actual=15.0,
        )
    )
    return pl.DataFrame(rows, strict=False)


def test_expanded_decision_review_compares_selected_and_static_policies():
    artifacts = build_open_meteo_expanded_decision_review_artifacts(
        predictions=_promotable_predictions(),
        selection=_selection(),
    )

    policy_rows = artifacts["open_meteo_expanded_policy_rows_v1"]
    policy_metrics = artifacts["open_meteo_expanded_policy_metrics_v1"]
    slice_metrics = artifacts["open_meteo_expanded_policy_slice_metrics_v1"]
    decision = artifacts["open_meteo_expanded_policy_decision_v1"].row(0, named=True)

    selected = policy_rows.filter(pl.col("policy_id") == "selected_policy")
    assert selected.height == 4
    assert set(selected.filter(pl.col("outer_test_year") == 2024)["candidate_id"]) == {
        "om_family_season_bias_corrected"
    }
    assert set(selected.filter(pl.col("outer_test_year") == 2025)["candidate_id"]) == {
        "om_family_recent_bias_corrected"
    }
    assert set(policy_metrics["policy_id"]) == {
        "selected_policy",
        "always_season",
        "always_recent",
        "always_augmented",
    }
    assert {
        "mae",
        "exact_bracket_pct",
        "any_cp_exact_pct",
        "cp23_exact_pct",
    }.issubset(policy_metrics.columns)
    assert {
        "overall",
        "year",
        "month",
        "cp",
        "binary_macro_regime_label",
        "year_regime",
        "month_cp",
    }.issubset(set(slice_metrics["slice_type"]))
    assert decision["decision_status"] == (
        "PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
    )
    assert decision["best_policy_id"] == "selected_policy"
    assert decision["selected_mae_delta_vs_augmented"] < 0
    assert decision["production_status"] == PRODUCTION_STATUS


def test_expanded_decision_review_keeps_augmented_when_regime_guard_fails():
    rows: list[dict[str, object]] = []
    for year in [2024, 2025]:
        rows.extend(
            _prediction_rows(
                augmented_error=1.2,
                season_error=0.1,
                recent_error=0.1,
                year=year,
                regime="macro_non_southerly",
            )
        )
        rows.extend(
            _prediction_rows(
                augmented_error=0.2,
                season_error=0.5,
                recent_error=0.5,
                year=year,
                regime="macro_southerly_flow",
                cp="20:00",
                actual=15.0,
            )
        )

    artifacts = build_open_meteo_expanded_decision_review_artifacts(
        predictions=pl.DataFrame(rows, strict=False),
        selection=_selection(),
    )

    decision = artifacts["open_meteo_expanded_policy_decision_v1"].row(0, named=True)
    assert decision["decision_status"] == (
        "KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE"
    )
    assert decision["max_regime_mae_delta_selected_vs_augmented"] > 0.025


def test_expanded_decision_review_requires_forward_collection_for_one_fold():
    artifacts = build_open_meteo_expanded_decision_review_artifacts(
        predictions=_promotable_predictions().filter(pl.col("outer_test_year") == 2025),
        selection=_selection().filter(pl.col("outer_test_year") == 2025),
    )

    decision = artifacts["open_meteo_expanded_policy_decision_v1"].row(0, named=True)
    assert decision["decision_status"] == "REQUIRE_MORE_FORWARD_COLLECTION_FOR_OPEN_METEO"
    assert decision["n_outer_folds"] == 1


def test_write_expanded_decision_review_artifacts_creates_report(tmp_path: Path):
    artifacts = build_open_meteo_expanded_decision_review_artifacts(
        predictions=_promotable_predictions(),
        selection=_selection(),
    )

    paths = write_open_meteo_expanded_decision_review_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 11),
    )

    assert paths["open_meteo_expanded_decision_review_report_md"].exists()
    assert paths["open_meteo_expanded_policy_decision_v1"].exists()
    report = paths["open_meteo_expanded_decision_review_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Open-Meteo OM-M13 Expanded-Surface Decision Review" in report
    assert "EXPERIMENT_ONLY" in report
