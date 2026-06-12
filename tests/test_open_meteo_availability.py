from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import polars as pl
import pytest

from solarstorm.open_meteo import (
    OPEN_METEO_FILENAMES,
    PRODUCTION_STATUS,
    assert_no_open_meteo_features_created,
    build_availability_summaries,
    build_blocked_source_register,
    build_decision_update,
    build_probe_plan,
    build_source_registry_frame,
    cp_local_to_utc,
    render_availability_report,
    run_probe_plan,
    select_latest_eligible_run,
    write_open_meteo_availability_artifacts,
)
from solarstorm.open_meteo._client import (
    OpenMeteoResponse,
    build_request_url,
    hash_text,
)

EXPECTED_VARIABLES = [
    "temperature_2m",
    "dew_point_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "pressure_msl",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]
EXPECTED_VARIABLES_CSV = ",".join(EXPECTED_VARIABLES)
EXPECTED_PREVIOUS_RUNS_VARIABLES = [
    "temperature_2m_previous_day1",
    "dew_point_2m_previous_day1",
    "cloud_cover_previous_day1",
    "cloud_cover_low_previous_day1",
    "pressure_msl_previous_day1",
    "wind_speed_10m_previous_day1",
    "wind_gusts_10m_previous_day1",
    "wind_direction_10m_previous_day1",
]
EXPECTED_PREVIOUS_RUNS_VARIABLES_CSV = ",".join(EXPECTED_PREVIOUS_RUNS_VARIABLES)


def test_source_registry_includes_all_open_meteo_source_classes():
    registry = build_source_registry_frame()

    assert registry.height == 5
    assert set(registry["causal_class"].to_list()) == {
        "live_seamless_forecast",
        "seamless_historical_forecast",
        "fixed_lead_forecast",
        "forecast_snapshot",
        "reanalysis_not_forecast",
    }
    assert set(registry["endpoint"].to_list()) == {
        "forecast",
        "historical_forecast",
        "previous_runs",
        "single_runs",
        "historical_weather",
    }
    assert set(registry["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_source_registry_contract_pins_metadata_for_later_artifacts():
    registry = build_source_registry_frame()

    assert registry.columns == [
        "station",
        "latitude",
        "longitude",
        "source_id",
        "endpoint",
        "endpoint_url",
        "model",
        "causal_class",
        "nominal_available_from",
        "expected_run_cadence_h",
        "expected_horizon_h",
        "variables",
        "default_decision",
        "production_status",
    ]

    by_id = {row["source_id"]: row for row in registry.iter_rows(named=True)}
    assert set(by_id) == {
        "forecast_api_best_match",
        "historical_forecast_best_match",
        "previous_runs_gfs_temperature",
        "single_runs_ecmwf_ifs_hres",
        "historical_weather_era5",
    }

    for row in by_id.values():
        assert row["station"] == "NZWN"
        assert row["latitude"] == -41.3272
        assert row["longitude"] == 174.8053
        assert row["production_status"] == PRODUCTION_STATUS

    expected_variables_by_source = {
        "forecast_api_best_match": EXPECTED_VARIABLES,
        "historical_forecast_best_match": EXPECTED_VARIABLES,
        "previous_runs_gfs_temperature": EXPECTED_PREVIOUS_RUNS_VARIABLES,
        "single_runs_ecmwf_ifs_hres": EXPECTED_VARIABLES,
        "historical_weather_era5": EXPECTED_VARIABLES,
    }
    for source_id, expected_variables in expected_variables_by_source.items():
        assert by_id[source_id]["variables"] == ",".join(expected_variables)
        assert by_id[source_id]["variables"].split(",") == expected_variables

    assert by_id["forecast_api_best_match"] == {
        "station": "NZWN",
        "latitude": -41.3272,
        "longitude": 174.8053,
        "source_id": "forecast_api_best_match",
        "endpoint": "forecast",
        "endpoint_url": "https://api.open-meteo.com/v1/forecast",
        "model": "best_match",
        "causal_class": "live_seamless_forecast",
        "nominal_available_from": None,
        "expected_run_cadence_h": None,
        "expected_horizon_h": 168,
        "variables": EXPECTED_VARIABLES_CSV,
        "default_decision": "USE_LIVE_FORWARD_COLLECTION_ONLY",
        "production_status": PRODUCTION_STATUS,
    }
    assert by_id["historical_forecast_best_match"] == {
        "station": "NZWN",
        "latitude": -41.3272,
        "longitude": 174.8053,
        "source_id": "historical_forecast_best_match",
        "endpoint": "historical_forecast",
        "endpoint_url": "https://historical-forecast-api.open-meteo.com/v1/forecast",
        "model": "best_match",
        "causal_class": "seamless_historical_forecast",
        "nominal_available_from": dt.date(2021, 1, 1),
        "expected_run_cadence_h": None,
        "expected_horizon_h": None,
        "variables": EXPECTED_VARIABLES_CSV,
        "default_decision": "AUDIT_ONLY_UNTIL_CAUSAL_METADATA_PROVEN",
        "production_status": PRODUCTION_STATUS,
    }
    assert by_id["previous_runs_gfs_temperature"] == {
        "station": "NZWN",
        "latitude": -41.3272,
        "longitude": 174.8053,
        "source_id": "previous_runs_gfs_temperature",
        "endpoint": "previous_runs",
        "endpoint_url": "https://previous-runs-api.open-meteo.com/v1/forecast",
        "model": "gfs_seamless",
        "causal_class": "fixed_lead_forecast",
        "nominal_available_from": dt.date(2021, 3, 23),
        "expected_run_cadence_h": 6,
        "expected_horizon_h": 168,
        "variables": EXPECTED_PREVIOUS_RUNS_VARIABLES_CSV,
        "default_decision": "FIXED_LEAD_SKILL_AUDIT_ONLY",
        "production_status": PRODUCTION_STATUS,
    }
    assert by_id["single_runs_ecmwf_ifs_hres"] == {
        "station": "NZWN",
        "latitude": -41.3272,
        "longitude": 174.8053,
        "source_id": "single_runs_ecmwf_ifs_hres",
        "endpoint": "single_runs",
        "endpoint_url": "https://single-runs-api.open-meteo.com/v1/forecast",
        "model": "ecmwf_ifs025",
        "causal_class": "forecast_snapshot",
        "nominal_available_from": dt.date(2024, 3, 14),
        "expected_run_cadence_h": 6,
        "expected_horizon_h": 240,
        "variables": EXPECTED_VARIABLES_CSV,
        "default_decision": "PRIMARY_CAUSAL_PILOT_CANDIDATE",
        "production_status": PRODUCTION_STATUS,
    }
    assert by_id["historical_weather_era5"] == {
        "station": "NZWN",
        "latitude": -41.3272,
        "longitude": 174.8053,
        "source_id": "historical_weather_era5",
        "endpoint": "historical_weather",
        "endpoint_url": "https://archive-api.open-meteo.com/v1/archive",
        "model": "era5",
        "causal_class": "reanalysis_not_forecast",
        "nominal_available_from": dt.date(1940, 1, 1),
        "expected_run_cadence_h": None,
        "expected_horizon_h": None,
        "variables": EXPECTED_VARIABLES_CSV,
        "default_decision": "DIAGNOSTIC_ONLY_BLOCKED_AS_CAUSAL_PREDICTOR",
        "production_status": PRODUCTION_STATUS,
    }


def test_registry_blocks_reanalysis_and_non_snapshot_sources_from_causal_features():
    registry = build_source_registry_frame()
    blocked = build_blocked_source_register(registry)

    assert blocked.columns == [
        "source_id",
        "endpoint",
        "model",
        "causal_class",
        "causal_feature_allowed",
        "blocked_reason",
        "production_status",
    ]
    assert blocked.height == registry.height
    assert set(blocked["source_id"].to_list()) == set(registry["source_id"].to_list())

    by_id = {row["source_id"]: row for row in blocked.iter_rows(named=True)}

    assert by_id["historical_weather_era5"]["causal_feature_allowed"] is False
    assert by_id["historical_weather_era5"]["blocked_reason"] == (
        "reanalysis_not_forecast"
    )
    assert by_id["forecast_api_best_match"]["causal_feature_allowed"] is False
    assert by_id["forecast_api_best_match"]["blocked_reason"] == (
        "live_seamless_no_historical_runs"
    )
    assert by_id["historical_forecast_best_match"]["causal_feature_allowed"] is False
    assert by_id["historical_forecast_best_match"]["blocked_reason"] == (
        "seamless_no_run_metadata_until_proven"
    )
    assert by_id["previous_runs_gfs_temperature"]["causal_feature_allowed"] is False
    assert by_id["previous_runs_gfs_temperature"]["blocked_reason"] == (
        "fixed_lead_audit_only"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["causal_feature_allowed"] is True
    assert by_id["single_runs_ecmwf_ifs_hres"]["blocked_reason"] == (
        "run_initialisation_preserved"
    )
    assert set(blocked["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_blocked_source_register_allows_only_forecast_snapshots():
    registry = build_source_registry_frame()
    blocked = build_blocked_source_register(registry)

    assert blocked.height == registry.height
    assert set(blocked["source_id"].to_list()) == set(registry["source_id"].to_list())

    for row in blocked.iter_rows(named=True):
        assert row["causal_feature_allowed"] is (
            row["causal_class"] == "forecast_snapshot"
        )


def test_cp_local_to_utc_respects_new_zealand_dst():
    summer = cp_local_to_utc(dt.date(2025, 1, 15), "23:00")
    winter = cp_local_to_utc(dt.date(2025, 7, 15), "23:00")

    assert summer == dt.datetime(2025, 1, 15, 10, 0, tzinfo=dt.UTC)
    assert winter == dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)


def test_select_latest_eligible_run_blocks_runs_available_after_checkpoint():
    cp_utc = dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)
    valid_time_utc = dt.datetime(2025, 7, 15, 12, 0, tzinfo=dt.UTC)

    selected = select_latest_eligible_run(
        cp_utc=cp_utc,
        valid_time_utc=valid_time_utc,
        candidate_run_times_utc=[
            dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC),
            dt.datetime(2025, 7, 15, 6, 0, tzinfo=dt.UTC),
        ],
        availability_lag_h=6,
        safety_margin_minutes=10,
    )

    assert selected is not None
    assert selected["selected_run_time_utc"] == "2025-07-15T00:00:00+00:00"
    assert selected["selected_available_time_utc"] == "2025-07-15T06:10:00+00:00"
    assert selected["selected_valid_time_utc"] == "2025-07-15T12:00:00+00:00"
    assert selected["selected_lead_h"] == 12


def test_select_latest_eligible_run_returns_none_when_no_run_available_before_checkpoint():
    selected = select_latest_eligible_run(
        cp_utc=dt.datetime(2025, 7, 15, 5, 0, tzinfo=dt.UTC),
        valid_time_utc=dt.datetime(2025, 7, 15, 12, 0, tzinfo=dt.UTC),
        candidate_run_times_utc=[
            dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC),
            dt.datetime(2025, 7, 15, 6, 0, tzinfo=dt.UTC),
        ],
        availability_lag_h=6,
        safety_margin_minutes=10,
    )

    assert selected is None


def test_select_latest_eligible_run_rejects_non_forecast_valid_time():
    cp_utc = dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC)

    selected = select_latest_eligible_run(
        cp_utc=cp_utc,
        valid_time_utc=dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC),
        candidate_run_times_utc=[dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC)],
        availability_lag_h=0,
        safety_margin_minutes=0,
    )

    assert selected is None


