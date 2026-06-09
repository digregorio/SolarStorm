"""Calm/radiative feature-hypothesis diagnostics for CEXP-002."""
from __future__ import annotations

import datetime as dt
import math
from collections.abc import Iterable
from pathlib import Path

import polars as pl

EXPERIMENT_ID = "CEXP-CALM-RADIATIVE-002"
CALM_MACRO = "macro_calm_radiative"
DEFAULT_CALM_RADIATIVE_CANDIDATE_FEATURES: tuple[str, ...] = (
    "cloud_base_transparency",
    "nocturnal_plateau_flag",
    "dewpoint_depression",
    "cloud_cover_suppression",
    "pressure_trend_3h",
    "warming_rate_06_09",
    "dewpoint_collapse_rate_3h",
    "sst_maritime_cap",
)

OUTCOME_OR_TARGET_PROXY_COLUMNS = {
    "remaining_warming",
    "tmax_int",
    "tmpf_max",
    "tmax_hour",
    "tmax_hour_local",
    "tmax_hour_utc",
    "tmax_dec",
    "tmax_anomaly",
    "tmax_atypical_hour",
    "risco_de_flip",
    "late_warming_anomaly",
    "tmax_hour_by_regime_month",
}

FEATURE_HYPOTHESIS_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "feature_column": pl.Utf8,
    "n_rows": pl.Int64,
    "n_unique_days": pl.Int64,
    "date_window_start": pl.Utf8,
    "date_window_end": pl.Utf8,
    "feature_missing_rate": pl.Float64,
    "feature_mean": pl.Float64,
    "feature_std": pl.Float64,
    "remaining_warming_mean": pl.Float64,
    "pearson_corr": pl.Float64,
    "abs_corr": pl.Float64,
    "ols_intercept": pl.Float64,
    "ols_slope": pl.Float64,
    "variance_status": pl.Utf8,
    "leakage_class": pl.Utf8,
    "causal_role": pl.Utf8,
    "recommended_disposition": pl.Utf8,
    "diagnostic_note": pl.Utf8,
    "production_status": pl.Utf8,
}


def _empty_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=FEATURE_HYPOTHESIS_SCHEMA)


def _normalize_keys(frame: pl.DataFrame) -> pl.DataFrame:
    out = frame
    if "date_local" in out.columns and out.schema["date_local"] == pl.Utf8:
        out = out.with_columns(pl.col("date_local").str.to_date())
    if "cp" in out.columns:
        out = out.with_columns(pl.col("cp").cast(pl.Utf8))
    return out


def _validate_inputs(
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
) -> None:
    required_assignments = {
        "date_local",
        "cp",
        "macro_regime_label",
        "production_status",
    }
    missing_assignments = required_assignments - set(assignments.columns)
    if missing_assignments:
        raise ValueError(
            "assignments missing required columns: "
            f"{', '.join(sorted(missing_assignments))}"
        )
    if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("assignments production_status must be NOT_PRODUCTION")

    required_features = {"date_local", "cp"}
    missing_features = required_features - set(features.columns)
    if missing_features:
        raise ValueError(
            "features missing required columns: "
            f"{', '.join(sorted(missing_features))}"
        )

    required_labels = {"date_local", "tmax_int"}
    missing_labels = required_labels - set(labels.columns)
    if missing_labels:
        raise ValueError(
            "labels missing required columns: "
            f"{', '.join(sorted(missing_labels))}"
        )


def _date_text(value: object) -> str:
    if value is None:
        return ""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _cp_code(cp: object) -> str:
    return str(cp).replace(":", "")


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    if not vals:
        return None
    return float(sum(vals) / len(vals))


def _std(values: Iterable[float]) -> float | None:
    vals = list(values)
    if not vals:
        return None
    if len(vals) == 1:
        return 0.0
    mean = sum(vals) / len(vals)
    variance = sum((value - mean) ** 2 for value in vals) / (len(vals) - 1)
    return float(variance**0.5)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_dev = [value - x_mean for value in xs]
    y_dev = [value - y_mean for value in ys]
    x_ss = sum(value * value for value in x_dev)
    y_ss = sum(value * value for value in y_dev)
    if x_ss <= 1e-12 or y_ss <= 1e-12:
        return None
    return float(sum(x * y for x, y in zip(x_dev, y_dev, strict=True)) / (x_ss * y_ss) ** 0.5)


