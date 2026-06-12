from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from statistics import median

import polars as pl

from solarstorm.onda3._pooled_iteration import normalize_pooled_cp_column
from solarstorm.open_meteo._availability import PRODUCTION_STATUS

PROVIDER_CALIBRATION_FILENAMES = {
    "open_meteo_provider_calibrated_candidates_v1": (
        "open_meteo_provider_calibrated_candidates_v1.csv"
    ),
    "open_meteo_provider_calibrated_candidate_metrics_v1": (
        "open_meteo_provider_calibrated_candidate_metrics_v1.csv"
    ),
    "open_meteo_provider_calibrated_candidate_coverage_v1": (
        "open_meteo_provider_calibrated_candidate_coverage_v1.csv"
    ),
    "open_meteo_provider_calibration_decision_v1": (
        "open_meteo_provider_calibration_decision_v1.csv"
    ),
    "open_meteo_stabilized_calibration_support_v1": (
        "open_meteo_stabilized_calibration_support_v1.csv"
    ),
}

DEFAULT_FAMILY_PRIORITY = (
    "ecmwf_ifs025",
    "ecmwf_aifs025_single",
    "icon_seamless",
    "gem_global",
    "gfs_seamless",
    "jma_seamless",
)
RAW_GFS_ID = "om_gfs_previous_runs_raw"
RAW_FAMILY_MEAN_ID = "om_family_mean_raw"
RAW_FAMILY_MEDIAN_ID = "om_family_median_raw"
INVERSE_MAE_ID = "om_family_inverse_mae_weighted"
RECENT_BIAS_ID = "om_family_recent_bias_corrected"
REGIME_BIAS_ID = "om_family_regime_bias_corrected"
MONTH_BIAS_ID = "om_family_month_bias_corrected"
SEASON_BIAS_ID = "om_family_season_bias_corrected"


def _month_bucket(date_local: dt.date) -> str:
    return f"{date_local.month:02d}"


def _season_bucket(date_local: dt.date) -> str:
    month = date_local.month
    if month in {12, 1, 2}:
        return "DJF"
    if month in {3, 4, 5}:
        return "MAM"
    if month in {6, 7, 8}:
        return "JJA"
    return "SON"


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _provider_prediction(row: dict[str, object]) -> float | None:
    for column in [
        "om_provider_tmax_pred_c",
        "om_prev_d1_day_max_c",
        "om_prev_d1_temp_23_local_c",
    ]:
        value = row.get(column)
        if value is None:
            continue
        try:
            if math.isnan(float(value)):
                continue
        except TypeError:
            continue
        return float(value)
    return None


def _priority_index(model: object, priority: list[str] | tuple[str, ...]) -> int:
    text = str(model)
    return priority.index(text) if text in priority else len(priority)


