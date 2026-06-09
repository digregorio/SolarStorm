"""Target diagnostics for CEXP-CALM-RADIATIVE-001."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

TARGET_DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "month": pl.Int64,
    "cp": pl.Utf8,
    "n_assignment_rows": pl.Int64,
    "n_unique_days": pl.Int64,
    "date_window_start": pl.Utf8,
    "date_window_end": pl.Utf8,
    "remaining_warming_p10": pl.Float64,
    "remaining_warming_p25": pl.Float64,
    "remaining_warming_p50": pl.Float64,
    "remaining_warming_p75": pl.Float64,
    "remaining_warming_p90": pl.Float64,
    "remaining_warming_mean": pl.Float64,
    "remaining_warming_std": pl.Float64,
    "tmax_int_p50": pl.Float64,
    "tmax_hour_p10": pl.Float64,
    "tmax_hour_p50": pl.Float64,
    "tmax_hour_p90": pl.Float64,
    "tmax_hour_before_13_share": pl.Float64,
    "tmax_hour_13_17_share": pl.Float64,
    "tmax_hour_after_17_share": pl.Float64,
    "underpowered_n_lt_min_cell": pl.Boolean,
    "causal_role": pl.Utf8,
    "diagnostic_note": pl.Utf8,
    "production_status": pl.Utf8,
}

EXPERIMENT_ID = "CEXP-CALM-RADIATIVE-001"
CAUSAL_ROLE = "FULL_DAY_TARGET_AUDIT_ONLY"


def _empty_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=TARGET_DIAGNOSTIC_SCHEMA)


def _normalize_keys(frame: pl.DataFrame) -> pl.DataFrame:
    out = frame
    if "date_local" in out.columns and out.schema["date_local"] == pl.Utf8:
        out = out.with_columns(pl.col("date_local").str.to_date())
    if "cp" in out.columns:
        out = out.with_columns(pl.col("cp").cast(pl.Utf8))
    return out


def _validate_inputs(assignments: pl.DataFrame, labels: pl.DataFrame) -> None:
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

    required_labels = {"date_local", "tmax_int", "tmax_hour"}
    missing_labels = required_labels - set(labels.columns)
    if missing_labels:
        raise ValueError(
            "labels missing required columns: "
            f"{', '.join(sorted(missing_labels))}"
        )


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    index = int(q * (len(sorted_values) - 1) + 0.5)
    return float(sorted_values[index])


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return float(variance**0.5)


def _date_text(value: object) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _target_rows(
    assignments: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    train_end: dt.date,
) -> list[dict[str, object]]:
    label_by_day = {
        row["date_local"]: row
        for row in labels.iter_rows(named=True)
        if bool(row.get("day_complete", True))
    }
    rows: list[dict[str, object]] = []
    for row in assignments.iter_rows(named=True):
        date_local = row["date_local"]
        if date_local is None or date_local > train_end:
            continue
        label_row = label_by_day.get(date_local)
        if not label_row:
            continue
        cp = str(row["cp"])
        k_col = f"k_cp__cp_{cp.replace(':', '')}"
        k_cp = label_row.get(k_col)
        tmax = label_row.get("tmax_int")
        tmax_hour = label_row.get("tmax_hour")
        if k_cp is None or tmax is None or tmax_hour is None:
            continue
        rows.append(
            {
                "date_local": date_local,
                "month": int(date_local.month),
                "cp": cp,
                "macro_regime_label": str(row["macro_regime_label"]),
                "remaining_warming": float(tmax) - float(k_cp),
                "tmax_int": float(tmax),
                "tmax_hour": float(tmax_hour),
            }
        )
    return rows


def _aggregate_context(context: pl.DataFrame, *, min_cell_rows: int) -> pl.DataFrame:
    if context.height == 0:
        return _empty_frame()

    rows: list[dict[str, object]] = []
    groups = context.partition_by(
        ["macro_regime_label", "month", "cp"],
        as_dict=True,
        maintain_order=True,
    )
    for key, group in groups.items():
        macro, month, cp = key
        remaining = [float(value) for value in group["remaining_warming"].to_list()]
        tmax_hour = [float(value) for value in group["tmax_hour"].to_list()]
        tmax_int = [float(value) for value in group["tmax_int"].to_list()]
        n_rows = group.height
        before_13 = sum(1 for value in tmax_hour if value < 13.0)
        between_13_17 = sum(1 for value in tmax_hour if 13.0 <= value <= 17.0)
        after_17 = sum(1 for value in tmax_hour if value > 17.0)
        rows.append(
            {
                "experiment_id": EXPERIMENT_ID,
                "candidate_version": "v2.3-target-diagnostic",
                "macro_regime_label": str(macro),
                "month": int(month),
                "cp": str(cp),
                "n_assignment_rows": n_rows,
                "n_unique_days": int(group["date_local"].n_unique()),
                "date_window_start": _date_text(group["date_local"].min()),
                "date_window_end": _date_text(group["date_local"].max()),
                "remaining_warming_p10": _quantile(remaining, 0.10),
                "remaining_warming_p25": _quantile(remaining, 0.25),
                "remaining_warming_p50": _quantile(remaining, 0.50),
                "remaining_warming_p75": _quantile(remaining, 0.75),
                "remaining_warming_p90": _quantile(remaining, 0.90),
                "remaining_warming_mean": _mean(remaining),
                "remaining_warming_std": _std(remaining),
                "tmax_int_p50": _quantile(tmax_int, 0.50),
                "tmax_hour_p10": _quantile(tmax_hour, 0.10),
                "tmax_hour_p50": _quantile(tmax_hour, 0.50),
                "tmax_hour_p90": _quantile(tmax_hour, 0.90),
                "tmax_hour_before_13_share": before_13 / n_rows if n_rows else 0.0,
                "tmax_hour_13_17_share": between_13_17 / n_rows if n_rows else 0.0,
                "tmax_hour_after_17_share": after_17 / n_rows if n_rows else 0.0,
                "underpowered_n_lt_min_cell": n_rows < min_cell_rows,
                "causal_role": CAUSAL_ROLE,
                "diagnostic_note": (
                    "Full-day target distribution for regime-design diagnosis; "
                    "not a CP feature."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, schema=TARGET_DIAGNOSTIC_SCHEMA, strict=False).sort(
        ["macro_regime_label", "month", "cp"]
    )


def build_regime_calm_radiative_target_diagnostics(
    *,
    assignments: pl.DataFrame,
    labels: pl.DataFrame,
    train_end: dt.date,
    min_cell_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Build train-window target diagnostics by macro x month x CP."""
    assignments = _normalize_keys(assignments)
    labels = _normalize_keys(labels)
    _validate_inputs(assignments, labels)
    context = pl.DataFrame(_target_rows(assignments, labels, train_end=train_end))
    diagnostics = _aggregate_context(context, min_cell_rows=min_cell_rows)
    return {"regime_calm_radiative_target_diagnostics_v1": diagnostics}


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    diagnostics = artifacts["regime_calm_radiative_target_diagnostics_v1"]
    calm = (
        diagnostics.filter(pl.col("macro_regime_label") == "macro_calm_radiative")
        if diagnostics.height
        else _empty_frame()
    )
    underpowered = (
        diagnostics.filter(pl.col("underpowered_n_lt_min_cell")).height
        if diagnostics.height
        else 0
    )
    lines = [
        f"# CEXP-CALM-RADIATIVE-001 Target Diagnostics - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        (
            "This artifact uses full-day targets as audit evidence only. "
            f"Causal role: {CAUSAL_ROLE}."
        ),
        "",
        f"- Diagnostic rows: {diagnostics.height}",
        f"- Calm/radiative rows: {calm.height}",
        f"- Underpowered cells: {underpowered}",
        "",
        "## Calm/Radiative Target Cells",
        "",
        "| Month | CP | Rows | Remaining p50 | Remaining p90 | Tmax-hour p50 | Underpowered |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in calm.sort(["month", "cp"]).iter_rows(named=True):
        lines.append(
            "| "
            f"{row['month']} | "
            f"{row['cp']} | "
            f"{row['n_assignment_rows']} | "
            f"{row['remaining_warming_p50']} | "
            f"{row['remaining_warming_p90']} | "
            f"{row['tmax_hour_p50']} | "
            f"{row['underpowered_n_lt_min_cell']} |"
        )
    lines += [
        "",
        "## Decision",
        "",
        (
            "This artifact may guide calm/radiative target and feature "
            "hypotheses, but it does not promote Onda 3 or change production "
            "regime labels."
        ),
    ]
    return lines


def write_regime_calm_radiative_target_diagnostics_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    diagnostics = artifacts["regime_calm_radiative_target_diagnostics_v1"]

    csv_path = out_dir / "regime_calm_radiative_target_diagnostics_v1.csv"
    md_path = out_dir / "regime_calm_radiative_target_diagnostics_v1.md"
    diagnostics.write_csv(csv_path)
    md_path.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")
    return {
        "regime_calm_radiative_target_diagnostics_csv": csv_path,
        "regime_calm_radiative_target_diagnostics_md": md_path,
    }
