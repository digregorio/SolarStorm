from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
import pytest

from solarstorm.open_meteo import (
    OPEN_METEO_FEATURE_FILENAMES,
    PRODUCTION_STATUS,
    build_decision_update,
    build_feature_source_eligibility,
    build_open_meteo_feature_artifacts,
    build_previous_runs_feature_rows,
    build_raw_response_cache,
    ensure_source_allowed_for_features,
    write_open_meteo_feature_artifacts,
)
from solarstorm.open_meteo._client import OpenMeteoResponse


def _decision_with_previous_runs_success() -> pl.DataFrame:
    return pl.DataFrame(
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
                "decision_status": "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT",
                "pilot_scope_note": "fixed_lead_skill_audit_only",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "historical_weather_era5",
                "endpoint": "historical_weather",
                "model": "era5",
                "causal_class": "reanalysis_not_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
                "pilot_scope_note": "diagnostic_only_reanalysis",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "historical_forecast_best_match",
                "endpoint": "historical_forecast",
                "model": "best_match",
                "causal_class": "seamless_historical_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY",
                "pilot_scope_note": "requires_run_metadata_before_causal_use",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "single_runs_ecmwf_ifs_hres",
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "causal_class": "forecast_snapshot",
                "n_probes": 1,
                "n_success": 0,
                "n_success_years": 0,
                "has_run_metadata": True,
                "has_lead_metadata": True,
                "success_pct": 0.0,
                "decision_status": "OPEN_METEO_BLOCKED_BY_AVAILABILITY",
                "pilot_scope_note": "no_successful_probe",
                "production_status": PRODUCTION_STATUS,
            },
        ]
    )


