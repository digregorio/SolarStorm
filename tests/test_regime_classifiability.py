from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_classifiability import (
    build_regime_classifiability_artifacts,
    prepare_classifiability_feature_matrix,
    select_physical_classifiability_features,
    write_regime_classifiability_artifacts,
)


def _features() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_nw_continuum",
                "drct_sin_mean": -0.173648,
                "drct_cos_mean": 0.984807,
                "sknt_mean": 15.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.5,
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_southerly_flow",
                "drct_sin_mean": 0.0,
                "drct_cos_mean": -1.0,
                "sknt_mean": 16.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum": 0.1,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp": -0.4,
            },
        ]
    )


def _physical_features_with_forbidden_columns() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "drct_sin_mean": -0.1,
                "drct_cos_mean": 0.9,
                "sknt_mean": 15.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.5,
                "tmax_anomaly": 3.0,
                "remaining_warming": 2.0,
                "tmax_dminus1": 25.0,
                "foehn_score": 70.0,
                "regime_label": "strong_nw_foehn",
            },
            {
                "date_local": dt.date(2020, 1, 2),
                "cp": "20:00",
                "drct_sin_mean": 0.0,
                "drct_cos_mean": -1.0,
                "sknt_mean": 18.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum": 0.2,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp": -0.4,
                "tmax_anomaly": -2.0,
                "remaining_warming": -1.0,
                "tmax_dminus1": 22.0,
                "foehn_score": 5.0,
                "regime_label": "southerly_disrupted",
            },
        ]
    )


def _assignments_v21(*, causal_window: str = "valid < CP") -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2.1",
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "candidate_regime_label": "macro_nw_continuum",
                "component_entropy": 0.2,
                "component_margin": 0.7,
                "distance_to_candidate": 0.3,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_nw_continuum",
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": causal_window,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v2.1",
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "candidate_regime_label": "macro_southerly_flow",
                "component_entropy": 0.3,
                "component_margin": 0.6,
                "distance_to_candidate": 0.4,
                "assignment_confidence": 0.7,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_southerly_flow",
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": causal_window,
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def _comparison_v21() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2.1",
                "macro_regime_label": "macro_nw_continuum",
                "v21_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2.1",
                "macro_regime_label": "macro_southerly_flow",
                "v21_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )


def _candidate_v2() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )


def _features_v22() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "drct_sin_mean": -0.173648,
                "drct_cos_mean": 0.984807,
                "sknt_mean": 15.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.5,
            },
            {
                "date_local": dt.date(2020, 1, 2),
                "cp": "20:00",
                "drct_sin_mean": 0.0,
                "drct_cos_mean": -1.0,
                "sknt_mean": 16.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum": 0.1,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp": -0.4,
            },
            {
                "date_local": dt.date(2022, 1, 2),
                "cp": "20:00",
                "drct_sin_mean": 0.2,
                "drct_cos_mean": 0.9,
                "sknt_mean": 4.0,
                "qnh_hpa_mean": 1014.0,
                "relh_mean": 92.0,
                "dewpoint_depression_mean": 1.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 3.5,
                "temp_slope_pre_cp": 0.0,
            },
        ]
    )


