"""Tests for the experiment-only cloud-cover suppression baseline experiment."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._cloud_cover_baseline_experiment import (
    build_cloud_cover_baseline_experiment,
    write_cloud_cover_baseline_experiment_artifacts,
)

runner = CliRunner()


def _features() -> pl.DataFrame:
    rows = []
    for year in (2023, 2024, 2025):
        for idx in range(8):
            day = dt.date(year, 1, 1) + dt.timedelta(days=idx)
            cloud = float(idx % 4)
            rows.append(
                {
                    "date_local": day,
                    "cp": "20:00",
                    "cloud_cover_suppression": cloud,
                    "k_cp__cp_2000": 20.0,
                }
            )
    return pl.DataFrame(rows)


def _labels() -> pl.DataFrame:
    rows = []
    for year in (2023, 2024, 2025):
        for idx in range(8):
            day = dt.date(year, 1, 1) + dt.timedelta(days=idx)
            cloud = float(idx % 4)
            rows.append({"date_local": day, "tmax_int": 24.0 - cloud})
    return pl.DataFrame(rows)


def test_cloud_cover_baseline_experiment_is_walk_forward_and_experiment_only():
    artifacts = build_cloud_cover_baseline_experiment(
        features=_features(),
        labels=_labels(),
        test_years=(2024, 2025),
        cp_set=("20:00",),
    )
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    assert results.height == 2
    assert set(results["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert set(results["feature_column"].to_list()) == {"cloud_cover_suppression"}
    assert results["candidate_mae"].mean() < results["baseline_mae"].mean()
    assert results.filter(pl.col("train_rows") > 0).height == 2


def test_experiment_id_is_correct():
    artifacts = build_cloud_cover_baseline_experiment(
        features=_features(),
        labels=_labels(),
        test_years=(2025,),
        cp_set=("20:00",),
    )
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    assert all(eid == "BEXP-CLOUD-COVER-SUPPRESSION-001" for eid in results["experiment_id"].to_list())


def test_missing_feature_column_raises():
    bad_features = _features().drop("cloud_cover_suppression")
    with pytest.raises(ValueError, match="missing required columns"):
        build_cloud_cover_baseline_experiment(
            features=bad_features,
            labels=_labels(),
            test_years=(2025,),
        )


def test_missing_tmax_int_raises():
    bad_labels = _labels().drop("tmax_int")
    with pytest.raises(ValueError, match="labels require"):
        build_cloud_cover_baseline_experiment(
            features=_features(),
            labels=bad_labels,
            test_years=(2025,),
        )


def test_returns_empty_when_insufficient_data():
    tiny_features = _features().head(3)
    tiny_labels = _labels().head(3)
    artifacts = build_cloud_cover_baseline_experiment(
        features=tiny_features,
        labels=tiny_labels,
        test_years=(2025,),
        min_train_rows=100,
    )
    assert artifacts["cloud_cover_baseline_experiment_v1"].height == 0


def test_cloud_cover_baseline_writer_and_cli(tmp_path: Path):
    artifacts = build_cloud_cover_baseline_experiment(
        features=_features(),
        labels=_labels(),
        test_years=(2024,),
        cp_set=("20:00",),
    )
    paths = write_cloud_cover_baseline_experiment_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )
    assert (tmp_path / "cloud_cover_baseline_experiment_v1.csv").exists()
    assert (tmp_path / "cloud_cover_baseline_experiment_v1.md").exists()
    assert "experiment-only" in paths["cloud_cover_baseline_experiment_md"].read_text(encoding="utf-8")

    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    output_dir = tmp_path / "cli"
    _features().write_parquet(features_path)
    _labels().write_parquet(labels_path)
    result = runner.invoke(
        app,
        [
            "cloud-cover-baseline-experiment",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
            "--cp-set",
            "20:00",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "cloud_cover_baseline_experiment_v1.csv").exists()
    assert "cloud_cover_suppression" in result.output