def collapse_provider_family_predictions(
    rows: list[dict[str, object]],
    *,
    priority: list[str] | tuple[str, ...] = DEFAULT_FAMILY_PRIORITY,
) -> dict[str, dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    selected_rank: dict[str, int] = {}
    for row in rows:
        family = str(row["provider_family"])
        value = row.get("value")
        if value is None:
            continue
        rank = _priority_index(row.get("model"), priority)
        if family not in selected or rank < selected_rank[family]:
            selected[family] = {"model": row.get("model"), "value": float(value)}
            selected_rank[family] = rank
    return selected


def _provider_observations(
    provider_features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None,
) -> pl.DataFrame:
    features = normalize_pooled_cp_column(_ensure_date(provider_features))
    labels = _ensure_date(labels)
    if features.is_empty():
        return pl.DataFrame()
    joined = features.join(
        labels.select(["date_local", "tmax_int"]).unique(),
        on="date_local",
        how="inner",
    )
    if assignments is not None and not assignments.is_empty():
        assign = normalize_pooled_cp_column(_ensure_date(assignments))
        if {"date_local", "cp", "binary_macro_regime_label"}.issubset(assign.columns):
            joined = joined.join(
                assign.select(["date_local", "cp", "binary_macro_regime_label"]),
                on=["date_local", "cp"],
                how="left",
            )
    if "binary_macro_regime_label" not in joined.columns:
        joined = joined.with_columns(
            pl.lit("unknown").alias("binary_macro_regime_label")
        )

    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        prediction = _provider_prediction(row)
        if prediction is None:
            continue
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": row["cp"],
                "endpoint": row.get("endpoint") or row.get("om_endpoint"),
                "model": row.get("model") or row.get("om_model"),
                "provider": row.get("provider"),
                "provider_family": row.get("provider_family", ""),
                "provider_prediction": prediction,
                "actual_tmax": float(row["tmax_int"]),
                "binary_macro_regime_label": row["binary_macro_regime_label"],
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _history_rows(
    base_rows: list[dict[str, object]],
    *,
    date_local: dt.date,
    calibration_window_days: int,
    regime: str | None = None,
    month_bucket: str | None = None,
    season_bucket: str | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in base_rows:
        past_date = row["date_local"]
        if not isinstance(past_date, dt.date):
            continue
        age = (date_local - past_date).days
        if age <= 0 or age > calibration_window_days:
            continue
        if regime is not None and row.get("binary_macro_regime_label") != regime:
            continue
        if month_bucket is not None and row.get("month_bucket") != month_bucket:
            continue
        if season_bucket is not None and row.get("season_bucket") != season_bucket:
            continue
        rows.append(row)
    return rows


def _shrunken_bias_adjustment(
    errors: list[float],
    *,
    min_samples: int,
    shrinkage_denominator: int,
    max_abs_bias_adjustment: float,
) -> tuple[float, int, bool]:
    n_samples = len(errors)
    if n_samples < min_samples:
        return 0.0, n_samples, False
    signed_bias = sum(errors) / float(n_samples)
    shrinkage = n_samples / float(n_samples + shrinkage_denominator)
    adjustment = -signed_bias * shrinkage
    adjustment = max(-max_abs_bias_adjustment, min(max_abs_bias_adjustment, adjustment))
    return adjustment, n_samples, True


def _base_candidate_rows(
    observations: pl.DataFrame,
    *,
    family_priority: list[str] | tuple[str, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if observations.is_empty():
        return rows
    grouped = observations.group_by(["date_local", "cp"], maintain_order=True)
    for key, frame in grouped:
        date_local, cp = key if isinstance(key, tuple) else (key, None)
        provider_rows = [
            {
                "model": row["model"],
                "provider_family": row["provider_family"],
                "value": row["provider_prediction"],
            }
            for row in frame.iter_rows(named=True)
        ]
        collapsed = collapse_provider_family_predictions(
            provider_rows,
            priority=family_priority,
        )
        if not collapsed:
            continue
        values = [float(row["value"]) for row in collapsed.values()]
        actual = float(frame["actual_tmax"][0])
        regime = frame["binary_macro_regime_label"][0]
        gfs_value = (
            float(collapsed["NOAA_GFS"]["value"])
            if "NOAA_GFS" in collapsed
            else None
        )
        rows.append(
            {
                "date_local": date_local,
                "cp": cp,
                "actual_tmax": actual,
                "binary_macro_regime_label": regime,
                "family_predictions": collapsed,
                "family_values": values,
                "gfs_value": gfs_value,
                "raw_family_mean": sum(values) / float(len(values)),
                "raw_family_median": float(median(values)),
                "month_bucket": _month_bucket(date_local),
                "season_bucket": _season_bucket(date_local),
                "n_provider_families": len(values),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return sorted(rows, key=lambda row: (row["date_local"], str(row["cp"])))


def _inverse_mae_prediction(
    base_row: dict[str, object],
    observations: pl.DataFrame,
    *,
    calibration_window_days: int,
) -> tuple[float, int, str]:
    date_local = base_row["date_local"]
    family_predictions = base_row["family_predictions"]
    family_weights: dict[str, float] = {}
    sample_count = 0
    for family in family_predictions:
        history = observations.filter(
            (pl.col("provider_family") == family)
            & (pl.col("date_local") < date_local)
            & (
                pl.col("date_local")
                >= date_local - dt.timedelta(days=calibration_window_days)
            )
        )
        if history.is_empty():
            continue
        errors = (
            history["provider_prediction"].cast(pl.Float64)
            - history["actual_tmax"].cast(pl.Float64)
        ).abs()
        mae = float(errors.mean())
        family_weights[family] = 1.0 / max(mae, 0.05)
        sample_count += history.height
    if len(family_weights) < 2:
        return float(base_row["raw_family_mean"]), sample_count, "fallback_raw_family_mean"
    numerator = sum(
        float(family_predictions[family]["value"]) * weight
        for family, weight in family_weights.items()
    )
    denominator = sum(family_weights.values())
    return numerator / denominator, sample_count, "inverse_mae_weighted"


def _candidate_row(
    base_row: dict[str, object],
    *,
    candidate_id: str,
    prediction: float,
    calibration_window_days: int,
    bias_adjustment: float,
    bias_samples: int,
    calibration_status: str,
    calibration_bucket_type: str = "none",
    calibration_bucket: str = "",
    fallback_reason: str = "",
) -> dict[str, object]:
    actual = float(base_row["actual_tmax"])
    error = prediction - actual
    return {
        "date_local": base_row["date_local"],
        "cp": base_row["cp"],
        "candidate_id": candidate_id,
        "prediction": prediction,
        "actual_tmax": actual,
        "error": error,
        "absolute_error": abs(error),
        "squared_error": error * error,
        "actual_bracket": math.floor(actual + 0.5),
        "pred_bracket": math.floor(prediction + 0.5),
        "exact_bracket": math.floor(actual + 0.5) == math.floor(prediction + 0.5),
        "n_provider_families": base_row["n_provider_families"],
        "binary_macro_regime_label": base_row["binary_macro_regime_label"],
        "month_bucket": base_row["month_bucket"],
        "season_bucket": base_row["season_bucket"],
        "calibration_window_days": calibration_window_days,
        "calibration_bucket_type": calibration_bucket_type,
        "calibration_bucket": calibration_bucket,
        "bias_adjustment": bias_adjustment,
        "bias_samples": bias_samples,
        "calibration_status": calibration_status,
        "fallback_reason": fallback_reason,
        "production_status": PRODUCTION_STATUS,
    }


def build_provider_calibrated_candidates(
    *,
    provider_features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None = None,
    calibration_window_days: int = 30,
    min_bias_samples: int = 30,
    min_regime_bias_samples: int = 60,
    seasonal_calibration_window_days: int = 730,
    min_month_bias_samples: int = 60,
    min_season_bias_samples: int = 90,
    seasonal_max_abs_bias_adjustment: float = 1.25,
    seasonal_shrinkage_denominator: int = 60,
    max_abs_bias_adjustment: float = 2.0,
    shrinkage_denominator: int = 30,
    family_priority: list[str] | tuple[str, ...] = DEFAULT_FAMILY_PRIORITY,
) -> pl.DataFrame:
    observations = _provider_observations(provider_features, labels, assignments)
    base_rows = _base_candidate_rows(observations, family_priority=family_priority)
    candidate_rows: list[dict[str, object]] = []
    completed_base_rows: list[dict[str, object]] = []

    for base_row in base_rows:
        if base_row["gfs_value"] is not None:
            candidate_rows.append(
                _candidate_row(
                    base_row,
                    candidate_id=RAW_GFS_ID,
                    prediction=float(base_row["gfs_value"]),
                    calibration_window_days=calibration_window_days,
                    bias_adjustment=0.0,
                    bias_samples=0,
                    calibration_status="raw_gfs",
                )
            )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=RAW_FAMILY_MEAN_ID,
                prediction=float(base_row["raw_family_mean"]),
                calibration_window_days=calibration_window_days,
                bias_adjustment=0.0,
                bias_samples=0,
                calibration_status="raw_family_dedup",
            )
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=RAW_FAMILY_MEDIAN_ID,
                prediction=float(base_row["raw_family_median"]),
                calibration_window_days=calibration_window_days,
                bias_adjustment=0.0,
                bias_samples=0,
                calibration_status="raw_family_dedup",
            )
        )
        inverse_prediction, inverse_samples, inverse_status = _inverse_mae_prediction(
            base_row,
            observations,
            calibration_window_days=calibration_window_days,
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=INVERSE_MAE_ID,
                prediction=inverse_prediction,
                calibration_window_days=calibration_window_days,
                bias_adjustment=0.0,
                bias_samples=inverse_samples,
                calibration_status=inverse_status,
            )
        )

        recent_history = _history_rows(
            completed_base_rows,
            date_local=base_row["date_local"],
            calibration_window_days=calibration_window_days,
        )
        recent_adjustment, recent_samples, recent_ok = _shrunken_bias_adjustment(
            [
                float(row["raw_family_mean"]) - float(row["actual_tmax"])
                for row in recent_history
            ],
            min_samples=min_bias_samples,
            shrinkage_denominator=shrinkage_denominator,
            max_abs_bias_adjustment=max_abs_bias_adjustment,
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=RECENT_BIAS_ID,
                prediction=float(base_row["raw_family_mean"]) + recent_adjustment,
                calibration_window_days=calibration_window_days,
                bias_adjustment=recent_adjustment,
                bias_samples=recent_samples,
                calibration_status=(
                    "recent_bias_corrected"
                    if recent_ok
                    else "fallback_raw_family_mean"
                ),
            )
        )

        regime = str(base_row["binary_macro_regime_label"])
        regime_history = _history_rows(
            completed_base_rows,
            date_local=base_row["date_local"],
            calibration_window_days=calibration_window_days,
            regime=regime,
        )
        regime_adjustment, regime_samples, regime_ok = _shrunken_bias_adjustment(
            [
                float(row["raw_family_mean"]) - float(row["actual_tmax"])
                for row in regime_history
            ],
            min_samples=min_regime_bias_samples,
            shrinkage_denominator=shrinkage_denominator,
            max_abs_bias_adjustment=max_abs_bias_adjustment,
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=REGIME_BIAS_ID,
                prediction=float(base_row["raw_family_mean"]) + regime_adjustment,
                calibration_window_days=calibration_window_days,
                bias_adjustment=regime_adjustment,
                bias_samples=regime_samples,
                calibration_status=(
                    "regime_bias_corrected"
                    if regime_ok
                    else "fallback_insufficient_regime_support"
                ),
                calibration_bucket_type="binary_macro_regime_label",
                calibration_bucket=regime,
                fallback_reason="" if regime_ok else "insufficient_regime_support",
            )
        )

        month_bucket = str(base_row["month_bucket"])
        month_history = _history_rows(
            completed_base_rows,
            date_local=base_row["date_local"],
            calibration_window_days=seasonal_calibration_window_days,
            month_bucket=month_bucket,
        )
        month_adjustment, month_samples, month_ok = _shrunken_bias_adjustment(
            [
                float(row["raw_family_mean"]) - float(row["actual_tmax"])
                for row in month_history
            ],
            min_samples=min_month_bias_samples,
            shrinkage_denominator=seasonal_shrinkage_denominator,
            max_abs_bias_adjustment=seasonal_max_abs_bias_adjustment,
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=MONTH_BIAS_ID,
                prediction=float(base_row["raw_family_mean"]) + month_adjustment,
                calibration_window_days=seasonal_calibration_window_days,
                bias_adjustment=month_adjustment,
                bias_samples=month_samples,
                calibration_status=(
                    "month_bias_corrected"
                    if month_ok
                    else "fallback_raw_family_mean"
                ),
                calibration_bucket_type="month",
                calibration_bucket=month_bucket,
                fallback_reason="" if month_ok else "insufficient_month_support",
            )
        )

        season_bucket = str(base_row["season_bucket"])
        season_history = _history_rows(
            completed_base_rows,
            date_local=base_row["date_local"],
            calibration_window_days=seasonal_calibration_window_days,
            season_bucket=season_bucket,
        )
        season_adjustment, season_samples, season_ok = _shrunken_bias_adjustment(
            [
                float(row["raw_family_mean"]) - float(row["actual_tmax"])
                for row in season_history
            ],
            min_samples=min_season_bias_samples,
            shrinkage_denominator=seasonal_shrinkage_denominator,
            max_abs_bias_adjustment=seasonal_max_abs_bias_adjustment,
        )
        candidate_rows.append(
            _candidate_row(
                base_row,
                candidate_id=SEASON_BIAS_ID,
                prediction=float(base_row["raw_family_mean"]) + season_adjustment,
                calibration_window_days=seasonal_calibration_window_days,
                bias_adjustment=season_adjustment,
                bias_samples=season_samples,
                calibration_status=(
                    "season_bias_corrected"
                    if season_ok
                    else "fallback_raw_family_mean"
                ),
                calibration_bucket_type="season",
                calibration_bucket=season_bucket,
                fallback_reason="" if season_ok else "insufficient_season_support",
            )
        )
        completed_base_rows.append(base_row)

    if not candidate_rows:
        return pl.DataFrame()
    return pl.DataFrame(candidate_rows, strict=False).sort(
        ["date_local", "cp", "candidate_id"]
    )


