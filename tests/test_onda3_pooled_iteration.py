from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._pooled_iteration import (
    add_pooled_temporal_features,
    build_onda3_pooled_iteration,
)


def _pooled_matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00", "22:00", "23:00"):
        for year in (2022, 2023, 2024, 2025):
            for month in (1, 4, 7, 10):
                for day in range(1, 4):
                    date = dt.date(year, month, day)
                    macro = (
                        "macro_non_southerly"
                        if day % 2
                        else "macro_southerly_flow"
                    )
                    k_cp = float(12 + day + month / 10)
                    rows.append(
                        {
                            "date_local": date,
                            "cp": cp,
                            "k_cp": k_cp,
                            "foehn_score": float(day * 5),
                            "cloud_cover_suppression": float(4 - day),
                            "binary_macro_regime_label": macro,
                            "regime_label": "warm_nw" if day % 2 else "cool_s",
                            "regime_score_argmax": macro,
                            "day_sequence_pattern": "warming"
                            if day % 2
                            else "cooling",
                            "tmax_int": k_cp + (0.6 if macro == "macro_non_southerly" else -0.4),
                        }
                    )
    return pl.DataFrame(rows)


def test_add_pooled_temporal_features_adds_cyclic_columns():
    enriched = add_pooled_temporal_features(_pooled_matrix())

    for column in ("cp_sin", "cp_cos", "month_sin", "month_cos", "doy_sin", "doy_cos"):
        assert column in enriched.columns
        assert enriched.schema[column].is_numeric()
        values = enriched[column].to_list()
        assert min(values) >= -1.0
        assert max(values) <= 1.0


def test_add_pooled_temporal_features_handles_time_typed_cp_values():
    frame = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1)] * 4,
            "cp": [
                dt.time(20, 0),
                dt.time(21, 0),
                dt.time(22, 0),
                dt.time(23, 0),
            ],
        }
    )

    enriched = add_pooled_temporal_features(frame)
    cp_cycles = enriched.select(["cp", "cp_sin", "cp_cos"]).unique(
        ["cp_sin", "cp_cos"]
    )

    assert set(enriched["cp"].to_list()) == {"20:00", "21:00", "22:00", "23:00"}
    assert cp_cycles.height == 4


def test_build_onda3_pooled_iteration_trains_one_model_per_year():
    artifacts = build_onda3_pooled_iteration(
        _pooled_matrix(),
        test_years=[2024, 2025],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=[
            "binary_macro_regime_label",
            "regime_label",
            "regime_score_argmax",
            "day_sequence_pattern",
        ],
    )

    results = artifacts["onda3_pooled_model_results_v1"]
    predictions = artifacts["onda3_pooled_predictions_v1"]
    bracket = artifacts["onda3_pooled_bracket_overall_v1"]
    decision = artifacts["onda3_pooled_decision_update_v1"].row(0, named=True)

    assert set(results["test_year"].to_list()) == {2024, 2025}
    assert set(results["cp"].to_list()) == {"ALL"}
    assert set(predictions["cp"].unique().to_list()) == {
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    }
    assert "cp_2300_exact_pct" in bracket.columns
    assert decision["decision_status"] in {
        "READY_FOR_ONDA3_AUDIT_COMPARISON",
        "KEEP_IN_ONDA3_EXPERIMENT_REVIEW",
    }
    for artifact in artifacts.values():
        if artifact.is_empty():
            continue
        assert "production_status" in artifact.columns
        assert set(artifact["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_build_onda3_pooled_iteration_handles_years_without_valid_folds():
    artifacts = build_onda3_pooled_iteration(
        _pooled_matrix(),
        test_years=[2030],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
    )

    decision = artifacts["onda3_pooled_decision_update_v1"].row(0, named=True)
    temporal = artifacts["onda3_pooled_temporal_diagnostics_v1"].row(0, named=True)

    assert artifacts["onda3_pooled_model_results_v1"].is_empty()
    assert artifacts["onda3_pooled_predictions_v1"].is_empty()
    assert decision["decision_status"] == "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
    assert "No valid pooled folds" in decision["decision_rationale"]
    assert temporal["status"] == "BLOCK"
