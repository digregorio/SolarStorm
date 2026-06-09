from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_v23_calm_feature_hypotheses import (
    build_regime_calm_radiative_feature_hypotheses,
    write_regime_calm_radiative_feature_hypotheses_artifacts,
)

runner = CliRunner()


def _assignments() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(7):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=idx)
        if idx == 6:
            day = dt.date(2026, 1, 1)
        rows.append(
            {
                "candidate_version": "v2.2",
                "date_local": day,
                "cp": "20:00",
                "macro_regime_label": "macro_calm_radiative",
                "candidate_regime_label": "macro_calm_radiative",
                "production_status": "NOT_PRODUCTION",
            }
        )
    rows.append(
        {
            "candidate_version": "v2.2",
            "date_local": dt.date(2025, 1, 8),
            "cp": "20:00",
            "macro_regime_label": "macro_nw_continuum",
            "candidate_regime_label": "macro_nw_continuum",
            "production_status": "NOT_PRODUCTION",
        }
    )
    return pl.DataFrame(rows)


def _features() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(7):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=idx)
        if idx == 6:
            day = dt.date(2026, 1, 1)
        rows.append(
            {
                "date_local": day,
                "cp": "20:00",
                "cloud_base_transparency": float(idx + 1),
                "nocturnal_plateau_flag": 1,
            }
        )
    rows.append(
        {
            "date_local": dt.date(2025, 1, 8),
            "cp": "20:00",
            "cloud_base_transparency": 99.0,
            "nocturnal_plateau_flag": 0,
        }
    )
    return pl.DataFrame(rows)


def _labels() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(7):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=idx)
        if idx == 6:
            day = dt.date(2026, 1, 1)
        rows.append(
            {
                "date_local": day,
                "day_complete": True,
                "tmax_int": 20 + idx,
                "tmax_hour": 13,
                "k_cp__cp_2000": 19,
            }
        )
    rows.append(
        {
            "date_local": dt.date(2025, 1, 8),
            "day_complete": True,
            "tmax_int": 30,
            "tmax_hour": 17,
            "k_cp__cp_2000": 20,
        }
    )
    return pl.DataFrame(rows)


def test_calm_feature_hypotheses_screen_causal_features_train_only():
    artifacts = build_regime_calm_radiative_feature_hypotheses(
        assignments=_assignments(),
        features=_features(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        candidate_features=(
            "cloud_base_transparency",
            "nocturnal_plateau_flag",
            "remaining_warming",
        ),
        min_rows=5,
        min_abs_corr=0.7,
    )

    results = artifacts["regime_calm_radiative_feature_hypotheses_v1"]
    signal = results.filter(
        pl.col("feature_column") == "cloud_base_transparency"
    ).row(0, named=True)
    constant = results.filter(
        pl.col("feature_column") == "nocturnal_plateau_flag"
    ).row(0, named=True)
    blocked = results.filter(pl.col("feature_column") == "remaining_warming").row(
        0,
        named=True,
    )

    assert signal["experiment_id"] == "CEXP-CALM-RADIATIVE-002"
    assert signal["n_rows"] == 6
    assert signal["date_window_end"] == "2025-01-06"
    assert signal["pearson_corr"] > 0.99
    assert signal["ols_slope"] > 0.9
    assert signal["causal_role"] == "CAUSAL_CANDIDATE_SCREEN"
    assert signal["recommended_disposition"] == "CANDIDATE_SIGNAL"
    assert signal["production_status"] == "EXPERIMENT_ONLY"

    assert constant["variance_status"] == "CONSTANT"
    assert constant["recommended_disposition"] == "CONSTANT_FEATURE"

    assert blocked["leakage_class"] == "excluded_outcome"
    assert blocked["causal_role"] == "FULL_DAY_TARGET_OR_PROXY_AUDIT_ONLY"
    assert blocked["recommended_disposition"] == "BLOCKED_LEAKAGE_FEATURE"


def test_calm_feature_hypotheses_blocks_any_tmax_proxy_feature():
    artifacts = build_regime_calm_radiative_feature_hypotheses(
        assignments=_assignments(),
        features=_features().with_columns(
            pl.col("cloud_base_transparency").alias("tmax_hour_bucket")
        ),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        candidate_features=("tmax_hour_bucket",),
        min_rows=5,
    )

    blocked = artifacts["regime_calm_radiative_feature_hypotheses_v1"].row(
        0,
        named=True,
    )

    assert blocked["leakage_class"] == "excluded_outcome"
    assert blocked["causal_role"] == "FULL_DAY_TARGET_OR_PROXY_AUDIT_ONLY"
    assert blocked["recommended_disposition"] == "BLOCKED_LEAKAGE_FEATURE"


def test_calm_feature_hypotheses_target_mean_uses_feature_valid_rows():
    features = _features().with_columns(
        pl.when(pl.col("date_local") == dt.date(2025, 1, 1))
        .then(None)
        .otherwise(pl.col("cloud_base_transparency"))
        .alias("cloud_base_transparency")
    )

    artifacts = build_regime_calm_radiative_feature_hypotheses(
        assignments=_assignments(),
        features=features,
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        candidate_features=("cloud_base_transparency",),
        min_rows=5,
    )

    signal = artifacts["regime_calm_radiative_feature_hypotheses_v1"].row(
        0,
        named=True,
    )

    assert signal["n_rows"] == 5
    assert signal["remaining_warming_mean"] == 4.0


def test_calm_feature_hypotheses_writer_outputs_csv_and_markdown(tmp_path: Path):
    artifacts = build_regime_calm_radiative_feature_hypotheses(
        assignments=_assignments(),
        features=_features(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        candidate_features=("cloud_base_transparency",),
        min_rows=5,
    )

    paths = write_regime_calm_radiative_feature_hypotheses_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (
        tmp_path / "regime_calm_radiative_feature_hypotheses_v1.csv"
    ).exists()
    assert (
        tmp_path / "regime_calm_radiative_feature_hypotheses_v1.md"
    ).exists()
    report = paths["regime_calm_radiative_feature_hypotheses_md"].read_text(
        encoding="utf-8"
    )
    assert "CEXP-CALM-RADIATIVE-002 Feature Hypotheses - 2026-06-08" in report
    assert "CAUSAL_CANDIDATE_SCREEN" in report
    assert "not a production classifier" in report


def test_calm_feature_hypotheses_cli_writes_artifacts(tmp_path: Path):
    assignments_path = tmp_path / "regime_candidate_assignments_v2_2.csv"
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    output_dir = tmp_path / "regime-design"
    _assignments().write_csv(assignments_path)
    _features().write_parquet(features_path)
    _labels().write_parquet(labels_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v23-calm-feature-hypotheses",
            "--assignments-v22-path",
            str(assignments_path),
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(output_dir),
            "--train-end",
            "2025-12-31",
            "--candidate-features",
            "cloud_base_transparency,nocturnal_plateau_flag",
            "--min-rows",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        output_dir / "regime_calm_radiative_feature_hypotheses_v1.csv"
    ).exists()
    assert "CEXP-CALM-RADIATIVE-002" in result.output
