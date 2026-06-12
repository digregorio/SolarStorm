from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    apply_forward_row_maturity,
    build_forward_availability_audit,
    build_forward_provider_features,
    filter_forward_rows_for_nested_validation,
    validate_new_collection_key,
    write_forward_collection_artifacts,
)

runner = CliRunner()


def fixture_forecast_response() -> dict[str, object]:
    return {
        "latitude": -41.3272,
        "longitude": 174.8053,
        "generationtime_ms": 1.0,
        "hourly_units": {"time": "iso8601", "temperature_2m": "C"},
        "hourly": {
            "time": ["2026-06-12T08:00"],
            "temperature_2m": [13.4],
        },
    }


def fixture_forecast_response_text() -> str:
    return json.dumps(fixture_forecast_response(), sort_keys=True)


def fixture_settled_labels(
    target_date_local: str = "2026-06-12",
    label_settled_at_utc: str = "2026-06-13T12:00:00Z",
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "target_date_local": [target_date_local],
            "label_settled_at_utc": [label_settled_at_utc],
            "label_source": ["labels.parquet"],
        }
    )


def fixture_pending_forward_rows(target_date_local: str = "2026-06-12") -> pl.DataFrame:
    return build_forward_provider_features(
        target_date_local=target_date_local,
        cp="20:00",
        endpoint="forecast",
        model="gfs_seamless",
        run_time_utc="2026-06-11T12:00:00Z",
        available_time_utc="2026-06-11T18:10:00Z",
        retrieved_at_utc="2026-06-11T18:15:00Z",
        response=fixture_forecast_response(),
        settled_labels=pl.DataFrame(
            {"target_date_local": [], "label_settled_at_utc": []}
        ),
    )


def fixture_collection_request() -> dict[str, object]:
    return {
        "target_date_local": "2026-06-12",
        "cp": "20:00",
        "endpoint": "forecast",
        "model": "gfs_seamless",
        "run_time_utc": "2026-06-11T12:00:00Z",
        "request_url": "https://api.open-meteo.com/v1/forecast?fixture=1",
        "retrieved_at_utc": "2026-06-11T18:15:00Z",
        "http_status": 200,
    }


def fixture_forward_row(target_date_local: str, row_status: str) -> pl.DataFrame:
    rows = fixture_pending_forward_rows(target_date_local=target_date_local).with_columns(
        pl.lit(row_status).alias("row_status"),
        pl.lit("unique").alias("duplicate_key_status"),
        pl.lit("usable").alias("availability_status"),
    )
    if row_status == "mature":
        rows = rows.with_columns(
            pl.lit("2026-06-13T12:00:00Z").alias("label_settled_at_utc")
        )
    return rows