def test_select_latest_eligible_run_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="UTC-aware"):
        select_latest_eligible_run(
            cp_utc=dt.datetime(2025, 7, 15, 11, 0),
            valid_time_utc=dt.datetime(2025, 7, 15, 12, 0, tzinfo=dt.UTC),
            candidate_run_times_utc=[dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC)],
            availability_lag_h=6,
            safety_margin_minutes=10,
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        select_latest_eligible_run(
            cp_utc=dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC),
            valid_time_utc=dt.datetime(2025, 7, 15, 12, 0),
            candidate_run_times_utc=[dt.datetime(2025, 7, 15, 0, 0, tzinfo=dt.UTC)],
            availability_lag_h=6,
            safety_margin_minutes=10,
        )

    with pytest.raises(ValueError, match="UTC-aware"):
        select_latest_eligible_run(
            cp_utc=dt.datetime(2025, 7, 15, 11, 0, tzinfo=dt.UTC),
            valid_time_utc=dt.datetime(2025, 7, 15, 12, 0, tzinfo=dt.UTC),
            candidate_run_times_utc=[dt.datetime(2025, 7, 15, 0, 0)],
            availability_lag_h=6,
            safety_margin_minutes=10,
        )


def test_build_probe_plan_is_bounded_and_excludes_live_forecast_by_default():
    registry = build_source_registry_frame()

    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["20:00", "23:00"],
        month_days=[(1, 15), (7, 15)],
    )

    assert "forecast_api_best_match" not in set(plan["source_id"].to_list())
    assert set(plan["source_id"].to_list()) == {
        "historical_forecast_best_match",
        "previous_runs_gfs_temperature",
        "single_runs_ecmwf_ifs_hres",
        "historical_weather_era5",
    }
    assert set(plan.columns) >= {
        "probe_id",
        "station",
        "source_id",
        "endpoint",
        "endpoint_url",
        "model",
        "variable_group",
        "date_local",
        "calendar_year",
        "month",
        "cp",
        "cp_utc",
        "target_valid_time_utc",
        "selected_run_time_utc",
        "selected_available_time_utc",
        "selected_lead_h",
        "causal_class",
        "request_params_json",
        "request_url",
        "request_url_sha256",
        "request_params_sha256",
        "production_status",
    }
    assert plan.height > 0
    assert plan["probe_id"].n_unique() == plan.height
    assert set(plan["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert set(plan["cp"].to_list()) == {"20:00", "23:00"}
    assert set(plan["date_local"].dt.year().to_list()) == {2024}
    plan_month_days = {
        (row["date_local"].month, row["date_local"].day)
        for row in plan.select("date_local").unique().iter_rows(named=True)
    }
    assert plan_month_days <= {(1, 15), (7, 15)}
    assert (7, 15) in plan_month_days

    for row in plan.iter_rows(named=True):
        assert row["request_url"] is not None
        assert row["request_url_sha256"] is not None
        assert row["request_params_sha256"] is not None
        assert len(row["request_url_sha256"]) == 64
        assert len(row["request_params_sha256"]) == 64
        assert row["request_url"] == build_request_url(
            row["endpoint_url"],
            json.loads(row["request_params_json"]),
        )
        assert row["request_url_sha256"] == hash_text(row["request_url"])
        assert row["request_params_sha256"] == hash_text(row["request_params_json"])

    single_rows = plan.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres")
    assert single_rows.height > 0
    assert set(single_rows["endpoint_url"].to_list()) == {
        "https://single-runs-api.open-meteo.com/v1/forecast"
    }
    assert single_rows["selected_run_time_utc"].null_count() == 0
    assert single_rows["selected_available_time_utc"].null_count() == 0
    assert single_rows["selected_lead_h"].null_count() == 0
    assert not single_rows.filter(
        (pl.col("date_local").dt.month() == 1) & (pl.col("date_local").dt.day() == 15)
    ).height

    single_params = json.loads(single_rows.row(0, named=True)["request_params_json"])
    assert single_params["latitude"] == -41.3272
    assert single_params["longitude"] == 174.8053
    assert single_params["hourly"] == EXPECTED_VARIABLES_CSV
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", single_params["run"])
    assert "Z" not in single_params["run"]

    previous_rows = plan.filter(pl.col("source_id") == "previous_runs_gfs_temperature")
    assert previous_rows.height > 0
    previous_params = json.loads(previous_rows.row(0, named=True)["request_params_json"])
    assert previous_params["hourly"] == EXPECTED_PREVIOUS_RUNS_VARIABLES_CSV
    assert "previous_days" not in previous_params


class FakeOpenMeteoClient:
    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        text = json.dumps(
            {
                "hourly": {
                    "time": ["2024-07-15T23:00"],
                    "temperature_2m": [12.4],
                }
            }
        )
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?fake=1",
            status_code=200,
            text=text,
        )


class MissingHourlyTimeOpenMeteoClient:
    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?empty=1",
            status_code=200,
            text=json.dumps({"hourly": {"temperature_2m": [12.4]}}),
        )


