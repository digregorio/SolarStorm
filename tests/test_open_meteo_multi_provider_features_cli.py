from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.open_meteo import PRODUCTION_STATUS
from tests.test_open_meteo_features import _previous_runs_payload
from tests.test_open_meteo_multi_provider_features import _provider_decisions

runner = CliRunner()


def _raw_cache(
    path: Path,
    *,
    single_family: bool = False,
    dates: list[dt.date] | None = None,
) -> None:
    rows = []
    for date_local in dates or [dt.date(2024, 7, 15)]:
        rows.append(
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "provider": "NOAA",
                "provider_family": "NOAA_GFS",
                "date_local": date_local,
                "success": True,
                "status_code": 200,
                "request_url_sha256": f"gfs-request-{date_local}",
                "response_sha256": f"gfs-response-{date_local}",
                "response_text": json.dumps(_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        )
        if not single_family:
            rows.append(
                {
                    "endpoint": "previous_runs",
                    "model": "ecmwf_ifs025",
                    "provider": "ECMWF",
                    "provider_family": "ECMWF_IFS",
                    "date_local": date_local,
                    "success": True,
                    "status_code": 200,
                    "request_url_sha256": f"ecmwf-request-{date_local}",
                    "response_sha256": f"ecmwf-response-{date_local}",
                    "response_text": json.dumps(_previous_runs_payload()),
                    "production_status": PRODUCTION_STATUS,
                }
            )
    pl.DataFrame(rows, strict=False).write_csv(path)


def test_open_meteo_build_multi_provider_features_cli_writes_artifacts(
    tmp_path: Path,
):
    raw_path = tmp_path / "raw.csv"
    decision_path = tmp_path / "decision.csv"
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    output_dir = tmp_path / "reports"
    _raw_cache(raw_path)
    _provider_decisions().write_csv(decision_path)
    output_features.parent.mkdir()
    (output_features.parent / "features.parquet").write_text(
        "local",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--raw-responses-path",
            str(raw_path),
            "--provider-decision-path",
            str(decision_path),
            "--output-features",
            str(output_features),
            "--output-dir",
            str(output_dir),
            "--dates",
            "2024-07-15",
            "--cps",
            "22:00,23:00",
            "--models",
            "gfs_seamless,ecmwf_ifs025",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo multi-provider feature build complete." in result.stdout
    assert "provider family coverage" in result.stdout
    assert "production_status: EXPERIMENT_ONLY" in result.stdout
    assert output_features.exists()
    assert (output_features.parent / "features.parquet").read_text(
        encoding="utf-8"
    ) == "local"
    assert (output_dir / "open_meteo_multi_provider_feature_report_v1.md").exists()
    features = pl.read_parquet(output_features)
    assert features.height == 4
    assert set(features["provider_family"].to_list()) == {"NOAA_GFS", "ECMWF_IFS"}


def test_open_meteo_build_multi_provider_features_cli_accepts_date_range(
    tmp_path: Path,
):
    raw_path = tmp_path / "raw.csv"
    decision_path = tmp_path / "decision.csv"
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    _raw_cache(
        raw_path,
        dates=[dt.date(2024, 7, 15), dt.date(2024, 7, 16)],
    )
    _provider_decisions().write_csv(decision_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--raw-responses-path",
            str(raw_path),
            "--provider-decision-path",
            str(decision_path),
            "--output-features",
            str(output_features),
            "--output-dir",
            str(tmp_path / "reports"),
            "--date-range",
            "2024-07-15:2024-07-16",
            "--cps",
            "22:00,23:00",
            "--models",
            "gfs_seamless,ecmwf_ifs025",
        ],
    )

    assert result.exit_code == 0
    features = pl.read_parquet(output_features)
    assert features.height == 8
    assert features["date_local"].n_unique() == 2


def test_open_meteo_build_multi_provider_features_cli_blocks_single_family(
    tmp_path: Path,
):
    raw_path = tmp_path / "raw.csv"
    decision_path = tmp_path / "decision.csv"
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    _raw_cache(raw_path, single_family=True)
    _provider_decisions().write_csv(decision_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--raw-responses-path",
            str(raw_path),
            "--provider-decision-path",
            str(decision_path),
            "--output-features",
            str(output_features),
            "--output-dir",
            str(tmp_path / "reports"),
            "--dates",
            "2024-07-15",
            "--cps",
            "23:00",
            "--models",
            "gfs_seamless",
        ],
    )

    assert result.exit_code == 3
    assert "BLOCK_MULTI_PROVIDER_FEATURES_BY_COVERAGE" in result.stdout
    assert output_features.exists()


def test_open_meteo_build_multi_provider_features_cli_dry_run_feasibility_does_not_write_features(
    tmp_path: Path,
):
    raw_path = tmp_path / "raw.csv"
    decision_path = tmp_path / "decision.csv"
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    output_dir = tmp_path / "reports"
    _raw_cache(raw_path, dates=[dt.date(2024, 7, 15)])
    _provider_decisions().write_csv(decision_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--raw-responses-path",
            str(raw_path),
            "--provider-decision-path",
            str(decision_path),
            "--output-features",
            str(output_features),
            "--output-dir",
            str(output_dir),
            "--date-range",
            "2022-01-01:2024-12-31",
            "--cps",
            "22:00,23:00",
            "--models",
            "gfs_seamless,ecmwf_ifs025",
            "--dry-run-feasibility",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo multi-provider backfill feasibility complete." in result.stdout
    assert "production_status: EXPERIMENT_ONLY" in result.stdout
    assert not output_features.exists()
    assert (output_dir / "open_meteo_backfill_feasibility_v1.csv").exists()
    assert (output_dir / "open_meteo_backfill_feasibility_report_v1.md").exists()


def test_open_meteo_build_multi_provider_features_cli_dry_run_uses_existing_feature_parquet(
    tmp_path: Path,
):
    decision_path = tmp_path / "decision.csv"
    output_features = tmp_path / "data" / "open_meteo_multi_provider_features.parquet"
    output_dir = tmp_path / "reports"
    raw_path = tmp_path / "raw.csv"
    _raw_cache(raw_path, dates=[dt.date(2024, 7, 15)])
    _provider_decisions().write_csv(decision_path)
    output_features.parent.mkdir()
    pl.read_csv(raw_path, try_parse_dates=True).write_parquet(output_features)

    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--provider-decision-path",
            str(decision_path),
            "--output-features",
            str(output_features),
            "--output-dir",
            str(output_dir),
            "--date-range",
            "2022-01-01:2024-12-31",
            "--cps",
            "22:00,23:00",
            "--models",
            "gfs_seamless,ecmwf_ifs025",
            "--dry-run-feasibility",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo multi-provider backfill feasibility complete." in result.stdout
    assert (output_dir / "open_meteo_backfill_feasibility_v1.csv").exists()


def test_open_meteo_build_multi_provider_features_cli_blocks_missing_inputs(
    tmp_path: Path,
):
    result = runner.invoke(
        app,
        [
            "open-meteo-build-multi-provider-features",
            "--raw-responses-path",
            str(tmp_path / "missing.csv"),
            "--provider-decision-path",
            str(tmp_path / "missing-decision.csv"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
