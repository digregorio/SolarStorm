"""Offline diagnostics for candidate regime repair work."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "candidate_regime_family": pl.Utf8,
    "assignment_rows": pl.Int64,
    "cp_count": pl.Int64,
    "month_count": pl.Int64,
    "mean_assignment_confidence": pl.Float64,
    "min_assignment_confidence": pl.Float64,
    "mean_distance_to_candidate": pl.Float64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "power_status": pl.Utf8,
    "recommended_repair": pl.Utf8,
    "production_status": pl.Utf8,
}


def _empty_diagnostics() -> pl.DataFrame:
    return pl.DataFrame(schema=DIAGNOSTIC_SCHEMA)


def _normalize_family(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_pass(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "t", "1", "yes", "y", "pass", "passed"}


def _month_count(frame: pl.DataFrame) -> int:
    if frame.height == 0 or "date_local" not in frame.columns:
        return 0
    months = set()
    for value in frame["date_local"].drop_nulls().to_list():
        month = getattr(value, "month", None)
        if month is not None:
            months.add(int(month))
    return len(months)


def _mean(frame: pl.DataFrame, column: str) -> float | None:
    if frame.height == 0 or column not in frame.columns:
        return None
    value = frame[column].mean()
    return float(value) if value is not None else None


def _min(frame: pl.DataFrame, column: str) -> float | None:
    if frame.height == 0 or column not in frame.columns:
        return None
    value = frame[column].min()
    return float(value) if value is not None else None


def _family_assignments(
    assignments: pl.DataFrame,
    *,
    family: str,
    cp_set: tuple[str, ...],
) -> pl.DataFrame:
    if assignments.height == 0:
        return assignments.head(0)
    filters = []
    if "candidate_regime_family" in assignments.columns:
        filters.append(pl.col("candidate_regime_family").map_elements(_normalize_family) == family)
    if "candidate_regime_label" in assignments.columns:
        filters.append(pl.col("candidate_regime_label").map_elements(_normalize_family) == family)
    if not filters:
        return assignments.head(0)
    predicate = filters[0]
    for extra in filters[1:]:
        predicate = predicate | extra
    if "cp" in assignments.columns:
        predicate = predicate & pl.col("cp").cast(pl.Utf8).is_in(cp_set)
    return assignments.filter(predicate)


def _family_r2_rows(
    r2_validation: pl.DataFrame,
    *,
    family: str,
    cp_set: tuple[str, ...],
) -> tuple[int, int]:
    if r2_validation.height == 0 or "regime" not in r2_validation.columns:
        return 0, 0
    predicate = pl.col("regime").map_elements(_normalize_family) == family
    if "cp" in r2_validation.columns:
        predicate = predicate & pl.col("cp").cast(pl.Utf8).is_in(cp_set)
    rows = r2_validation.filter(predicate)
    if rows.height == 0 or "passes" not in rows.columns:
        return rows.height, 0
    pass_rows = sum(1 for value in rows["passes"].to_list() if _normalize_pass(value))
    return rows.height, int(pass_rows)


def _recommended_repair(*, r2_dead_status: str, power_status: str) -> str:
    if r2_dead_status == "DEAD" and power_status == "UNDERPOWERED":
        return "repair candidate family and collect more support before production promotion"
    if r2_dead_status == "DEAD":
        return "repair candidate family before production promotion"
    if power_status == "UNDERPOWERED":
        return "collect more support before production promotion"
    return "keep in design review before production promotion"


def build_regime_repair_diagnostics(
    candidate: pl.DataFrame,
    assignments: pl.DataFrame,
    r2_validation: pl.DataFrame,
    *,
    dead_families: tuple[str, ...] = (
        "candidate_maritime_cloudy",
        "candidate_mixed_or_transition",
    ),
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    min_support_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Build offline dead-family repair diagnostics.

    The candidate frame is accepted for API symmetry with the regime-design
    pipeline. This diagnostic only summarizes assignments and R2 validation.
    """
    _ = candidate
    if not dead_families:
        return {"regime_repair_diagnostics": _empty_diagnostics()}

    rows: list[dict[str, object]] = []
    for raw_family in dead_families:
        family = _normalize_family(raw_family)
        family_assignments = _family_assignments(assignments, family=family, cp_set=cp_set)
        r2_rows, r2_pass_rows = _family_r2_rows(
            r2_validation,
            family=family,
            cp_set=cp_set,
        )
        r2_dead_status = "DEAD" if r2_pass_rows == 0 else "PASS"
        power_status = "UNDERPOWERED" if family_assignments.height < min_support_rows else "OK"
        rows.append(
            {
                "candidate_regime_family": family,
                "assignment_rows": int(family_assignments.height),
                "cp_count": (
                    int(family_assignments["cp"].n_unique())
                    if family_assignments.height and "cp" in family_assignments.columns
                    else 0
                ),
                "month_count": _month_count(family_assignments),
                "mean_assignment_confidence": _mean(
                    family_assignments,
                    "assignment_confidence",
                ),
                "min_assignment_confidence": _min(
                    family_assignments,
                    "assignment_confidence",
                ),
                "mean_distance_to_candidate": _mean(
                    family_assignments,
                    "distance_to_candidate",
                ),
                "r2_rows": int(r2_rows),
                "r2_pass_rows": int(r2_pass_rows),
                "r2_dead_status": r2_dead_status,
                "power_status": power_status,
                "recommended_repair": _recommended_repair(
                    r2_dead_status=r2_dead_status,
                    power_status=power_status,
                ),
                "production_status": "NOT_PRODUCTION",
            }
        )
    return {
        "regime_repair_diagnostics": pl.DataFrame(
            rows,
            schema=DIAGNOSTIC_SCHEMA,
            strict=False,
        )
    }


def _report_lines(diagnostics: pl.DataFrame, report_date: dt.date) -> list[str]:
    lines = [
        f"# Regime Repair Diagnostics v1 - {report_date.isoformat()}",
        "",
        "NOT_PRODUCTION diagnostic artifact for regime-design repair only.",
        "",
        f"Rows: {diagnostics.height}",
        "",
        "| Candidate family | Assignment rows | R2 rows | R2 pass rows | R2 status | Power status | Production status |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in diagnostics.iter_rows(named=True):
        lines.append(
            "| "
            f"{row['candidate_regime_family']} | "
            f"{row['assignment_rows']} | "
            f"{row['r2_rows']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_dead_status']} | "
            f"{row['power_status']} | "
            f"{row['production_status']} |"
        )
    return lines


def write_regime_repair_diagnostics_artifacts(
    artifacts: dict[str, pl.DataFrame],
    output_dir: str | Path,
    *,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write regime repair diagnostics CSV and markdown artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    diagnostics = artifacts["regime_repair_diagnostics"]

    csv_path = out_dir / "regime_repair_diagnostics_v1.csv"
    md_path = out_dir / "regime_repair_diagnostics_v1.md"
    diagnostics.write_csv(csv_path)
    md_path.write_text("\n".join(_report_lines(diagnostics, report_date)), encoding="utf-8")
    return {
        "regime_repair_diagnostics_csv": csv_path,
        "regime_repair_diagnostics_md": md_path,
    }
