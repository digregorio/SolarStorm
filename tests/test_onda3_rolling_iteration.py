from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._rolling_iteration import build_onda3_rolling_iteration


def _rolling_matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00"):
        for year in (2022, 2023, 2024, 2025):
            for day in range(1, 7):
                macro = "macro_non_southerly" if day % 2 == 0 else "macro_southerly_flow"
                k_cp = float(year - 2000 + day)
                rows.append(
                    {
                        "date_local": dt.date(year, 1, day),
                        "cp": cp,
                        "k_cp": k_cp,
                        "cloud_cover_suppression": float(day % 3),
                        "binary_macro_regime_label": macro,
                        "tmax_int": k_cp + (0.25 if macro == "macro_non_southerly" else 0.75),
                    }
                )
    return pl.DataFrame(rows)


def test_rolling_iteration_reports_year_cp_results_and_decision():
    artifacts = build_onda3_rolling_iteration(
        _rolling_matrix(),
        test_years=[2024, 2025],
        numeric_feature_columns=["k_cp", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
    )

    results = artifacts["onda3_rolling_model_results_v1"]
    temporal = artifacts["onda3_rolling_temporal_diagnostics_v1"]
    decision = artifacts["onda3_rolling_decision_update_v1"].row(0, named=True)

    assert set(results["test_year"].to_list()) == {2024, 2025}
    assert set(results["cp"].to_list()) == {"20:00", "21:00"}
    assert set(results["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert temporal.filter(pl.col("diagnostic") == "all_challengers_beat_null").height == 1
    assert decision["decision_status"] == "READY_FOR_ONDA4_MODEL_RERUN"
    assert decision["production_status"] == "EXPERIMENT_ONLY"
