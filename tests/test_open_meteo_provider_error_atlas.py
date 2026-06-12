from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_provider_error_atlas_artifacts,
    build_provider_error_dataset,
    build_provider_error_metrics,
)


def _provider_features() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 7, 15),
                "cp": "23:00",
                "om_endpoint": "previous_runs",
                "om_model": "gfs_seamless",
                "om_causal_class": "fixed_lead_forecast",
                "om_prev_d1_day_max_c": 16.0,
                "production_status": PRODUCTION_STATUS,
            },
            {
                "date_local": dt.date(2024, 7, 16),
                "cp": "23:00",
                "om_endpoint": "previous_runs",
                "om_model": "gfs_seamless",
                "om_causal_class": "fixed_lead_forecast",
                "om_prev_d1_day_max_c": 20.0,
                "production_status": PRODUCTION_STATUS,
            },
            {
                "date_local": dt.date(2024, 8, 1),
                "cp": "20:00",
                "om_endpoint": "previous_runs",
                "om_model": "ecmwf_ifs025",
                "om_causal_class": "fixed_lead_forecast",
                "om_provider_tmax_pred_c": 10.0,
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )


def _labels() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"date_local": dt.date(2024, 7, 15), "tmax_int": 17},
            {"date_local": dt.date(2024, 7, 16), "tmax_int": 18},
            {"date_local": dt.date(2024, 8, 1), "tmax_int": 10},
        ]
    )


def _assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 7, 15),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_non_southerly",
            },
            {
                "date_local": dt.date(2024, 7, 16),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_southerly_flow",
            },
            {
                "date_local": dt.date(2024, 8, 1),
                "cp": "20:00",
                "binary_macro_regime_label": "macro_non_southerly",
            },
        ]
    )


def _eligibility() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "provider_family": "NOAA_GFS",
                "decision_status": "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "feature_gate_scope": "fixed_lead_provider_error_atlas",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "endpoint": "previous_runs",
                "model": "ecmwf_ifs025",
                "provider_family": "ECMWF_IFS",
                "decision_status": "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "feature_gate_scope": "fixed_lead_provider_error_atlas",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "provider_family": "ECMWF_IFS",
                "decision_status": "OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT",
                "feature_gate_scope": "single_runs_request_contract_not_proven",
                "production_status": PRODUCTION_STATUS,
            },
        ]
    )


def test_provider_error_dataset_uses_only_eligible_provider_rows():
    dataset = build_provider_error_dataset(
        open_meteo_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        provider_decision_update=_eligibility(),
    )

    assert dataset.height == 3
    assert set(dataset["provider_family"].to_list()) == {"NOAA_GFS", "ECMWF_IFS"}
    assert set(dataset["feature_gate_scope"].to_list()) == {
        "fixed_lead_provider_error_atlas"
    }
    assert set(dataset["provider_prediction_column"].to_list()) == {
        "om_prev_d1_day_max_c",
        "om_provider_tmax_pred_c",
    }
    assert set(dataset["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_provider_error_dataset_accepts_multi_provider_feature_schema():
    features = pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 7, 15),
                "cp": "23:00",
                "endpoint": "previous_runs",
                "model": "ecmwf_ifs025",
                "provider_family": "ECMWF_IFS",
                "om_causal_class": "fixed_lead_forecast",
                "om_provider_tmax_pred_c": 18.0,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )

    dataset = build_provider_error_dataset(
        open_meteo_features=features,
        labels=pl.DataFrame(
            [{"date_local": dt.date(2024, 7, 15), "tmax_int": 17}]
        ),
        assignments=None,
        provider_decision_update=_eligibility(),
    )

    row = dataset.row(0, named=True)
    assert row["endpoint"] == "previous_runs"
    assert row["model"] == "ecmwf_ifs025"
    assert row["provider_family"] == "ECMWF_IFS"
    assert row["provider_prediction_column"] == "om_provider_tmax_pred_c"
    assert row["provider_prediction"] == 18.0
    assert row["actual_tmax"] == 17.0


def test_provider_error_metrics_report_signed_bias_and_exact_rate():
    dataset = build_provider_error_dataset(
        open_meteo_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        provider_decision_update=_eligibility(),
    )

    metrics = build_provider_error_metrics(dataset)
    overall = metrics.filter(
        (pl.col("model") == "gfs_seamless")
        & (pl.col("slice_type") == "overall")
        & (pl.col("slice_name") == "overall")
    ).row(0, named=True)

    assert overall["n_rows"] == 2
    assert overall["mae"] == 1.5
    assert overall["rmse"] > 1.5
    assert overall["signed_bias"] == 0.5
    assert overall["exact_bracket_pct"] == 0.0
    assert overall["warm_bias_pct"] == 50.0
    assert overall["cold_bias_pct"] == 50.0
    assert overall["production_status"] == PRODUCTION_STATUS


def test_provider_error_atlas_artifacts_include_required_slices():
    artifacts = build_provider_error_atlas_artifacts(
        open_meteo_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        provider_decision_update=_eligibility(),
    )

    metrics = artifacts["open_meteo_provider_error_metrics_v1"]
    slice_types = set(metrics["slice_type"].to_list())

    assert {
        "overall",
        "year",
        "month",
        "cp",
        "binary_macro_regime_label",
        "month_cp",
        "binary_macro_regime_label_cp",
    }.issubset(slice_types)
    assert artifacts["open_meteo_provider_error_dataset_v1"].height == 3
    assert artifacts["open_meteo_provider_error_support_warnings_v1"].height >= 1
