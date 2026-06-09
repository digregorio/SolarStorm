"""Onda 2E evidence-to-decision gate artifacts."""
from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

import polars as pl

from solarstorm.onda2e._atlas import Thesis

DECISION_STATUSES: frozenset[str] = frozenset(
    {
        "SUPPORTED",
        "REJECTED",
        "ADAPTED",
        "BLOCKED",
        "PROMOTED_TO_REGIME_DESIGN",
        "PROMOTED_TO_FEATURE_CANDIDATE",
        "QUARANTINED_BASELINE",
    }
)

DECISION_SCHEMA: dict[str, pl.DataType] = {
    "decision_id": pl.Utf8,
    "item_id": pl.Utf8,
    "item_type": pl.Utf8,
    "domain": pl.Utf8,
    "decision_status": pl.Utf8,
    "evidence_level": pl.Utf8,
    "source_artifact": pl.Utf8,
    "strata": pl.Utf8,
    "sample_size_warning": pl.Utf8,
    "causal_availability": pl.Utf8,
    "leakage_risk": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "next_allowed_action": pl.Utf8,
}

BASELINE_SCHEMA: dict[str, pl.DataType] = {
    "rule_id": pl.Utf8,
    "domain": pl.Utf8,
    "rule_name": pl.Utf8,
    "affected_surface": pl.Utf8,
    "hardcoded_value": pl.Utf8,
    "decision_status": pl.Utf8,
    "source_artifact": pl.Utf8,
    "evidence_gap": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "next_allowed_action": pl.Utf8,
}

QUEUE_SCHEMA: dict[str, pl.DataType] = {
    "queue_id": pl.Utf8,
    "rule_id": pl.Utf8,
    "source_item_id": pl.Utf8,
    "source_item_type": pl.Utf8,
    "domain": pl.Utf8,
    "source_decision_status": pl.Utf8,
    "source_artifact": pl.Utf8,
    "evidence_gap": pl.Utf8,
    "next_action": pl.Utf8,
}

FEATURE_QUEUE_SCHEMA: dict[str, pl.DataType] = {
    "queue_id": pl.Utf8,
    "thesis_id": pl.Utf8,
    "domain": pl.Utf8,
    "source_decision_status": pl.Utf8,
    "source_artifact": pl.Utf8,
    "causal_availability": pl.Utf8,
    "leakage_risk": pl.Utf8,
    "next_action": pl.Utf8,
}

REJECTION_SCHEMA: dict[str, pl.DataType] = {
    "decision_id": pl.Utf8,
    "item_id": pl.Utf8,
    "domain": pl.Utf8,
    "source_artifact": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "reentry_condition": pl.Utf8,
}