def test_future_target_rows_are_pending_until_labels_settle():
    rows = fixture_pending_forward_rows()

    assert set(rows["row_status"].to_list()) == {"pending"}
    assert rows["label_settled_at_utc"].null_count() == rows.height
    assert set(rows["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert {
        "target_date_local",
        "cp",
        "cp_utc",
        "endpoint",
        "model",
        "provider_family",
        "run_time_utc",
        "available_time_utc",
        "retrieved_at_utc",
        "valid_time_utc",
        "horizon_hours",
        "variable",
        "feature_name",
        "feature_value",
        "collection_key_sha256",
        "request_url_sha256",
        "response_sha256",
        "row_status",
        "label_settled_at_utc",
        "production_status",
    }.issubset(rows.columns)


def test_rows_available_after_cp_are_blocked_by_causality():
    rows = build_forward_provider_features(
        target_date_local="2026-06-12",
        cp="20:00",
        endpoint="forecast",
        model="gfs_seamless",
        run_time_utc="2026-06-11T18:00:00Z",
        available_time_utc="2026-06-12T08:30:00Z",
        retrieved_at_utc="2026-06-12T08:35:00Z",
        response=fixture_forecast_response(),
        settled_labels=fixture_settled_labels("2026-06-12"),
    )

    assert rows["available_time_utc"].null_count() == 0
    assert set(rows["row_status"].to_list()) == {"blocked_by_causality"}


def test_duplicate_collection_keys_are_rejected():
    existing_manifest = pl.DataFrame(
        {
            "target_date_local": ["2026-06-12"],
            "cp": ["20:00"],
            "endpoint": ["forecast"],
            "model": ["gfs_seamless"],
            "run_time_utc": ["2026-06-11T12:00:00Z"],
        }
    )

    with pytest.raises(ValueError, match="duplicate collection key"):
        validate_new_collection_key(
            existing_manifest=existing_manifest,
            target_date_local="2026-06-12",
            cp="20:00",
            endpoint="forecast",
            model="gfs_seamless",
            run_time_utc="2026-06-11T12:00:00Z",
        )


def test_raw_cache_and_normalized_rows_share_response_hash(tmp_path: Path):
    artifacts = write_forward_collection_artifacts(
        output_dir=tmp_path,
        collection_request=fixture_collection_request(),
        response_text=fixture_forecast_response_text(),
        normalized_rows=fixture_pending_forward_rows(),
    )

    raw_meta = pl.read_csv(artifacts.raw_manifest_path)
    rows = pl.read_parquet(artifacts.provider_features_path)

    assert raw_meta.row(0, named=True)["response_sha256"] == rows.row(0, named=True)[
        "response_sha256"
    ]
    assert set(raw_meta["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert set(rows["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert artifacts.report_path.exists()


def test_pending_rows_become_mature_after_labels_settle():
    pending = fixture_pending_forward_rows(target_date_local="2026-06-12")

    matured = apply_forward_row_maturity(
        pending,
        fixture_settled_labels(
            target_date_local="2026-06-12",
            label_settled_at_utc="2026-06-13T12:00:00Z",
        ),
    )

    assert set(matured["row_status"].to_list()) == {"mature"}
    assert matured["label_settled_at_utc"].null_count() == 0


def test_forward_rows_do_not_enter_nested_validation_until_mature():
    forward_rows = pl.concat(
        [
            fixture_forward_row(target_date_local="2026-06-12", row_status="mature"),
            fixture_forward_row(target_date_local="2026-06-13", row_status="pending"),
        ],
        how="diagonal_relaxed",
    )

    eligible, exclusions = filter_forward_rows_for_nested_validation(forward_rows)

    assert eligible.height == 1
    assert str(eligible.row(0, named=True)["target_date_local"]) == "2026-06-12"
    assert set(eligible["row_status"].to_list()) == {"mature"}
    assert exclusions.filter(pl.col("exclusion_reason") == "pending").height == 1


def test_availability_audit_groups_by_endpoint_model_and_horizon():
    rows = pl.DataFrame(
        {
            "endpoint": ["forecast", "forecast", "forecast"],
            "model": ["gfs_seamless", "gfs_seamless", "ecmwf_ifs025"],
            "horizon_hours": [12, 36, 12],
            "variable": ["temperature_2m", "temperature_2m", "temperature_2m"],
            "cp": ["20:00", "20:00", "21:00"],
            "target_date_local": ["2026-06-12", "2026-06-12", "2026-06-13"],
            "row_status": ["mature", "blocked_by_availability", "pending"],
            "production_status": [PRODUCTION_STATUS] * 3,
        }
    )

    audit = build_forward_availability_audit(rows)

    assert {"endpoint", "model", "horizon_hours"}.issubset(audit.columns)
    assert set(audit["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert audit.filter(pl.col("row_status") == "blocked_by_availability").height == 1


def test_open_meteo_forward_collection_cli_fixture_mode_writes_artifacts(
    tmp_path: Path,
):
    fixture_path = tmp_path / "open_meteo_forecast_fixture.json"
    fixture_path.write_text(fixture_forecast_response_text(), encoding="utf-8")
    output_dir = tmp_path / "forward"

    result = runner.invoke(
        app,
        [
            "open-meteo-forward-collection",
            "--fixture",
            str(fixture_path),
            "--target-date-local",
            "2026-06-12",
            "--cp",
            "20:00",
            "--model",
            "gfs_seamless",
            "--run-time-utc",
            "2026-06-11T12:00:00Z",
            "--available-time-utc",
            "2026-06-11T18:10:00Z",
            "--retrieved-at-utc",
            "2026-06-11T18:15:00Z",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo OM-M14 forward collection complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "open_meteo_forward_raw_manifest_v1.csv").exists()
    assert (output_dir / "open_meteo_forward_provider_features_v1.parquet").exists()
    assert (output_dir / "open_meteo_forward_maturity_audit_v1.csv").exists()
    assert (output_dir / "open_meteo_forward_causality_audit_v1.csv").exists()
    assert (output_dir / "open_meteo_forward_availability_audit_v1.csv").exists()
    assert (output_dir / "open_meteo_forward_duplicate_key_report_v1.csv").exists()
    assert (output_dir / "open_meteo_forward_collection_report_v1.md").exists()
