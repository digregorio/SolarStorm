from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from solarstorm.onda3._audit_comparison import build_onda3_audit_comparison


def _audit_predictions() -> pl.DataFrame:
    rows = []
    model_offsets = {
        "onda3_d_binary_macro_interactions": 0.45,
        "onda3_e_legacy_2009_start": 0.44,
        "onda3_e_continuous_2012_start": 0.43,
        "onda3_f_pooled_temporal_regime": 0.25,
    }
    labels = {
        "onda3_d_binary_macro_interactions": "Onda 3D binary-macro interactions",
        "onda3_e_legacy_2009_start": "Onda 3E legacy 2009-start",
        "onda3_e_continuous_2012_start": "Onda 3E continuous 2012-start",
        "onda3_f_pooled_temporal_regime": "Onda 3F pooled temporal/regime",
    }
    for iteration_id, offset in model_offsets.items():
        for day in range(1, 9):
            date = dt.date(2024, 1 if day <= 4 else 2, day if day <= 4 else day - 4)
            macro = "macro_non_southerly" if day % 2 else "macro_southerly_flow"
            for cp in ("20:00", "21:00", "22:00", "23:00"):
                actual = 15 + day % 3
                rows.append(
                    {
                        "iteration_id": iteration_id,
                        "iteration_label": labels[iteration_id],
                        "date_local": date,
                        "calendar_year": date.year,
                        "test_year": 2024,
                        "month": date.strftime("%Y-%m"),
                        "cp": cp,
                        "actual": actual,
                        "prediction": actual + offset,
                        "absolute_error": offset,
                        "actual_bracket": int(actual),
                        "pred_bracket": int(actual if offset < 0.5 else actual + 1),
                        "exact_bracket": offset < 0.5,
                        "binary_macro_regime_label": macro,
                        "model_name": "ridge_challenger",
                        "production_status": "EXPERIMENT_ONLY",
                    }
                )
    return pl.DataFrame(rows)


def _audit_features() -> pl.DataFrame:
    rows = []
    for day in range(1, 9):
        date = dt.date(2024, 1 if day <= 4 else 2, day if day <= 4 else day - 4)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "regime_label": "calm_radiative" if day in (1, 5) else "other",
                    "foehn_score": float(day * 10),
                    "cloud_cover_suppression": float(90 - day),
                }
            )
    return pl.DataFrame(rows)


def test_build_onda3_audit_comparison_compares_model_surfaces():
    artifacts = build_onda3_audit_comparison(
        predictions=_audit_predictions(),
        features=_audit_features(),
    )

    summary = artifacts["onda3_audit_model_summary_v1"]
    deltas = artifacts["onda3_audit_pairwise_delta_v1"]
    regime_winner = artifacts["onda3_audit_regime_winner_v1"]
    feature_slice = artifacts["onda3_audit_feature_slice_v1"]
    decision = artifacts["onda3_audit_decision_update_v1"].row(0, named=True)

    assert set(summary["iteration_id"].to_list()) == {
        "onda3_d_binary_macro_interactions",
        "onda3_e_legacy_2009_start",
        "onda3_e_continuous_2012_start",
        "onda3_f_pooled_temporal_regime",
    }
    assert "onda3_f_minus_onda3_d" in deltas["comparison_id"].to_list()
    assert set(regime_winner["binary_macro_regime_label"].to_list()) == {
        "macro_non_southerly",
        "macro_southerly_flow",
    }
    assert "top_quartile_foehn_score" in feature_slice["slice_id"].to_list()
    assert decision["decision_status"] in {
        "CARRY_ONDA3D_AND_ONDA3F_TO_NESTED_VALIDATION",
        "CARRY_ONDA3F_TO_NESTED_VALIDATION",
        "KEEP_ONDA3D_REFERENCE_AND_REVIEW_ONDA3F",
    }
    for artifact in artifacts.values():
        if artifact.is_empty():
            continue
        assert "production_status" in artifact.columns
        assert set(artifact["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_build_onda3_audit_comparison_recomputes_stale_bracket_columns():
    stale = _audit_predictions().with_columns(
        pl.lit(999).alias("actual_bracket"),
        pl.lit(-999).alias("pred_bracket"),
        pl.lit(False).alias("exact_bracket"),
    )

    artifacts = build_onda3_audit_comparison(
        predictions=stale,
        features=_audit_features(),
    )

    summary = artifacts["onda3_audit_model_summary_v1"]
    pooled = summary.filter(
        pl.col("iteration_id") == "onda3_f_pooled_temporal_regime"
    ).row(0, named=True)

    assert pooled["any_cp_exact_pct"] == 100.0
    assert pooled["cp23_exact_pct"] == 100.0


def test_build_onda3_audit_comparison_blocks_duplicate_feature_keys():
    duplicated_features = pl.concat(
        [_audit_features(), _audit_features().head(1)],
        how="vertical",
    )

    with pytest.raises(ValueError, match="duplicate feature rows"):
        build_onda3_audit_comparison(
            predictions=_audit_predictions(),
            features=duplicated_features,
        )


def test_build_onda3_audit_comparison_feature_top_quartile_is_cardinality_slice():
    features = _audit_features().with_columns(
        pl.lit(1.0).alias("cloud_cover_suppression")
    )

    artifacts = build_onda3_audit_comparison(
        predictions=_audit_predictions(),
        features=features,
    )

    cloud_slice = artifacts["onda3_audit_feature_slice_v1"].filter(
        (pl.col("slice_id") == "top_quartile_cloud_cover_suppression")
        & (pl.col("iteration_id") == "onda3_f_pooled_temporal_regime")
    )

    assert cloud_slice.row(0, named=True)["n_cp_rows"] == 8
