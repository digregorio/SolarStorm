"""Causal robustness screen for the calm/radiative cloud signal."""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import numpy as np
import polars as pl

EXPERIMENT_ID = "CEXP-CALM-RADIATIVE-002B"
CEXP003_ID = "CEXP-CALM-RADIATIVE-003"
CALM_MACRO = "macro_calm_radiative"
CLOUD_FEATURE = "cloud_cover_suppression"
CONTROL_FEATURES: tuple[str, ...] = (
    "dewpoint_depression",
    "warming_rate_06_09",
    "dewpoint_collapse_rate_3h",
    "pressure_trend_3h",
)
PROXY_CHECK_FEATURES: tuple[str, ...] = (
    "tmax_dminus1",
    "tmin_delta_tmax",
    "late_warming_anomaly",
    "tmax_hour_by_regime_month",
)

VALIDATION_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "feature_column": pl.Utf8,
    "n_rows": pl.Int64,
    "n_unique_days": pl.Int64,
    "date_window_start": pl.Utf8,
    "date_window_end": pl.Utf8,
    "overall_corr": pl.Float64,
    "overall_slope": pl.Float64,
    "abs_corr": pl.Float64,
    "cp_cells_tested": pl.Int64,
    "cp_negative_slope_share": pl.Float64,
    "month_cp_cells_tested": pl.Int64,
    "cell_negative_slope_share": pl.Float64,
    "controlled_rows": pl.Int64,
    "controlled_slope": pl.Float64,
    "controlled_slope_retention": pl.Float64,
    "control_features_used": pl.Utf8,
    "max_proxy_abs_corr": pl.Float64,
    "max_proxy_feature": pl.Utf8,
    "lineage_status": pl.Utf8,
    "validation_decision": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "next_experiment": pl.Utf8,
    "production_status": pl.Utf8,
}

DEMOTE_SPLIT_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "candidate_option": pl.Utf8,
    "option_label": pl.Utf8,
    "blocker": pl.Utf8,
    "rationale": pl.Utf8,
    "required_next_artifact": pl.Utf8,
    "recommended_disposition": pl.Utf8,
    "production_status": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


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

    required_features = {"date_local", "cp", CLOUD_FEATURE}
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


def _candidate_version(assignments: pl.DataFrame) -> str:
    if "candidate_version" not in assignments.columns:
        return "v2.2"
    values = assignments["candidate_version"].drop_nulls().unique().sort()
    return str(values[0]) if values.len() else "v2.2"


def _ols_slope_corr(frame: pl.DataFrame, x_col: str, y_col: str) -> tuple[float | None, float | None]:
    if frame.height < 3:
        return None, None
    xs = np.array([_safe_float(value) for value in frame[x_col].to_list()], dtype=float)
    ys = np.array([_safe_float(value) for value in frame[y_col].to_list()], dtype=float)
    mask = ~(np.isnan(xs) | np.isnan(ys))
    xs = xs[mask]
    ys = ys[mask]
    if len(xs) < 3 or float(np.std(xs)) <= 1e-12 or float(np.std(ys)) <= 1e-12:
        return None, None
    design = np.vstack([np.ones_like(xs), xs]).T
    slope = float(np.linalg.lstsq(design, ys, rcond=None)[0][1])
    corr = float(np.corrcoef(xs, ys)[0, 1])
    return slope, corr


def _negative_slope_share(
    context: pl.DataFrame,
    *,
    by: list[str],
    min_rows: int,
) -> tuple[int, float | None]:
    tested = 0
    negative = 0
    if context.height == 0:
        return 0, None
    for group in context.partition_by(by, maintain_order=True):
        if group.height < min_rows:
            continue
        slope, _corr = _ols_slope_corr(group, CLOUD_FEATURE, "remaining_warming")
        if slope is None:
            continue
        tested += 1
        if slope < 0:
            negative += 1
    return tested, (negative / tested if tested else None)


def _controlled_slope(
    context: pl.DataFrame,
    controls: tuple[str, ...],
) -> tuple[int, float | None, str]:
    available = [column for column in controls if column in context.columns]
    required = [CLOUD_FEATURE, "remaining_warming", *available]
    complete = context.drop_nulls(required)
    if complete.height < 5:
        return complete.height, None, ";".join(available)

    x_cloud = complete[CLOUD_FEATURE].to_numpy().astype(float)
    if float(np.std(x_cloud)) <= 1e-12:
        return complete.height, None, ";".join(available)

    columns = [np.ones(complete.height), x_cloud]
    used: list[str] = []
    for control in available:
        values = complete[control].to_numpy().astype(float)
        if float(np.std(values)) <= 1e-12:
            continue
        columns.append(values)
        used.append(control)
    design = np.column_stack(columns)
    y = complete["remaining_warming"].to_numpy().astype(float)
    if float(np.std(y)) <= 1e-12:
        return complete.height, None, ";".join(used)
    slope = float(np.linalg.lstsq(design, y, rcond=None)[0][1])
    return complete.height, slope, ";".join(used)


