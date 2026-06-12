from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

from solarstorm.onda3._pooled_iteration import normalize_pooled_cp_column
from solarstorm.open_meteo._availability import PRODUCTION_STATUS

PROVIDER_ERROR_ATLAS_FILENAMES = {
    "open_meteo_provider_error_dataset_v1": (
        "open_meteo_provider_error_dataset_v1.csv"
    ),
    "open_meteo_provider_error_metrics_v1": (
        "open_meteo_provider_error_metrics_v1.csv"
    ),
    "open_meteo_provider_error_support_warnings_v1": (
        "open_meteo_provider_error_support_warnings_v1.csv"
    ),
}
READY_STATUS = "OPEN_METEO_PROVIDER_READY_FOR_ERROR_ATLAS"
MIN_SLICE_SUPPORT = 30


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _prediction_column(row: dict[str, object]) -> str | None:
    if row.get("om_provider_tmax_pred_c") is not None:
        return "om_provider_tmax_pred_c"
    if row.get("om_prev_d1_day_max_c") is not None:
        return "om_prev_d1_day_max_c"
    if row.get("om_prev_d1_temp_23_local_c") is not None:
        return "om_prev_d1_temp_23_local_c"
    return None


def _eligible_provider_decisions(decision_update: pl.DataFrame) -> pl.DataFrame:
    if decision_update.is_empty():
        return pl.DataFrame()
    required = {"endpoint", "model", "provider_family", "decision_status"}
    missing = required - set(decision_update.columns)
    if missing:
        raise ValueError(
            "provider decision update missing columns: " + ", ".join(sorted(missing))
        )
    optional_columns = [
        column
        for column in ["feature_gate_scope", "production_status"]
        if column in decision_update.columns
    ]
    return decision_update.filter(pl.col("decision_status") == READY_STATUS).select(
        ["endpoint", "model", "provider_family", "decision_status", *optional_columns]
    )


