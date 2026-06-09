"""Foundation experiment catalog artifacts for EDA-driven implementation."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import polars as pl

FOUNDATION_EXPERIMENT_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "experiment_family": pl.Utf8,
    "domain": pl.Utf8,
    "source_decision_id": pl.Utf8,
    "source_artifacts": pl.Utf8,
    "weakness_target": pl.Utf8,
    "candidate_surface": pl.Utf8,
    "implementation_kind": pl.Utf8,
    "input_columns_or_artifacts": pl.Utf8,
    "strata": pl.Utf8,
    "causal_status": pl.Utf8,
    "leakage_risk": pl.Utf8,
    "power_warning": pl.Utf8,
    "baseline_comparator": pl.Utf8,
    "success_metric": pl.Utf8,
    "acceptance_gate": pl.Utf8,
    "stop_condition": pl.Utf8,
    "production_status": pl.Utf8,
    "next_action": pl.Utf8,
}

FOUNDATION_WARNING_SCHEMA: dict[str, pl.DataType] = {
    "artifact": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

_REQUIRED_ONDA2E_INPUTS = {
    "decision_register": "evidence_decision_register.csv",
    "regime_design_queue": "regime_design_queue.csv",
    "quarantined_baselines": "quarantined_baseline_register.csv",
}

_REQUIRED_INPUT_COLUMNS = {
    "decision_register": {
        "decision_id",
        "item_id",
        "domain",
        "decision_status",
        "source_artifact",
    },
    "regime_design_queue": {
        "queue_id",
        "source_item_id",
        "domain",
        "source_decision_status",
        "source_artifact",
        "evidence_gap",
        "next_action",
    },
    "quarantined_baselines": {
        "rule_id",
        "domain",
        "decision_status",
        "source_artifact",
        "affected_surface",
        "evidence_gap",
        "next_allowed_action",
    },
}

_QUEUE_STATUSES = frozenset({"PROMOTED_TO_REGIME_DESIGN", "QUARANTINED_BASELINE"})

_OPTIONAL_ONDA2E_INPUTS = {
    "rejection_register": "rejection_register.csv",
    "domain_eda_next_experiments": "domain_eda_next_experiments.csv",
    "domain_thesis_evidence": "domain_thesis_evidence.csv",
    "domain_timing_norms_by_month_regime": "domain_timing_norms_by_month_regime.csv",
    "domain_timing_bucket_priors": "domain_timing_bucket_priors.csv",
    "cooling_effects_by_month_regime_cp": "cooling_effects_by_month_regime_cp.csv",
    "cooling_event_taxonomy_by_day_cp": "cooling_event_taxonomy_by_day_cp.csv",
    "domain_foehn_score_bins_by_month_cp": "domain_foehn_score_bins_by_month_cp.csv",
    "foehn_repair_candidates": "foehn_regime_repair_candidates.csv",
    "wind_sector_effects_by_month_cp": "wind_sector_effects_by_month_cp.csv",
    "wind_repair_candidates": "wind_regime_repair_candidates.csv",
    "regime_design_candidate_v1": "regime_design_candidate_v1.csv",
}

_OPTIONAL_REGIME_DESIGN_INPUTS = {
    "regime_candidate_r2_validation": "regime_candidate_r2_validation.csv",
    "regime_candidate_decision_update": "regime_candidate_decision_update.csv",
    "regime_candidate_validation_report": "regime_candidate_validation_report.md",
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _validate_required_input_frame(name: str, frame: pl.DataFrame) -> None:
    if frame.height == 0:
        raise ValueError(f"{name} has zero rows; required foundation input cannot be empty.")
    missing = _REQUIRED_INPUT_COLUMNS[name] - set(frame.columns)
    if missing:
        raise ValueError(
            f"{name} missing required columns: {', '.join(sorted(missing))}"
        )


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value)
    if text.lower() == "null":
        return default
    return text


def _row(**values: str) -> dict[str, str]:
    row = {column: "" for column in FOUNDATION_EXPERIMENT_SCHEMA}
    row.update(values)
    row["production_status"] = "EXPERIMENT_ONLY"
    return row


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return normalized or "UNKNOWN"


def _rule_experiment_id(rule_id: str, domain: str) -> str:
    known = {
        "REGIME_CLASSIFIER_CURRENT": "BEXP-QUAR-REGIME-CLASSIFIER-001",
        "RULE_LATE_WARMING_FIXED_18": "BEXP-QUAR-LATE-TMAX-001",
        "RULE_COOLING_FIXED_MINUS_2_C_PER_H": "BEXP-QUAR-COOLING-FIXED-001",
        "RULE_FOEHN_SCORE_FIXED_60": "BEXP-QUAR-FOEHN-FIXED-001",
        "RULE_ONDA2R_PHYSICAL_REGIME_FAMILY": "BEXP-QUAR-ONDA2R-REGIME-FAMILY-001",
    }
    if rule_id in known:
        return known[rule_id]
    return f"BEXP-QUAR-{_slug(domain)}-{_slug(rule_id)[:36]}-001"


def _weakness_from_rule(rule_id: str, domain: str) -> str:
    if "FIXED" in rule_id or domain in {"TIMING", "COOLING", "FOEHN"}:
        return "fixed_threshold"
    if "REGIME" in rule_id or domain == "REGIME":
        return "quarantined_baseline"
    return "baseline_gap"


def _implementation_from_rule(rule_id: str, domain: str) -> str:
    if "FIXED" in rule_id or domain in {"TIMING", "COOLING", "FOEHN"}:
        return "threshold_calibration"
    return "baseline_variant"


def _static_foundation_rows() -> list[dict[str, str]]:
    return [
        _row(
            experiment_id="BEXP-L2-MONTH-REGIME-001",
            experiment_family="baseline",
            domain="BASELINE",
            source_decision_id="ADR-012-BASELINE-L2",
            source_artifacts=(
                "reports/onda2e/domain_timing_norms_by_month_regime.csv; "
                "reports/regime-design/regime_candidate_assignments_v1.csv"
            ),
            weakness_target="high_mae",
            candidate_surface="baseline_ladder",
            implementation_kind="new_baseline",
            input_columns_or_artifacts="month; candidate_regime_label; tmax_int",
            strata="month x candidate regime",
            causal_status="outcome_only",
            leakage_risk="Fit month/regime climatology on train folds only; never use validation Tmax norms.",
            power_warning="Require minimum train rows per month x regime cell before leaderboard use.",
            baseline_comparator="L2",
            success_metric="mae_delta",
            acceptance_gate="Candidate MAE beats L2 with non-negative lower confidence bound across walk-forward years.",
            stop_condition="Underpowered cells dominate or candidate degrades MAE versus L2.",
            next_action="Implement train-only month/regime climatology baseline and compare on leaderboard.",
        ),
        _row(
            experiment_id="BEXP-L4-MONTH-CP-REGIME-001",
            experiment_family="baseline",
            domain="BASELINE",
            source_decision_id="ADR-012-BASELINE-L4",
            source_artifacts=(
                "reports/onda2e/regime_design_candidate_v1.csv; "
                "reports/regime-design/regime_candidate_assignments_v1.csv"
            ),
            weakness_target="high_mae",
            candidate_surface="baseline_ladder",
            implementation_kind="baseline_variant",
            input_columns_or_artifacts="month; CP; candidate_regime_label; remaining_warming",
            strata="month x CP x candidate regime",
            causal_status="outcome_only",
            leakage_risk="Use train-fold conditional means only; candidate regime labels must be pre-CP.",
            power_warning="Sparse month x CP x regime cells require fallback to month x CP.",
            baseline_comparator="L4",
            success_metric="mae_delta",
            acceptance_gate="Candidate reduces MAE versus L4 and fallback rate is reported.",
            stop_condition="Fallback rate is high or candidate loses to L4 in repeated years.",
            next_action="Add empirical conditional baseline variant for month/CP/candidate-regime strata.",
        ),
        _row(
            experiment_id="BEXP-LATE-TMAX-Q90-001",
            experiment_family="baseline",
            domain="TIMING",
            source_decision_id="RULE_LATE_WARMING_FIXED_18",
            source_artifacts=(
                "reports/onda2e/domain_timing_norms_by_month_regime.csv; "
                "reports/onda2e/domain_timing_bucket_priors.csv"
            ),
            weakness_target="fixed_threshold",
            candidate_surface="baseline_ladder",
            implementation_kind="baseline_variant",
            input_columns_or_artifacts="month; candidate_regime_label; tmax_hour",
            strata="month x candidate regime",
            causal_status="outcome_only",
            leakage_risk="Compute q90 timing norms on train folds only and use as diagnostic comparator.",
            power_warning="Report cells with too few Tmax-hour observations before interpreting q90.",
            baseline_comparator="RULE_LATE_WARMING_FIXED_18",
            success_metric="late_tmax_risk_delta",
            acceptance_gate="Train-only q90 rule explains late-Tmax risk better than fixed 18:00 diagnostic.",
            stop_condition="Q90 rule is unstable by year or leaks validation timing distribution.",
            next_action="Replace fixed late-hour diagnostic with train-only month/regime q90 experiment.",
        ),
        _row(
            experiment_id="BEXP-COOLING-MECHANISM-001",
            experiment_family="baseline",
            domain="COOLING",
            source_decision_id="RULE_COOLING_FIXED_MINUS_2_C_PER_H",
            source_artifacts=(
                "reports/onda2e/cooling_effects_by_month_regime_cp.csv; "
                "reports/onda2e/cooling_event_taxonomy_by_day_cp.csv"
            ),
            weakness_target="fixed_threshold",
            candidate_surface="baseline_ladder",
            implementation_kind="baseline_variant",
            input_columns_or_artifacts="cooling_mechanism; month; CP; remaining_warming",
            strata="month x CP x cooling mechanism",
            causal_status="causal_available",
            leakage_risk="Mechanism assignment must use pre-CP observations only.",
            power_warning="Cooling taxonomy has sparse mechanism cells; require fallback reporting.",
            baseline_comparator="L0;L4;RULE_COOLING_FIXED_MINUS_2_C_PER_H",
            success_metric="mae_delta",
            acceptance_gate="Mechanism-aware baseline improves MAE or documents a repeatable cooling weakness.",
            stop_condition="Mechanism split is underpowered or fails against L0/L4.",
            next_action="Implement cooling-mechanism baseline adjustment as an experiment-only comparator.",
        ),
        _row(
            experiment_id="TEXP-COOLING-MECHANISM-001",
            experiment_family="threshold",
            domain="COOLING",
            source_decision_id="WCT-COOL-003",
            source_artifacts=(
                "reports/onda2e/cooling_effects_by_month_regime_cp.csv; "
                "reports/onda2e/cooling_event_taxonomy_by_day_cp.csv"
            ),
            weakness_target="fixed_threshold",
            candidate_surface="regime_assignment",
            implementation_kind="threshold_calibration",
            input_columns_or_artifacts="temp_slope_pre_cp; wind shift; rain; pressure; cooling_mechanism",
            strata="month x CP x cooling mechanism",
            causal_status="causal_available",
            leakage_risk="Do not use final Tmax or post-CP cooling to assign a live regime.",
            power_warning="Require per-mechanism power checks before any regime split advances.",
            baseline_comparator="RULE_COOLING_FIXED_MINUS_2_C_PER_H",
            success_metric="dead_regime_count",
            acceptance_gate="Calibrated cooling split reduces dead regimes without increasing leakage risk.",
            stop_condition="Split remains dead, sparse, or requires outcome-derived assignment.",
            next_action="Calibrate cooling thresholds by mechanism/month/CP inside candidate regime design only.",
        ),
        _row(
            experiment_id="FEXP-FOEHN-CONTINUOUS-001",
            experiment_family="feature",
            domain="FOEHN",
            source_decision_id="WCT-FOEHN-001",
            source_artifacts="reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
            weakness_target="fixed_threshold",
            candidate_surface="feature_builder",
            implementation_kind="feature_probe",
            input_columns_or_artifacts="foehn_score; wind sector; dewpoint_depression; month; CP",
            strata="month x CP x foehn_score bin",
            causal_status="causal_available",
            leakage_risk="Use pre-CP score only; outcome effects can evaluate but not assign live regimes.",
            power_warning="55/272 FOEHN score-bin cells may be underpowered in current EDA.",
            baseline_comparator="RULE_FOEHN_SCORE_FIXED_60",
            success_metric="mae_delta",
            acceptance_gate="Continuous or binned score improves validation versus fixed >60 comparator.",
            stop_condition="Effect disappears in walk-forward years or score bins are too sparse.",
            next_action="Test continuous and binned foehn_score variants before any threshold promotion.",
        ),
        _row(
            experiment_id="WEXP-SOUTHERLY-DEPTH-001",
            experiment_family="regime",
            domain="WIND",
            source_decision_id="WCT-WIND-019",
            source_artifacts=(
                "reports/onda2e/wind_sector_effects_by_month_cp.csv; "
                "reports/onda2e/wind_direction_reliability_by_day_cp.csv"
            ),
            weakness_target="regime_split",
            candidate_surface="regime_assignment",
            implementation_kind="regime_revision",
            input_columns_or_artifacts="southerly_count; southerly_depth; month; CP",
            strata="month x CP x wind sector depth",
            causal_status="causal_available",
            leakage_risk="Use only pre-CP wind-sector observations for assignment.",
            power_warning="Wind EDA reports 28/412 sector effect cells with n_obs < 30.",
            baseline_comparator="REGIME_CLASSIFIER_CURRENT",
            success_metric="dead_regime_count",
            acceptance_gate="Southerly-depth split improves candidate R2 screen and keeps passing families alive.",
            stop_condition="Split is unstable, sparse, or worsens dead-regime count.",
            next_action="Evaluate southerly count/depth as regime-design split, not as production feature.",
        ),
    ]


def _baseline_rows(quarantined_baselines: pl.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in quarantined_baselines.iter_rows(named=True):
        rule_id = _text(item.get("rule_id"))
        domain = _text(item.get("domain"), "BASELINE")
        rows.append(
            _row(
                experiment_id=_rule_experiment_id(rule_id, domain),
                experiment_family="baseline",
                domain=domain,
                source_decision_id=rule_id,
                source_artifacts=_text(item.get("source_artifact")),
                weakness_target=_weakness_from_rule(rule_id, domain),
                candidate_surface="baseline_ladder",
                implementation_kind=_implementation_from_rule(rule_id, domain),
                input_columns_or_artifacts=_text(item.get("affected_surface")),
                strata="month; CP; candidate regime; physical mechanism as supported by EDA",
                causal_status="audit_only",
                leakage_risk=(
                    "Quarantined comparator; use only as baseline/audit surface until ADR-012 advances it."
                ),
                power_warning=_text(item.get("evidence_gap"), "Not calibrated; report sample power."),
                baseline_comparator=rule_id,
                success_metric="mae_delta",
                acceptance_gate="Experiment must beat or clarify the quarantined comparator without leakage.",
                stop_condition="Comparator remains arbitrary, underpowered, or worse than current ladder.",
                next_action=_text(item.get("next_allowed_action")),
            )
        )
    return rows


def _validate_quarantined_baselines(quarantined_baselines: pl.DataFrame) -> None:
    _validate_required_input_frame("quarantined_baselines", quarantined_baselines)
    missing = _REQUIRED_INPUT_COLUMNS["quarantined_baselines"] - set(quarantined_baselines.columns)
    if missing:
        raise ValueError(
            "quarantined_baselines missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    invalid = quarantined_baselines.filter(
        pl.col("decision_status") != "QUARANTINED_BASELINE"
    )
    if invalid.height:
        ids = ", ".join(str(value) for value in invalid.get_column("rule_id").to_list())
        raise ValueError(
            "quarantined_baselines rows must have decision_status=QUARANTINED_BASELINE: "
            f"{ids}"
        )


def _queue_experiment_family(status: str, domain: str) -> str:
    if status == "PROMOTED_TO_REGIME_DESIGN" or domain in {"REGIME", "WIND"}:
        return "regime"
    if domain in {"TIMING", "COOLING", "FOEHN"}:
        return "threshold"
    return "validation"


def _queue_experiment_id(queue_id: str, family: str, domain: str) -> str:
    prefix = {
        "baseline": "BEXP",
        "feature": "FEXP",
        "regime": "REXP",
        "threshold": "TEXP",
        "validation": "VEXP",
    }[family]
    return f"{prefix}-{_slug(domain)}-{_slug(queue_id)}"


def _queue_rows(regime_design_queue: pl.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in regime_design_queue.iter_rows(named=True):
        status = _text(item.get("source_decision_status"))
        domain = _text(item.get("domain"), "REGIME")
        family = _queue_experiment_family(status, domain)
        source_id = _text(item.get("source_item_id")) or _text(item.get("rule_id"))
        rule_id = _text(item.get("rule_id")) or source_id
        weakness = "regime_design_review" if family == "regime" else _weakness_from_rule(rule_id, domain)
        rows.append(
            _row(
                experiment_id=_queue_experiment_id(_text(item.get("queue_id")), family, domain),
                experiment_family=family,
                domain=domain,
                source_decision_id=source_id,
                source_artifacts=_text(item.get("source_artifact")),
                weakness_target=weakness,
                candidate_surface="regime_assignment" if family == "regime" else "validation_harness",
                implementation_kind="regime_revision" if family == "regime" else "threshold_calibration",
                input_columns_or_artifacts=_text(item.get("source_artifact")),
                strata="month x CP x candidate regime",
                causal_status="causal_available" if status == "PROMOTED_TO_REGIME_DESIGN" else "audit_only",
                leakage_risk="Experiment-only queue item; no production classifier or feature mutation.",
                power_warning=_text(item.get("evidence_gap")),
                baseline_comparator=rule_id or "current_best",
                success_metric="dead_regime_count" if family == "regime" else "mae_delta",
                acceptance_gate=(
                    "Advance only if candidate improves R2/dead-regime screen and passes Onda 4 review."
                    if family == "regime"
                    else "Advance only if calibrated threshold beats quarantined comparator."
                ),
                stop_condition="Park if sparse, leaky, or no better than the existing comparator.",
                next_action=_text(item.get("next_action")),
            )
        )
    return rows


def _rejected_ids(
    decision_register: pl.DataFrame,
    rejection_register: pl.DataFrame | None,
) -> set[str]:
    ids: set[str] = set()
    if {"item_id", "decision_status"}.issubset(decision_register.columns):
        rejected = decision_register.filter(pl.col("decision_status") == "REJECTED")
        ids.update(str(value) for value in rejected.get_column("item_id").to_list())
    if rejection_register is not None and "item_id" in rejection_register.columns:
        ids.update(str(value) for value in rejection_register.get_column("item_id").to_list())
    return ids


def _validate_regime_design_queue(
    regime_design_queue: pl.DataFrame,
    *,
    rejected_item_ids: set[str],
) -> None:
    _validate_required_input_frame("regime_design_queue", regime_design_queue)
    missing = _REQUIRED_INPUT_COLUMNS["regime_design_queue"] - set(regime_design_queue.columns)
    if missing:
        raise ValueError(
            "regime_design_queue missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    invalid_status = regime_design_queue.filter(
        ~pl.col("source_decision_status").is_in(_QUEUE_STATUSES)
    )
    if invalid_status.height:
        statuses = ", ".join(
            str(value)
            for value in invalid_status.get_column("source_decision_status").unique().to_list()
        )
        raise ValueError(f"regime_design_queue has unsupported or rejected statuses: {statuses}")

    rejected = regime_design_queue.filter(pl.col("source_item_id").is_in(rejected_item_ids))
    if rejected.height:
        ids = ", ".join(str(value) for value in rejected.get_column("source_item_id").to_list())
        raise ValueError(f"regime_design_queue contains rejected item ids: {ids}")


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"true", "1", "yes", "y", "pass", "passes"}


def _dead_family_id(family: str) -> str:
    known = {
        "candidate_maritime_cloudy": "REXP-DEAD-MARITIME-001",
        "candidate_mixed_or_transition": "REXP-DEAD-MIXED-001",
    }
    if family in known:
        return known[family]
    return f"REXP-DEAD-{_slug(family.removeprefix('candidate_'))[:40]}-001"


def _dead_family_next_action(family: str) -> str:
    if family == "candidate_maritime_cloudy":
        return "Repair maritime/cloudy assignment by splitting calm/radiative and cloudy maritime cases."
    if family == "candidate_mixed_or_transition":
        return "Split or merge mixed/transition family before rerunning candidate R2 validation."
    return f"Revise dead candidate family {family} before any Onda 4 promotion path."


def _dead_family_rows(regime_candidate_r2_validation: pl.DataFrame | None) -> list[dict[str, str]]:
    if regime_candidate_r2_validation is None or regime_candidate_r2_validation.height == 0:
        return []
    if not {"regime", "passes"}.issubset(regime_candidate_r2_validation.columns):
        return []

    rows: list[dict[str, str]] = []
    for family in sorted(regime_candidate_r2_validation.get_column("regime").drop_nulls().unique()):
        subset = regime_candidate_r2_validation.filter(pl.col("regime") == family)
        has_pass = any(_truthy(value) for value in subset.get_column("passes").to_list())
        if has_pass:
            continue
        rows.append(
            _row(
                experiment_id=_dead_family_id(str(family)),
                experiment_family="regime",
                domain="REGIME",
                source_decision_id=str(family),
                source_artifacts=(
                    "reports/regime-design/regime_candidate_r2_validation.csv; "
                    "reports/regime-design/regime_candidate_validation_report.md"
                ),
                weakness_target="dead_regime",
                candidate_surface="regime_assignment",
                implementation_kind="regime_revision",
                input_columns_or_artifacts="candidate_regime_label; pre-CP Onda 2E cluster inputs",
                strata="candidate regime family x CP",
                causal_status="causal_available",
                leakage_risk="Candidate labels are assigned offline from pre-CP inputs; no production overwrite.",
                power_warning=(
                    f"All {subset.height} R2 validation rows fail for {family}; inspect sparse cells."
                ),
                baseline_comparator="RULE_ONDA2R_PHYSICAL_REGIME_FAMILY",
                success_metric="dead_regime_count",
                acceptance_gate="Dead candidate family count decreases and no passing family becomes dead.",
                stop_condition="Family remains dead or revision requires outcome/post-CP assignment.",
                next_action=_dead_family_next_action(str(family)),
            )
        )
    return rows


def _repair_rows(
    repair_candidates: pl.DataFrame | None,
    *,
    default_domain: str,
    experiment_family: str,
) -> list[dict[str, str]]:
    if repair_candidates is None or repair_candidates.height == 0:
        return []

    rows: list[dict[str, str]] = []
    for item in repair_candidates.iter_rows(named=True):
        candidate_id = _text(item.get("candidate_id"))
        source_rule = _text(item.get("source_rule_id"), "current_best")
        domain = _text(item.get("domain"), default_domain)
        rows.append(
            _row(
                experiment_id=f"REXP-REPAIR-{_slug(candidate_id)}",
                experiment_family=experiment_family,
                domain=domain,
                source_decision_id=source_rule,
                source_artifacts=_text(item.get("evidence_artifact")),
                weakness_target="regime_repair",
                candidate_surface="regime_assignment",
                implementation_kind="regime_revision",
                input_columns_or_artifacts=_text(item.get("candidate_action")),
                strata="month x CP x candidate regime",
                causal_status="causal_available",
                leakage_risk="Repair candidate is experiment-only and must use pre-CP evidence.",
                power_warning=_text(item.get("rationale")),
                baseline_comparator=source_rule,
                success_metric="dead_regime_count",
                acceptance_gate="Repair improves R2/dead-regime validation without production mutation.",
                stop_condition="Repair remains dead, sparse, or leaky.",
                next_action=_text(item.get("next_action")),
            )
        )
    return rows


def _domain_next_rows(domain_eda_next_experiments: pl.DataFrame | None) -> list[dict[str, str]]:
    if domain_eda_next_experiments is None or domain_eda_next_experiments.height == 0:
        return []

    rows: list[dict[str, str]] = []
    for item in domain_eda_next_experiments.iter_rows(named=True):
        thesis_id = _text(item.get("thesis_id"))
        domain = _text(item.get("domain"), "DOMAIN")
        rows.append(
            _row(
                experiment_id=f"VEXP-DOMAIN-{_slug(thesis_id)}",
                experiment_family="validation",
                domain=domain,
                source_decision_id=thesis_id,
                source_artifacts=_text(item.get("required_artifact")),
                weakness_target=_text(item.get("blocker"), "blocked_thesis"),
                candidate_surface="validation_harness",
                implementation_kind="stratified_validation",
                input_columns_or_artifacts=_text(item.get("required_artifact")),
                strata="domain-specific blocked thesis strata",
                causal_status="audit_only",
                leakage_risk="Resolve as experiment-only validation before any feature or regime use.",
                power_warning="Blocked thesis requires explicit artifact before implementation.",
                baseline_comparator="current_best",
                success_metric="passing_years",
                acceptance_gate="Required artifact exists and produces an ADR-012 supported/adapted decision.",
                stop_condition="Artifact remains missing or thesis remains blocked.",
                next_action=_text(item.get("recommended_experiment")),
            )
        )
    return rows


def _dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        experiment_id = row["experiment_id"]
        if experiment_id in seen:
            continue
        seen.add(experiment_id)
        deduped.append(row)
    return deduped


def build_foundation_experiment_catalog(
    *,
    decision_register: pl.DataFrame,
    regime_design_queue: pl.DataFrame,
    quarantined_baselines: pl.DataFrame,
    rejection_register: pl.DataFrame | None = None,
    domain_eda_next_experiments: pl.DataFrame | None = None,
    foehn_repair_candidates: pl.DataFrame | None = None,
    wind_repair_candidates: pl.DataFrame | None = None,
    regime_candidate_r2_validation: pl.DataFrame | None = None,
    optional_artifact_warnings: pl.DataFrame | None = None,
) -> dict[str, pl.DataFrame]:
    """Build the v1 experiment catalog from Onda 2E decision artifacts."""
    _validate_required_input_frame("decision_register", decision_register)
    _validate_regime_design_queue(
        regime_design_queue,
        rejected_item_ids=_rejected_ids(decision_register, rejection_register),
    )
    _validate_quarantined_baselines(quarantined_baselines)
    rows = _dedupe_rows(
        [
            *_static_foundation_rows(),
            *_baseline_rows(quarantined_baselines),
            *_queue_rows(regime_design_queue),
            *_dead_family_rows(regime_candidate_r2_validation),
            *_repair_rows(
                foehn_repair_candidates,
                default_domain="FOEHN",
                experiment_family="regime",
            ),
            *_repair_rows(
                wind_repair_candidates,
                default_domain="WIND",
                experiment_family="regime",
            ),
            *_domain_next_rows(domain_eda_next_experiments),
        ]
    )
    catalog = (
        pl.DataFrame(rows, schema=FOUNDATION_EXPERIMENT_SCHEMA, strict=False)
        if rows
        else _empty_frame(FOUNDATION_EXPERIMENT_SCHEMA)
    )
    if catalog.height:
        catalog = catalog.sort(["experiment_family", "domain", "experiment_id"])

    warnings = (
        optional_artifact_warnings
        if optional_artifact_warnings is not None
        else _empty_frame(FOUNDATION_WARNING_SCHEMA)
    )
    if warnings.height:
        warnings = pl.DataFrame(
            warnings.select(list(FOUNDATION_WARNING_SCHEMA)).to_dicts(),
            schema=FOUNDATION_WARNING_SCHEMA,
            strict=False,
        )
    else:
        warnings = _empty_frame(FOUNDATION_WARNING_SCHEMA)

    return {
        "foundation_experiment_catalog": catalog,
        "foundation_experiment_warnings": warnings,
    }


def _read_optional_csv(
    path: Path,
    *,
    warnings: list[dict[str, str]],
) -> pl.DataFrame | None:
    if not path.exists():
        warnings.append(
            {
                "artifact": str(path),
                "status": "MISSING_OPTIONAL",
                "detail": "Optional foundation experiment source artifact was not found.",
            }
        )
        return None
    return pl.read_csv(path)


def load_foundation_experiment_inputs(
    *,
    onda2e_dir: str | Path,
    regime_design_dir: str | Path,
) -> dict[str, pl.DataFrame]:
    """Load foundation experiment source artifacts from local report directories."""
    onda2e_path = Path(onda2e_dir)
    regime_design_path = Path(regime_design_dir)
    inputs: dict[str, pl.DataFrame] = {}
    warnings: list[dict[str, str]] = []

    for key, filename in _REQUIRED_ONDA2E_INPUTS.items():
        path = onda2e_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Required foundation experiment input missing: {path}")
        frame = pl.read_csv(path)
        _validate_required_input_frame(key, frame)
        inputs[key] = frame

    for key, filename in _OPTIONAL_ONDA2E_INPUTS.items():
        frame = _read_optional_csv(onda2e_path / filename, warnings=warnings)
        if frame is not None:
            inputs[key] = frame

    for key, filename in _OPTIONAL_REGIME_DESIGN_INPUTS.items():
        path = regime_design_path / filename
        if filename.endswith(".md"):
            if not path.exists():
                warnings.append(
                    {
                        "artifact": str(path),
                        "status": "MISSING_OPTIONAL",
                        "detail": "Optional foundation experiment markdown source was not found.",
                    }
                )
            continue
        frame = _read_optional_csv(path, warnings=warnings)
        if frame is not None:
            inputs[key] = frame

    inputs.setdefault("rejection_register", _empty_frame({
        "decision_id": pl.Utf8,
        "item_id": pl.Utf8,
        "domain": pl.Utf8,
        "source_artifact": pl.Utf8,
        "decision_rationale": pl.Utf8,
        "reentry_condition": pl.Utf8,
    }))
    inputs["optional_artifact_warnings"] = (
        pl.DataFrame(warnings, schema=FOUNDATION_WARNING_SCHEMA, strict=False)
        if warnings
        else _empty_frame(FOUNDATION_WARNING_SCHEMA)
    )
    return inputs


def _md(value: object) -> str:
    return _text(value).replace("|", "/")


def _count_table(catalog: pl.DataFrame, column: str) -> list[str]:
    label = "Family" if column == "experiment_family" else column.replace("_", " ").title()
    lines = [
        f"## Counts By {label}",
        "",
        f"| {label} | Rows |",
        "|---|---:|",
    ]
    if catalog.height == 0:
        lines.append("| none | 0 |")
        return lines
    counts = catalog.group_by(column).len(name="n").sort(column)
    for row in counts.iter_rows(named=True):
        lines.append(f"| {_md(row[column])} | {row['n']} |")
    return lines


def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    catalog = artifacts["foundation_experiment_catalog"]
    warnings = artifacts.get("foundation_experiment_warnings", _empty_frame(FOUNDATION_WARNING_SCHEMA))
    lines = [
        f"# Foundation Experiment Catalog - {report_date.isoformat()}",
        "",
        "This is not a production promotion.",
        "Every row is an experiment candidate and keeps `production_status = EXPERIMENT_ONLY`.",
        "",
        f"- Catalog rows: {catalog.height}",
        f"- Families: {catalog['experiment_family'].n_unique() if catalog.height else 0}",
        f"- Domains: {catalog['domain'].n_unique() if catalog.height else 0}",
        "",
    ]
    for column in ("experiment_family", "domain", "weakness_target", "candidate_surface"):
        lines.extend(_count_table(catalog, column))
        lines.append("")

    priority = catalog.filter(
        pl.col("experiment_id").is_in(
            [
                "BEXP-L2-MONTH-REGIME-001",
                "BEXP-L4-MONTH-CP-REGIME-001",
                "REXP-DEAD-MARITIME-001",
                "REXP-DEAD-MIXED-001",
                "TEXP-COOLING-MECHANISM-001",
                "FEXP-FOEHN-CONTINUOUS-001",
                "WEXP-SOUTHERLY-DEPTH-001",
            ]
        )
    )
    lines += [
        "## Priority Experiments",
        "",
        "| Experiment | Family | Domain | Target | Comparator | Next action |",
        "|---|---|---|---|---|---|",
    ]
    for row in priority.sort("experiment_id").iter_rows(named=True):
        lines.append(
            "| "
            f"{_md(row['experiment_id'])} | "
            f"{_md(row['experiment_family'])} | "
            f"{_md(row['domain'])} | "
            f"{_md(row['weakness_target'])} | "
            f"{_md(row['baseline_comparator'])} | "
            f"{_md(row['next_action'])} |"
        )

    lines += [
        "",
        "## Missing Optional Artifacts",
        "",
        "| Artifact | Status | Detail |",
        "|---|---|---|",
    ]
    if warnings.height == 0:
        lines.append("| none | PASS | All optional artifacts found. |")
    else:
        for row in warnings.iter_rows(named=True):
            lines.append(
                f"| {_md(row['artifact'])} | {_md(row['status'])} | {_md(row['detail'])} |"
            )
    lines += [
        "",
        "## Production Guard",
        "",
        "The catalog can guide implementation experiments, but it does not promote a feature, "
        "baseline, model, or regime classifier to production. Experiment results must be "
        "recorded separately before ADR-012 can advance any candidate.",
    ]
    return lines


def write_foundation_experiment_catalog_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write the v1 foundation experiment catalog CSV and markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()

    catalog_path = out_dir / "foundation_experiment_catalog_v1.csv"
    artifacts["foundation_experiment_catalog"].write_csv(catalog_path)
    report_path = out_dir / "foundation_experiment_catalog_v1.md"
    report_path.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")

    return {
        "foundation_experiment_catalog_csv": catalog_path,
        "foundation_experiment_catalog_md": report_path,
    }