def _max_proxy_corr(context: pl.DataFrame) -> tuple[float | None, str]:
    best_corr: float | None = None
    best_feature = ""
    for column in PROXY_CHECK_FEATURES:
        if column not in context.columns:
            continue
        subset = context.drop_nulls([CLOUD_FEATURE, column])
        if subset.height < 5:
            continue
        xs = subset[CLOUD_FEATURE].to_numpy().astype(float)
        proxy = subset[column].to_numpy().astype(float)
        if float(np.std(xs)) <= 1e-12 or float(np.std(proxy)) <= 1e-12:
            continue
        corr = abs(float(np.corrcoef(xs, proxy)[0, 1]))
        if best_corr is None or corr > best_corr:
            best_corr = corr
            best_feature = column
    return best_corr, best_feature


def _build_context(
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    train_end: dt.date,
) -> pl.DataFrame:
    feature_by_key = {
        (row["date_local"], str(row["cp"])): row for row in features.iter_rows(named=True)
    }
    label_by_day = {
        row["date_local"]: row
        for row in labels.iter_rows(named=True)
        if bool(row.get("day_complete", True))
    }
    rows: list[dict[str, object]] = []
    extra_columns = [*CONTROL_FEATURES, *PROXY_CHECK_FEATURES]
    for assignment in assignments.iter_rows(named=True):
        date_local = assignment["date_local"]
        if (
            date_local is None
            or date_local > train_end
            or str(assignment["macro_regime_label"]) != CALM_MACRO
        ):
            continue
        feature_row = feature_by_key.get((date_local, str(assignment["cp"])))
        label_row = label_by_day.get(date_local)
        if feature_row is None or label_row is None:
            continue
        cloud_value = _safe_float(feature_row.get(CLOUD_FEATURE))
        tmax = _safe_float(label_row.get("tmax_int"))
        k_cp = _safe_float(label_row.get(f"k_cp__cp_{_cp_code(assignment['cp'])}"))
        if cloud_value is None or tmax is None or k_cp is None:
            continue
        out: dict[str, object] = {
            "date_local": date_local,
            "cp": str(assignment["cp"]),
            "month": int(date_local.month),
            CLOUD_FEATURE: cloud_value,
            "remaining_warming": tmax - k_cp,
        }
        for column in extra_columns:
            value = _safe_float(feature_row.get(column))
            if value is not None:
                out[column] = value
        rows.append(out)
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _validation_decision(
    *,
    n_rows: int,
    overall_corr: float | None,
    overall_slope: float | None,
    cp_negative_slope_share: float | None,
    cell_negative_slope_share: float | None,
    controlled_slope: float | None,
    controlled_slope_retention: float | None,
    max_proxy_abs_corr: float | None,
    min_rows: int,
    min_abs_corr: float,
    min_cp_negative_share: float,
    min_cell_negative_share: float,
    min_controlled_slope_retention: float,
    max_proxy_abs_corr_threshold: float,
) -> tuple[str, str]:
    failures: list[str] = []
    if n_rows < min_rows:
        failures.append("underpowered")
    if overall_slope is None or overall_slope >= 0:
        failures.append("wrong_or_missing_overall_slope")
    if overall_corr is None or abs(overall_corr) < min_abs_corr:
        failures.append("weak_overall_correlation")
    if (
        cp_negative_slope_share is None
        or cp_negative_slope_share < min_cp_negative_share
    ):
        failures.append("cp_instability")
    if (
        cell_negative_slope_share is None
        or cell_negative_slope_share < min_cell_negative_share
    ):
        failures.append("month_cp_instability")
    if controlled_slope is None or controlled_slope >= 0:
        failures.append("controlled_slope_not_negative")
    if (
        controlled_slope_retention is None
        or controlled_slope_retention < min_controlled_slope_retention
    ):
        failures.append("controlled_signal_not_retained")
    if (
        max_proxy_abs_corr is not None
        and max_proxy_abs_corr > max_proxy_abs_corr_threshold
    ):
        failures.append("proxy_correlation_too_high")
    if failures:
        return "FAILS_CAUSAL_ROBUSTNESS_SCREEN", ";".join(failures)
    return (
        "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN",
        "pre_cp_cloud_signal_negative_stable_controlled_and_not_proxy_like",
    )