def _ols(xs: list[float], ys: list[float]) -> tuple[float | None, float | None]:
    if len(xs) < 2 or len(xs) != len(ys):
        return None, None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_ss = sum((value - x_mean) ** 2 for value in xs)
    if x_ss <= 1e-12:
        return None, None
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True)) / x_ss
    intercept = y_mean - slope * x_mean
    return float(intercept), float(slope)


def _is_outcome_or_target_proxy(feature_column: str) -> bool:
    return (
        feature_column in OUTCOME_OR_TARGET_PROXY_COLUMNS
        or feature_column.startswith("tmax_")
    )


def _candidate_version(assignments: pl.DataFrame) -> str:
    if "candidate_version" not in assignments.columns:
        return "v2.2"
    values = assignments["candidate_version"].drop_nulls().unique().sort()
    return str(values[0]) if values.len() else "v2.2"


def _feature_rows(
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    train_end: dt.date,
    candidate_features: tuple[str, ...],
) -> list[dict[str, object]]:
    feature_by_key = {
        (row["date_local"], str(row["cp"])): row for row in features.iter_rows(named=True)
    }
    label_by_day = {
        row["date_local"]: row
        for row in labels.iter_rows(named=True)
        if bool(row.get("day_complete", True))
    }

    rows: list[dict[str, object]] = []
    for assignment in assignments.iter_rows(named=True):
        date_local = assignment["date_local"]
        if (
            date_local is None
            or date_local > train_end
            or str(assignment["macro_regime_label"]) != CALM_MACRO
        ):
            continue
        label_row = label_by_day.get(date_local)
        if label_row is None:
            continue
        cp = str(assignment["cp"])
        k_cp = label_row.get(f"k_cp__cp_{_cp_code(cp)}")
        tmax = label_row.get("tmax_int")
        if k_cp is None or tmax is None:
            continue
        feature_row = feature_by_key.get((date_local, cp), {})
        out: dict[str, object] = {
            "date_local": date_local,
            "candidate_version": str(assignment.get("candidate_version", "v2.2")),
            "remaining_warming": float(tmax) - float(k_cp),
        }
        for feature in candidate_features:
            if feature in feature_row:
                out[feature] = feature_row[feature]
        rows.append(out)
    return rows


def _base_result(
    *,
    candidate_version: str,
    feature_column: str,
    context: pl.DataFrame,
    n_rows: int,
    dates: list[object],
    xs: list[float] | None = None,
    leakage_class: str,
    variance_status: str,
    recommended_disposition: str,
    diagnostic_note: str,
    causal_role: str = "CAUSAL_CANDIDATE_SCREEN",
    remaining_values: list[float] | None = None,
    pearson_corr: float | None = None,
    ols_intercept: float | None = None,
    ols_slope: float | None = None,
) -> dict[str, object]:
    xs = xs or []
    remaining = remaining_values
    if remaining is None:
        remaining = [
            value
            for value in (
                _safe_float(row["remaining_warming"])
                for row in context.iter_rows(named=True)
            )
            if value is not None
        ]
    abs_corr = abs(pearson_corr) if pearson_corr is not None else None
    return {
        "experiment_id": EXPERIMENT_ID,
        "candidate_version": candidate_version,
        "macro_regime_label": CALM_MACRO,
        "feature_column": feature_column,
        "n_rows": n_rows,
        "n_unique_days": len(set(dates)),
        "date_window_start": _date_text(min(dates)) if dates else "",
        "date_window_end": _date_text(max(dates)) if dates else "",
        "feature_missing_rate": None,
        "feature_mean": _mean(xs),
        "feature_std": _std(xs),
        "remaining_warming_mean": _mean(remaining),
        "pearson_corr": pearson_corr,
        "abs_corr": abs_corr,
        "ols_intercept": ols_intercept,
        "ols_slope": ols_slope,
        "variance_status": variance_status,
        "leakage_class": leakage_class,
        "causal_role": causal_role,
        "recommended_disposition": recommended_disposition,
        "diagnostic_note": diagnostic_note,
        "production_status": "EXPERIMENT_ONLY",
    }