def build_provider_error_dataset(
    *,
    open_meteo_features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None,
    provider_decision_update: pl.DataFrame,
) -> pl.DataFrame:
    om = normalize_pooled_cp_column(_ensure_date(open_meteo_features))
    labels = _ensure_date(labels)
    eligible = _eligible_provider_decisions(provider_decision_update)
    if om.is_empty() or eligible.is_empty():
        return pl.DataFrame()

    rename_map = {}
    if "om_endpoint" in om.columns and "endpoint" not in om.columns:
        rename_map["om_endpoint"] = "endpoint"
    if "om_model" in om.columns and "model" not in om.columns:
        rename_map["om_model"] = "model"
    if rename_map:
        om = om.rename(rename_map)
    joined = om.join(eligible, on=["endpoint", "model"], how="inner", suffix="_gate")
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

    joined = joined.join(
        labels.select(["date_local", "tmax_int"]).unique(),
        on="date_local",
        how="inner",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        pred_col = _prediction_column(row)
        if pred_col is None:
            continue
        prediction = float(row[pred_col])
        actual = float(row["tmax_int"])
        error = prediction - actual
        rows.append(
            {
                "date_local": row["date_local"],
                "calendar_year": row["date_local"].year,
                "month": f"{row['date_local']:%Y-%m}",
                "cp": row["cp"],
                "endpoint": row["endpoint"],
                "model": row["model"],
                "provider_family": row["provider_family"],
                "causal_class": row.get("om_causal_class"),
                "feature_gate_scope": row.get("feature_gate_scope"),
                "binary_macro_regime_label": row["binary_macro_regime_label"],
                "provider_prediction_column": pred_col,
                "provider_prediction": prediction,
                "actual_tmax": actual,
                "error": error,
                "absolute_error": abs(error),
                "squared_error": error * error,
                "actual_bracket": math.floor(actual + 0.5),
                "pred_bracket": math.floor(prediction + 0.5),
                "exact_bracket": math.floor(actual + 0.5)
                == math.floor(prediction + 0.5),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _metric_row(
    frame: pl.DataFrame,
    *,
    endpoint: str,
    model: str,
    provider_family: str,
    slice_type: str,
    slice_name: str,
) -> dict[str, object]:
    n_rows = frame.height
    mae = float(frame["absolute_error"].mean()) if n_rows else None
    rmse = float(math.sqrt(frame["squared_error"].mean())) if n_rows else None
    signed_bias = float(frame["error"].mean()) if n_rows else None
    exact = (
        float(frame["exact_bracket"].cast(pl.Float64).mean() * 100.0)
        if n_rows
        else None
    )
    warm = (
        float((frame["error"] > 0).cast(pl.Float64).mean() * 100.0)
        if n_rows
        else None
    )
    cold = (
        float((frame["error"] < 0).cast(pl.Float64).mean() * 100.0)
        if n_rows
        else None
    )
    return {
        "endpoint": endpoint,
        "model": model,
        "provider_family": provider_family,
        "slice_type": slice_type,
        "slice_name": slice_name,
        "n_rows": n_rows,
        "mae": mae,
        "rmse": rmse,
        "signed_bias": signed_bias,
        "exact_bracket_pct": exact,
        "warm_bias_pct": warm,
        "cold_bias_pct": cold,
        "production_status": PRODUCTION_STATUS,
    }


def _slice_metrics(
    dataset: pl.DataFrame,
    *,
    slice_type: str,
    columns: list[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_cols = ["endpoint", "model", "provider_family"]
    grouped = dataset.group_by([*base_cols, *columns])
    for key, frame in grouped:
        if not isinstance(key, tuple):
            key = (key,)
        key_values = dict(zip([*base_cols, *columns], key, strict=False))
        slice_values = [str(key_values[column]) for column in columns]
        rows.append(
            _metric_row(
                frame,
                endpoint=str(key_values["endpoint"]),
                model=str(key_values["model"]),
                provider_family=str(key_values["provider_family"]),
                slice_type=slice_type,
                slice_name="|".join(slice_values) if slice_values else "overall",
            )
        )
    return rows


def build_provider_error_metrics(dataset: pl.DataFrame) -> pl.DataFrame:
    if dataset.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    rows.extend(_slice_metrics(dataset, slice_type="overall", columns=[]))
    rows.extend(_slice_metrics(dataset, slice_type="year", columns=["calendar_year"]))
    rows.extend(_slice_metrics(dataset, slice_type="month", columns=["month"]))
    rows.extend(_slice_metrics(dataset, slice_type="cp", columns=["cp"]))
    rows.extend(
        _slice_metrics(
            dataset,
            slice_type="binary_macro_regime_label",
            columns=["binary_macro_regime_label"],
        )
    )
    rows.extend(_slice_metrics(dataset, slice_type="month_cp", columns=["month", "cp"]))
    rows.extend(
        _slice_metrics(
            dataset,
            slice_type="binary_macro_regime_label_cp",
            columns=["binary_macro_regime_label", "cp"],
        )
    )
    return pl.DataFrame(rows, strict=False).sort(
        ["endpoint", "model", "slice_type", "slice_name"]
    )


def _support_warnings(metrics: pl.DataFrame) -> pl.DataFrame:
    if metrics.is_empty():
        return pl.DataFrame()
    warnings = metrics.filter(pl.col("n_rows") < MIN_SLICE_SUPPORT).with_columns(
        pl.lit("low_support_for_calibration").alias("warning"),
        pl.lit(MIN_SLICE_SUPPORT).alias("minimum_rows"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )
    return warnings.select(
        [
            "endpoint",
            "model",
            "provider_family",
            "slice_type",
            "slice_name",
            "n_rows",
            "minimum_rows",
            "warning",
            "production_status",
        ]
    )


def build_provider_error_atlas_artifacts(
    *,
    open_meteo_features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None,
    provider_decision_update: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    dataset = build_provider_error_dataset(
        open_meteo_features=open_meteo_features,
        labels=labels,
        assignments=assignments,
        provider_decision_update=provider_decision_update,
    )
    metrics = build_provider_error_metrics(dataset)
    return {
        "open_meteo_provider_error_dataset_v1": dataset,
        "open_meteo_provider_error_metrics_v1": metrics,
        "open_meteo_provider_error_support_warnings_v1": _support_warnings(metrics),
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 40) -> str:
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


def render_provider_error_atlas_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Provider Error Atlas",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "This report measures raw causal provider prediction error. It "
                "does not train, blend, calibrate, or approve production use."
            ),
            "## Metrics",
            _markdown_table(artifacts["open_meteo_provider_error_metrics_v1"]),
            "## Support Warnings",
            _markdown_table(
                artifacts["open_meteo_provider_error_support_warnings_v1"]
            ),
        ]
    ) + "\n"


def write_provider_error_atlas_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in PROVIDER_ERROR_ATLAS_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_provider_error_atlas_report_v1.md"
    report_path.write_text(
        render_provider_error_atlas_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_provider_error_atlas_report_md"] = report_path
    return paths
