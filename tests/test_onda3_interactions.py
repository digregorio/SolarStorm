from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._interactions import (
    add_binary_macro_interaction_features,
    build_onda3_interaction_iteration,
)


def _interaction_matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00"):
        for year in (2022, 2023, 2024, 2025):
            for day in range(1, 7):
                macro = "macro_non_southerly" if day % 2 == 0 else "macro_southerly_flow"
                foehn = float(day * 10)
                cloud = float(6 - day)
                target = 15.0 + 0.1 * day
                if macro == "macro_non_southerly":
                    target += 0.06 * foehn - 0.08 * cloud
                else:
                    target -= 0.03 * foehn + 0.05 * cloud
                rows.append(
                    {
                        "date_local": dt.date(year, 1, day),
                        "cp": cp,
                        "k_cp": 14.0 + day,
                        "foehn_score": foehn,
                        "cloud_cover_suppression": cloud,
                        "binary_macro_regime_label": macro,
                        "tmax_int": target,
                    }
                )
    return pl.DataFrame(rows)


def test_add_binary_macro_interaction_features_adds_expected_columns():
    enriched, interaction_columns = add_binary_macro_interaction_features(
        _interaction_matrix()
    )

    assert {
        "foehn_score_x_macro_non_southerly",
        "foehn_score_x_macro_southerly_flow",
        "cloud_cover_suppression_x_macro_non_southerly",
        "cloud_cover_suppression_x_macro_southerly_flow",
    }.issubset(set(interaction_columns))
    assert "foehn_score_x_macro_non_southerly" in enriched.columns
    assert enriched.filter(
        pl.col("binary_macro_regime_label") == "macro_southerly_flow"
    )["foehn_score_x_macro_non_southerly"].sum() == 0.0


def test_interaction_iteration_reports_interaction_feature_audit_and_decision():
    artifacts = build_onda3_interaction_iteration(
        _interaction_matrix(),
        test_years=[2024, 2025],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
    )

    audit = artifacts["onda3_interaction_feature_audit_v1"]
    results = artifacts["onda3_interaction_model_results_v1"]
    decision = artifacts["onda3_interaction_decision_update_v1"].row(0, named=True)

    assert audit.height == 4
    assert set(audit["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert set(results["test_year"].to_list()) == {2024, 2025}
    assert decision["decision_status"] == "READY_FOR_ONDA4_MODEL_RERUN"
    assert decision["production_status"] == "EXPERIMENT_ONLY"