def test_feature_source_eligibility_allows_previous_runs_only_after_success():
    eligibility = build_feature_source_eligibility(
        _decision_with_previous_runs_success()
    )

    by_id = {row["source_id"]: row for row in eligibility.iter_rows(named=True)}

    assert by_id["previous_runs_gfs_temperature"][
        "feature_generation_allowed"
    ] is True
    assert by_id["previous_runs_gfs_temperature"]["feature_generation_reason"] == (
        "fixed_lead_forecast_pilot_allowed"
    )
    assert by_id["historical_weather_era5"]["feature_generation_allowed"] is False
    assert by_id["historical_weather_era5"]["feature_generation_reason"] == (
        "reanalysis_blocked_as_predictor"
    )
    assert by_id["historical_forecast_best_match"][
        "feature_generation_allowed"
    ] is False
    assert by_id["historical_forecast_best_match"][
        "feature_generation_reason"
    ] == "seamless_historical_forecast_lacks_run_metadata"
    assert by_id["single_runs_ecmwf_ifs_hres"]["feature_generation_allowed"] is False
    assert by_id["single_runs_ecmwf_ifs_hres"]["feature_generation_reason"] == (
        "forecast_snapshot_not_available"
    )
    assert set(eligibility["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_feature_source_eligibility_blocks_previous_runs_without_success():
    availability = pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "causal_class": "fixed_lead_forecast",
                "n_probes": 1,
                "n_success": 0,
                "n_success_years": 0,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 0.0,
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )
    decision = build_decision_update(availability)

    eligibility = build_feature_source_eligibility(decision)

    row = eligibility.row(0, named=True)
    assert row["source_id"] == "previous_runs_gfs_temperature"
    assert row["feature_generation_allowed"] is False
    assert row["feature_generation_reason"] == "fixed_lead_forecast_no_success"


def test_ensure_source_allowed_for_features_raises_for_blocked_source():
    eligibility = build_feature_source_eligibility(
        _decision_with_previous_runs_success()
    )

    assert (
        ensure_source_allowed_for_features(
            eligibility,
            "previous_runs_gfs_temperature",
        )
        == "fixed_lead_forecast_pilot_allowed"
    )

    with pytest.raises(ValueError, match="historical_weather_era5"):
        ensure_source_allowed_for_features(eligibility, "historical_weather_era5")

    with pytest.raises(ValueError, match="missing Open-Meteo source decision"):
        ensure_source_allowed_for_features(eligibility, "missing_source")


def _previous_runs_payload() -> dict[str, object]:
    return {
        "hourly": {
            "time": [
                "2024-07-15T00:00",
                "2024-07-15T10:00",
                "2024-07-15T11:00",
                "2024-07-15T23:00",
            ],
            "temperature_2m_previous_day1": [8.0, 11.0, 12.0, 16.0],
            "dew_point_2m_previous_day1": [5.0, 7.0, 7.0, 8.0],
            "cloud_cover_previous_day1": [70.0, 50.0, 40.0, 20.0],
            "cloud_cover_low_previous_day1": [80.0, 60.0, 30.0, 10.0],
            "pressure_msl_previous_day1": [1018.0, 1017.0, 1016.0, 1014.0],
            "wind_speed_10m_previous_day1": [8.0, 12.0, 14.0, 20.0],
            "wind_gusts_10m_previous_day1": [12.0, 18.0, 22.0, 30.0],
            "wind_direction_10m_previous_day1": [300.0, 315.0, 330.0, 340.0],
        }
    }


def test_build_previous_runs_feature_rows_extracts_day1_physical_features():
    rows = build_previous_runs_feature_rows(
        payload=_previous_runs_payload(),
        source_id="previous_runs_gfs_temperature",
        endpoint="previous_runs",
        model="gfs_seamless",
        date_local=dt.date(2024, 7, 15),
        cps=["23:00"],
        request_url_sha256="request-hash",
        response_sha256="response-hash",
    )

    assert rows.height == 1
    row = rows.row(0, named=True)
    assert row["date_local"] == dt.date(2024, 7, 15)
    assert row["cp"] == "23:00"
    assert row["om_source_id"] == "previous_runs_gfs_temperature"
    assert row["om_endpoint"] == "previous_runs"
    assert row["om_model"] == "gfs_seamless"
    assert row["om_causal_class"] == "fixed_lead_forecast"
    assert row["om_feature_status"] == "fixed_lead_forecast_pilot_allowed"
    assert row["om_fixed_lead_days"] == 1
    assert row["om_fixed_lead_hours"] == 24
    assert row["om_prev_d1_temp_23_local_c"] == 16.0
    assert row["om_prev_d1_temp_cp_c"] == 12.0
    assert row["om_prev_d1_remaining_warming_c"] == 4.0
    assert row["om_prev_d1_day_max_c"] == 16.0
    assert row["om_prev_d1_day_min_c"] == 8.0
    assert row["om_prev_d1_cloud_cover_mean_pct"] == 45.0
    assert row["om_prev_d1_cloud_cover_low_mean_pct"] == 45.0
    assert row["om_prev_d1_pressure_msl_mean_hpa"] == 1016.25
    assert row["om_prev_d1_wind_speed_10m_mean"] == 13.5
    assert row["om_prev_d1_wind_gusts_10m_max"] == 30.0
    assert 320.0 < row["om_prev_d1_wind_dir_10m_circular_mean"] < 325.0
    assert row["om_prev_d1_dewpoint_depression_23_local_c"] == 8.0
    assert row["om_prev_d1_foehn_support"] > 0
    assert row["om_prev_d1_stratus_support"] > 0
    assert row["om_request_url_sha256"] == "request-hash"
    assert row["om_response_sha256"] == "response-hash"
    assert row["production_status"] == PRODUCTION_STATUS


def test_build_previous_runs_feature_rows_uses_cp_local_hour():
    rows = build_previous_runs_feature_rows(
        payload=_previous_runs_payload(),
        source_id="previous_runs_gfs_temperature",
        endpoint="previous_runs",
        model="gfs_seamless",
        date_local=dt.date(2024, 7, 15),
        cps=["22:00", "23:00"],
        request_url_sha256="request-hash",
        response_sha256="response-hash",
    )

    by_cp = {row["cp"]: row for row in rows.iter_rows(named=True)}

    assert by_cp["22:00"]["om_prev_d1_temp_cp_c"] == 11.0
    assert by_cp["22:00"]["om_prev_d1_remaining_warming_c"] == 5.0
    assert by_cp["23:00"]["om_prev_d1_temp_cp_c"] == 12.0
    assert by_cp["23:00"]["om_prev_d1_remaining_warming_c"] == 4.0


def _raw_previous_runs_frame() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "date_local": dt.date(2024, 7, 15),
                "request_url_sha256": "request-hash",
                "response_sha256": "response-hash",
                "response_text": json.dumps(_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )


class FakeRawClient:
    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?fake=raw",
            status_code=200,
            text=json.dumps(_previous_runs_payload()),
        )


