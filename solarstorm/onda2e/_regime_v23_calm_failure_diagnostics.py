"""v2.3 diagnostics for the calm/radiative regime-design blocker."""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

DIAGNOSTIC_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "unique_days": pl.Int64,
    "cp_count": pl.Int64,
    "smallest_cp_support": pl.Int64,
    "reassigned_rows": pl.Int64,
    "source_macro_summary": pl.Utf8,
    "low_confidence_share": pl.Float64,
    "mean_assignment_confidence": pl.Float64,
    "mean_component_entropy": pl.Float64,
    "mean_component_margin": pl.Float64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_pass_share": pl.Float64,
    "r2_dead_status": pl.Utf8,
    "r2_median_n_days": pl.Float64,
    "r2_min_n_days": pl.Int64,
    "r2_max_n_days": pl.Int64,
    "tested_feature_columns": pl.Utf8,
    "feature_coverage_share": pl.Float64,
    "feature_coverage_status": pl.Utf8,
    "target_complete_days": pl.Int64,
    "target_tmax_median": pl.Float64,
    "target_remaining_warming_median": pl.Float64,
    "sample_support_status": pl.Utf8,
    "diagnosis": pl.Utf8,
    "recommended_next_action": pl.Utf8,
    "production_status": pl.Utf8,
}

NEXT_EXPERIMENT_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "domain": pl.Utf8,
    "blocker": pl.Utf8,
    "required_artifact": pl.Utf8,
    "recommended_experiment": pl.Utf8,
    "rationale": pl.Utf8,
    "production_status": pl.Utf8,
}

CALM_MACRO = "macro_calm_radiative"


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _normalize_keys(frame: pl.DataFrame) -> pl.DataFrame:
    out = frame
    if "date_local" in out.columns and out.schema["date_local"] == pl.Utf8:
        out = out.with_columns(pl.col("date_local").str.to_date())
    if "cp" in out.columns:
        out = out.with_columns(pl.col("cp").cast(pl.Utf8))
    return out