def _candidate_metrics(candidates: pl.DataFrame) -> pl.DataFrame:
    if candidates.is_empty():
        return pl.DataFrame()
    return (
        candidates.group_by("candidate_id")
        .agg(
            pl.len().alias("n_rows"),
            pl.col("date_local").n_unique().alias("n_dates"),
            pl.col("absolute_error").mean().alias("mae"),
            pl.col("squared_error").mean().sqrt().alias("rmse"),
            pl.col("error").mean().alias("signed_bias"),
            pl.col("exact_bracket").cast(pl.Float64).mean().mul(100.0).alias(
                "exact_bracket_pct"
            ),
            pl.col("n_provider_families").mean().alias("mean_provider_families"),
            pl.col("bias_adjustment").mean().alias("mean_bias_adjustment"),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort("mae")
    )


def _candidate_coverage(candidates: pl.DataFrame) -> pl.DataFrame:
    if candidates.is_empty():
        return pl.DataFrame()
    return (
        candidates.group_by("candidate_id")
        .agg(
            pl.len().alias("n_rows"),
            pl.col("date_local").n_unique().alias("n_dates"),
            pl.col("cp").n_unique().alias("n_cps"),
            pl.col("n_provider_families").min().alias("min_provider_families"),
            pl.col("n_provider_families").max().alias("max_provider_families"),
            pl.col("date_local").min().alias("min_date"),
            pl.col("date_local").max().alias("max_date"),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort("candidate_id")
    )


def _support_slice(candidates: pl.DataFrame, slice_type: str, columns: list[str]) -> pl.DataFrame:
    if candidates.is_empty():
        return pl.DataFrame()
    stabilized = candidates.filter(
        pl.col("candidate_id").is_in([MONTH_BIAS_ID, SEASON_BIAS_ID])
    )
    if stabilized.is_empty():
        return pl.DataFrame()
    if not columns:
        frames = [(("overall",), stabilized)]
    else:
        frames = list(stabilized.group_by(["candidate_id", *columns], maintain_order=True))
    rows: list[dict[str, object]] = []
    for key, frame in frames:
        values = key if isinstance(key, tuple) else (key,)
        if columns:
            candidate_id = str(values[0])
            slice_values = values[1:]
            slice_name = "|".join(str(value) for value in slice_values)
        else:
            candidate_id = "ALL_STABILIZED"
            slice_name = "overall"
        fallback_count = int((frame["fallback_reason"].cast(pl.Utf8) != "").sum())
        mean_abs_adjustment = float(frame["bias_adjustment"].abs().mean())
        fallback_pct = fallback_count * 100.0 / float(frame.height)
        rows.append(
            {
                "candidate_id": candidate_id,
                "slice_type": slice_type,
                "slice_name": slice_name,
                "n_rows": frame.height,
                "mean_bias_samples": float(frame["bias_samples"].mean()),
                "min_bias_samples": int(frame["bias_samples"].min()),
                "fallback_pct": fallback_pct,
                "mean_abs_bias_adjustment": mean_abs_adjustment,
                "support_warning": (
                    "fallback_pct_gt_40" if fallback_pct > 40.0 else ""
                ),
                "adjustment_warning": (
                    "mean_abs_bias_adjustment_gt_1"
                    if mean_abs_adjustment > 1.0
                    else ""
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _stabilized_support(candidates: pl.DataFrame) -> pl.DataFrame:
    candidates_with_year = (
        candidates.with_columns(pl.col("date_local").dt.year().alias("calendar_year"))
        if not candidates.is_empty()
        else candidates
    )
    frames = [
        _support_slice(candidates_with_year, "overall", []),
        _support_slice(candidates_with_year, "year", ["calendar_year"]),
        _support_slice(candidates_with_year, "month", ["month_bucket"]),
        _support_slice(candidates_with_year, "season", ["season_bucket"]),
        _support_slice(candidates_with_year, "cp", ["cp"]),
        _support_slice(
            candidates_with_year,
            "binary_macro_regime_label",
            ["binary_macro_regime_label"],
        ),
    ]
    normalized = [frame for frame in frames if not frame.is_empty()]
    if not normalized:
        return pl.DataFrame()
    return pl.concat(normalized, how="diagonal_relaxed").sort(
        ["candidate_id", "slice_type", "slice_name"]
    )


def _decision(candidates: pl.DataFrame, metrics: pl.DataFrame) -> pl.DataFrame:
    if candidates.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": "BLOCK_PROVIDER_CALIBRATION_BY_COVERAGE",
                    "decision_rationale": (
                        "No causal provider candidate rows were available for "
                        "calibration."
                    ),
                    "best_candidate_id": None,
                    "best_candidate_mae": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    best = metrics.row(0, named=True) if not metrics.is_empty() else {}
    return pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_CALIBRATED_OPEN_METEO_NESTED_VALIDATION"
                ),
                "decision_rationale": (
                    "Raw and bias-corrected provider-family candidates were "
                    "generated as experiment-only inputs for nested validation."
                ),
                "best_candidate_id": best.get("candidate_id"),
                "best_candidate_mae": best.get("mae"),
                "n_candidate_rows": candidates.height,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_provider_calibration_artifacts(
    *,
    provider_features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None = None,
    calibration_window_days: int = 30,
    min_bias_samples: int = 30,
    min_regime_bias_samples: int = 60,
    seasonal_calibration_window_days: int = 730,
    min_month_bias_samples: int = 60,
    min_season_bias_samples: int = 90,
    seasonal_max_abs_bias_adjustment: float = 1.25,
    seasonal_shrinkage_denominator: int = 60,
    max_abs_bias_adjustment: float = 2.0,
    shrinkage_denominator: int = 30,
) -> dict[str, pl.DataFrame]:
    candidates = build_provider_calibrated_candidates(
        provider_features=provider_features,
        labels=labels,
        assignments=assignments,
        calibration_window_days=calibration_window_days,
        min_bias_samples=min_bias_samples,
        min_regime_bias_samples=min_regime_bias_samples,
        seasonal_calibration_window_days=seasonal_calibration_window_days,
        min_month_bias_samples=min_month_bias_samples,
        min_season_bias_samples=min_season_bias_samples,
        seasonal_max_abs_bias_adjustment=seasonal_max_abs_bias_adjustment,
        seasonal_shrinkage_denominator=seasonal_shrinkage_denominator,
        max_abs_bias_adjustment=max_abs_bias_adjustment,
        shrinkage_denominator=shrinkage_denominator,
    )
    metrics = _candidate_metrics(candidates)
    return {
        "open_meteo_provider_calibrated_candidates_v1": candidates,
        "open_meteo_provider_calibrated_candidate_metrics_v1": metrics,
        "open_meteo_provider_calibrated_candidate_coverage_v1": (
            _candidate_coverage(candidates)
        ),
        "open_meteo_stabilized_calibration_support_v1": _stabilized_support(candidates),
        "open_meteo_provider_calibration_decision_v1": _decision(
            candidates,
            metrics,
        ),
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| "
        + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns)
        + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_provider_calibration_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Provider Calibration Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "This report builds family-deduplicated raw and bias-corrected "
                "provider candidates. It does not approve production use."
            ),
            "## Decision",
            _markdown_table(artifacts["open_meteo_provider_calibration_decision_v1"]),
            "## Candidate Metrics",
            _markdown_table(
                artifacts["open_meteo_provider_calibrated_candidate_metrics_v1"],
                max_rows=40,
            ),
            "## Candidate Coverage",
            _markdown_table(
                artifacts["open_meteo_provider_calibrated_candidate_coverage_v1"],
                max_rows=40,
            ),
            "## Stabilized Calibration Support",
            _markdown_table(
                artifacts["open_meteo_stabilized_calibration_support_v1"],
                max_rows=60,
            ),
        ]
    ) + "\n"


def write_provider_calibration_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    candidates = artifacts["open_meteo_provider_calibrated_candidates_v1"]
    parquet_path = output_dir / "open_meteo_provider_calibrated_candidates_v1.parquet"
    candidates.write_parquet(parquet_path)
    paths["open_meteo_provider_calibrated_candidates_parquet"] = parquet_path

    for key, filename in PROVIDER_CALIBRATION_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path

    report_path = output_dir / "open_meteo_provider_calibration_report_v1.md"
    report_path.write_text(
        render_provider_calibration_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_provider_calibration_report_md"] = report_path
    return paths