def _missing_rate(context: pl.DataFrame, feature_column: str) -> float:
    if context.height == 0 or feature_column not in context.columns:
        return 1.0
    missing = sum(
        1
        for row in context.iter_rows(named=True)
        if _safe_float(row.get(feature_column)) is None
    )
    return float(missing / context.height)


def _feature_result(
    *,
    candidate_version: str,
    context: pl.DataFrame,
    feature_column: str,
    features: pl.DataFrame,
    min_rows: int,
    min_abs_corr: float,
) -> dict[str, object]:
    if _is_outcome_or_target_proxy(feature_column):
        row = _base_result(
            candidate_version=candidate_version,
            feature_column=feature_column,
            context=context,
            n_rows=context.height,
            dates=context["date_local"].to_list() if context.height else [],
            leakage_class="excluded_outcome",
            variance_status="BLOCKED",
            causal_role="FULL_DAY_TARGET_OR_PROXY_AUDIT_ONLY",
            recommended_disposition="BLOCKED_LEAKAGE_FEATURE",
            diagnostic_note="Full-day outcome or target proxy; never eligible as CP feature.",
        )
        row["feature_missing_rate"] = None
        return row

    if feature_column not in features.columns:
        row = _base_result(
            candidate_version=candidate_version,
            feature_column=feature_column,
            context=context,
            n_rows=0,
            dates=[],
            leakage_class="missing_feature",
            variance_status="MISSING",
            causal_role="UNAVAILABLE_CANDIDATE",
            recommended_disposition="MISSING_FEATURE",
            diagnostic_note="Candidate feature column is absent from features parquet.",
        )
        row["feature_missing_rate"] = 1.0
        return row

    pairs: list[tuple[object, float, float]] = []
    non_numeric_seen = False
    for row in context.iter_rows(named=True):
        x_value = _safe_float(row.get(feature_column))
        y_value = _safe_float(row.get("remaining_warming"))
        if x_value is None:
            if row.get(feature_column) is not None:
                non_numeric_seen = True
            continue
        if y_value is None:
            continue
        pairs.append((row["date_local"], x_value, y_value))

    xs = [x for _, x, _ in pairs]
    ys = [y for _, _, y in pairs]
    dates = [date for date, _, _ in pairs]
    n_rows = len(pairs)
    feature_missing_rate = _missing_rate(context, feature_column)

    if n_rows == 0 and non_numeric_seen:
        row = _base_result(
            candidate_version=candidate_version,
            feature_column=feature_column,
            context=context,
            n_rows=0,
            dates=[],
            xs=[],
            remaining_values=[],
            leakage_class="causal_candidate",
            variance_status="NON_NUMERIC",
            recommended_disposition="UNSUPPORTED_FEATURE",
            diagnostic_note="Feature is present but not numeric in the calm/radiative context.",
        )
        row["feature_missing_rate"] = feature_missing_rate
        return row

    if n_rows < min_rows:
        row = _base_result(
            candidate_version=candidate_version,
            feature_column=feature_column,
            context=context,
            n_rows=n_rows,
            dates=dates,
            xs=xs,
            remaining_values=ys,
            leakage_class="causal_candidate",
            variance_status="UNDERPOWERED",
            recommended_disposition="UNDERPOWERED_FEATURE",
            diagnostic_note="Not enough train-window calm/radiative rows for a feature screen.",
        )
        row["feature_missing_rate"] = feature_missing_rate
        return row

    feature_std = _std(xs)
    if feature_std is None or feature_std <= 1e-12:
        row = _base_result(
            candidate_version=candidate_version,
            feature_column=feature_column,
            context=context,
            n_rows=n_rows,
            dates=dates,
            xs=xs,
            remaining_values=ys,
            leakage_class="causal_candidate",
            variance_status="CONSTANT",
            recommended_disposition="CONSTANT_FEATURE",
            diagnostic_note="Feature is constant in the calm/radiative train context.",
        )
        row["feature_missing_rate"] = feature_missing_rate
        return row

    corr = _pearson(xs, ys)
    intercept, slope = _ols(xs, ys)
    abs_corr = abs(corr) if corr is not None else 0.0
    disposition = (
        "CANDIDATE_SIGNAL" if abs_corr >= min_abs_corr else "WEAK_SIGNAL"
    )
    row = _base_result(
        candidate_version=candidate_version,
        feature_column=feature_column,
        context=context,
        n_rows=n_rows,
        dates=dates,
        xs=xs,
        remaining_values=ys,
        leakage_class="causal_candidate",
        variance_status="USABLE",
        recommended_disposition=disposition,
        diagnostic_note=(
            "Train-only univariate screen against remaining_warming audit target; "
            "requires independent validation before model use."
        ),
        pearson_corr=corr,
        ols_intercept=intercept,
        ols_slope=slope,
    )
    row["feature_missing_rate"] = feature_missing_rate
    return row


