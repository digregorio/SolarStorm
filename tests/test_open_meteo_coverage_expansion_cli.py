from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_coverage_expansion import (
    _local_features,
    _open_meteo_features,
    _single_runs_probe_results,
)

runner = CliRunner()


def test_open_meteo_coverage_expansion_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    open_meteo_path = tmp_path / "open_meteo.parquet"
    multi_provider_path = tmp_path / "multi_provider.parquet"
    candidates_path = tmp_path / "candidates.parquet"
    single_runs_path = tmp_path / "single_runs.csv"
    output_dir = tmp_path / "coverage"

    _local_features().write_parquet(features_path)
    _open_meteo_features(start_year=2023).write_parquet(open_meteo_path)
    _open_meteo_features(start_year=2023).write_parquet(multi_provider_path)
    _open_meteo_features(start_year=2023).with_columns(
        pl.lit("om_family_recent_bias_corrected").alias("candidate_id")
    ).write_parquet(candidates_path)
    _single_runs_probe_results().write_csv(single_runs_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-coverage-expansion",
            "--features-path",
            str(features_path),
            "--open-meteo-features-path",
            str(open_meteo_path),
            "--multi-provider-features-path",
            str(multi_provider_path),
            "--calibrated-candidates-path",
            str(candidates_path),
            "--single-runs-probe-results-path",
            str(single_runs_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024,2025",
            "--train-start",
            "2022-01-01",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo coverage/fold expansion complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "open_meteo_coverage_expansion_report_v1.md").exists()
    decision = pl.read_csv(
        output_dir / "open_meteo_coverage_expansion_decision_v1.csv"
    )
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_open_meteo_coverage_expansion_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-coverage-expansion",
            "--features-path",
            str(tmp_path / "missing.parquet"),
            "--open-meteo-features-path",
            str(tmp_path / "missing-om.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
