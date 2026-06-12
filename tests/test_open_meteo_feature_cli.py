from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

import solarstorm.__main__ as cli
from solarstorm.__main__ import app
from solarstorm.open_meteo import PRODUCTION_STATUS
from solarstorm.open_meteo._client import OpenMeteoResponse
from tests.test_open_meteo_features import (
    _decision_with_previous_runs_success,
    _previous_runs_payload,
)

runner = CliRunner()


class FakeOpenMeteoClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def get(self, base_url: str, params: dict[str, object]) -> OpenMeteoResponse:
        return OpenMeteoResponse.from_text(
            request_url=f"{base_url}?fake=fetch",
            status_code=200,
            text=json.dumps(_previous_runs_payload()),
        )


def test_open_meteo_fetch_cli_writes_raw_response_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(cli, "OpenMeteoClient", FakeOpenMeteoClient)
    decision_path = tmp_path / "decision.csv"
    _decision_with_previous_runs_success().write_csv(decision_path)
    output_path = tmp_path / "raw.csv"

    result = runner.invoke(
        app,
        [
            "open-meteo-fetch",
            "--decision-path",
            str(decision_path),
            "--output-path",
            str(output_path),
            "--years",
            "2024",
            "--cps",
            "23:00",
            "--month-days",
            "7-15",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo raw response cache complete." in result.stdout
    raw = pl.read_csv(output_path, try_parse_dates=True)
    assert raw.height == 1
    row = raw.row(0, named=True)
    assert row["source_id"] == "previous_runs_gfs_temperature"
    assert row["success"] is True
    assert row["response_text"] == json.dumps(_previous_runs_payload())


def test_open_meteo_build_features_cli_writes_feature_artifacts(tmp_path: Path):
    decision_path = tmp_path / "decision.csv"
    raw_path = tmp_path / "raw.csv"
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "reports"
    _decision_with_previous_runs_success().write_csv(decision_path)
    pl.DataFrame(
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
    ).write_csv(raw_path)
    data_dir.mkdir()
    (data_dir / "features.parquet").write_text("local", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "open-meteo-build-features",
            "--raw-responses-path",
            str(raw_path),
            "--decision-path",
            str(decision_path),
            "--data-dir",
            str(data_dir),
            "--output-dir",
            str(output_dir),
            "--cps",
            "22:00,23:00",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo feature build complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    features_path = data_dir / "open_meteo_features.parquet"
    assert features_path.exists()
    assert (data_dir / "features.parquet").read_text(encoding="utf-8") == "local"
    features = pl.read_parquet(features_path)
    assert features.height == 2
    assert set(features["cp"].to_list()) == {"22:00", "23:00"}
    assert (output_dir / "open_meteo_feature_report_v1.md").exists()


def test_open_meteo_build_features_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-build-features",
            "--raw-responses-path",
            str(tmp_path / "missing.csv"),
            "--decision-path",
            str(tmp_path / "missing-decision.csv"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