def build_regime_calm_radiative_feature_hypotheses(
    *,
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    train_end: dt.date,
    candidate_features: tuple[str, ...] = DEFAULT_CALM_RADIATIVE_CANDIDATE_FEATURES,
    min_rows: int = 30,
    min_abs_corr: float = 0.2,
) -> dict[str, pl.DataFrame]:
    """Build train-only CEXP-002 feature-hypothesis diagnostics."""
    assignments = _normalize_keys(assignments)
    features = _normalize_keys(features)
    labels = _normalize_keys(labels)
    _validate_inputs(assignments, features, labels)
    unique_features = tuple(dict.fromkeys(candidate_features))
    candidate_version = _candidate_version(assignments)
    context_rows = _feature_rows(
        assignments,
        features,
        labels,
        train_end=train_end,
        candidate_features=unique_features,
    )
    context = pl.DataFrame(context_rows) if context_rows else pl.DataFrame()
    results = [
        _feature_result(
            candidate_version=candidate_version,
            context=context,
            feature_column=feature,
            features=features,
            min_rows=min_rows,
            min_abs_corr=min_abs_corr,
        )
        for feature in unique_features
    ]
    frame = (
        pl.DataFrame(results, schema=FEATURE_HYPOTHESIS_SCHEMA, strict=False)
        if results
        else _empty_frame()
    )
    return {
        "regime_calm_radiative_feature_hypotheses_v1": frame.sort("feature_column")
    }


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    diagnostics = artifacts["regime_calm_radiative_feature_hypotheses_v1"]
    signals = (
        diagnostics.filter(pl.col("recommended_disposition") == "CANDIDATE_SIGNAL").height
        if diagnostics.height
        else 0
    )
    blocked = (
        diagnostics.filter(
            pl.col("recommended_disposition") == "BLOCKED_LEAKAGE_FEATURE"
        ).height
        if diagnostics.height
        else 0
    )
    lines = [
        f"# CEXP-CALM-RADIATIVE-002 Feature Hypotheses - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        (
            "This artifact screens train-only calm/radiative feature hypotheses "
            "against the remaining_warming audit target."
        ),
        "",
        f"- Candidate features screened: {diagnostics.height}",
        f"- Candidate signals: {signals}",
        f"- Blocked leakage features: {blocked}",
        "",
        "## Feature Screen",
        "",
        "| Feature | Rows | Corr | Slope | Variance | Leakage | Causal role | Disposition |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in diagnostics.iter_rows(named=True):
        lines.append(
            "| "
            f"{row['feature_column']} | "
            f"{row['n_rows']} | "
            f"{row['pearson_corr']} | "
            f"{row['ols_slope']} | "
            f"{row['variance_status']} | "
            f"{row['leakage_class']} | "
            f"{row['causal_role']} | "
            f"{row['recommended_disposition']} |"
        )
    lines += [
        "",
        "## Decision",
        "",
        (
            "CEXP-002 may nominate causal feature work for a future baseline, "
            "but it does not promote Onda 3, alter regime labels, or write "
            "production features."
        ),
    ]
    return lines


def write_regime_calm_radiative_feature_hypotheses_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    diagnostics = artifacts["regime_calm_radiative_feature_hypotheses_v1"]

    csv_path = out_dir / "regime_calm_radiative_feature_hypotheses_v1.csv"
    md_path = out_dir / "regime_calm_radiative_feature_hypotheses_v1.md"
    diagnostics.write_csv(csv_path)
    md_path.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")
    return {
        "regime_calm_radiative_feature_hypotheses_csv": csv_path,
        "regime_calm_radiative_feature_hypotheses_md": md_path,
    }
