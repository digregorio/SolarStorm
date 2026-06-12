from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_multi_provider_availability_artifacts,
    build_multi_provider_probe_plan,
    build_multi_provider_registry,
    run_multi_provider_probe_plan,
)


def test_multi_provider_registry_separates_global_and_regional_candidates():
    registry = build_multi_provider_registry()
    by_model = {row["model"]: row for row in registry.iter_rows(named=True)}

    assert by_model["gfs_seamless"]["provider_family"] == "NOAA_GFS"
    assert by_model["ecmwf_ifs025"]["provider_family"] == "ECMWF_IFS"
    assert by_model["ecmwf_aifs025_single"]["provider_family"] == "ECMWF_AIFS"
    assert by_model["icon_seamless"]["provider_family"] == "DWD_ICON"
    assert by_model["gem_global"]["provider_family"] == "ECCC_GEM"
    assert by_model["jma_seamless"]["provider_family"] == "JMA_GSM"
    assert by_model["icon_d2"]["coverage_expectation"] == (
        "regional_expected_missing_for_wellington"
    )
    assert set(registry["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_multi_provider_probe_plan_includes_previous_runs_and_single_runs():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
        endpoints=["previous_runs", "single_runs"],
    )

    assert set(plan["endpoint"].to_list()) == {"previous_runs", "single_runs"}
    assert set(plan["model"].to_list()) == {"gfs_seamless", "ecmwf_ifs025"}
    assert set(plan["cp"].to_list()) == {"20:00", "23:00"}
    assert "request_url_sha256" in plan.columns
    assert "selected_run_time_utc" in plan.columns
    assert "selected_available_time_utc" in plan.columns
    assert "selected_lead_h" in plan.columns
    assert set(plan["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_multi_provider_plan_only_results_feed_decision_artifacts():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15)],
        cps=["23:00"],
        models=["gfs_seamless"],
        endpoints=["previous_runs", "single_runs"],
    )
    results = run_multi_provider_probe_plan(plan, client=None, live=False)

    assert results.height == plan.height
    assert set(results["success"].to_list()) == {False}
    assert set(results["error"].to_list()) == {"plan_only_not_requested"}

    artifacts = build_multi_provider_availability_artifacts(
        registry=build_multi_provider_registry(),
        probe_plan=plan,
        probe_results=results,
    )
    matrix = artifacts["open_meteo_multi_provider_availability_matrix_v1"]
    decision = artifacts["open_meteo_multi_provider_decision_update_v1"]

    assert not matrix.is_empty()
    assert set(matrix["production_status"].to_list()) == {PRODUCTION_STATUS}
    by_model_endpoint = {
        (row["model"], row["endpoint"]): row for row in decision.iter_rows(named=True)
    }
    assert by_model_endpoint[("gfs_seamless", "previous_runs")][
        "decision_status"
    ] == "OPEN_METEO_PROVIDER_BLOCKED_BY_AVAILABILITY"
    assert by_model_endpoint[("gfs_seamless", "single_runs")][
        "decision_status"
    ] == "OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT"


def test_multi_provider_live_success_marks_previous_runs_eligible():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15)],
        cps=["23:00"],
        models=["gfs_seamless"],
        endpoints=["previous_runs"],
    )
    successful = plan.with_columns(
        pl.lit(True).alias("success"),
        pl.lit(200).alias("status_code"),
        pl.lit(24).alias("n_hourly_times"),
        pl.lit("response-hash").alias("response_sha256"),
        pl.lit(None, dtype=pl.String).alias("error"),
    )

    artifacts = build_multi_provider_availability_artifacts(
        registry=build_multi_provider_registry(),
        probe_plan=plan,
        probe_results=successful,
    )
    decision = artifacts["open_meteo_multi_provider_decision_update_v1"]
    row = decision.row(0, named=True)

    assert row["model"] == "gfs_seamless"
    assert row["endpoint"] == "previous_runs"
    assert row["decision_status"] == "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS"
    assert row["feature_gate_scope"] == "fixed_lead_provider_error_atlas"
