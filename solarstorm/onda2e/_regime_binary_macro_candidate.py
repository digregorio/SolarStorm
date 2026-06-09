"""Experiment-only binary macro regime candidate.

Collapses the current three-macro surface into two:

- ``macro_southerly_flow``  — retained unchanged (robust directional macro).
- ``macro_non_southerly``   — absorbs NW, foehn-like, calm/radiative, marine,
  and transition cases.

All outputs carry ``production_status = EXPERIMENT_ONLY`` and must not
overwrite ``data/features.parquet``.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

SOUTHERLY = "macro_southerly_flow"
NON_SOUTHERLY = "macro_non_southerly"


def _source_macro_column(assignments: pl.DataFrame) -> str:
    if "macro_regime_label" in assignments.columns:
        return "macro_regime_label"
    if "candidate_regime_label" in assignments.columns:
        return "candidate_regime_label"
    raise ValueError("assignments require macro_regime_label or candidate_regime_label column")


def build_regime_binary_macro_candidate_artifacts(
    assignments: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Build the binary macro candidate, assignment, and audit artifacts."""
    if "production_status" not in assignments.columns:
        raise ValueError("assignments missing required column: production_status")
    invalid = assignments.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid.height:
        raise ValueError(
            f"source assignments must remain NOT_PRODUCTION; found {invalid.height} row(s) with other status"
        )

    macro_col = _source_macro_column(assignments)
    mapped = assignments.select(
        [
            "date_local",
            "cp",
            pl.col(macro_col).alias("source_macro_regime_label"),
        ]
    ).with_columns(
        pl.when(pl.col("source_macro_regime_label") == SOUTHERLY)
        .then(pl.lit(SOUTHERLY))
        .otherwise(pl.lit(NON_SOUTHERLY))
        .alias("binary_macro_regime_label"),
        pl.lit("southerly vs non-southerly experiment-only collapse").alias("assignment_rule"),
        pl.lit("EXPERIMENT_ONLY").alias("production_status"),
    )

    counts = (
        mapped.group_by("binary_macro_regime_label")
        .len(name="n_rows")
        .rename({"binary_macro_regime_label": "macro_regime_label"})
    )
    candidate = (
        pl.DataFrame(
            [
                {
                    "candidate_version": "binary_v1",
                    "macro_regime_label": SOUTHERLY,
                    "description": ("Southerly/frontal flow retained as the robust directional macro."),
                    "production_status": "EXPERIMENT_ONLY",
                },
                {
                    "candidate_version": "binary_v1",
                    "macro_regime_label": NON_SOUTHERLY,
                    "description": (
                        "NW, foehn-like, calm/radiative, marine, and transition cases collapsed."
                    ),
                    "production_status": "EXPERIMENT_ONLY",
                },
            ],
            strict=False,
        )
        .join(counts, on="macro_regime_label", how="left")
        .with_columns(pl.col("n_rows").fill_null(0))
    )

    audit = pl.DataFrame(
        [
            {
                "audit_item": "source_production_status",
                "status": "PASS",
                "detail": "All source assignment rows are NOT_PRODUCTION.",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "audit_item": "binary_label_set",
                "status": "PASS",
                "detail": ("Assignments use only macro_southerly_flow and macro_non_southerly."),
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )
    return {
        "regime_binary_macro_candidate_v1": candidate,
        "regime_binary_macro_assignments_v1": mapped,
        "regime_binary_macro_assignment_audit_v1": audit,
    }


def write_regime_binary_macro_candidate_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write binary candidate CSVs and markdown report."""
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_csv = out_dir / "regime_binary_macro_candidate_v1.csv"
    candidate_md = out_dir / "regime_binary_macro_candidate_v1.md"
    assignments_csv = out_dir / "regime_binary_macro_assignments_v1.csv"
    audit_csv = out_dir / "regime_binary_macro_assignment_audit_v1.csv"
    artifacts["regime_binary_macro_candidate_v1"].write_csv(candidate_csv)
    artifacts["regime_binary_macro_assignments_v1"].write_csv(assignments_csv)
    artifacts["regime_binary_macro_assignment_audit_v1"].write_csv(audit_csv)
    lines = [
        f"# Regime Binary Macro Candidate - {today.isoformat()}",
        "",
        "This is an experiment-only candidate and not a production classifier.",
        "",
        "| macro | rows |",
        "|---|---:|",
    ]
    for row in artifacts["regime_binary_macro_candidate_v1"].iter_rows(named=True):
        lines.append(f"| {row['macro_regime_label']} | {row['n_rows']} |")
    candidate_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "regime_binary_macro_candidate_csv": candidate_csv,
        "regime_binary_macro_candidate_md": candidate_md,
        "regime_binary_macro_assignments_csv": assignments_csv,
        "regime_binary_macro_assignment_audit_csv": audit_csv,
    }
