from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_open_meteo_coverage_expansion_artifacts,
    write_open_meteo_coverage_expansion_artifacts,
)


def _local_features() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in [2021, 2022, 2023, 2024, 2025]:
        for day in range(1, 4):
            for cp in ["20:00", "23:00"]:
                rows.append(
                    {
                        "date_local": dt.date(year, 1, day),
                        "cp": cp,
                        "tmax_int": 15 + day,
                        "production_status": PRODUCTION_STATUS,
                    }
                )
    return pl.DataFrame(rows, strict=False)


def _open_meteo_features(start_year: int = 2023) -> pl.DataFrame:
    return _local_features().filter(pl.col("date_local").dt.year() >= start_year)


def _single_runs_probe_results() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "success": False,
                "status_code": 400,
                "error": "http_400",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "success": True,
                "status_code": 200,
                "error": "",
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )


def test_coverage_expansion_identifies_current_one_fold_and_2022_two_fold_path():
    artifacts = build_open_meteo_coverage_expansion_artifacts(
        local_features=_local_features(),
        open_meteo_features=_open_meteo_features(start_year=2023),
        multi_provider_features=_open_meteo_features(start_year=2023),
        calibrated_candidates=_open_meteo_features(start_year=2023).with_columns(
            pl.lit("om_family_recent_bias_corrected").alias("candidate_id")
        ),
        single_runs_probe_results=_single_runs_probe_results(),
        test_years=[2024, 2025],
    )

    scenario = artifacts["open_meteo_coverage_expansion_scenarios_v1"]
    current = scenario.filter(pl.col("scenario_id") == "current_strict_common_rows").row(
        0,
        named=True,
    )
    previous_runs_2022 = scenario.filter(
        pl.col("scenario_id") == "previous_runs_history_from_2022"
    ).row(0, named=True)
    decision = artifacts["open_meteo_coverage_expansion_decision_v1"].row(0, named=True)

    assert current["n_valid_outer_folds"] == 1
    assert current["meets_two_fold_gate"] is False
    assert previous_runs_2022["n_valid_outer_folds"] == 2
    assert previous_runs_2022["meets_two_fold_gate"] is True
    assert decision["decision_status"] == "COVERAGE_EXPANSION_REQUIRES_2022_HISTORY"
    assert decision["production_status"] == PRODUCTION_STATUS


def test_coverage_expansion_records_single_runs_request_contract_blocker():
    artifacts = build_open_meteo_coverage_expansion_artifacts(
        local_features=_local_features(),
        open_meteo_features=_open_meteo_features(start_year=2023),
        multi_provider_features=_open_meteo_features(start_year=2023),
        calibrated_candidates=_open_meteo_features(start_year=2023).with_columns(
            pl.lit("om_family_recent_bias_corrected").alias("candidate_id")
        ),
        single_runs_probe_results=_single_runs_probe_results(),
        test_years=[2024, 2025],
    )

    single_runs = artifacts["open_meteo_single_runs_contract_audit_v1"].row(
        0,
        named=True,
    )

    assert single_runs["endpoint"] == "single_runs"
    assert single_runs["n_success"] == 0
    assert single_runs["contract_status"] == "BLOCKED_BY_REQUEST_CONTRACT"
    assert single_runs["production_status"] == PRODUCTION_STATUS


def test_write_coverage_expansion_artifacts_creates_csvs_and_report(tmp_path: Path):
    artifacts = build_open_meteo_coverage_expansion_artifacts(
        local_features=_local_features(),
        open_meteo_features=_open_meteo_features(start_year=2023),
        multi_provider_features=_open_meteo_features(start_year=2023),
        calibrated_candidates=_open_meteo_features(start_year=2023).with_columns(
            pl.lit("om_family_recent_bias_corrected").alias("candidate_id")
        ),
        single_runs_probe_results=_single_runs_probe_results(),
        test_years=[2024, 2025],
    )

    paths = write_open_meteo_coverage_expansion_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    assert paths["open_meteo_coverage_expansion_report_md"].exists()
    report = paths["open_meteo_coverage_expansion_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Open-Meteo Coverage/Fold Expansion Report" in report
    assert "EXPERIMENT_ONLY" in report
