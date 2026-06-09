"""Tests for the Onda 4 robustness CLI."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app

runner = CliRunner()


def _write_minimal_artifacts(base: Path) -> tuple[Path, Path, Path]:
    rng = np.random.default_rng(42)
    dates = [dt.date(2018, 1, 1) + dt.timedelta(days=i) for i in range(365 * 7)]
    tmax = np.round(20 + 8 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)).astype(int)
    remaining = rng.normal(0, 3, len(dates))
    remaining -= remaining.mean()
    remaining_i = np.round(remaining).astype(int)
    signal = remaining_i.astype(float) + rng.normal(0, 0.1, len(dates))

    labels_rows = []
    features_rows = []
    for i, d in enumerate(dates):
        label_row = {
            "date_local": d,
            "tmax_int": int(tmax[i]),
            "day_complete": True,
            "tmax_hour": 14,
        }
        for cp in ("20:00",):
            label_row[f"k_cp__cp_{cp.replace(':', '')}"] = int(tmax[i] - remaining_i[i])
            features_rows.append(
                {
                    "date_local": d,
                    "cp": cp,
                    "regime_label": "calm_radiative",
                    "feat_signal": float(signal[i]),
                }
            )
        labels_rows.append(label_row)

    features_path = base / "features.parquet"
    labels_path = base / "labels.parquet"
    pl.DataFrame(features_rows).write_parquet(features_path)
    pl.DataFrame(labels_rows).write_parquet(labels_path)

    report_dir = base / "reports" / "2026-06-05"
    report_dir.mkdir(parents=True)
    contract_path = report_dir / "validated_feature_contract.json"
    contract = {
        "validated_features": [
            {
                "id": "H_SIG",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "regime": "all",
                "effect_size": 0.5,
                "ci_lo": 0.1,
                "ci_hi": 0.9,
                "p_value": 0.001,
                "best_null_name": "L0_persistence",
                "best_null_mae": 2.0,
            }
        ]
    }
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    return features_path, labels_path, contract_path


def test_robustness_help_lists_command():
    result = runner.invoke(app, ["robustness", "--help"])

    assert result.exit_code == 0
    assert "robustness" in result.stdout.lower()


def test_robustness_command_uses_latest_contract_and_writes_artifacts(tmp_path: Path):
    features_path, labels_path, _contract_path = _write_minimal_artifacts(tmp_path)
    output_dir = tmp_path / "out"

    with patch("solarstorm.__main__.REPORTS_DIR", tmp_path / "reports"):
        result = runner.invoke(
            app,
            [
                "robustness",
                "--features-path",
                str(features_path),
                "--labels-path",
                str(labels_path),
                "--output-dir",
                str(output_dir),
                "--test-years",
                "2024",
            ],
        )

    assert result.exit_code in (0, 1)
    assert list(output_dir.glob("*-robustness-report.md"))
    assert (output_dir / "robustness_drift_snapshot.json").exists()
    assert (output_dir / "late_spike_candidates.json").exists()


def test_robustness_command_accepts_short_option_aliases(tmp_path: Path):
    features_path, labels_path, _contract_path = _write_minimal_artifacts(tmp_path)
    output_dir = tmp_path / "short-alias-out"

    with patch("solarstorm.__main__.REPORTS_DIR", tmp_path / "reports"):
        result = runner.invoke(
            app,
            [
                "robustness",
                "--features",
                str(features_path),
                "--labels",
                str(labels_path),
                "--output",
                str(output_dir),
                "--test-years",
                "2024",
            ],
        )

    assert result.exit_code in (0, 1)
    assert list(output_dir.glob("*-robustness-report.md"))


def test_robustness_command_accepts_candidate_regime_set(tmp_path: Path):
    features_path, labels_path, _contract_path = _write_minimal_artifacts(tmp_path)
    output_dir = tmp_path / "candidate-regime-out"
    features = pl.read_parquet(features_path).with_columns(
        pl.lit("macro_nw_continuum").alias("regime_label")
    )
    features.write_parquet(features_path)

    with patch("solarstorm.__main__.REPORTS_DIR", tmp_path / "reports"):
        result = runner.invoke(
            app,
            [
                "robustness",
                "--features-path",
                str(features_path),
                "--labels-path",
                str(labels_path),
                "--output-dir",
                str(output_dir),
                "--test-years",
                "2024",
                "--regime-set",
                "macro_nw_continuum",
            ],
        )

    assert result.exit_code in (0, 1), result.output
    report = next(output_dir.glob("*-robustness-report.md")).read_text(
        encoding="utf-8"
    )
    assert "macro_nw_continuum" in report
    assert "calm_radiative" not in report