def _normalize_pass(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {
        "true",
        "t",
        "1",
        "yes",
        "y",
        "pass",
        "passed",
    }


def _validate_inputs(
    assignments: pl.DataFrame,
    r2_validation: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
) -> None:
    required_assignments = {
        "date_local",
        "cp",
        "macro_regime_label",
        "candidate_regime_label",
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

    required_r2 = {"regime", "passes", "cp"}
    missing_r2 = required_r2 - set(r2_validation.columns)
    if missing_r2:
        raise ValueError(
            "r2_validation missing required columns: "
            f"{', '.join(sorted(missing_r2))}"
        )

    required_features = {"date_local", "cp"}
    missing_features = required_features - set(features.columns)
    if missing_features:
        raise ValueError(
            "features missing required columns: "
            f"{', '.join(sorted(missing_features))}"
        )

    if "date_local" not in labels.columns:
        raise ValueError("labels missing required column: date_local")


def _mean(frame: pl.DataFrame, column: str) -> float | None:
    if frame.height == 0 or column not in frame.columns:
        return None
    value = frame[column].mean()
    return float(value) if value is not None and math.isfinite(float(value)) else None


def _median(frame: pl.DataFrame, column: str) -> float | None:
    if frame.height == 0 or column not in frame.columns:
        return None
    value = frame[column].median()
    return float(value) if value is not None and math.isfinite(float(value)) else None


def _min_int(frame: pl.DataFrame, column: str) -> int:
    if frame.height == 0 or column not in frame.columns:
        return 0
    value = frame[column].min()
    return int(value) if value is not None else 0


def _max_int(frame: pl.DataFrame, column: str) -> int:
    if frame.height == 0 or column not in frame.columns:
        return 0
    value = frame[column].max()
    return int(value) if value is not None else 0


def _smallest_cp_support(frame: pl.DataFrame) -> int:
    if frame.height == 0 or "cp" not in frame.columns:
        return 0
    value = frame.group_by("cp").len(name="n")["n"].min()
    return int(value) if value is not None else 0


def _source_macro_summary(frame: pl.DataFrame) -> str:
    if frame.height == 0 or "original_v21_macro_regime_label" not in frame.columns:
        return ""
    grouped = (
        frame.group_by("original_v21_macro_regime_label")
        .len(name="n")
        .sort("original_v21_macro_regime_label")
    )
    return ";".join(
        f"{row['original_v21_macro_regime_label']}={row['n']}"
        for row in grouped.iter_rows(named=True)
    )


def _tested_features(r2_subset: pl.DataFrame) -> list[str]:
    if r2_subset.height == 0 or "feature_column" not in r2_subset.columns:
        return []
    return sorted(str(value) for value in r2_subset["feature_column"].drop_nulls().unique())


def _feature_coverage_share(
    macro_assignments: pl.DataFrame,
    features: pl.DataFrame,
    feature_columns: list[str],
) -> float | None:
    available = [column for column in feature_columns if column in features.columns]
    if not available:
        return None
    keys = macro_assignments.select(["date_local", "cp"]).unique()
    if keys.height == 0:
        return 0.0
    joined = keys.join(features.select(["date_local", "cp", *available]), on=["date_local", "cp"], how="left")
    total_cells = joined.height * len(available)
    if total_cells == 0:
        return 0.0
    non_null = sum(joined[column].drop_nulls().len() for column in available)
    return float(non_null / total_cells)


def _target_summary(
    macro_assignments: pl.DataFrame,
    labels: pl.DataFrame,
) -> tuple[int, float | None, float | None]:
    if macro_assignments.height == 0:
        return 0, None, None
    day_keys = macro_assignments.select("date_local").unique()
    label_cols = ["date_local"]
    for column in ("day_complete", "tmax_int"):
        if column in labels.columns:
            label_cols.append(column)
    joined = day_keys.join(labels.select(label_cols), on="date_local", how="left")
    if "day_complete" in joined.columns:
        joined = joined.filter(pl.col("day_complete").fill_null(False))
    target_complete_days = joined.height
    tmax_median = _median(joined, "tmax_int")
    remaining_values: list[float] = []
    cp_codes = sorted(str(value).replace(":", "") for value in macro_assignments["cp"].drop_nulls().unique())
    labels_by_day = {
        row["date_local"]: row
        for row in labels.iter_rows(named=True)
        if "date_local" in row and (row.get("day_complete", True) is True)
    }
    for row in macro_assignments.select(["date_local", "cp"]).iter_rows(named=True):
        label_row = labels_by_day.get(row["date_local"])
        if not label_row:
            continue
        cp_code = str(row["cp"]).replace(":", "")
        if cp_code not in cp_codes:
            continue
        k_col = f"k_cp__cp_{cp_code}"
        tmax = label_row.get("tmax_int")
        k_cp = label_row.get(k_col)
        if tmax is None or k_cp is None:
            continue
        remaining_values.append(float(tmax) - float(k_cp))
    remaining_median = (
        float(pl.Series(remaining_values).median()) if remaining_values else None
    )
    return target_complete_days, tmax_median, remaining_median


def _diagnosis(
    *,
    macro: str,
    assignment_rows: int,
    smallest_cp_support: int,
    r2_rows: int,
    r2_pass_rows: int,
    feature_coverage_status: str,
    min_assignment_rows: int,
    min_cp_rows: int,
) -> str:
    if assignment_rows < min_assignment_rows or smallest_cp_support < min_cp_rows:
        return "UNDERPOWERED_ASSIGNMENT_SUPPORT"
    if r2_rows == 0:
        return "MISSING_R2_VALIDATION_ROWS"
    if feature_coverage_status == "FAIL":
        return "MISSING_FEATURE_COVERAGE"
    if macro == CALM_MACRO and r2_pass_rows == 0:
        return "CALM_RADIATIVE_VALIDATION_TARGET_GAP"
    if r2_pass_rows == 0:
        return "DEAD_MACRO_R2_SIGNAL"
    return "R2_SIGNAL_PRESENT"


def _recommended_next_action(diagnosis: str) -> str:
    if diagnosis == "CALM_RADIATIVE_VALIDATION_TARGET_GAP":
        return (
            "Do not promote. Run v2.3 calm-specific target and hypothesis "
            "experiments before another ontology redesign."
        )
    if diagnosis == "UNDERPOWERED_ASSIGNMENT_SUPPORT":
        return "Do not promote. Increase support or demote the macro to subtype/audit."
    if diagnosis == "MISSING_FEATURE_COVERAGE":
        return "Do not promote. Repair feature coverage before R2 interpretation."
    if diagnosis == "MISSING_R2_VALIDATION_ROWS":
        return "Do not promote. Generate R2 validation rows for this macro."
    if diagnosis == "DEAD_MACRO_R2_SIGNAL":
        return "Do not promote. Redesign or demote the macro after targeted diagnostics."
    return "Keep in design review until full Onda C and Onda 4 acceptance."


def _macro_row(
    *,
    macro: str,
    assignments: pl.DataFrame,
    r2_validation: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    min_assignment_rows: int,
    min_cp_rows: int,
) -> dict[str, object]:
    macro_assignments = assignments.filter(pl.col("macro_regime_label") == macro)
    r2_subset = r2_validation.filter(pl.col("regime") == macro)
    pass_values = (
        [_normalize_pass(value) for value in r2_subset["passes"].to_list()]
        if "passes" in r2_subset.columns
        else []
    )
    r2_pass_rows = sum(1 for value in pass_values if value)
    r2_rows = r2_subset.height
    feature_columns = _tested_features(r2_subset)
    feature_coverage = _feature_coverage_share(macro_assignments, features, feature_columns)
    feature_coverage_status = (
        "PASS"
        if feature_coverage is not None and feature_coverage >= 0.95
        else ("WARN" if feature_coverage is not None and feature_coverage > 0 else "FAIL")
    )
    assignment_rows = macro_assignments.height
    smallest_cp = _smallest_cp_support(macro_assignments)
    sample_support_status = (
        "PASS"
        if assignment_rows >= min_assignment_rows and smallest_cp >= min_cp_rows
        else "UNDERPOWERED"
    )
    diagnosis = _diagnosis(
        macro=macro,
        assignment_rows=assignment_rows,
        smallest_cp_support=smallest_cp,
        r2_rows=r2_rows,
        r2_pass_rows=r2_pass_rows,
        feature_coverage_status=feature_coverage_status,
        min_assignment_rows=min_assignment_rows,
        min_cp_rows=min_cp_rows,
    )
    target_complete_days, tmax_median, remaining_median = _target_summary(
        macro_assignments,
        labels,
    )
    low_confidence_share = (
        float(
            macro_assignments.filter(pl.col("low_confidence_flag").fill_null(False)).height
            / assignment_rows
        )
        if assignment_rows and "low_confidence_flag" in macro_assignments.columns
        else None
    )
    reassigned_rows = (
        macro_assignments.filter(
            pl.col("reassigned_to_calm_radiative").fill_null(False)
        ).height
        if "reassigned_to_calm_radiative" in macro_assignments.columns
        else 0
    )
    return {
        "candidate_version": "v2.3-diagnostic",
        "macro_regime_label": macro,
        "assignment_rows": assignment_rows,
        "unique_days": (
            macro_assignments["date_local"].n_unique()
            if assignment_rows and "date_local" in macro_assignments.columns
            else 0
        ),
        "cp_count": (
            macro_assignments["cp"].n_unique()
            if assignment_rows and "cp" in macro_assignments.columns
            else 0
        ),
        "smallest_cp_support": smallest_cp,
        "reassigned_rows": reassigned_rows,
        "source_macro_summary": _source_macro_summary(macro_assignments),
        "low_confidence_share": low_confidence_share,
        "mean_assignment_confidence": _mean(macro_assignments, "assignment_confidence"),
        "mean_component_entropy": _mean(macro_assignments, "component_entropy"),
        "mean_component_margin": _mean(macro_assignments, "component_margin"),
        "r2_rows": r2_rows,
        "r2_pass_rows": r2_pass_rows,
        "r2_pass_share": float(r2_pass_rows / r2_rows) if r2_rows else 0.0,
        "r2_dead_status": "DEAD" if r2_pass_rows == 0 else "PASS",
        "r2_median_n_days": _median(r2_subset, "n_days"),
        "r2_min_n_days": _min_int(r2_subset, "n_days"),
        "r2_max_n_days": _max_int(r2_subset, "n_days"),
        "tested_feature_columns": ";".join(feature_columns),
        "feature_coverage_share": feature_coverage,
        "feature_coverage_status": feature_coverage_status,
        "target_complete_days": target_complete_days,
        "target_tmax_median": tmax_median,
        "target_remaining_warming_median": remaining_median,
        "sample_support_status": sample_support_status,
        "diagnosis": diagnosis,
        "recommended_next_action": _recommended_next_action(diagnosis),
        "production_status": "EXPERIMENT_ONLY",
    }


def _next_experiments(diagnostics: pl.DataFrame) -> pl.DataFrame:
    calm = (
        diagnostics.filter(pl.col("macro_regime_label") == CALM_MACRO).row(0, named=True)
        if diagnostics.filter(pl.col("macro_regime_label") == CALM_MACRO).height
        else {}
    )
    diagnosis = str(calm.get("diagnosis") or "CALM_RADIATIVE_UNRESOLVED")
    rows = [
        {
            "experiment_id": "CEXP-CALM-RADIATIVE-001",
            "domain": "REGIME_CALM_RADIATIVE",
            "blocker": diagnosis,
            "required_artifact": (
                "reports/regime-design/"
                "regime_calm_radiative_target_diagnostics_v1.csv"
            ),
            "recommended_experiment": (
                "Build a calm/radiative target diagnostic using train-only "
                "month x CP remaining-warming and Tmax-hour distributions."
            ),
            "rationale": (
                "v2.2 has assignment support, but R2 has no passing "
                "calm/radiative rows; test whether the current R2 target is "
                "misaligned with radiative physics."
            ),
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "experiment_id": "CEXP-CALM-RADIATIVE-002",
            "domain": "FEATURE_HYPOTHESIS",
            "blocker": diagnosis,
            "required_artifact": (
                "reports/regime-design/"
                "regime_calm_radiative_feature_hypotheses_v1.csv"
            ),
            "recommended_experiment": (
                "Evaluate calm-specific causal features: nocturnal plateau, "
                "cloud transparency, dewpoint depression persistence, and "
                "weak-wind morning warming."
            ),
            "rationale": (
                "The EDA feature surface contains calm/radiative candidates, "
                "but the v2.2 R2 pass rate is zero."
            ),
            "production_status": "EXPERIMENT_ONLY",
        },
        {
            "experiment_id": "CEXP-CALM-RADIATIVE-003",
            "domain": "REGIME_ONTOLOGY",
            "blocker": diagnosis,
            "required_artifact": (
                "reports/regime-design/"
                "regime_calm_radiative_demote_or_split_v1.csv"
            ),
            "recommended_experiment": (
                "Compare protected macro, subtype/audit demotion, and "
                "radiative-clear versus cloudy split before another Onda C run."
            ),
            "rationale": (
                "If target and feature diagnostics still fail, calm/radiative "
                "should not remain a protected macro by name alone."
            ),
            "production_status": "EXPERIMENT_ONLY",
        },
    ]
    return pl.DataFrame(rows, schema=NEXT_EXPERIMENT_SCHEMA, strict=False)


def build_regime_v23_calm_failure_diagnostics(
    *,
    assignments: pl.DataFrame,
    r2_validation: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    min_assignment_rows: int = 30,
    min_cp_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Build experiment-only diagnostics for the v2.2 calm/radiative failure."""
    assignments = _normalize_keys(assignments)
    features = _normalize_keys(features)
    labels = _normalize_keys(labels)
    _validate_inputs(assignments, r2_validation, features, labels)
    macros = sorted(
        str(value)
        for value in assignments["macro_regime_label"].drop_nulls().unique().to_list()
    )
    diagnostics = (
        pl.DataFrame(
            [
                _macro_row(
                    macro=macro,
                    assignments=assignments,
                    r2_validation=r2_validation,
                    features=features,
                    labels=labels,
                    min_assignment_rows=min_assignment_rows,
                    min_cp_rows=min_cp_rows,
                )
                for macro in macros
            ],
            schema=DIAGNOSTIC_SCHEMA,
            strict=False,
        )
        if macros
        else _empty_frame(DIAGNOSTIC_SCHEMA)
    )
    return {
        "regime_calm_radiative_failure_diagnostics_v1": diagnostics,
        "regime_v23_next_experiments": _next_experiments(diagnostics),
    }


def _report_lines(artifacts: dict[str, pl.DataFrame], today: dt.date) -> list[str]:
    diagnostics = artifacts["regime_calm_radiative_failure_diagnostics_v1"]
    experiments = artifacts["regime_v23_next_experiments"]
    calm = (
        diagnostics.filter(pl.col("macro_regime_label") == CALM_MACRO).row(0, named=True)
        if diagnostics.filter(pl.col("macro_regime_label") == CALM_MACRO).height
        else {}
    )
    lines = [
        f"# Regime v2.3 Calm/Radiative Failure Diagnostics - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        (
            "v2.3 explains the v2.2 calm/radiative R2 blocker and converts it "
            "into experiment-only follow-up work."
        ),
        "",
        f"- Calm/radiative diagnosis: {calm.get('diagnosis', '')}",
        f"- Calm/radiative assignment rows: {calm.get('assignment_rows', 0)}",
        f"- Calm/radiative R2 pass rows: {calm.get('r2_pass_rows', 0)}",
        f"- Calm/radiative R2 median n_days: {calm.get('r2_median_n_days', '')}",
        "",
        "## Macro Diagnostics",
        "",
        "| Macro | Assignments | Smallest CP | R2 pass rows | R2 median n_days | Diagnosis |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in diagnostics.sort("macro_regime_label").iter_rows(named=True):
        lines.append(
            "| "
            f"{row['macro_regime_label']} | "
            f"{row['assignment_rows']} | "
            f"{row['smallest_cp_support']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_median_n_days']} | "
            f"{row['diagnosis']} |"
        )
    lines += [
        "",
        "## Next Experiments",
        "",
        "| Experiment | Domain | Blocker | Required artifact |",
        "|---|---|---|---|",
    ]
    for row in experiments.iter_rows(named=True):
        lines.append(
            "| "
            f"{row['experiment_id']} | "
            f"{row['domain']} | "
            f"{row['blocker']} | "
            f"{row['required_artifact']} |"
        )
    lines += [
        "",
        "## Decision",
        "",
        "Onda 3 remains blocked. v2.3 does not promote v2.2; it defines the next "
        "data-backed experiments needed before another regime promotion attempt.",
    ]
    return lines


def write_regime_v23_calm_failure_diagnostics_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    diagnostics = artifacts["regime_calm_radiative_failure_diagnostics_v1"]
    experiments = artifacts["regime_v23_next_experiments"]

    diagnostics_csv = out_dir / "regime_calm_radiative_failure_diagnostics_v1.csv"
    experiments_csv = out_dir / "regime_v23_next_experiments.csv"
    report_md = out_dir / "regime_calm_radiative_failure_diagnostics_v1.md"
    diagnostics.write_csv(diagnostics_csv)
    experiments.write_csv(experiments_csv)
    report_md.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")
    return {
        "regime_calm_radiative_failure_diagnostics_csv": diagnostics_csv,
        "regime_v23_next_experiments_csv": experiments_csv,
        "regime_calm_radiative_failure_diagnostics_md": report_md,
    }