def _assignments_v22() -> pl.DataFrame:
    base = _assignments_v21()
    calm = pl.DataFrame(
        [
            {
                "candidate_version": "v2.2",
                "date_local": dt.date(2022, 1, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_calm_radiative",
                "subtype_label": "subtype_calm_radiative",
                "candidate_regime_label": "macro_calm_radiative",
                "component_entropy": 0.0,
                "component_margin": 0.8,
                "distance_to_candidate": 0.1,
                "assignment_confidence": 0.9,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_nw_continuum",
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        ],
        strict=False,
    )
    return pl.concat(
        [
            base.with_columns(pl.lit("v2.2").alias("candidate_version")),
            calm,
        ],
        how="diagonal_relaxed",
    )


def _comparison_v22() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2.2",
                "macro_regime_label": "macro_calm_radiative",
                "v22_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2.2",
                "macro_regime_label": "macro_nw_continuum",
                "v22_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2.2",
                "macro_regime_label": "macro_southerly_flow",
                "v22_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )


def test_onda_c_accepts_v22_with_calm_radiative_protected_macro():
    res = build_regime_classifiability_artifacts(
        features=_features_v22(),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v22(),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v22(),
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
        candidate_under_review_version="v2.2",
        candidate_under_review_method="distance_softmax_v22",
        protected_macros=(
            "macro_calm_radiative",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        comparison_dead_count_column="v22_dead_regimes",
    )

    assignments = res["regime_classifiability_assignments"]
    comparison = res["regime_classifiability_comparison"]

    assert "distance_softmax_v22" in set(assignments["method"])
    reviewed = comparison.filter(pl.col("method") == "distance_softmax_v22")
    assert reviewed.row(0, named=True)["candidate_version"] == "v2.2"
    assert reviewed.row(0, named=True)["macro_count"] == 3
    assert reviewed.row(0, named=True)["dead_regimes"] == 0
    assert reviewed.row(0, named=True)["protected_regression_flag"] is False


def test_onda_c_records_block_when_v22_candidate_comparison_is_not_ready():
    blocked_comparison = _comparison_v22().with_columns(
        pl.when(pl.col("macro_regime_label") == "macro_calm_radiative")
        .then(pl.lit(1))
        .otherwise(pl.col("v22_dead_regimes"))
        .alias("v22_dead_regimes"),
        pl.lit("KEEP_IN_REGIME_DESIGN_REVIEW").alias("decision_update"),
    )

    res = build_regime_classifiability_artifacts(
        features=_features_v22(),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v22(),
        candidate_v2=_candidate_v2(),
        comparison_v21=blocked_comparison,
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
        candidate_under_review_version="v2.2",
        candidate_under_review_method="distance_softmax_v22",
        protected_macros=(
            "macro_calm_radiative",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        comparison_dead_count_column="v22_dead_regimes",
        allow_blocked_candidate_for_onda_c=True,
    )

    comparison = res["regime_classifiability_comparison"]
    reviewed = comparison.filter(pl.col("method") == "distance_softmax_v22")
    assert reviewed.row(0, named=True)["decision_update"] == "BLOCK_ONDA_C_PROMOTION"

    diagnostics = res["regime_classifiability_diagnostics"]
    candidate_gate = diagnostics.filter(
        pl.col("diagnostic_item") == "candidate comparison gate"
    ).row(0, named=True)
    assert candidate_gate["status"] == "FAIL"
    assert "blocked before Onda C promotion" in candidate_gate["detail"]


def test_physical_feature_selector_uses_only_approved_meteorological_columns():
    selected, audit = select_physical_classifiability_features(
        _physical_features_with_forbidden_columns()
    )

    assert selected == [
        "drct_sin_mean",
        "drct_cos_mean",
        "sknt_mean",
        "qnh_hpa_mean",
        "relh_mean",
        "dewpoint_depression_mean",
        "precip_pre_cp_sum",
        "cloud_cover_score_mean",
        "temp_slope_pre_cp",
    ]
    assert set(audit.get_column("production_status")) == {"EXPERIMENT_ONLY"}

    included = audit.filter(pl.col("included_in_classifiability"))
    assert set(included.get_column("feature")) == set(selected)

    rejected = audit.filter(~pl.col("included_in_classifiability"))
    rejected_by_feature = {row["feature"]: row for row in rejected.iter_rows(named=True)}
    assert rejected_by_feature["tmax_anomaly"]["leakage_class"] == "excluded_outcome"
    assert (
        rejected_by_feature["remaining_warming"]["leakage_class"]
        == "excluded_outcome"
    )
    assert (
        rejected_by_feature["tmax_dminus1"]["leakage_class"]
        == "excluded_model_feature"
    )
    assert (
        rejected_by_feature["foehn_score"]["leakage_class"]
        == "excluded_quarantined_label"
    )
    assert (
        rejected_by_feature["regime_label"]["leakage_class"]
        == "excluded_quarantined_label"
    )


def test_physical_feature_selector_rejects_model_feature_fallback_basis():
    model_features = pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "tmax_dminus1": 20.0,
                "late_warming_anomaly": 1.5,
                "foehn_score": 80.0,
            },
            {
                "date_local": dt.date(2020, 1, 2),
                "cp": "20:00",
                "tmax_dminus1": 21.0,
                "late_warming_anomaly": 2.0,
                "foehn_score": 10.0,
            },
        ]
    )

    with pytest.raises(ValueError, match="physical classifiability basis"):
        select_physical_classifiability_features(model_features)


def test_onda_c_builds_feature_basis_audit_and_physical_diagnostics():
    res = build_regime_classifiability_artifacts(
        features=_physical_features_with_forbidden_columns().drop(
            [
                "tmax_anomaly",
                "remaining_warming",
                "tmax_dminus1",
                "foehn_score",
                "regime_label",
            ]
        ),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v21(),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
    )

    assert "regime_classifiability_feature_basis_audit" in res
    audit = res["regime_classifiability_feature_basis_audit"]
    assert audit.filter(pl.col("included_in_classifiability")).height == 9

    diagnostics = res["regime_classifiability_diagnostics"]
    diagnostic_names = set(diagnostics.get_column("diagnostic_item"))
    assert "obs_labels_features_join_valid" in diagnostic_names
    assert "physical_feature_basis_loaded" in diagnostic_names
    assert "approved_physical_feature_count" in diagnostic_names
    assert "forbidden_numeric_fallback_not_used" in diagnostic_names
    assert "outcome_columns_excluded" in diagnostic_names
    assert "quarantined_labels_excluded" in diagnostic_names


def test_onda_c_rejects_non_causal_assignment_window():
    with pytest.raises(ValueError, match="causal_window"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(causal_window="leaky"),
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_rejects_duplicate_assignment_keys():
    duplicated = pl.concat([_assignments_v21(), _assignments_v21()])
    with pytest.raises(ValueError, match="duplicate assignment"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=duplicated,
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_requires_candidate_v2_physical_macros():
    with pytest.raises(ValueError, match="candidate_v2"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=pl.DataFrame(
                [
                    {
                        "candidate_version": "v2",
                        "macro_regime_label": "macro_nw_continuum",
                        "subtype_label": "subtype_standard_nw",
                        "production_status": "EXPERIMENT_ONLY",
                    }
                ],
                strict=False,
            ),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_requires_candidate_v2_schema():
    with pytest.raises(ValueError, match="candidate_v2"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=pl.DataFrame([{"production_status": "EXPERIMENT_ONLY"}]),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_rejects_v21_comparison_with_dead_or_regressed_macros():
    bad_comparison = _comparison_v21().with_columns(
        pl.when(pl.col("macro_regime_label") == "macro_nw_continuum")
        .then(pl.lit(1))
        .otherwise(pl.col("v21_dead_regimes"))
        .alias("v21_dead_regimes")
    )
    with pytest.raises(ValueError, match="comparison_v21"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=_candidate_v2(),
            comparison_v21=bad_comparison,
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_builds_distance_softmax_baseline_artifacts():
    res = build_regime_classifiability_artifacts(
        features=_features(),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v21(),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
    )

    assert "regime_classifiability_assignments" in res
    assert "regime_classifiability_metrics" in res
    assert "regime_classifiability_comparison" in res
    assert "regime_classifiability_diagnostics" in res

    assignments = res["regime_classifiability_assignments"]
    assert assignments.height > 0
    assert set(assignments["method"].unique()) == {"distance_softmax_v2", "distance_softmax_v21"}
    assert set(assignments["production_status"]) == {"EXPERIMENT_ONLY"}

    metrics = res["regime_classifiability_metrics"]
    assert metrics.height > 0
    assert set(metrics["method"].unique()) == {"distance_softmax_v2", "distance_softmax_v21"}
    assert set(metrics["production_status"]) == {"EXPERIMENT_ONLY"}

    comparison = res["regime_classifiability_comparison"]
    assert comparison.height > 0
    assert set(comparison["method"].unique()) == {"distance_softmax_v2", "distance_softmax_v21"}
    assert set(comparison["production_status"]) == {"EXPERIMENT_ONLY"}

    decisions = comparison["decision_update"].to_list()
    for d in decisions:
        assert d in {"READY_FOR_ONDA3_DESIGN_REVIEW", "KEEP_IN_REGIME_DESIGN_REVIEW", "BLOCK_ONDA_C_PROMOTION"}


def test_onda_c_gmm_som_michelangeli_are_train_only_and_do_not_write_models():
    dates = [dt.date(2020, 1, i) for i in range(1, 11)]
    feats_list = []
    for i, date in enumerate(dates):
        feats_list.append({
            "date_local": date,
            "cp": "20:00",
            "regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
            "drct_sin_mean": -0.17 if i < 5 else 0.0,
            "drct_cos_mean": 0.98 if i < 5 else -1.0,
            "sknt_mean": 15.0 + i,
            "qnh_hpa_mean": 1012.0 - i,
            "relh_mean": 60.0 + i,
            "dewpoint_depression_mean": 8.0 - (i % 3),
            "precip_pre_cp_sum": 0.0,
            "cloud_cover_score_mean": 1.0 + (i % 2),
            "temp_slope_pre_cp": 0.5 + (i * 0.01),
        })
    feats_df = pl.DataFrame(feats_list)

    assign_v21_list = []
    for i, date in enumerate(dates):
        assign_v21_list.append({
            "candidate_version": "v2.1",
            "date_local": date,
            "cp": "20:00",
            "macro_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
            "subtype_label": "subtype_standard_nw" if i < 5 else "subtype_frontal_southerly",
            "candidate_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
            "component_entropy": 0.2,
            "component_margin": 0.7,
            "distance_to_candidate": 0.3,
            "assignment_confidence": 0.8,
            "low_confidence_flag": False,
            "original_macro_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
            "absorbed_from_residual": False,
            "causal_window": "valid < CP",
            "production_status": "NOT_PRODUCTION",
        })
    assign_df = pl.DataFrame(assign_v21_list, strict=False)

    res = build_regime_classifiability_artifacts(
        features=feats_df,
        assignments_v2=assign_df,
        assignments_v21=assign_df,
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2020, 1, 5),
        test_start=dt.date(2020, 1, 6),
    )

    assignments = res["regime_classifiability_assignments"]
    methods = assignments["method"].unique().to_list()
    assert "train_only_gmm" in methods
    assert "som_topological" in methods
    assert "michelangeli_stability" in methods

    gmm_test_rows = assignments.filter((pl.col("method") == "train_only_gmm") & (pl.col("test_fold") == "test"))
    assert gmm_test_rows.height > 0

    diagnostics = res["regime_classifiability_diagnostics"]
    leakage = diagnostics.filter(pl.col("diagnostic_item") == "train/test leakage check").row(0, named=True)
    assert leakage["status"] == "PASS"

    import glob
    assert len(glob.glob("*.pkl")) == 0
    assert len(glob.glob("*.pickle")) == 0
    assert len(glob.glob("*.joblib")) == 0


def test_onda_c_keeps_design_review_when_alternative_method_contradicts_v21():
    dates = [dt.date(2020, 1, i) for i in range(1, 11)]
    feats_df = pl.DataFrame(
        [
            {
                "date_local": date,
                "cp": "20:00",
                "regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
                "drct_sin_mean": -0.17 if i < 5 else 0.0,
                "drct_cos_mean": 0.98 if i < 5 else -1.0,
                "sknt_mean": 15.0 + i,
                "qnh_hpa_mean": 1012.0 - i,
                "relh_mean": 60.0 + i,
                "dewpoint_depression_mean": 8.0 - (i % 3),
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0 + (i % 2),
                "temp_slope_pre_cp": 0.5 + (i * 0.01),
            }
            for i, date in enumerate(dates)
        ]
    )
    assign_df = pl.DataFrame(
        [
            {
                "candidate_version": "v2.1",
                "date_local": date,
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
                "subtype_label": "subtype_standard_nw" if i < 5 else "subtype_frontal_southerly",
                "candidate_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
                "component_entropy": 0.2,
                "component_margin": 0.7,
                "distance_to_candidate": 0.3,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_nw_continuum" if i < 5 else "macro_southerly_flow",
                "absorbed_from_residual": False,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
            for i, date in enumerate(dates)
        ],
        strict=False,
    )

    res = build_regime_classifiability_artifacts(
        features=feats_df,
        assignments_v2=assign_df,
        assignments_v21=assign_df,
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2020, 1, 5),
        test_start=dt.date(2020, 1, 6),
    )

    comparison = res["regime_classifiability_comparison"]
    assert "KEEP_IN_REGIME_DESIGN_REVIEW" in set(comparison["decision_update"])
    ready = comparison.filter(pl.col("decision_update") == "READY_FOR_ONDA3_DESIGN_REVIEW")
    assert ready.height == 0


def test_train_only_gmm_mapping_preserves_minority_macro_when_clusters_are_imbalanced():
    rows = []
    assignments = []
    date0 = dt.date(2020, 1, 1)
    for i in range(120):
        date = date0 + dt.timedelta(days=i)
        is_train = i < 100
        if is_train:
            if i < 70:
                label = "macro_nw_continuum"
                x = 0.0
            elif i < 85:
                label = "macro_southerly_flow"
                x = 0.1
            elif i < 95:
                label = "macro_nw_continuum"
                x = 8.0
            else:
                label = "macro_southerly_flow"
                x = 8.1
        else:
            label = "macro_nw_continuum" if i < 110 else "macro_southerly_flow"
            x = 0.0 if label == "macro_nw_continuum" else 8.0

        rows.append(
            {
                "date_local": date,
                "cp": "20:00",
                "regime_label": label,
                "drct_sin_mean": x,
                "drct_cos_mean": x * 0.5,
                "sknt_mean": 10.0 + x,
                "qnh_hpa_mean": 1010.0 - x,
                "relh_mean": 60.0 + x,
                "dewpoint_depression_mean": 8.0 - (x * 0.1),
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0 + (x * 0.01),
                "temp_slope_pre_cp": 0.5 + (x * 0.01),
            }
        )
        assignments.append(
            {
                "candidate_version": "v2.1",
                "date_local": date,
                "cp": "20:00",
                "macro_regime_label": label,
                "subtype_label": label,
                "candidate_regime_label": label,
                "component_entropy": 0.2,
                "component_margin": 0.7,
                "distance_to_candidate": 0.3,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "original_macro_regime_label": label,
                "absorbed_from_residual": False,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )

    res = build_regime_classifiability_artifacts(
        features=pl.DataFrame(rows),
        assignments_v2=pl.DataFrame(assignments, strict=False),
        assignments_v21=pl.DataFrame(assignments, strict=False),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2020, 4, 9),
        test_start=dt.date(2020, 4, 10),
    )

    gmm = res["regime_classifiability_comparison"].filter(pl.col("method") == "train_only_gmm").row(0, named=True)
    assert gmm["macro_count"] == 2
    assert gmm["dead_regimes"] == 0
    assert not gmm["protected_regression_flag"]


def test_classifiability_feature_matrix_filters_constant_duplicate_and_encodes_categoricals():
    features = pl.DataFrame(
        {
            "date_local": [dt.date(2020, 1, 1), dt.date(2020, 1, 2), dt.date(2020, 1, 3), dt.date(2020, 1, 4)],
            "cp": ["20:00", "20:00", "20:00", "20:00"],
            "signal": [0.0, 1.0, 2.0, 3.0],
            "signal_copy": [0.0, 1.0, 2.0, 3.0],
            "constant": [1.0, 1.0, 1.0, 1.0],
            "regime_score_argmax": ["standard_nw", "southerly_disrupted", "standard_nw", None],
            "day_sequence_pattern": ["flat", "cooling", "warming", "flat"],
            "regime_flags": ["{\"x\": 1}", "{\"x\": 2}", "{\"x\": 3}", "{\"x\": 4}"],
        }
    )

    matrix, cols = prepare_classifiability_feature_matrix(features, features)

    assert matrix.shape[0] == 4
    assert "signal" in cols
    assert "signal_copy" not in cols
    assert "constant" not in cols
    assert any(c.startswith("regime_score_argmax=") for c in cols)
    assert any(c.startswith("day_sequence_pattern=") for c in cols)
    assert not any(c.startswith("regime_flags=") for c in cols)


def test_classifiability_feature_matrix_honors_explicit_allowed_physical_columns():
    features = pl.DataFrame(
        {
            "date_local": [
                dt.date(2020, 1, 1),
                dt.date(2020, 1, 2),
                dt.date(2020, 1, 3),
                dt.date(2020, 1, 4),
            ],
            "cp": ["20:00", "20:00", "20:00", "20:00"],
            "drct_sin_mean": [0.0, 0.1, 0.2, 0.3],
            "drct_cos_mean": [1.0, 0.9, 0.8, 0.7],
            "tmax_anomaly": [10.0, -10.0, 9.0, -9.0],
            "foehn_score": [99.0, 0.0, 95.0, 1.0],
            "regime_score_argmax": ["a", "b", "a", "b"],
        }
    )

    matrix, cols = prepare_classifiability_feature_matrix(
        features,
        features,
        allowed_numeric_features=["drct_sin_mean", "drct_cos_mean"],
    )

    assert matrix.shape == (4, 2)
    assert cols == ["drct_sin_mean", "drct_cos_mean"]


def test_precomputed_classifiability_rejects_legacy_wind_column_names():
    legacy = pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_nw_continuum",
                "wind_dir_deg": 350.0,
                "wind_speed": 15.0,
                "qnh_hpa": 1012.0,
                "relh": 60.0,
                "dewpoint_depression": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score": 1.0,
                "temp_slope_pre_cp": 0.5,
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_southerly_flow",
                "wind_dir_deg": 180.0,
                "wind_speed": 16.0,
                "qnh_hpa": 1007.0,
                "relh": 85.0,
                "dewpoint_depression": 2.0,
                "precip_pre_cp_sum": 0.1,
                "cloud_cover_score": 3.0,
                "temp_slope_pre_cp": -0.4,
            },
        ]
    )

    with pytest.raises(ValueError, match="physical classifiability basis"):
        build_regime_classifiability_artifacts(
            features=legacy,
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_write_regime_classifiability_artifacts(tmp_path: Path):
    res = build_regime_classifiability_artifacts(
        features=_features(),
        assignments_v2=_assignments_v21(),
        assignments_v21=_assignments_v21(),
        candidate_v2=_candidate_v2(),
        comparison_v21=_comparison_v21(),
        train_end=dt.date(2021, 12, 31),
        test_start=dt.date(2022, 1, 1),
    )

    write_regime_classifiability_artifacts(
        res,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_classifiability_assignments_v1.csv").exists()
    assert (tmp_path / "regime_classifiability_metrics_v1.csv").exists()
    assert (tmp_path / "regime_classifiability_comparison_v1.csv").exists()
    assert (tmp_path / "regime_classifiability_diagnostics_v1.csv").exists()
    assert (tmp_path / "regime_classifiability_feature_basis_audit_v1.csv").exists()
    assert (tmp_path / "regime_classifiability_feature_basis_audit_v1.md").exists()
    assert (tmp_path / "regime_classifiability_report_v1.md").exists()

    report_content = (tmp_path / "regime_classifiability_report_v1.md").read_text(encoding="utf-8")
    assert "Onda C Regime Classifiability" in report_content
    assert "not a production classifier" in report_content
    assert "Onda C comes before Onda 3" in report_content
    assert "v2.2 regime redesign" in report_content
    assert "Blocking Evidence" in report_content

    feature_basis_report = (
        tmp_path / "regime_classifiability_feature_basis_audit_v1.md"
    ).read_text(encoding="utf-8")
    assert "Regime Classifiability Feature Basis Audit" in feature_basis_report
    assert "physical" in feature_basis_report.lower()
    assert "forbidden numeric fallback" in feature_basis_report.lower()

    bad_res = dict(res)
    bad_res["regime_classifiability_comparison"] = bad_res["regime_classifiability_comparison"].with_columns(
        pl.lit("INVALID_DECISION").alias("decision_update")
    )
    with pytest.raises(ValueError, match="decision_update"):
        write_regime_classifiability_artifacts(
            bad_res,
            output_dir=tmp_path,
            today=dt.date(2026, 6, 8),
        )


def _labels_for_physical_cli() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "day_complete": True,
                "tmax_int": 25,
                "tmax_hour": 14,
                "k_cp__cp_2000": 21,
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "day_complete": True,
                "tmax_int": 18,
                "tmax_hour": 13,
                "k_cp__cp_2000": 20,
            },
        ]
    )


def _obs_for_physical_cli() -> pl.DataFrame:
    rows = []
    for base_date, direction, speed, alti, relh, cloud, temps in (
        (
            dt.date(2019, 12, 31),
            350.0,
            15.0,
            29.90,
            60.0,
            "FEW",
            [(18, 20), (19, 21)],
        ),
        (
            dt.date(2021, 12, 31),
            180.0,
            16.0,
            29.70,
            85.0,
            "BKN",
            [(18, 16), (19, 15)],
        ),
    ):
        for hour, temp in temps:
            rows.append(
                {
                    "valid": dt.datetime(
                        base_date.year,
                        base_date.month,
                        base_date.day,
                        hour,
                        0,
                        tzinfo=dt.UTC,
                    ),
                    "tmp_c_int": temp,
                    "dwp_c_int": temp - (8 if direction == 350.0 else 2),
                    "dw_depression_c_int": 8 if direction == 350.0 else 2,
                    "drct": direction,
                    "sknt": speed,
                    "alti": alti,
                    "relh": relh,
                    "p01i": 0.0 if direction == 350.0 else 0.1,
                    "skyc1": cloud,
                    "dq_tmp_c_int": "ok",
                }
            )
    return pl.DataFrame(rows)


def test_regime_classifiability_cli_writes_artifacts(tmp_path: Path):
    runner = CliRunner()
    features_path = tmp_path / "features.parquet"
    assignments_v2_path = tmp_path / "v2.csv"
    assignments_v21_path = tmp_path / "v21.csv"
    candidate_v2_path = tmp_path / "candidate.csv"
    comparison_v21_path = tmp_path / "comparison.csv"
    output_dir = tmp_path / "regime-classifiability"

    _features().write_parquet(features_path)
    _assignments_v21().write_csv(assignments_v2_path)
    _assignments_v21().write_csv(assignments_v21_path)
    _candidate_v2().write_csv(candidate_v2_path)
    _comparison_v21().write_csv(comparison_v21_path)

    result = runner.invoke(
        app,
        [
            "regime-classifiability-benchmark",
            "--basis-mode",
            "precomputed",
            "--features-path",
            str(features_path),
            "--assignments-v2-path",
            str(assignments_v2_path),
            "--assignments-v21-path",
            str(assignments_v21_path),
            "--candidate-v2-path",
            str(candidate_v2_path),
            "--comparison-v21-path",
            str(comparison_v21_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2021-12-31",
            "--test-start",
            "2022-01-01",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_classifiability_assignments_v1.csv").exists()
    assert (output_dir / "regime_classifiability_metrics_v1.csv").exists()
    assert (output_dir / "regime_classifiability_comparison_v1.csv").exists()
    assert (output_dir / "regime_classifiability_diagnostics_v1.csv").exists()
    assert (output_dir / "regime_classifiability_report_v1.md").exists()


def test_regime_classifiability_cli_physical_mode_writes_feature_basis_audit(
    tmp_path: Path,
):
    runner = CliRunner()
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    assignments_v2_path = tmp_path / "v2.csv"
    assignments_v21_path = tmp_path / "v21.csv"
    candidate_v2_path = tmp_path / "candidate.csv"
    comparison_v21_path = tmp_path / "comparison.csv"
    output_dir = tmp_path / "regime-classifiability"

    pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_nw_continuum",
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_southerly_flow",
            },
        ]
    ).write_parquet(features_path)
    _labels_for_physical_cli().write_parquet(labels_path)
    _obs_for_physical_cli().write_parquet(obs_path)
    _assignments_v21().write_csv(assignments_v2_path)
    _assignments_v21().write_csv(assignments_v21_path)
    _candidate_v2().write_csv(candidate_v2_path)
    _comparison_v21().write_csv(comparison_v21_path)

    result = runner.invoke(
        app,
        [
            "regime-classifiability-benchmark",
            "--basis-mode",
            "physical",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--assignments-v2-path",
            str(assignments_v2_path),
            "--assignments-v21-path",
            str(assignments_v21_path),
            "--candidate-v2-path",
            str(candidate_v2_path),
            "--comparison-v21-path",
            str(comparison_v21_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2021-12-31",
            "--test-start",
            "2022-01-01",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_classifiability_feature_basis_audit_v1.csv").exists()
    audit = pl.read_csv(output_dir / "regime_classifiability_feature_basis_audit_v1.csv")
    assert audit.filter(pl.col("included_in_classifiability")).height >= 2