QUARANTINED_BASELINE_RULES: tuple[dict[str, str], ...] = (
    {
        "rule_id": "REGIME_CLASSIFIER_CURRENT",
        "domain": "REGIME",
        "rule_name": "Current physical regime classifier",
        "affected_surface": "regime_label and regime-stratified validation",
        "hardcoded_value": "southerly_disrupted, standard_nw, strong_nw_foehn, calm_radiative heuristic ontology",
        "source_artifact": "solarstorm/eda/_regimes.py; docs/decisions/006-regime-classifier.md; docs/decisions/011-regime-ontology-repair.md",
        "evidence_gap": "Onda 4 still reports dead causal physical regimes and Onda 2E has not produced a replacement ontology decision.",
        "decision_rationale": "Retain only as a diagnostic comparator until Wellington climatology resolves stable physical classes.",
        "next_allowed_action": "Run Onda 2E domain EDA and promote only supported/adapted rules into regime design.",
    },
    {
        "rule_id": "RULE_LATE_WARMING_FIXED_18",
        "domain": "TIMING",
        "rule_name": "Fixed late Tmax hour threshold",
        "affected_surface": "late Tmax, late-spike, and timing-risk diagnostics",
        "hardcoded_value": "tmax_hour >= 18 or evening_after_18 bucket",
        "source_artifact": "docs/decisions/011-regime-ontology-repair.md; solarstorm/robustness/_tmax_hour.py",
        "evidence_gap": "Late Tmax must be month/regime-relative; fixed 18:00 ignores seasonal and physical timing norms.",
        "decision_rationale": "Fixed timing is useful only as a deprecated diagnostic reference, not production truth.",
        "next_allowed_action": "Compute train-only month/regime Tmax-hour distributions and decide retain/adapt/reject.",
    },
    {
        "rule_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
        "domain": "COOLING",
        "rule_name": "Fixed material cooling threshold",
        "affected_surface": "cooling taxonomy and southerly_disrupted trigger",
        "hardcoded_value": "min_delta_t_per_h < -2.0",
        "source_artifact": "solarstorm/onda2e/_atlas.py; solarstorm/robustness/_regime_diagnostics.py; reports/regime/2026-06-06-cooling-rule-experiment.md",
        "evidence_gap": "Cooling has not yet been calibrated by month, mechanism, wind context, rain, pressure, or sample power.",
        "decision_rationale": "The threshold mixed several physical cooling mechanisms and cannot justify regime design by itself.",
        "next_allowed_action": "Use cooling taxonomy EDA to decide mechanism-specific and month-aware cooling rules.",
    },
    {
        "rule_id": "RULE_FOEHN_SCORE_FIXED_60",
        "domain": "FOEHN",
        "rule_name": "Fixed foehn score threshold",
        "affected_surface": "strong_nw_foehn trigger and foehn feature candidates",
        "hardcoded_value": "foehn_score > 60.0",
        "source_artifact": "solarstorm/robustness/_regime_diagnostics.py; reports/onda2e/thesis_atlas_v1.md",
        "evidence_gap": "Foehn threshold has not been calibrated by month, wind sector, dewpoint behavior, and Tmax anomaly.",
        "decision_rationale": "Keep as an audit threshold only until the Onda 2E foehn theses resolve calibration.",
        "next_allowed_action": "Run foehn-domain EDA and decide calibrated thresholds or continuous alternatives.",
    },
    {
        "rule_id": "RULE_ONDA2R_PHYSICAL_REGIME_FAMILY",
        "domain": "REGIME",
        "rule_name": "Onda 2R physical regime family",
        "affected_surface": "candidate regime design queue",
        "hardcoded_value": "southerly_disrupted, standard_nw, strong_nw_foehn, calm_radiative",
        "source_artifact": "docs/decisions/011-regime-ontology-repair.md; docs/regime_model_card.md",
        "evidence_gap": "The family is repaired relative to late_warming, but not proven as the final climatology ontology.",
        "decision_rationale": "Treat as baseline ontology to investigate, not as authority to unlock model work.",
        "next_allowed_action": "Resolve regime, wind, cooling, timing, rain, pressure, and foehn thesis decisions first.",
    },
)


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _power_warning(prereq_artifacts: dict[str, pl.DataFrame] | None) -> str:
    if not prereq_artifacts or "power_map" not in prereq_artifacts:
        return "Consult reports/onda2e/prereq_power_map.csv before stratified use."

    power_map = prereq_artifacts["power_map"]
    if power_map.height == 0 or "underpowered_n_lt_30" not in power_map.columns:
        return "Power map is empty or incomplete; no stratified promotion allowed."

    underpowered = power_map.filter(pl.col("underpowered_n_lt_30")).height
    return (
        f"Consult reports/onda2e/prereq_power_map.csv; "
        f"{underpowered}/{power_map.height} month x regime x CP cells have n < 30."
    )


def _thesis_decision_reason(row: dict[str, object]) -> tuple[str, str, str]:
    testability = str(row["testability"])
    if testability == "registry_missing_detail":
        return (
            "E0_registry_gap",
            "Official atlas scope includes this thesis, but the markdown registry lacks enough detail to test it.",
            "Repair the atlas row before any EDA, regime design, or feature design use.",
        )
    if testability == "blocked_external_data":
        return (
            "E0_external_data_gap",
            "The thesis requires data not present in the current obs, labels, or feature artifacts.",
            "Acquire and document required external data, or keep the thesis blocked.",
        )
    if testability == "gap_audit":
        return (
            "E1_gap_candidate",
            "The thesis is a gap audit item; prerequisite artifacts can scope it but cannot resolve it.",
            "Complete the named domain EDA and update the decision register with evidence.",
        )
    return (
        "E1_prerequisite_candidate",
        "The thesis is locally testable, but prerequisite EDA is descriptive and does not support promotion.",
        "Run domain EDA, assess causal availability/leakage, and record a supported, adapted, rejected, or blocked decision.",
    )