def _demote_split_matrix(blocker: str) -> pl.DataFrame:
    rows = [
        {
            "experiment_id": CEXP003_ID,
            "candidate_option": "keep_protected_macro",
            "option_label": "Keep calm/radiative as protected macro",
            "blocker": blocker,
            "rationale": (
                "Not preferred if the only calm-specific signal fails causal "
                "robustness; macro protection would remain name-driven."
            ),
            "required_next_artifact": (
                "reports/regime-design/"
                "regime_candidate_assignments_after_calm_decision.csv"
            ),
            "recommended_disposition": "REJECT_IF_SIGNAL_FAILS",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "experiment_id": CEXP003_ID,
            "candidate_option": "demote_to_subtype_audit",
            "option_label": "Demote calm/radiative to subtype or audit layer",
            "blocker": blocker,
            "rationale": (
                "Preferred failure response: preserve diagnostic evidence "
                "without forcing an unsupported production macro."
            ),
            "required_next_artifact": (
                "reports/regime-design/"
                "regime_calm_radiative_demote_audit_validation_v1.csv"
            ),
            "recommended_disposition": "PREFERRED_IF_SIGNAL_FAILS",
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "experiment_id": CEXP003_ID,
            "candidate_option": "split_radiative_clear_cloudy",
            "option_label": "Split radiative-clear and cloudy calm contexts",
            "blocker": blocker,
            "rationale": (
                "Investigate only if demotion loses useful physical structure "
                "or if cloud signal heterogeneity is still informative."
            ),
            "required_next_artifact": (
                "reports/regime-design/"
                "regime_calm_radiative_clear_cloudy_split_v1.csv"
            ),
            "recommended_disposition": "SECONDARY_EXPERIMENT",
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    return pl.DataFrame(rows, schema=DEMOTE_SPLIT_SCHEMA, strict=False)


def build_regime_calm_radiative_cloud_signal_validation(
    *,
    assignments: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    train_end: dt.date,
    min_rows: int = 30,
    min_cell_rows: int = 30,
    min_abs_corr: float = 0.2,
    min_cp_negative_share: float = 0.75,
    min_cell_negative_share: float = 0.75,
    min_controlled_slope_retention: float = 0.4,
    max_proxy_abs_corr: float = 0.8,
) -> dict[str, pl.DataFrame]:
    """Validate whether the cloud-cover signal survives causal audit screens."""
    assignments = _normalize_keys(assignments)
    features = _normalize_keys(features)
    labels = _normalize_keys(labels)
    _validate_inputs(assignments, features, labels)

    context = _build_context(
        assignments,
        features,
        labels,
        train_end=train_end,
    )
    overall_slope, overall_corr = _ols_slope_corr(
        context,
        CLOUD_FEATURE,
        "remaining_warming",
    )
    cp_cells, cp_negative_share = _negative_slope_share(
        context,
        by=["cp"],
        min_rows=min_cell_rows,
    )
    month_cp_cells, cell_negative_share = _negative_slope_share(
        context,
        by=["month", "cp"],
        min_rows=min_cell_rows,
    )
    controlled_rows, controlled_slope, control_features_used = _controlled_slope(
        context,
        CONTROL_FEATURES,
    )
    if overall_slope is not None and controlled_slope is not None:
        controlled_retention = abs(controlled_slope) / abs(overall_slope)
    else:
        controlled_retention = None
    proxy_corr, proxy_feature = _max_proxy_corr(context)

    decision, rationale = _validation_decision(
        n_rows=context.height,
        overall_corr=overall_corr,
        overall_slope=overall_slope,
        cp_negative_slope_share=cp_negative_share,
        cell_negative_slope_share=cell_negative_share,
        controlled_slope=controlled_slope,
        controlled_slope_retention=controlled_retention,
        max_proxy_abs_corr=proxy_corr,
        min_rows=min_rows,
        min_abs_corr=min_abs_corr,
        min_cp_negative_share=min_cp_negative_share,
        min_cell_negative_share=min_cell_negative_share,
        min_controlled_slope_retention=min_controlled_slope_retention,
        max_proxy_abs_corr_threshold=max_proxy_abs_corr,
    )
    next_experiment = (
        "CEXP_003_TRIGGERED"
        if decision == "FAILS_CAUSAL_ROBUSTNESS_SCREEN"
        else "CEXP_003_NOT_TRIGGERED"
    )
    dates = context["date_local"].to_list() if context.height else []
    validation = pl.DataFrame(
        [
            {
                "experiment_id": EXPERIMENT_ID,
                "candidate_version": _candidate_version(assignments),
                "macro_regime_label": CALM_MACRO,
                "feature_column": CLOUD_FEATURE,
                "n_rows": context.height,
                "n_unique_days": (
                    int(context["date_local"].n_unique()) if context.height else 0
                ),
                "date_window_start": _date_text(min(dates)) if dates else "",
                "date_window_end": _date_text(max(dates)) if dates else "",
                "overall_corr": overall_corr,
                "overall_slope": overall_slope,
                "abs_corr": abs(overall_corr) if overall_corr is not None else None,
                "cp_cells_tested": cp_cells,
                "cp_negative_slope_share": cp_negative_share,
                "month_cp_cells_tested": month_cp_cells,
                "cell_negative_slope_share": cell_negative_share,
                "controlled_rows": controlled_rows,
                "controlled_slope": controlled_slope,
                "controlled_slope_retention": controlled_retention,
                "control_features_used": control_features_used,
                "max_proxy_abs_corr": proxy_corr,
                "max_proxy_feature": proxy_feature,
                "lineage_status": "PASS_PRE_CP_CLOUD_OBSERVATION",
                "validation_decision": decision,
                "decision_rationale": rationale,
                "next_experiment": next_experiment,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        schema=VALIDATION_SCHEMA,
        strict=False,
    )
    artifacts = {"regime_calm_radiative_cloud_signal_validation_v1": validation}
    if next_experiment == "CEXP_003_TRIGGERED":
        artifacts["regime_calm_radiative_demote_split_v1"] = _demote_split_matrix(
            rationale
        )
    return artifacts


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    validation = artifacts["regime_calm_radiative_cloud_signal_validation_v1"]
    row = validation.row(0, named=True) if validation.height else {}
    lines = [
        f"# CEXP-CALM-RADIATIVE-002B Cloud Signal Validation - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        (
            "This artifact validates whether `cloud_cover_suppression` is a "
            "causal pre-CP signal or a proxy/artifact."
        ),
        "",
        f"- Decision: {row.get('validation_decision', '')}",
        f"- Rows: {row.get('n_rows', 0)}",
        f"- Overall slope: {row.get('overall_slope', '')}",
        f"- Controlled slope: {row.get('controlled_slope', '')}",
        f"- CP negative slope share: {row.get('cp_negative_slope_share', '')}",
        f"- Month x CP negative slope share: {row.get('cell_negative_slope_share', '')}",
        f"- Max proxy corr: {row.get('max_proxy_abs_corr', '')}",
        f"- Next experiment: {row.get('next_experiment', '')}",
        "",
        "## Decision",
        "",
        (
            "A surviving signal may proceed only to further experiment-only "
            "robustness work. A failing signal triggers the CEXP-003 "
            "demote/split matrix. Neither path promotes Onda 3."
        ),
    ]
    if "regime_calm_radiative_demote_split_v1" in artifacts:
        matrix = artifacts["regime_calm_radiative_demote_split_v1"]
        lines += [
            "",
            "## CEXP-003 Demote/Split Matrix",
            "",
            "| Option | Disposition |",
            "|---|---|",
        ]
        for option in matrix.iter_rows(named=True):
            lines.append(
                "| "
                f"{option['candidate_option']} | "
                f"{option['recommended_disposition']} |"
            )
    return lines


def write_regime_calm_radiative_cloud_signal_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    validation = artifacts["regime_calm_radiative_cloud_signal_validation_v1"]

    validation_csv = out_dir / "regime_calm_radiative_cloud_signal_validation_v1.csv"
    validation_md = out_dir / "regime_calm_radiative_cloud_signal_validation_v1.md"
    validation.write_csv(validation_csv)
    validation_md.write_text(
        "\n".join(_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths = {
        "regime_calm_radiative_cloud_signal_validation_csv": validation_csv,
        "regime_calm_radiative_cloud_signal_validation_md": validation_md,
    }
    if "regime_calm_radiative_demote_split_v1" in artifacts:
        matrix_csv = out_dir / "regime_calm_radiative_demote_split_v1.csv"
        artifacts["regime_calm_radiative_demote_split_v1"].write_csv(matrix_csv)
        paths["regime_calm_radiative_demote_split_csv"] = matrix_csv
    return paths
