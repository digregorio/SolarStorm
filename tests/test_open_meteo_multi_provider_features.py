from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
import pytest

from solarstorm.open_meteo import (
    MULTI_PROVIDER_FEATURE_FILENAMES,
    PRODUCTION_STATUS,
    build_multi_provider_backfill_feasibility,
    build_multi_provider_feature_artifacts,
    build_multi_provider_previous_runs_features,
    build_multi_provider_probe_plan,
    build_multi_provider_raw_response_cache,
    select_multi_provider_feature_sources,
    write_multi_provider_feature_artifacts,
)
from solarstorm.open_meteo._client import OpenMeteoResponse
from tests.test_open_meteo_features import _previous_runs_payload


def _provider_decisions() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "provider": "NOAA",
                "provider_family": "NOAA_GFS",
                "decision_status": "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "feature_gate_scope": "fixed_lead_provider_error_atlas",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "endpoint": "previous_runs",
                "model": "ecmwf_ifs025",
                "provider": "ECMWF",
                "provider_family": "ECMWF_IFS",
                "decision_status": "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS",
                "feature_gate_scope": "fixed_lead_provider_error_atlas",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "endpoint": "single_runs",
                "model": "gfs_seamless",
                "provider": "NOAA",
                "provider_family": "NOAA_GFS",
                "decision_status": "OPEN_METEO_PROVIDER_BLOCKED_BY_REQUEST_CONTRACT",
                "feature_gate_scope": "single_runs_request_contract_not_proven",
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )


