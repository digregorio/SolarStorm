"""Experiment-only cloud-cover suppression baseline comparison.

Tests ``cloud_cover_suppression`` as a standalone baseline feature via a
walk-forward expanding-window OLS, independent of unresolved regime labels.

Every output row carries ``production_status = EXPERIMENT_ONLY``.
No full-day outcome columns may appear as model inputs; ``tmax_int`` is the
evaluation target only.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

RESULT_SCHEMA = {
    "experiment_id": pl.Utf8,
    "test_year": pl.Int64,
    "cp": pl.Utf8,
    "month": pl.Int64,
    "feature_column": pl.Utf8,
    "train_rows": pl.Int64,
    "test_rows": pl.Int64,
    "baseline_mae": pl.Float64,
    "candidate_mae": pl.Float64,
    "mae_delta": pl.Float64,
    "slope": pl.Float64,
    "intercept": pl.Float64,
    "production_status": pl.Utf8,
}


def _cp_temp_column(cp: str) -> str:
    return f"k_cp__cp_{cp.replace(':', '')}"


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    design = np.column_stack([np.ones(len(x)), x])
    result = np.linalg.lstsq(design, y, rcond=None)
    intercept, slope = result[0]
    return float(intercept), float(slope)


def _mae(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values))) if len(values) else float("nan")


def build_cloud_cover_baseline_experiment(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    test_years: tuple[int, ...] = (2024, 2025),
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    feature_column: str = "cloud_cover_suppression",
    min_train_rows: int = 8,
    min_test_rows: int = 3,
) -> dict[str, pl.DataFrame]:
    """Walk-forward OLS experiment: cloud_cover_suppression vs train-mean baseline.

    The baseline prediction for each (train) month/CP is the mean remaining
    warming from training rows.  The candidate adds a train-calibrated OLS
    slope on ``feature_column``.  Both are evaluated on the test-year rows.

    Causal rule: ``tmax_int`` from ``labels`` is the target only; it never
    enters as a predictor.  The CP temperature column (``k_cp__cp_HHMM``) is
    the anchor used to compute remaining warming.
    """
    required_features = {"date_local", "cp", feature_column}
    missing_features = required_features - set(features.columns)
    if missing_features:
        raise ValueError(f"features missing required columns: {sorted(missing_features)}")
    if {"date_local", "tmax_int"} - set(labels.columns):
        raise ValueError("labels require date_local and tmax_int")

    # The CP temperature anchor (k_cp__cp_HHMM) may be in labels or features.
    # Include all available cp anchor columns from labels in the join.
    label_cols = ["date_local", "tmax_int"] + [c for c in labels.columns if c.startswith("k_cp__cp_")]
    joined = features.join(labels.select(label_cols), on="date_local", how="inner")
    if joined.schema["date_local"] == pl.Utf8:
        joined = joined.with_columns(pl.col("date_local").str.to_date())
    joined = joined.with_columns(
        pl.col("date_local").dt.year().alias("year"),
        pl.col("date_local").dt.month().alias("month"),
    )

    rows = []
    for test_year in test_years:
        for cp in cp_set:
            cp_col = _cp_temp_column(cp)
            if cp_col not in joined.columns:
                continue
            cp_frame = joined.filter(pl.col("cp").cast(pl.Utf8) == cp)
            for month in sorted(cp_frame["month"].drop_nulls().unique().to_list()):
                train = cp_frame.filter((pl.col("year") < test_year) & (pl.col("month") == month)).drop_nulls(
                    [feature_column, "tmax_int", cp_col]
                )
                test = cp_frame.filter((pl.col("year") == test_year) & (pl.col("month") == month)).drop_nulls(
                    [feature_column, "tmax_int", cp_col]
                )
                if train.height < min_train_rows or test.height < min_test_rows:
                    continue
                x_train = train[feature_column].to_numpy().astype(float)
                y_train = (train["tmax_int"] - train[cp_col]).to_numpy().astype(float)
                intercept, slope = _ols(x_train, y_train)
                x_test = test[feature_column].to_numpy().astype(float)
                y_test = (test["tmax_int"] - test[cp_col]).to_numpy().astype(float)
                baseline_remaining = float(np.mean(y_train))
                baseline_error = baseline_remaining - y_test
                candidate_error = (intercept + slope * x_test) - y_test
                baseline_mae = _mae(baseline_error)
                candidate_mae = _mae(candidate_error)
                rows.append(
                    {
                        "experiment_id": "BEXP-CLOUD-COVER-SUPPRESSION-001",
                        "test_year": int(test_year),
                        "cp": cp,
                        "month": int(month),
                        "feature_column": feature_column,
                        "train_rows": train.height,
                        "test_rows": test.height,
                        "baseline_mae": baseline_mae,
                        "candidate_mae": candidate_mae,
                        "mae_delta": baseline_mae - candidate_mae,
                        "slope": slope,
                        "intercept": intercept,
                        "production_status": "EXPERIMENT_ONLY",
                    }
                )
    return {"cloud_cover_baseline_experiment_v1": pl.DataFrame(rows, schema=RESULT_SCHEMA, strict=False)}


def write_cloud_cover_baseline_experiment_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write cloud-cover experiment CSV and markdown summary."""
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "cloud_cover_baseline_experiment_v1.csv"
    md_path = out_dir / "cloud_cover_baseline_experiment_v1.md"
    results = artifacts["cloud_cover_baseline_experiment_v1"]
    results.write_csv(csv_path)
    mean_delta = float(results["mae_delta"].mean()) if results.height else 0.0
    positive_delta = int(results.filter(pl.col("mae_delta") > 0).height) if results.height else 0
    lines = [
        f"# Cloud Cover Baseline Experiment - {today.isoformat()}",
        "",
        "This is an experiment-only baseline comparison and not a production feature promotion.",
        "",
        f"- Rows: {results.height}",
        "- Feature: cloud_cover_suppression",
        f"- Mean MAE delta (positive = candidate beats baseline): {mean_delta:.4f}",
        f"- Cells where candidate beats baseline: {positive_delta}/{results.height}",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "cloud_cover_baseline_experiment_csv": csv_path,
        "cloud_cover_baseline_experiment_md": md_path,
    }