def _thesis_decision_rows(
    theses: list[Thesis],
    testability: pl.DataFrame,
    *,
    prereq_artifacts: dict[str, pl.DataFrame] | None,
) -> list[dict[str, str]]:
    thesis_ids = {thesis.id for thesis in theses}
    rows: list[dict[str, str]] = []
    for row in testability.sort(["priority", "domain", "id"]).iter_rows(named=True):
        thesis_id = str(row["id"])
        if thesis_id not in thesis_ids:
            continue
        evidence_level, rationale, next_action = _thesis_decision_reason(row)
        rows.append(
            {
                "decision_id": f"DEC-{thesis_id}",
                "item_id": thesis_id,
                "item_type": "thesis",
                "domain": str(row["domain"]),
                "decision_status": "BLOCKED",
                "evidence_level": evidence_level,
                "source_artifact": "reports/onda2e/thesis_testability_audit.csv",
                "strata": str(row["key_strata"]),
                "sample_size_warning": _power_warning(prereq_artifacts),
                "causal_availability": "Not assessed by domain EDA.",
                "leakage_risk": "Not assessed by domain EDA.",
                "decision_rationale": rationale,
                "next_allowed_action": next_action,
            }
        )
    return rows


def _baseline_frame() -> pl.DataFrame:
    rows = [
        {
            **rule,
            "decision_status": "QUARANTINED_BASELINE",
        }
        for rule in QUARANTINED_BASELINE_RULES
    ]
    return pl.DataFrame(rows, schema=BASELINE_SCHEMA)