def _raw_cache(*, models: list[str] | None = None) -> pl.DataFrame:
    rows = []
    provider_by_model = {
        "gfs_seamless": ("NOAA", "NOAA_GFS"),
        "ecmwf_ifs025": ("ECMWF", "ECMWF_IFS"),
    }
    for model in models or ["gfs_seamless", "ecmwf_ifs025"]:
        provider, family = provider_by_model[model]
        rows.append(
            {
                "endpoint": "previous_runs",
                "model": model,
                "provider": provider,
                "provider_family": family,
                "date_local": dt.date(2024, 7, 15),
                "success": True,
                "status_code": 200,
                "request_url_sha256": f"{model}-request-hash",
                "response_sha256": f"{model}-response-hash",
                "response_text": json.dumps(_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _multi_day_previous_runs_payload() -> dict[str, object]:
    first = _previous_runs_payload()["hourly"]
    assert isinstance(first, dict)
    second = {
        key: list(value) if isinstance(value, list) else value
        for key, value in first.items()
    }
    second["time"] = [
        str(value).replace("2024-07-15", "2024-07-16")
        for value in second["time"]
    ]
    second["temperature_2m_previous_day1"] = [value + 1 for value in second["temperature_2m_previous_day1"]]
    hourly = {}
    for key, value in first.items():
        if isinstance(value, list):
            hourly[key] = [*value, *second[key]]
        else:
            hourly[key] = value
    return {"hourly": hourly}


def _range_raw_cache() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "provider": "NOAA",
                "provider_family": "NOAA_GFS",
                "date_local": dt.date(2024, 7, 15),
                "start_date": dt.date(2024, 7, 15),
                "end_date": dt.date(2024, 7, 16),
                "success": True,
                "status_code": 200,
                "request_url_sha256": "gfs-range-request-hash",
                "response_sha256": "gfs-range-response-hash",
                "response_text": json.dumps(_multi_day_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def test_select_multi_provider_feature_sources_uses_ready_previous_runs_only():
    selected = select_multi_provider_feature_sources(_provider_decisions())

    assert selected.select("endpoint").to_series().to_list() == [
        "previous_runs",
        "previous_runs",
    ]
    assert set(selected["model"].to_list()) == {"gfs_seamless", "ecmwf_ifs025"}
    assert set(selected["provider_family"].to_list()) == {"NOAA_GFS", "ECMWF_IFS"}
    assert set(selected["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_multi_provider_features_are_long_provider_keyed():
    features = build_multi_provider_previous_runs_features(
        cache=_raw_cache(),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15)],
        cps=["22:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    assert features.height == 4
    assert {
        "date_local",
        "cp",
        "endpoint",
        "model",
        "provider",
        "provider_family",
        "om_provider_tmax_pred_c",
        "om_provider_run_time_utc",
        "om_provider_available_time_utc",
        "om_provider_lead_hours",
        "request_url_sha256",
        "response_sha256",
        "source_decision_status",
        "production_status",
    }.issubset(features.columns)
    assert features.select(["date_local", "cp", "endpoint", "model"]).is_duplicated().sum() == 0
    assert set(features["endpoint"].to_list()) == {"previous_runs"}
    assert set(features["model"].to_list()) == {"gfs_seamless", "ecmwf_ifs025"}
    assert set(features["provider_family"].to_list()) == {"NOAA_GFS", "ECMWF_IFS"}
    assert set(features["om_provider_tmax_pred_c"].to_list()) == {16.0}
    assert set(features["om_provider_lead_hours"].to_list()) == {24}
    assert set(features["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_multi_provider_features_split_multi_day_previous_runs_payload():
    features = build_multi_provider_previous_runs_features(
        cache=_range_raw_cache(),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15), dt.date(2024, 7, 16)],
        cps=["23:00"],
        models=["gfs_seamless"],
    )

    by_date = {row["date_local"]: row for row in features.iter_rows(named=True)}

    assert features.height == 2
    assert by_date[dt.date(2024, 7, 15)]["om_provider_tmax_pred_c"] == 16.0
    assert by_date[dt.date(2024, 7, 16)]["om_provider_tmax_pred_c"] == 17.0
    assert set(features["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_multi_provider_features_reject_duplicate_provider_keys():
    duplicated = pl.concat([_raw_cache(models=["gfs_seamless"]), _raw_cache(models=["gfs_seamless"])])

    with pytest.raises(ValueError, match="duplicate Open-Meteo multi-provider feature keys"):
        build_multi_provider_previous_runs_features(
            cache=duplicated,
            provider_decision_update=_provider_decisions(),
            dates=[dt.date(2024, 7, 15)],
            cps=["23:00"],
            models=["gfs_seamless"],
        )


class FakeProviderClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        self.calls.append(dict(params))
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?model={params['models']}",
            status_code=200,
            text=json.dumps(_previous_runs_payload()),
        )


class FlakyProviderClient:
    def __init__(self) -> None:
        self.calls = 0

    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        self.calls += 1
        if self.calls == 2:
            raise TimeoutError("window timed out")
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?model={params['models']}",
            status_code=200,
            text=json.dumps(_previous_runs_payload()),
        )


def test_multi_provider_raw_cache_fetches_once_per_date_model_not_per_cp():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless"],
        endpoints=["previous_runs"],
    )
    client = FakeProviderClient()

    raw = build_multi_provider_raw_response_cache(
        probe_plan=plan,
        provider_decision_update=_provider_decisions(),
        client=client,
    )

    assert raw.height == 1
    assert len(client.calls) == 1
    row = raw.row(0, named=True)
    assert row["model"] == "gfs_seamless"
    assert row["success"] is True
    assert row["production_status"] == PRODUCTION_STATUS


def test_multi_provider_raw_cache_fetches_date_windows():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15), dt.date(2024, 7, 16), dt.date(2024, 7, 17)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless"],
        endpoints=["previous_runs"],
    )
    client = FakeProviderClient()

    raw = build_multi_provider_raw_response_cache(
        probe_plan=plan,
        provider_decision_update=_provider_decisions(),
        client=client,
        window_days=2,
    )

    assert raw.height == 2
    assert len(client.calls) == 2
    assert client.calls[0]["start_date"] == "2024-07-15"
    assert client.calls[0]["end_date"] == "2024-07-16"
    assert client.calls[1]["start_date"] == "2024-07-17"
    assert client.calls[1]["end_date"] == "2024-07-17"


def test_multi_provider_raw_cache_records_failed_windows_and_continues():
    plan = build_multi_provider_probe_plan(
        dates=[dt.date(2024, 7, 15), dt.date(2024, 7, 16), dt.date(2024, 7, 17)],
        cps=["20:00", "23:00"],
        models=["gfs_seamless"],
        endpoints=["previous_runs"],
    )
    client = FlakyProviderClient()

    raw = build_multi_provider_raw_response_cache(
        probe_plan=plan,
        provider_decision_update=_provider_decisions(),
        client=client,
        window_days=1,
    )

    assert raw.height == 3
    assert raw.filter(pl.col("success")).height == 2
    failed = raw.filter(~pl.col("success")).row(0, named=True)
    assert failed["error"] == "TimeoutError"
    assert failed["response_text"] == ""
    assert failed["production_status"] == PRODUCTION_STATUS


def test_multi_provider_feature_artifacts_report_family_overlap():
    artifacts = build_multi_provider_feature_artifacts(
        raw_responses=_raw_cache(),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15)],
        cps=["22:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    coverage = artifacts["open_meteo_multi_provider_feature_coverage_v1"].row(
        0,
        named=True,
    )
    decision = artifacts["open_meteo_multi_provider_feature_decision_v1"].row(
        0,
        named=True,
    )

    assert coverage["n_feature_rows"] == 4
    assert coverage["n_provider_families"] == 2
    assert decision["decision_status"] == "OPEN_METEO_MULTI_PROVIDER_FEATURES_READY"
    assert decision["production_status"] == PRODUCTION_STATUS


def test_multi_provider_feature_artifacts_block_single_family_overlap():
    artifacts = build_multi_provider_feature_artifacts(
        raw_responses=_raw_cache(models=["gfs_seamless"]),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15)],
        cps=["23:00"],
        models=["gfs_seamless"],
    )

    decision = artifacts["open_meteo_multi_provider_feature_decision_v1"].row(
        0,
        named=True,
    )

    assert decision["decision_status"] == "BLOCK_MULTI_PROVIDER_FEATURES_BY_COVERAGE"
    assert decision["n_overlapping_provider_families"] == 1
    assert decision["production_status"] == PRODUCTION_STATUS