class RaisingOpenMeteoClient:
    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        raise AssertionError("client should not be called")


def test_run_probe_plan_records_hashes_and_success_without_network():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)

    assert results.height == 1
    row = results.row(0, named=True)
    assert row["success"] is True
    assert row["status_code"] == 200
    assert row["n_hourly_times"] == 1
    assert len(row["request_url_sha256"]) == 64
    assert len(row["response_sha256"]) == 64
    assert row["request_url"] == "https://single-runs-api.open-meteo.com/v1/forecast?fake=1"
    assert row["request_url_sha256"] == hash_text(row["request_url"])
    assert row["production_status"] == PRODUCTION_STATUS


def test_run_probe_plan_plan_only_does_not_call_client():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=None, live=False)

    assert results.height == plan.height
    assert set(results["success"].to_list()) == {False}
    assert set(results["error"].to_list()) == {"plan_only_not_requested"}


def test_run_probe_plan_plan_only_ignores_provided_client_and_preserves_plan_url():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=RaisingOpenMeteoClient(), live=False)

    assert results.height == plan.height
    result = results.row(0, named=True)
    probe = plan.row(0, named=True)
    assert result["request_url"] == probe["request_url"]
    assert result["request_url_sha256"] == probe["request_url_sha256"]
    assert result["error"] == "plan_only_not_requested"