def test_build_open_meteo_feature_artifacts_writes_only_allowed_sources():
    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=_raw_previous_runs_frame(),
        decision_update=_decision_with_previous_runs_success(),
        cps=["22:00", "23:00"],
    )

    features = artifacts["open_meteo_features_v1"]
    manifest = artifacts["open_meteo_feature_manifest_v1"]
    coverage = artifacts["open_meteo_feature_coverage_v1"]

    assert features.height == 2
    assert set(features["cp"].to_list()) == {"22:00", "23:00"}
    assert features["date_local"].n_unique() == 1
    assert set(features["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert all(
        column in {"date_local", "cp"}
        or column.startswith("om_")
        or column == "production_status"
        for column in features.columns
    )
    assert manifest.height > 0
    assert set(manifest["feature_source"].to_list()) == {
        "open_meteo_previous_runs"
    }
    assert coverage.row(0, named=True)["n_feature_rows"] == 2


def test_build_raw_response_cache_fetches_allowed_previous_runs_payload():
    probe_plan = pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "endpoint_url": "https://previous-runs-api.open-meteo.com/v1/forecast",
                "model": "gfs_seamless",
                "date_local": dt.date(2024, 7, 15),
                "request_params_json": json.dumps({"latitude": -41.3272}),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )

    raw = build_raw_response_cache(
        probe_plan=probe_plan,
        eligibility=build_feature_source_eligibility(
            _decision_with_previous_runs_success()
        ),
        client=FakeRawClient(),
    )

    assert raw.height == 1
    row = raw.row(0, named=True)
    assert row["source_id"] == "previous_runs_gfs_temperature"
    assert row["success"] is True
    assert row["status_code"] == 200
    assert row["response_text"] == json.dumps(_previous_runs_payload())
    assert len(row["request_url_sha256"]) == 64
    assert len(row["response_sha256"]) == 64
    assert row["production_status"] == PRODUCTION_STATUS


def test_build_raw_response_cache_skips_blocked_sources():
    probe_plan = pl.DataFrame(
        [
            {
                "source_id": "historical_weather_era5",
                "endpoint": "historical_weather",
                "endpoint_url": "https://archive-api.open-meteo.com/v1/archive",
                "model": "era5",
                "date_local": dt.date(2024, 7, 15),
                "request_params_json": json.dumps({"latitude": -41.3272}),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )

    raw = build_raw_response_cache(
        probe_plan=probe_plan,
        eligibility=build_feature_source_eligibility(
            _decision_with_previous_runs_success()
        ),
        client=FakeRawClient(),
    )

    assert raw.height == 0


def test_build_open_meteo_feature_artifacts_rejects_blocked_sources_even_with_payload():
    raw = _raw_previous_runs_frame().with_columns(
        pl.lit("historical_weather_era5").alias("source_id"),
        pl.lit("historical_weather").alias("endpoint"),
        pl.lit("era5").alias("model"),
    )

    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=raw,
        decision_update=_decision_with_previous_runs_success(),
        cps=["23:00"],
    )

    assert artifacts["open_meteo_features_v1"].height == 0
    blocked = artifacts["open_meteo_feature_blocked_sources_v1"]
    assert blocked.height == 1
    assert blocked.row(0, named=True)["source_id"] == "historical_weather_era5"


def test_build_open_meteo_feature_artifacts_rejects_duplicate_keys():
    duplicated = pl.concat([_raw_previous_runs_frame(), _raw_previous_runs_frame()])

    with pytest.raises(ValueError, match="duplicate Open-Meteo feature keys"):
        build_open_meteo_feature_artifacts(
            raw_responses=duplicated,
            decision_update=_decision_with_previous_runs_success(),
            cps=["23:00"],
        )


def test_write_open_meteo_feature_artifacts_writes_parquet_and_report_without_overwriting_local_features(
    tmp_path: Path,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    local_features = data_dir / "features.parquet"
    local_features.write_text("do not touch", encoding="utf-8")

    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=_raw_previous_runs_frame(),
        decision_update=_decision_with_previous_runs_success(),
        cps=["23:00"],
    )
    paths = write_open_meteo_feature_artifacts(
        artifacts,
        data_dir=data_dir,
        output_dir=tmp_path / "reports",
        today=dt.date(2026, 6, 10),
    )

    assert paths["open_meteo_features_parquet"] == (
        data_dir / "open_meteo_features.parquet"
    )
    assert paths["open_meteo_features_parquet"].exists()
    assert local_features.read_text(encoding="utf-8") == "do not touch"
    for key, filename in OPEN_METEO_FEATURE_FILENAMES.items():
        assert paths[key] == tmp_path / "reports" / filename
        assert paths[key].exists()
    report = paths["open_meteo_feature_report_md"].read_text(encoding="utf-8")
    assert "Historical Weather and Historical Forecast remain blocked" in report
    assert "EXPERIMENT_ONLY" in report
