"""Calm/radiative restoration artifacts for Regime Ontology v2.2."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda2e._regime_design_validation import (
    _as_bool_passes,
    _r2_summary_for_regime,
)
from solarstorm.robustness._regime_analysis import detect_dead_regimes

PROTECTED_V22_MACROS: tuple[str, ...] = (
    "macro_calm_radiative",
    "macro_nw_continuum",
    "macro_southerly_flow",
)

ASSIGNMENT_V22_SCHEMA: dict[str, pl.DataType] = {
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
    "original_v21_macro_regime_label": pl.Utf8,
    "original_v21_subtype_label": pl.Utf8,
    "reassigned_to_calm_radiative": pl.Boolean,
    "calm_radiative_rule_score": pl.Int64,
    "calm_radiative_rule_reason": pl.Utf8,
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_V22_SCHEMA: dict[str, pl.DataType] = {
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "reassigned_calm_radiative_rows": pl.Int64,
    "production_status": pl.Utf8,
}

AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "diagnostic_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
    "n_rows": pl.Int64,
    "production_status": pl.Utf8,
}

COMPARISON_V22_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "reassigned_calm_radiative_rows": pl.Int64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "v21_dead_regimes": pl.Int64,
    "v22_dead_regimes": pl.Int64,
    "protected_regression_flag": pl.Boolean,
    "underpowered_macro_flag": pl.Boolean,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
}

PHYSICAL_COLUMNS: tuple[str, ...] = (
    "sknt_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp",
)


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _normalize_keys(frame: pl.DataFrame) -> pl.DataFrame:
    out = frame
    if "date_local" in out.columns and out.schema["date_local"] == pl.Utf8:
        out = out.with_columns(pl.col("date_local").str.to_date())
    if "cp" in out.columns:
        out = out.with_columns(pl.col("cp").cast(pl.Utf8))
    return out


def _validate_inputs(assignments_v21: pl.DataFrame, physical_matrix: pl.DataFrame) -> None:
    required_assignments = {
        "candidate_version",
        "date_local",
        "cp",
        "macro_regime_label",
        "subtype_label",
        "candidate_regime_label",
        "assignment_confidence",
        "low_confidence_flag",
        "causal_window",
        "production_status",
    }
    missing_assignments = required_assignments - set(assignments_v21.columns)
    if missing_assignments:
        raise ValueError(
            "assignments_v21 missing required columns: "
            f"{', '.join(sorted(missing_assignments))}"
        )
    required_matrix = {"date_local", "cp", *PHYSICAL_COLUMNS}
    missing_matrix = required_matrix - set(physical_matrix.columns)
    if missing_matrix:
        raise ValueError(
            "physical_matrix missing required columns: "
            f"{', '.join(sorted(missing_matrix))}"
        )
    if assignments_v21.filter(pl.col("candidate_version") != "v2.1").height:
        raise ValueError("assignments_v21 must have candidate_version = v2.1")
    if assignments_v21.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("assignments_v21 production_status must be NOT_PRODUCTION")
    if "causal_window" in assignments_v21.columns:
        bad_window = assignments_v21.filter(pl.col("causal_window") != "valid < CP")
        if bad_window.height:
            raise ValueError("assignments_v21 causal_window must be valid < CP")


def _quantile(frame: pl.DataFrame, column: str, q: float) -> float:
    value = frame.select(pl.col(column).quantile(q)).item()
    if value is None:
        raise ValueError(f"physical_matrix column {column} has no usable values")
    return float(value)


def _thresholds(physical_matrix: pl.DataFrame) -> dict[str, float]:
    return {
        "wind_low_q25": _quantile(physical_matrix, "sknt_mean", 0.25),
        "relh_high_q75": _quantile(physical_matrix, "relh_mean", 0.75),
        "dewpoint_depression_low_q25": _quantile(
            physical_matrix,
            "dewpoint_depression_mean",
            0.25,
        ),
        "cloud_cover_high_q75": _quantile(physical_matrix, "cloud_cover_score_mean", 0.75),
        "temp_slope_weak_q25": _quantile(physical_matrix, "temp_slope_pre_cp", 0.25),
    }


def _with_calm_rule(
    joined: pl.DataFrame,
    thresholds: dict[str, float],
) -> pl.DataFrame:
    return (
        joined.with_columns(
            [
                (pl.col("sknt_mean") <= thresholds["wind_low_q25"])
                .fill_null(False)
                .alias("low_wind_signal"),
                (pl.col("relh_mean") >= thresholds["relh_high_q75"])
                .fill_null(False)
                .alias("humid_signal"),
                (
                    pl.col("dewpoint_depression_mean")
                    <= thresholds["dewpoint_depression_low_q25"]
                )
                .fill_null(False)
                .alias("low_dewpoint_depression_signal"),
                (pl.col("cloud_cover_score_mean") >= thresholds["cloud_cover_high_q75"])
                .fill_null(False)
                .alias("cloudy_signal"),
                (pl.col("temp_slope_pre_cp") <= thresholds["temp_slope_weak_q25"])
                .fill_null(False)
                .alias("weak_pre_cp_slope_signal"),
            ]
        )
        .with_columns(
            (
                pl.col("low_wind_signal").cast(pl.Int64)
                + pl.col("humid_signal").cast(pl.Int64)
                + pl.col("low_dewpoint_depression_signal").cast(pl.Int64)
                + pl.col("cloudy_signal").cast(pl.Int64)
                + pl.col("weak_pre_cp_slope_signal").cast(pl.Int64)
            ).alias("calm_radiative_rule_score")
        )
        .with_columns(
            (
                pl.col("low_wind_signal")
                & ((pl.col("calm_radiative_rule_score") - 1) >= 2)
            ).alias("reassigned_to_calm_radiative")
        )
    )


def _rule_reason(row: dict[str, object]) -> str:
    if not bool(row["reassigned_to_calm_radiative"]):
        return "v2.1 macro retained; calm/radiative physical rule not met."
    signals = [
        "low_wind" if row["low_wind_signal"] else "",
        "humid" if row["humid_signal"] else "",
        "low_dewpoint_depression" if row["low_dewpoint_depression_signal"] else "",
        "cloudy" if row["cloudy_signal"] else "",
        "weak_pre_cp_slope" if row["weak_pre_cp_slope_signal"] else "",
    ]
    return "calm/radiative restored from physical signals: " + ",".join(
        signal for signal in signals if signal
    )


def _assignments(joined: pl.DataFrame) -> pl.DataFrame:
    if joined.height == 0:
        return _empty_frame(ASSIGNMENT_V22_SCHEMA)
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        reassign = bool(row["reassigned_to_calm_radiative"])
        original_macro = str(row["macro_regime_label"])
        original_subtype = str(row["subtype_label"])
        out = dict(row)
        out.update(
            {
                "candidate_version": "v2.2",
                "macro_regime_label": (
                    "macro_calm_radiative" if reassign else original_macro
                ),
                "subtype_label": (
                    "subtype_calm_radiative" if reassign else original_subtype
                ),
                "candidate_regime_label": (
                    "macro_calm_radiative" if reassign else original_macro
                ),
                "original_v21_macro_regime_label": original_macro,
                "original_v21_subtype_label": original_subtype,
                "calm_radiative_rule_score": int(row["calm_radiative_rule_score"]),
                "calm_radiative_rule_reason": _rule_reason(row),
                "assignment_confidence": (
                    max(float(row["assignment_confidence"] or 0.0), 0.7)
                    if reassign
                    else float(row["assignment_confidence"] or 0.0)
                ),
                "component_entropy": (
                    0.0 if reassign else float(row.get("component_entropy") or 0.0)
                ),
                "component_margin": (
                    max(float(row.get("component_margin") or 0.0), 0.7)
                    if reassign
                    else float(row.get("component_margin") or 0.0)
                ),
                "low_confidence_flag": (
                    False if reassign else bool(row.get("low_confidence_flag"))
                ),
                "production_status": "NOT_PRODUCTION",
            }
        )
        rows.append(out)
    return pl.DataFrame(rows, schema=ASSIGNMENT_V22_SCHEMA, strict=False)


def _ontology(assignments: pl.DataFrame) -> pl.DataFrame:
    if assignments.height == 0:
        return _empty_frame(ONTOLOGY_V22_SCHEMA)
    return (
        assignments.group_by("macro_regime_label")
        .agg(
            pl.len().alias("assignment_rows"),
            pl.col("reassigned_to_calm_radiative")
            .sum()
            .alias("reassigned_calm_radiative_rows"),
        )
        .with_columns(pl.lit("NOT_PRODUCTION").alias("production_status"))
        .select(list(ONTOLOGY_V22_SCHEMA))
    )


def _audit(
    assignments: pl.DataFrame,
    joined: pl.DataFrame,
    thresholds: dict[str, float],
    *,
    min_assignment_rows: int,
) -> pl.DataFrame:
    reassigned = (
        assignments.filter(pl.col("reassigned_to_calm_radiative"))
        if assignments.height
        else _empty_frame(ASSIGNMENT_V22_SCHEMA)
    )
    missing_physical = (
        joined.filter(pl.any_horizontal([pl.col(column).is_null() for column in PHYSICAL_COLUMNS])).height
        if joined.height
        else 0
    )
    calm_cp_min = (
        int(reassigned.group_by("cp").len(name="n")["n"].min())
        if reassigned.height
        else 0
    )
    threshold_detail = "; ".join(
        f"{key}={value:.6f}" for key, value in thresholds.items()
    )
    rows = [
        {
            "diagnostic_item": "physical_thresholds",
            "status": "PASS",
            "detail": threshold_detail,
            "n_rows": joined.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "calm_radiative_candidate_rows",
            "status": "PASS" if reassigned.height >= min_assignment_rows else "WARN",
            "detail": (
                f"{reassigned.height} rows meet the v2.2 calm/radiative physical rule."
            ),
            "n_rows": reassigned.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "calm_radiative_cp_support",
            "status": "PASS" if calm_cp_min >= min_assignment_rows else "WARN",
            "detail": (
                f"Smallest CP support for calm/radiative is {calm_cp_min} rows."
            ),
            "n_rows": calm_cp_min,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "missing_physical_rule_inputs",
            "status": "PASS" if missing_physical == 0 else "WARN",
            "detail": f"{missing_physical} joined rows have at least one missing rule input.",
            "n_rows": missing_physical,
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "diagnostic_item": "production_status",
            "status": (
                "PASS"
                if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height
                == 0
                else "FAIL"
            ),
            "detail": "v2.2 assignments remain NOT_PRODUCTION.",
            "n_rows": assignments.height,
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    return pl.DataFrame(rows, schema=AUDIT_SCHEMA, strict=False)


def build_regime_v22_calm_radiative_artifacts(
    assignments_v21: pl.DataFrame,
    physical_matrix: pl.DataFrame,
    *,
    min_assignment_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Restore calm/radiative as a protected non-production v2.2 macro."""
    assignments_v21 = _normalize_keys(assignments_v21)
    physical_matrix = _normalize_keys(physical_matrix)
    _validate_inputs(assignments_v21, physical_matrix)
    thresholds = _thresholds(physical_matrix)
    joined = assignments_v21.join(
        physical_matrix.select(["date_local", "cp", *PHYSICAL_COLUMNS]),
        on=["date_local", "cp"],
        how="left",
    )
    joined = _with_calm_rule(joined, thresholds)
    assignments = _assignments(joined)
    return {
        "regime_candidate_assignments_v2_2": assignments,
        "regime_candidate_ontology_v2_2": _ontology(assignments),
        "regime_calm_radiative_reassignment_audit": _audit(
            assignments,
            joined,
            thresholds,
            min_assignment_rows=min_assignment_rows,
        ),
    }