def test_run_probe_plan_invalid_request_params_json_fails_without_calling_client():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    ).with_columns(pl.lit("{bad json").alias("request_params_json"))

    results = run_probe_plan(plan, client=RaisingOpenMeteoClient(), live=True)

    assert results.height == plan.height
    result = results.row(0, named=True)
    assert result["success"] is False
    assert result["status_code"] is None
    assert result["n_hourly_times"] == 0
    assert result["error"] == "invalid_request_params_json"


def test_run_probe_plan_ok_response_without_hourly_time_records_error():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )

    results = run_probe_plan(plan, client=MissingHourlyTimeOpenMeteoClient(), live=True)

    result = results.row(0, named=True)
    assert result["success"] is False
    assert result["status_code"] == 200
    assert result["n_hourly_times"] == 0
    assert result["error"] == "missing_hourly_time"


def test_availability_summaries_include_registry_sources_without_probes():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)

    availability = build_availability_summaries(
        registry,
        plan,
        results,
    )["availability_by_source"]

    assert availability.height == registry.height
    assert set(availability["source_id"].to_list()) == set(
        registry["source_id"].to_list()
    )
    forecast = availability.filter(
        pl.col("source_id") == "forecast_api_best_match"
    ).row(0, named=True)
    assert forecast["causal_class"] == "live_seamless_forecast"
    assert forecast["n_probes"] == 0
    assert forecast["n_success"] == 0
    assert forecast["n_success_years"] == 0
    assert forecast["success_pct"] == 0.0
    assert forecast["has_run_metadata"] is False
    assert forecast["has_lead_metadata"] is False
    assert forecast["production_status"] == PRODUCTION_STATUS