def test_backfill_feasibility_reports_missing_provider_years():
    features = build_multi_provider_previous_runs_features(
        cache=_raw_cache(),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15)],
        cps=["22:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    report = build_multi_provider_backfill_feasibility(
        provider_features=features,
        provider_decision_update=_provider_decisions(),
        requested_start=dt.date(2022, 1, 1),
        requested_end=dt.date(2024, 12, 31),
        cps=["22:00", "23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    row_2022 = report.filter(
        (pl.col("year") == 2022)
        & (pl.col("cp") == "22:00")
        & (pl.col("model") == "gfs_seamless")
    ).row(0, named=True)
    row_2024 = report.filter(
        (pl.col("year") == 2024)
        & (pl.col("cp") == "22:00")
        & (pl.col("model") == "gfs_seamless")
    ).row(0, named=True)

    assert "coverage_status" in report.columns
    assert row_2022["coverage_status"] == "READY_FOR_BACKFILL"
    assert row_2022["observed_dates"] == 0
    assert row_2022["missing_dates"] == 365
    assert row_2024["coverage_status"] == "PARTIAL_BACKFILL_WITH_GAPS"
    assert row_2024["observed_dates"] == 1
    assert set(report["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_write_multi_provider_feature_artifacts_writes_parquet_without_overwriting_local_features(
    tmp_path: Path,
):
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    local_features = tmp_path / "data" / "features.parquet"
    local_features.parent.mkdir()
    local_features.write_text("do not touch", encoding="utf-8")
    artifacts = build_multi_provider_feature_artifacts(
        raw_responses=_raw_cache(),
        provider_decision_update=_provider_decisions(),
        dates=[dt.date(2024, 7, 15)],
        cps=["23:00"],
        models=["gfs_seamless", "ecmwf_ifs025"],
    )

    paths = write_multi_provider_feature_artifacts(
        artifacts,
        output_features_path=output_features,
        output_dir=tmp_path / "reports",
        today=dt.date(2026, 6, 10),
    )

    assert paths["open_meteo_multi_provider_features_parquet"] == output_features
    assert output_features.exists()
    assert local_features.read_text(encoding="utf-8") == "do not touch"
    for key, filename in MULTI_PROVIDER_FEATURE_FILENAMES.items():
        assert paths[key] == tmp_path / "reports" / filename
        assert paths[key].exists()
    report = paths["open_meteo_multi_provider_feature_report_md"].read_text(
        encoding="utf-8"
    )
    assert "provider-family overlap" in report
    assert "EXPERIMENT_ONLY" in report