def _reassigned_rows_for_macro(assignments: pl.DataFrame, macro: str) -> int:
    if assignments.height == 0:
        return 0
    return assignments.filter(
        (pl.col("macro_regime_label") == macro)
        & pl.col("reassigned_to_calm_radiative").fill_null(False)
    ).height


def _assignment_rows_for_macro(assignments: pl.DataFrame, macro: str) -> int:
    if assignments.height == 0:
        return 0
    return assignments.filter(pl.col("macro_regime_label") == macro).height


def compare_regime_candidate_v21_v22(
    *,
    v21_r2: pl.DataFrame,
    v22_r2: pl.DataFrame,
    v22_assignments: pl.DataFrame,
    v21_regimes: tuple[str, ...],
    v22_regimes: tuple[str, ...],
    protected_v22_regimes: tuple[str, ...] = PROTECTED_V22_MACROS,
    min_assignment_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Compare v2.1 and v2.2 macro R2 status after calm/radiative restoration."""
    if v22_assignments.height:
        if v22_assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
            raise ValueError("v22_assignments production_status must be NOT_PRODUCTION")
        if v22_assignments.filter(pl.col("candidate_version") != "v2.2").height:
            raise ValueError("v22_assignments must have candidate_version = v2.2")
    v21_norm = _as_bool_passes(v21_r2)
    v22_norm = _as_bool_passes(v22_r2)
    v21_dead = detect_dead_regimes(v21_norm, regimes=v21_regimes)
    v22_dead = detect_dead_regimes(v22_norm, regimes=v22_regimes)
    regressions = sorted(set(v22_dead) & set(protected_v22_regimes))
    missing_protected = [
        macro
        for macro in protected_v22_regimes
        if _assignment_rows_for_macro(v22_assignments, macro) == 0
    ]
    underpowered = [
        macro
        for macro in protected_v22_regimes
        if _assignment_rows_for_macro(v22_assignments, macro) < min_assignment_rows
    ]
    decision = (
        "READY_FOR_FULL_ONDA4_RERUN"
        if not v22_dead and not regressions and not missing_protected and not underpowered
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    rows: list[dict[str, object]] = []
    for macro in v22_regimes:
        r2_rows, r2_pass_rows = _r2_summary_for_regime(v22_norm, macro)
        rows.append(
            {
                "candidate_version": "v2.2",
                "macro_regime_label": macro,
                "assignment_rows": _assignment_rows_for_macro(v22_assignments, macro),
                "reassigned_calm_radiative_rows": _reassigned_rows_for_macro(
                    v22_assignments,
                    macro,
                ),
                "r2_rows": r2_rows,
                "r2_pass_rows": r2_pass_rows,
                "r2_dead_status": "DEAD" if macro in v22_dead else "PASS",
                "v21_dead_regimes": len(v21_dead),
                "v22_dead_regimes": len(v22_dead),
                "protected_regression_flag": (
                    macro in regressions or macro in missing_protected
                ),
                "underpowered_macro_flag": macro in underpowered,
                "decision_update": decision,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return {
        "regime_candidate_v21_v22_comparison": pl.DataFrame(
            rows,
            schema=COMPARISON_V22_SCHEMA,
            strict=False,
        )
    }


def _audit_report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    audit = artifacts["regime_calm_radiative_reassignment_audit"]
    assignments = artifacts["regime_candidate_assignments_v2_2"]
    calm_rows = (
        assignments.filter(pl.col("macro_regime_label") == "macro_calm_radiative").height
        if assignments.height
        else 0
    )
    lines = [
        f"# Regime v2.2 Calm/Radiative Reassignment Audit - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        "v2.2 restores calm/radiative from audited physical pre-CP signals.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Calm/radiative rows: {calm_rows}",
        "",
        "| Diagnostic | Status | Rows | Detail |",
        "|---|---|---:|---|",
    ]
    for row in audit.iter_rows(named=True):
        lines.append(
            f"| {row['diagnostic_item']} | {row['status']} | "
            f"{row['n_rows']} | {row['detail']} |"
        )
    return lines


def _validation_report_lines(
    artifacts: dict[str, pl.DataFrame],
    today: dt.date,
) -> list[str]:
    assignments = artifacts["regime_candidate_assignments_v2_2"]
    comparison = artifacts["regime_candidate_v21_v22_comparison"]
    decision = (
        str(comparison["decision_update"][0])
        if comparison.height and "decision_update" in comparison.columns
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    dead_count = (
        int(comparison["v22_dead_regimes"][0])
        if comparison.height and "v22_dead_regimes" in comparison.columns
        else 0
    )
    calm_rows = (
        assignments.filter(pl.col("macro_regime_label") == "macro_calm_radiative").height
        if assignments.height
        else 0
    )
    lines = [
        f"# Regime Candidate v2.2 Validation - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        "Regime Ontology v2.2 is a calm/radiative restoration screening experiment.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Calm/radiative rows: {calm_rows}",
        f"- v2.2 dead macros: {dead_count}",
        f"- Decision update: {decision}",
        "",
        "## v2.1-v2.2 Comparison",
        "",
        "| Macro regime | Assignments | Calm/radiative reassignments | R2 pass rows | Dead status | Decision |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in comparison.sort("macro_regime_label").iter_rows(named=True):
        lines.append(
            "| "
            f"{row['macro_regime_label']} | "
            f"{row['assignment_rows']} | "
            f"{row['reassigned_calm_radiative_rows']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_dead_status']} | "
            f"{row['decision_update']} |"
        )
    lines += [
        "",
        "## Next Action",
        "",
        (
            "Run corrected physical Onda C against v2.2 before any Onda 3 promotion."
            if decision == "READY_FOR_FULL_ONDA4_RERUN"
            else "Keep Onda 3 blocked and revise v2.2 before a full Onda 4/Onda C promotion path."
        ),
    ]
    return lines


def write_regime_v22_calm_radiative_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments_v2_2": "regime_candidate_assignments_v2_2.csv",
        "regime_candidate_ontology_v2_2": "regime_candidate_ontology_v2_2.csv",
        "regime_calm_radiative_reassignment_audit": (
            "regime_calm_radiative_reassignment_audit_v1.csv"
        ),
    }
    if "regime_candidate_r2_validation" in artifacts:
        filenames["regime_candidate_r2_validation"] = (
            "regime_candidate_r2_validation_v2_2.csv"
        )
    if "regime_candidate_v21_v22_comparison" in artifacts:
        filenames["regime_candidate_v21_v22_comparison"] = (
            "regime_candidate_v21_v22_comparison.csv"
        )
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    audit_report = out_dir / "regime_calm_radiative_reassignment_audit_v1.md"
    audit_report.write_text(
        "\n".join(_audit_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_calm_radiative_reassignment_audit_md"] = audit_report
    if "regime_candidate_v21_v22_comparison" in artifacts:
        validation_report = out_dir / "regime_candidate_v22_validation_report.md"
        validation_report.write_text(
            "\n".join(_validation_report_lines(artifacts, report_date)),
            encoding="utf-8",
        )
        paths["regime_candidate_v22_validation_report_md"] = validation_report
    return paths