def test_build_decision_update_empty_input_returns_stable_schema():
    decision = build_decision_update(pl.DataFrame())

    assert decision.height == 0
    assert decision.columns == [
        "source_id",
        "endpoint",
        "model",
        "causal_class",
        "n_probes",
        "n_success",
        "n_success_years",
        "has_run_metadata",
        "has_lead_metadata",
        "success_pct",
        "decision_status",
        "pilot_scope_note",
        "production_status",
    ]


def test_default_plan_only_decisions_cover_all_sources_conservatively():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)

    availability = build_availability_summaries(
        registry,
        plan,
        results,
    )["availability_by_source"]
    decision = build_decision_update(availability)

    by_id = {row["source_id"]: row for row in decision.iter_rows(named=True)}

    assert set(by_id) == set(registry["source_id"].to_list())
    assert by_id["forecast_api_best_match"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA"
    )
    assert by_id["forecast_api_best_match"]["pilot_scope_note"] == (
        "live_forward_collection_only"
    )
    assert by_id["historical_forecast_best_match"]["decision_status"] == (
        "OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY"
    )
    assert by_id["historical_forecast_best_match"]["pilot_scope_note"] == (
        "requires_run_metadata_before_causal_use"
    )
    assert by_id["previous_runs_gfs_temperature"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_AVAILABILITY"
    )
    assert by_id["previous_runs_gfs_temperature"]["pilot_scope_note"] == (
        "no_successful_probe"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_AVAILABILITY"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["pilot_scope_note"] == (
        "no_successful_probe"
    )
    assert by_id["historical_weather_era5"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA"
    )
    assert by_id["historical_weather_era5"]["pilot_scope_note"] == (
        "diagnostic_only_reanalysis"
    )
    assert set(decision["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_empty_probe_window_keeps_stable_schemas_and_no_probe_summaries():
    registry = build_source_registry_frame()
    empty_plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["20:00"],
        month_days=[(1, 15)],
    )

    assert empty_plan.height == 0
    assert "probe_id" in empty_plan.columns
    assert "request_url_sha256" in empty_plan.columns

    empty_results = run_probe_plan(empty_plan, client=None, live=False)
    assert empty_results.height == 0
    assert "success" in empty_results.columns
    assert "response_sha256" in empty_results.columns

    summaries = build_availability_summaries(registry, empty_plan, empty_results)
    availability = summaries["availability_by_source"]
    assert availability.height == registry.height
    assert set(availability["n_probes"].to_list()) == {0}
    assert set(availability["n_success"].to_list()) == {0}
    assert summaries["availability_by_year_month_cp"].height == 0
    assert "success_pct" in summaries["availability_by_year_month_cp"].columns
    assert summaries["causal_selection_audit"].height == 0
    assert "selected_run_time_utc" in summaries["causal_selection_audit"].columns


def test_run_probe_plan_empty_plan_returns_schema_even_when_live_without_client():
    registry = build_source_registry_frame()
    empty_plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["20:00"],
        month_days=[(1, 15)],
    )

    results = run_probe_plan(empty_plan, client=None, live=True)

    assert results.height == 0
    assert "success" in results.columns
    assert "response_sha256" in results.columns