def _baseline_decision_rows(baselines: pl.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in baselines.iter_rows(named=True):
        rows.append(
            {
                "decision_id": f"DEC-{row['rule_id']}",
                "item_id": str(row["rule_id"]),
                "item_type": "rule",
                "domain": str(row["domain"]),
                "decision_status": "QUARANTINED_BASELINE",
                "evidence_level": "baseline_quarantine",
                "source_artifact": str(row["source_artifact"]),
                "strata": "month, CP, regime, and physical mechanism pending Onda 2E domain EDA",
                "sample_size_warning": "Not calibrated; do not use as production evidence.",
                "causal_availability": "Diagnostic only until ADR-012 decision records retain or adapt it.",
                "leakage_risk": "Quarantined because current rule may encode ex-post timing, arbitrary threshold, or unstable ontology.",
                "decision_rationale": str(row["decision_rationale"]),
                "next_allowed_action": str(row["next_allowed_action"]),
            }
        )
    return rows


def _regime_design_queue(baselines: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(baselines.iter_rows(named=True), start=1):
        rows.append(
            {
                "queue_id": f"RDQ-{idx:03d}",
                "rule_id": str(row["rule_id"]),
                "source_item_id": str(row["rule_id"]),
                "source_item_type": "rule",
                "domain": str(row["domain"]),
                "source_decision_status": "QUARANTINED_BASELINE",
                "source_artifact": str(row["source_artifact"]),
                "evidence_gap": str(row["evidence_gap"]),
                "next_action": str(row["next_allowed_action"]),
            }
        )
    if not rows:
        return _empty_frame(QUEUE_SCHEMA)
    return pl.DataFrame(rows, schema=QUEUE_SCHEMA)


def _regime_design_queue_from_register(
    baselines: pl.DataFrame,
    decision_register: pl.DataFrame,
) -> pl.DataFrame:
    queue = _regime_design_queue(baselines)
    promoted = decision_register.filter(pl.col("decision_status") == "PROMOTED_TO_REGIME_DESIGN")
    if promoted.height == 0:
        return queue
    rows = queue.to_dicts()
    start_idx = len(rows) + 1
    for idx, row in enumerate(promoted.iter_rows(named=True), start=start_idx):
        rows.append(
            {
                "queue_id": f"RDQ-{idx:03d}",
                "rule_id": "",
                "source_item_id": str(row["item_id"]),
                "source_item_type": str(row["item_type"]),
                "domain": str(row["domain"]),
                "source_decision_status": str(row["decision_status"]),
                "source_artifact": str(row["source_artifact"]),
                "evidence_gap": str(row["decision_rationale"]),
                "next_action": str(row["next_allowed_action"]),
            }
        )
    return pl.DataFrame(rows, schema=QUEUE_SCHEMA)


def _feature_candidate_queue_from_register(decision_register: pl.DataFrame) -> pl.DataFrame:
    promoted = decision_register.filter(
        (pl.col("item_type") == "thesis")
        & (pl.col("decision_status") == "PROMOTED_TO_FEATURE_CANDIDATE")
    )
    if promoted.height == 0:
        return _empty_frame(FEATURE_QUEUE_SCHEMA)
    rows: list[dict[str, str]] = []
    for idx, row in enumerate(promoted.iter_rows(named=True), start=1):
        rows.append(
            {
                "queue_id": f"FCQ-{idx:03d}",
                "thesis_id": str(row["item_id"]),
                "domain": str(row["domain"]),
                "source_decision_status": str(row["decision_status"]),
                "source_artifact": str(row["source_artifact"]),
                "causal_availability": str(row["causal_availability"]),
                "leakage_risk": str(row["leakage_risk"]),
                "next_action": str(row["next_allowed_action"]),
            }
        )
    return pl.DataFrame(rows, schema=FEATURE_QUEUE_SCHEMA)


def _rejection_register_from_register(decision_register: pl.DataFrame) -> pl.DataFrame:
    rejected = decision_register.filter(pl.col("decision_status") == "REJECTED")
    if rejected.height == 0:
        return _empty_frame(REJECTION_SCHEMA)
    rows: list[dict[str, str]] = []
    for row in rejected.iter_rows(named=True):
        rows.append(
            {
                "decision_id": str(row["decision_id"]),
                "item_id": str(row["item_id"]),
                "domain": str(row["domain"]),
                "source_artifact": str(row["source_artifact"]),
                "decision_rationale": str(row["decision_rationale"]),
                "reentry_condition": str(row["next_allowed_action"]),
            }
        )
    return pl.DataFrame(rows, schema=REJECTION_SCHEMA)


def _with_decision_register(
    artifacts: dict[str, pl.DataFrame],
    decision_register: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    baselines = artifacts["quarantined_baseline_register"]
    return {
        **artifacts,
        "evidence_decision_register": decision_register,
        "regime_design_queue": _regime_design_queue_from_register(baselines, decision_register),
        "feature_candidate_queue": _feature_candidate_queue_from_register(decision_register),
        "rejection_register": _rejection_register_from_register(decision_register),
    }


def build_decision_gate_artifacts(
    theses: list[Thesis],
    testability: pl.DataFrame,
    prereq_artifacts: dict[str, pl.DataFrame] | None = None,
) -> dict[str, pl.DataFrame]:
    """Build ADR-012 decision-register artifacts for Onda 2E.

    Prerequisite EDA never promotes theses by itself. This initial gate converts
    all unresolved thesis rows into explicit blocked decisions and quarantines
    existing heuristic rules so future EDA must actively retain, adapt, reject,
    or replace them.
    """
    baselines = _baseline_frame()
    decision_rows = [
        *_thesis_decision_rows(theses, testability, prereq_artifacts=prereq_artifacts),
        *_baseline_decision_rows(baselines),
    ]
    decision_register = pl.DataFrame(decision_rows, schema=DECISION_SCHEMA)
    return _with_decision_register(
        {
            "evidence_decision_register": decision_register,
            "regime_design_queue": _empty_frame(QUEUE_SCHEMA),
            "feature_candidate_queue": _empty_frame(FEATURE_QUEUE_SCHEMA),
            "rejection_register": _empty_frame(REJECTION_SCHEMA),
            "quarantined_baseline_register": baselines,
        },
        decision_register,
    )


def remove_decision_items(
    artifacts: dict[str, pl.DataFrame],
    item_ids: Iterable[str],
    *,
    item_type: str | None = None,
) -> dict[str, pl.DataFrame]:
    """Return gate artifacts with decision-register rows removed and queues rebuilt."""
    ids = {str(item_id) for item_id in item_ids}
    if not ids:
        return dict(artifacts)

    register = artifacts["evidence_decision_register"]
    remove_expr = pl.col("item_id").is_in(ids)
    if item_type is not None:
        remove_expr = remove_expr & (pl.col("item_type") == item_type)
    updated_register = register.filter(~remove_expr)
    return _with_decision_register(artifacts, updated_register)


def apply_decision_updates(
    artifacts: dict[str, pl.DataFrame],
    decision_updates: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Return gate artifacts with decision-register rows replaced by updates."""
    if decision_updates.height == 0:
        return dict(artifacts)

    register = artifacts["evidence_decision_register"]
    update_keys = {
        (str(row["item_id"]), str(row["item_type"]))
        for row in decision_updates.select(["item_id", "item_type"]).iter_rows(named=True)
    }
    kept_rows = [
        row
        for row in register.iter_rows(named=True)
        if (str(row["item_id"]), str(row["item_type"])) not in update_keys
    ]
    updated_register = pl.DataFrame(
        [*kept_rows, *decision_updates.to_dicts()],
        schema=DECISION_SCHEMA,
    ).sort(["domain", "item_type", "item_id"])
    return _with_decision_register(artifacts, updated_register)


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    decision_register = artifacts["evidence_decision_register"]
    thesis_rows = decision_register.filter(pl.col("item_type") == "thesis")
    blocked_theses = thesis_rows.filter(pl.col("decision_status") == "BLOCKED")
    baselines = artifacts["quarantined_baseline_register"]
    active_quarantined = decision_register.filter(
        pl.col("decision_status") == "QUARANTINED_BASELINE"
    )
    regime_queue = artifacts["regime_design_queue"]
    feature_queue = artifacts["feature_candidate_queue"]
    rejection_register = artifacts["rejection_register"]

    lines = [
        f"# Onda 2E-Gate Decision Report - {report_date.isoformat()}",
        "",
        "No thesis is promoted by prerequisite EDA alone.",
        "Descriptive artifacts become actionable only after ADR-012 decision records resolve evidence, power, causality, and leakage.",
        "",
        "## Summary",
        "",
        f"- Thesis decisions: {thesis_rows.height}",
        f"- Blocked thesis decisions: {blocked_theses.height}",
        f"- Baseline-register entries: {baselines.height}",
        f"- Active quarantined decision rows: {active_quarantined.height}",
        f"- Regime design queue items: {regime_queue.height}",
        f"- Feature candidate queue items: {feature_queue.height}",
        f"- Rejected items: {rejection_register.height}",
        "",
        "## Decision Status Counts",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    status_counts = (
        decision_register.group_by("decision_status")
        .len(name="n")
        .sort("decision_status")
    )
    for row in status_counts.iter_rows(named=True):
        lines.append(f"| {row['decision_status']} | {row['n']} |")

    lines += [
        "",
        "## Required Registers",
        "",
        "| Artifact | Rows |",
        "|---|---:|",
    ]
    for name, frame in artifacts.items():
        lines.append(f"| `{name}.csv` | {frame.height} |")

    lines += [
        "",
        "## Baseline Comparator Register",
        "",
        "Active quarantine is counted separately in the decision register. This table lists deprecated or provisional rules kept only as diagnostic comparators.",
        "",
        "| Rule | Domain | Reason |",
        "|---|---|---|",
    ]
    for row in baselines.iter_rows(named=True):
        lines.append(
            f"| `{row['rule_id']}` | {row['domain']} | {row['decision_rationale']} |"
        )

    consequence = (
        "Onda 3 and regime-dependent Onda 4 reruns remain blocked until domain EDA updates evidence_decision_register.csv and its downstream queues with supported, adapted, rejected, or promoted decisions."
        if blocked_theses.height
        else "Domain EDA has resolved the active local thesis backlog. Onda 4 remains blocked until the regime-design queue produces and validates a data-backed regime repair; no production feature, model input, or classifier is promoted here."
    )
    lines += [
        "",
        "## Gate Consequence",
        "",
        consequence,
    ]
    return lines


def write_decision_gate_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write Onda 2E-Gate CSV registers and markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()

    filenames = {
        "evidence_decision_register": "evidence_decision_register.csv",
        "regime_design_queue": "regime_design_queue.csv",
        "feature_candidate_queue": "feature_candidate_queue.csv",
        "rejection_register": "rejection_register.csv",
        "quarantined_baseline_register": "quarantined_baseline_register.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        _write_csv(artifacts[key], path)
        paths[f"{key}_csv"] = path

    report_path = out_dir / "onda2e_decision_report.md"
    report_path.write_text(
        "\n".join(_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["decision_report_md"] = report_path
    return paths
