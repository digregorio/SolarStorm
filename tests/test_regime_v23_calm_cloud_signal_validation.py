from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_v23_calm_cloud_signal_validation import (
    build_regime_calm_radiative_cloud_signal_validation,
    write_regime_calm_radiative_cloud_signal_validation_artifacts,
)

runner = CliRunner()


def _assignments(n: int = 12) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(n):
        rows.append(
            {
                "candidate_version": "v2.2",
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "cp": "20:00" if idx % 2 == 0 else "21:00",
                "macro_regime_label": "macro_calm_radiative",
                "candidate_regime_label": "macro_calm_radiative",
                "production_status": "NOT_PRODUCTION",
            }
        )
    rows.append(
        {
            "candidate_version": "v2.2",
            "date_local": dt.date(2026, 1, 1),
            "cp": "20:00",
            "macro_regime_label": "macro_calm_radiative",
            "candidate_regime_label": "macro_calm_radiative",
            "production_status": "NOT_PRODUCTION",
        }
    )
    return pl.DataFrame(rows)


def _features(*, proxy_like: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(12):
        x = idx / 11
        rows.append(
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "cp": "20:00" if idx % 2 == 0 else "21:00",
                "cloud_cover_suppression": x,
                "dewpoint_depression": 2.0 + (idx % 3) * 0.1,
                "warming_rate_06_09": 0.4 + (idx % 4) * 0.05,
                "dewpoint_collapse_rate_3h": 0.1 + (idx % 2) * 0.03,
                "pressure_trend_3h": -0.2 + (idx % 5) * 0.02,
                "tmax_dminus1": x if proxy_like else float(idx % 5),
            }
        )
    rows.append(
        {
            "date_local": dt.date(2026, 1, 1),
            "cp": "20:00",
            "cloud_cover_suppression": 1.0,
            "dewpoint_depression": 2.0,
            "warming_rate_06_09": 0.5,
            "dewpoint_collapse_rate_3h": 0.1,
            "pressure_trend_3h": 0.0,
            "tmax_dminus1": 1.0,
        }
    )
    return pl.DataFrame(rows)


def _labels(*, inverted_signal: bool = False) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(12):
        x = idx / 11
        remaining = 2.0 + 3.0 * x if inverted_signal else 5.0 - 3.0 * x
        rows.append(
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=idx),
                "day_complete": True,
                "tmax_int": 20.0 + remaining,
                "k_cp__cp_2000": 20.0,
                "k_cp__cp_2100": 20.0,
            }
        )
    rows.append(
        {
            "date_local": dt.date(2026, 1, 1),
            "day_complete": True,
            "tmax_int": 30.0,
            "k_cp__cp_2000": 20.0,
            "k_cp__cp_2100": 20.0,
        }
    )
    return pl.DataFrame(rows)


def test_cloud_signal_survives_causal_robustness_screen():
    artifacts = build_regime_calm_radiative_cloud_signal_validation(
        assignments=_assignments(),
        features=_features(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        min_rows=8,
        min_cell_rows=3,
        min_abs_corr=0.2,
        min_controlled_slope_retention=0.4,
        max_proxy_abs_corr=0.9,
    )

    validation = artifacts["regime_calm_radiative_cloud_signal_validation_v1"].row(
        0,
        named=True,
    )

    assert validation["experiment_id"] == "CEXP-CALM-RADIATIVE-002B"
    assert validation["n_rows"] == 12
    assert validation["overall_slope"] < 0
    assert validation["cp_negative_slope_share"] == 1.0
    assert validation["cell_negative_slope_share"] == 1.0
    assert validation["controlled_slope"] < 0
    assert validation["controlled_slope_retention"] >= 0.4
    assert validation["lineage_status"] == "PASS_PRE_CP_CLOUD_OBSERVATION"
    assert validation["validation_decision"] == "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN"
    assert validation["next_experiment"] == "CEXP_003_NOT_TRIGGERED"
    assert validation["production_status"] == "EXPERIMENT_ONLY"
    assert "regime_calm_radiative_demote_split_v1" not in artifacts


def test_cloud_signal_failure_triggers_cexp003_demote_split_matrix():
    artifacts = build_regime_calm_radiative_cloud_signal_validation(
        assignments=_assignments(),
        features=_features(proxy_like=True),
        labels=_labels(inverted_signal=True),
        train_end=dt.date(2025, 12, 31),
        min_rows=8,
        min_cell_rows=3,
        max_proxy_abs_corr=0.5,
    )

    validation = artifacts["regime_calm_radiative_cloud_signal_validation_v1"].row(
        0,
        named=True,
    )
    matrix = artifacts["regime_calm_radiative_demote_split_v1"]

    assert validation["validation_decision"] == "FAILS_CAUSAL_ROBUSTNESS_SCREEN"
    assert validation["next_experiment"] == "CEXP_003_TRIGGERED"
    assert matrix.height == 3
    assert set(matrix["candidate_option"].to_list()) == {
        "keep_protected_macro",
        "demote_to_subtype_audit",
        "split_radiative_clear_cloudy",
    }
    preferred = matrix.filter(
        pl.col("recommended_disposition") == "PREFERRED_IF_SIGNAL_FAILS"
    ).row(0, named=True)
    assert preferred["candidate_option"] == "demote_to_subtype_audit"
    assert preferred["production_status"] == "EXPERIMENT_ONLY"


def test_cloud_signal_validation_writer_and_cli(tmp_path: Path):
    artifacts = build_regime_calm_radiative_cloud_signal_validation(
        assignments=_assignments(),
        features=_features(),
        labels=_labels(),
        train_end=dt.date(2025, 12, 31),
        min_rows=8,
        min_cell_rows=3,
        max_proxy_abs_corr=0.9,
    )
    paths = write_regime_calm_radiative_cloud_signal_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (
        tmp_path / "regime_calm_radiative_cloud_signal_validation_v1.csv"
    ).exists()
    assert (
        tmp_path / "regime_calm_radiative_cloud_signal_validation_v1.md"
    ).exists()
    report = paths["regime_calm_radiative_cloud_signal_validation_md"].read_text(
        encoding="utf-8"
    )
    assert "CEXP-CALM-RADIATIVE-002B Cloud Signal Validation - 2026-06-08" in report
    assert "not a production classifier" in report

    assignments_path = tmp_path / "assignments.csv"
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    cli_output = tmp_path / "cli"
    _assignments().write_csv(assignments_path)
    _features().write_parquet(features_path)
    _labels().write_parquet(labels_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v23-calm-cloud-validation",
            "--assignments-v22-path",
            str(assignments_path),
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--output-dir",
            str(cli_output),
            "--train-end",
            "2025-12-31",
            "--min-rows",
            "8",
            "--min-cell-rows",
            "3",
            "--max-proxy-abs-corr",
            "0.9",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        cli_output / "regime_calm_radiative_cloud_signal_validation_v1.csv"
    ).exists()
    assert "CEXP-CALM-RADIATIVE-002B" in result.output