def test_decision_update_maps_previous_runs_success_to_lead_audit():
    availability = pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "causal_class": "fixed_lead_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )

    row = build_decision_update(availability).row(0, named=True)

    assert row["decision_status"] == "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT"
    assert row["pilot_scope_note"] == "fixed_lead_skill_audit_only"


def test_decision_update_blocks_successful_snapshot_missing_metadata():
    availability = pl.DataFrame(
        [
            {
                "source_id": "single_runs_ecmwf_ifs_hres",
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "causal_class": "forecast_snapshot",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": True,
                "success_pct": 100.0,
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )

    row = build_decision_update(availability).row(0, named=True)

    assert row["decision_status"] == "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA"
    assert row["pilot_scope_note"] == "missing_run_or_lead_metadata"


def test_decisions_keep_historical_weather_blocked_and_narrow_single_runs_pilot():
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(
            pl.col("source_id").is_in(
                ["single_runs_ecmwf_ifs_hres", "historical_weather_era5"]
            )
        ),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)

    summaries = build_availability_summaries(registry, plan, results)
    decision = build_decision_update(summaries["availability_by_source"])

    by_id = {row["source_id"]: row for row in decision.iter_rows(named=True)}

    assert by_id["single_runs_ecmwf_ifs_hres"]["decision_status"] == (
        "OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["pilot_scope_note"] == (
        "narrow_to_available_window"
    )
    assert by_id["historical_weather_era5"]["decision_status"] == (
        "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA"
    )
    assert by_id["historical_weather_era5"]["pilot_scope_note"] == (
        "diagnostic_only_reanalysis"
    )
    assert set(decision["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_artifact_writer_creates_audit_outputs_and_no_feature_file(tmp_path: Path):
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "single_runs_ecmwf_ifs_hres"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=FakeOpenMeteoClient(), live=True)
    summaries = build_availability_summaries(registry, plan, results)
    summaries["decision_update"] = build_decision_update(
        summaries["availability_by_source"]
    )

    paths = write_open_meteo_availability_artifacts(
        summaries,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    for artifact_key, filename in OPEN_METEO_FILENAMES.items():
        assert paths[artifact_key] == tmp_path / filename
        assert paths[artifact_key].exists()
    assert paths["availability_report_md"].exists()
    assert not (tmp_path / "open_meteo_features.parquet").exists()
    assert_no_open_meteo_features_created(tmp_path)

    report = paths["availability_report_md"].read_text(encoding="utf-8")
    assert report == render_availability_report(summaries, today=dt.date(2026, 6, 9))
    assert "Historical Weather / reanalysis is blocked" in report
    assert (
        "Historical Forecast remains audit-only unless CP-causal run metadata "
        "is proven."
    ) in report
    assert (
        "Single Runs can narrow a pilot to its available history instead of "
        "changing the Onda 3H baseline."
    ) in report
    assert "This availability audit does not write open_meteo_features.parquet" in report
    assert "EXPERIMENT_ONLY" in report


def test_writer_derives_decision_update_from_natural_summaries(tmp_path: Path):
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)
    summaries = build_availability_summaries(registry, plan, results)

    paths = write_open_meteo_availability_artifacts(
        summaries,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    assert paths["decision_update"].exists()
    assert (tmp_path / "open_meteo_decision_update_v1.csv").exists()


def test_writer_allows_preexisting_gated_data_feature_file(tmp_path: Path):
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "reports"
    data_dir.mkdir()
    existing_feature = data_dir / "open_meteo_features.parquet"
    existing_feature.write_text("existing gated artifact", encoding="utf-8")
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry.filter(pl.col("source_id") == "historical_weather_era5"),
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)
    summaries = build_availability_summaries(registry, plan, results)

    paths = write_open_meteo_availability_artifacts(
        summaries,
        output_dir=output_dir,
        today=dt.date(2026, 6, 9),
        data_dir=data_dir,
    )

    assert paths["availability_report_md"].exists()
    assert existing_feature.read_text(encoding="utf-8") == "existing gated artifact"
    assert not (output_dir / "open_meteo_features.parquet").exists()


def test_writer_rejects_existing_feature_file_before_writing_artifacts(
    tmp_path: Path,
):
    (tmp_path / "open_meteo_features.parquet").write_text(
        "blocked",
        encoding="utf-8",
    )
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)
    summaries = build_availability_summaries(registry, plan, results)

    with pytest.raises(AssertionError, match="feature generation is blocked"):
        write_open_meteo_availability_artifacts(
            summaries,
            output_dir=tmp_path,
            today=dt.date(2026, 6, 9),
        )

    assert not (tmp_path / "open_meteo_source_registry_v1.csv").exists()
    assert not (tmp_path / "open_meteo_availability_report_v1.md").exists()


def test_writer_rejects_missing_required_summary_before_writing_artifacts(
    tmp_path: Path,
):
    registry = build_source_registry_frame()
    plan = build_probe_plan(
        registry,
        years=[2024],
        cps=["23:00"],
        month_days=[(7, 15)],
    )
    results = run_probe_plan(plan, client=None, live=False)
    summaries = build_availability_summaries(registry, plan, results)
    summaries.pop("probe_results")

    with pytest.raises(ValueError, match="missing Open-Meteo artifact summaries"):
        write_open_meteo_availability_artifacts(
            summaries,
            output_dir=tmp_path,
            today=dt.date(2026, 6, 9),
        )

    assert not (tmp_path / "open_meteo_source_registry_v1.csv").exists()
    assert not (tmp_path / "open_meteo_availability_report_v1.md").exists()


def test_no_features_guard_rejects_open_meteo_feature_file(tmp_path: Path):
    (tmp_path / "open_meteo_features.parquet").write_text(
        "not allowed",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="feature generation is blocked"):
        assert_no_open_meteo_features_created(tmp_path)


def test_no_features_guard_rejects_data_feature_file(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "open_meteo_features.parquet").write_text(
        "blocked",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="feature generation is blocked"):
        assert_no_open_meteo_features_created(
            tmp_path / "reports",
            data_dir=data_dir,
        )


def test_report_truncation_row_matches_markdown_table_width():
    decision_update = pl.DataFrame(
        [
            {
                "source_id": f"source_{index:02d}",
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "causal_class": "forecast_snapshot",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": True,
                "has_lead_metadata": True,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT",
                "pilot_scope_note": "narrow_to_available_window",
                "production_status": PRODUCTION_STATUS,
            }
            for index in range(21)
        ]
    )
    summaries = {
        "decision_update": decision_update,
        "availability_by_source": decision_update.select(
            [
                "source_id",
                "endpoint",
                "model",
                "causal_class",
                "n_probes",
                "n_success",
                "n_success_years",
                "has_run_metadata",
                "has_lead_metadata",
                "success_pct",
                "production_status",
            ]
        ),
        "blocked_source_register": pl.DataFrame(
            [
                {
                    "source_id": "source_00",
                    "endpoint": "single_runs",
                    "model": "ecmwf_ifs025",
                    "causal_class": "forecast_snapshot",
                    "causal_feature_allowed": True,
                    "blocked_reason": "run_initialisation_preserved",
                    "production_status": PRODUCTION_STATUS,
                }
            ]
        ),
    }

    report = render_availability_report(summaries, today=dt.date(2026, 6, 9))

    decision_table = report.split("## Decision Update", maxsplit=1)[1].split(
        "## Availability by Source",
        maxsplit=1,
    )[0]
    table_lines = [
        line for line in decision_table.splitlines() if line.startswith("|")
    ]
    truncation_line = next(line for line in table_lines if line.startswith("| ... |"))
    assert truncation_line.count("|") == table_lines[0].count("|")
