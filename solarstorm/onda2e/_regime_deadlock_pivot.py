"""Regime deadlock pivot: formal decision, audit-demotion, and superseded-path artifacts.

Records the pivot away from the v2.2/v2.3/CEXP threshold-restoration loop and
demotes ``macro_calm_radiative`` from a production-blocking macro to an
audit-only segment.  All outputs are EXPERIMENT_ONLY.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

PRODUCTION_MACROS = ("macro_nw_continuum", "macro_southerly_flow")
AUDIT_MACROS = ("macro_calm_radiative",)

DECISION_SCHEMA = {
    "decision_id": pl.Utf8,
    "source_report_path": pl.Utf8,
    "decision_status": pl.Utf8,
    "active_path": pl.Utf8,
    "superseded_path": pl.Utf8,
    "key_evidence": pl.Utf8,
    "allowed_next_actions": pl.Utf8,
    "blocked_next_actions": pl.Utf8,
    "production_status": pl.Utf8,
}

DEMOTION_SCHEMA = {
    "macro_regime_label": pl.Utf8,
    "gate_role": pl.Utf8,
    "blocks_production_gate": pl.Boolean,
    "r2_pass_rows": pl.Int64,
    "median_n_days": pl.Float64,
    "known_signal": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "production_status": pl.Utf8,
}

SUPERSEDED_SCHEMA = {
    "path_item": pl.Utf8,
    "superseded_status": pl.Utf8,
    "reason": pl.Utf8,
    "replacement_path": pl.Utf8,
    "production_status": pl.Utf8,
}


def _r2_summary(r2_validation: pl.DataFrame, regime: str) -> tuple[int, float | None]:
    if r2_validation.height == 0 or "regime" not in r2_validation.columns:
        return 0, None
    subset = r2_validation.filter(pl.col("regime") == regime)
    pass_rows = (
        int(subset.filter(pl.col("passes").fill_null(False)).height) if "passes" in subset.columns else 0
    )
    median_n = float(subset["n_days"].median()) if subset.height and "n_days" in subset.columns else None
    return pass_rows, median_n


def _cloud_signal(cloud_validation: pl.DataFrame) -> str:
    if cloud_validation.height == 0 or "validation_decision" not in cloud_validation.columns:
        return ""
    survived = cloud_validation.filter(pl.col("validation_decision") == "SURVIVES_CAUSAL_ROBUSTNESS_SCREEN")
    return "cloud_cover_suppression" if survived.height else ""


def build_regime_deadlock_pivot_artifacts(
    *,
    r2_validation: pl.DataFrame,
    cloud_validation: pl.DataFrame | None = None,
    source_report_path: str = "reports/onda2e/regime_deadlock_diagnosis_v1.md",
) -> dict[str, pl.DataFrame]:
    """Build the three pivot artifacts: decision, audit demotions, superseded path."""
    cloud_validation = cloud_validation if cloud_validation is not None else pl.DataFrame()
    key_evidence = (
        "train_only_gmm stability=0.0799; classifiability=0.0933; "
        "distance_softmax_v22 low_confidence_share=0.8226; "
        "macro_calm_radiative R2 median n_days=27; "
        "cloud_cover_suppression survives CEXP-002B"
    )
    decision = pl.DataFrame(
        [
            {
                "decision_id": "REGIME-DEADLOCK-PIVOT-001",
                "source_report_path": source_report_path,
                "decision_status": "PIVOT_ACCEPTED",
                "active_path": "OPTION_C_AUDIT_DEMOTION_PLUS_OPTION_A_BINARY_EXPERIMENT",
                "superseded_path": "V22_V23_CEXP_THRESHOLD_RESTORATION_LOOP",
                "key_evidence": key_evidence,
                "allowed_next_actions": (
                    "Generate audit-demotion artifacts; generate binary macro candidate; "
                    "run cloud-cover baseline experiment"
                ),
                "blocked_next_actions": (
                    "No v2.4 calm/radiative threshold tuning; no global R2 weakening; "
                    "no cloudy/clear macro split as active unlock path"
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        schema=DECISION_SCHEMA,
    )

    known_signal = _cloud_signal(cloud_validation)
    demotion_rows = []
    for regime in (*PRODUCTION_MACROS, *AUDIT_MACROS):
        pass_rows, median_n = _r2_summary(r2_validation, regime)
        is_audit = regime in AUDIT_MACROS
        demotion_rows.append(
            {
                "macro_regime_label": regime,
                "gate_role": "AUDIT_ONLY" if is_audit else "PRODUCTION_BLOCKING",
                "blocks_production_gate": not is_audit,
                "r2_pass_rows": pass_rows,
                "median_n_days": median_n,
                "known_signal": known_signal if regime == "macro_calm_radiative" else "",
                "decision_rationale": (
                    "Demoted because repeated R2 failure is underpowered and structurally ambiguous."
                    if is_audit
                    else "Retained as production-blocking because existing evidence supports this macro."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    superseded = pl.DataFrame(
        [
            {
                "path_item": "regime_v22_calm_radiative_restoration",
                "superseded_status": "SUPERSEDED_ACTIVE_UNLOCK_PATH",
                "reason": "Restoration did not resolve R2 deadlock.",
                "replacement_path": "OPTION_C_AUDIT_DEMOTION",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "path_item": "regime_v23_calm_failure_diagnostics",
                "superseded_status": "AUDIT_HISTORY_RETAINED",
                "reason": "Diagnostics explain the blocker but are not an unlock path.",
                "replacement_path": "REGIME_DEADLOCK_PIVOT",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "path_item": "v2.4_threshold_tuning",
                "superseded_status": "BLOCKED_BY_DECISION",
                "reason": "Report diagnoses structural information limit, not calibration.",
                "replacement_path": "OPTION_A_BINARY_EXPERIMENT",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        schema=SUPERSEDED_SCHEMA,
    )

    return {
        "regime_deadlock_pivot_decision_v1": decision,
        "regime_audit_demotions_v1": pl.DataFrame(demotion_rows, schema=DEMOTION_SCHEMA, strict=False),
        "regime_deadlock_superseded_path_v1": superseded,
    }


def _markdown_report(artifacts: dict[str, pl.DataFrame], today: dt.date) -> str:
    decision = artifacts["regime_deadlock_pivot_decision_v1"].row(0, named=True)
    demotions = artifacts["regime_audit_demotions_v1"]
    lines = [
        f"# Regime Deadlock Pivot Decision - {today.isoformat()}",
        "",
        "This is not a production classifier.",
        "Status: experiment-only; not a production classifier.",
        "",
        f"- Decision: {decision['decision_status']}",
        f"- Active path: {decision['active_path']}",
        f"- Superseded path: {decision['superseded_path']}",
        "",
        "## Gate Roles",
        "",
        "| macro | role | blocks gate | R2 pass rows | median n_days |",
        "|---|---|---:|---:|---:|",
    ]
    for row in demotions.iter_rows(named=True):
        lines.append(
            f"| {row['macro_regime_label']} | {row['gate_role']} | "
            f"{row['blocks_production_gate']} | {row['r2_pass_rows']} | {row['median_n_days']} |"
        )
    lines += [
        "",
        "## Note on Audit Demotion",
        "",
        "Demotion is not deletion. `macro_calm_radiative` is retained as an audit segment.",
        "It will be reported separately but will not block the production macro gate.",
        "The production-blocking macro set for the pivot review is",
        "`macro_nw_continuum` and `macro_southerly_flow`.",
    ]
    return "\n".join(lines) + "\n"


def write_regime_deadlock_pivot_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write the pivot decision, audit demotion, and superseded-path CSVs and MD."""
    today = today or dt.date.today()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    decision_csv = out_dir / "regime_deadlock_pivot_decision_v1.csv"
    decision_md = out_dir / "regime_deadlock_pivot_decision_v1.md"
    demotions_csv = out_dir / "regime_audit_demotions_v1.csv"
    demotions_md = out_dir / "regime_audit_demotions_v1.md"
    superseded_csv = out_dir / "regime_deadlock_superseded_path_v1.csv"
    artifacts["regime_deadlock_pivot_decision_v1"].write_csv(decision_csv)
    artifacts["regime_audit_demotions_v1"].write_csv(demotions_csv)
    artifacts["regime_deadlock_superseded_path_v1"].write_csv(superseded_csv)
    report = _markdown_report(artifacts, today)
    decision_md.write_text(report, encoding="utf-8")
    demotions_md.write_text(report, encoding="utf-8")
    return {
        "regime_deadlock_pivot_decision_csv": decision_csv,
        "regime_deadlock_pivot_decision_md": decision_md,
        "regime_audit_demotions_csv": demotions_csv,
        "regime_audit_demotions_md": demotions_md,
        "regime_deadlock_superseded_path_csv": superseded_csv,
    }
