"""Residual absorption artifacts for Regime Ontology v2.1."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

PHYSICAL_MACROS: tuple[str, ...] = ("macro_nw_continuum", "macro_southerly_flow")
RESIDUAL_MACRO = "macro_light_marine_or_residual"

ASSIGNMENT_V21_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "date_local": pl.Date,
    "cp": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "candidate_regime_label": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "component_argmax": pl.Utf8,
    "component_probabilities": pl.Utf8,
    "family_probabilities": pl.Utf8,
    "component_entropy": pl.Float64,
    "component_margin": pl.Float64,
    "nearest_alternative_macro": pl.Utf8,
    "distance_to_candidate": pl.Float64,
    "distance_to_alternative": pl.Float64,
    "assignment_confidence": pl.Float64,
    "low_confidence_flag": pl.Boolean,
    "original_macro_regime_label": pl.Utf8,
    "original_subtype_label": pl.Utf8,
    "absorbed_from_residual": pl.Boolean,
    "residual_absorption_reason": pl.Utf8,
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_V21_SCHEMA: dict[str, pl.DataType] = {
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "absorbed_residual_rows": pl.Int64,
    "production_status": pl.Utf8,
}

DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "diagnostic_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
    "n_rows": pl.Int64,
    "production_status": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _validate_assignments(assignments_v2: pl.DataFrame) -> None:
    required = set(ASSIGNMENT_V21_SCHEMA) - {
        "candidate_version",
        "original_macro_regime_label",
        "original_subtype_label",
        "absorbed_from_residual",
        "residual_absorption_reason",
    }
    missing = required - set(assignments_v2.columns)
    if missing:
        msg = f"assignments_v2 missing required columns: {', '.join(sorted(missing))}"
        raise ValueError(msg)
    invalid = assignments_v2.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid.height:
        raise ValueError("assignments_v2 production_status must be NOT_PRODUCTION")


def _absorb_row(row: dict[str, object]) -> dict[str, object]:
    original_macro = str(row["macro_regime_label"])
    original_subtype = str(row["subtype_label"])
    nearest = str(row.get("nearest_alternative_macro") or "")
    absorbed = original_macro == RESIDUAL_MACRO and nearest in PHYSICAL_MACROS
    invalid_target = original_macro == RESIDUAL_MACRO and nearest not in PHYSICAL_MACROS
    macro = nearest if absorbed else original_macro
    reason = (
        f"Residual macro absorbed into nearest physical macro {nearest}."
        if absorbed
        else (
            "Residual macro retained for audit because nearest alternative is invalid."
            if invalid_target
            else "Original physical macro retained."
        )
    )
    out = dict(row)
    out.update(
        {
            "candidate_version": "v2.1",
            "macro_regime_label": macro,
            "candidate_regime_label": macro,
            "original_macro_regime_label": original_macro,
            "original_subtype_label": original_subtype,
            "absorbed_from_residual": absorbed,
            "residual_absorption_reason": reason,
        }
    )
    return out


def _diagnostics(assignments: pl.DataFrame) -> pl.DataFrame:
    residual = assignments.filter(pl.col("original_macro_regime_label") == RESIDUAL_MACRO)
    invalid = residual.filter(~pl.col("macro_regime_label").is_in(PHYSICAL_MACROS))
    absorbed = assignments.filter(pl.col("absorbed_from_residual"))
    low_confidence = residual.filter(pl.col("low_confidence_flag"))
    low_share = float(low_confidence.height / residual.height) if residual.height else 0.0
    rows = [
        {
            "diagnostic_item": "residual_row_count",
            "status": "WARN" if residual.height else "PASS",
            "detail": f"{residual.height} v2 residual rows were evaluated for absorption.",
            "n_rows": residual.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "residual_low_confidence_share",
            "status": "WARN" if low_share > 0.5 else "PASS",
            "detail": f"{low_share:.6f} residual rows are low confidence.",
            "n_rows": low_confidence.height if residual.height else 0,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "invalid_absorption_targets",
            "status": "PASS" if invalid.height == 0 else "FAIL",
            "detail": (
                f"{invalid.height} residual rows lack a valid physical nearest "
                "alternative."
            ),
            "n_rows": invalid.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "absorbed_row_count",
            "status": "PASS",
            "detail": (
                f"{absorbed.height} residual rows were absorbed into physical macros."
            ),
            "n_rows": absorbed.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "v21_macro_count",
            "status": "PASS",
            "detail": (
                f"{assignments['macro_regime_label'].n_unique() if assignments.height else 0} "
                "v2.1 macros remain."
            ),
            "n_rows": (
                assignments["macro_regime_label"].n_unique() if assignments.height else 0
            ),
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "production_status",
            "status": (
                "PASS"
                if assignments.filter(
                    pl.col("production_status") != "NOT_PRODUCTION"
                ).height
                == 0
                else "FAIL"
            ),
            "detail": "v2.1 assignments remain NOT_PRODUCTION.",
            "n_rows": assignments.height,
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    return pl.DataFrame(rows, schema=DIAGNOSTIC_SCHEMA, strict=False)


def _ontology(assignments: pl.DataFrame) -> pl.DataFrame:
    if assignments.height == 0:
        return _empty_frame(ONTOLOGY_V21_SCHEMA)
    return (
        assignments.group_by("macro_regime_label")
        .agg(
            pl.len().alias("assignment_rows"),
            pl.col("absorbed_from_residual").sum().alias("absorbed_residual_rows"),
        )
        .with_columns(pl.lit("NOT_PRODUCTION").alias("production_status"))
        .select(list(ONTOLOGY_V21_SCHEMA))
    )


def build_regime_residual_absorption_artifacts(
    assignments_v2: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    _validate_assignments(assignments_v2)
    rows = [_absorb_row(row) for row in assignments_v2.iter_rows(named=True)]
    assignments = (
        pl.DataFrame(rows, schema=ASSIGNMENT_V21_SCHEMA, strict=False)
        if rows
        else _empty_frame(ASSIGNMENT_V21_SCHEMA)
    )
    return {
        "regime_candidate_assignments_v2_1": assignments,
        "regime_candidate_ontology_v2_1": _ontology(assignments),
        "regime_residual_absorption_diagnostics": _diagnostics(assignments),
    }


def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    assignments = artifacts["regime_candidate_assignments_v2_1"]
    diagnostics = artifacts["regime_residual_absorption_diagnostics"]
    absorbed = (
        assignments.filter(pl.col("absorbed_from_residual")).height
        if assignments.height
        else 0
    )
    lines = [
        f"# Regime Residual Absorption Diagnostics - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        (
            "Regime v2.1 absorbs residual assignments into nearest physical macros "
            "for screening only."
        ),
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Absorbed residual rows: {absorbed}",
        "",
        "| Diagnostic | Status | Rows | Detail |",
        "|---|---|---:|---|",
    ]
    for row in diagnostics.iter_rows(named=True):
        lines.append(
            f"| {row['diagnostic_item']} | {row['status']} | "
            f"{row['n_rows']} | {row['detail']} |"
        )
    return lines


def write_regime_residual_absorption_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments_v2_1": "regime_candidate_assignments_v2_1.csv",
        "regime_candidate_ontology_v2_1": "regime_candidate_ontology_v2_1.csv",
        "regime_residual_absorption_diagnostics": (
            "regime_residual_absorption_diagnostics_v1.csv"
        ),
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    report_path = out_dir / "regime_residual_absorption_diagnostics_v1.md"
    report_path.write_text(
        "\n".join(_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_residual_absorption_diagnostics_md"] = report_path
    return paths
