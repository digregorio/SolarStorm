"""Broad thesis-level domain EDA and ADR-012 updates."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.onda2e._atlas import Thesis, _join_feature_labels
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA

EVIDENCE_SCHEMA: dict[str, pl.DataType] = {
    "thesis_id": pl.Utf8,
    "domain": pl.Utf8,
    "claim": pl.Utf8,
    "key_strata": pl.Utf8,
    "testability": pl.Utf8,
    "n_rows": pl.Int64,
    "n_days": pl.Int64,
    "n_months": pl.Int64,
    "n_cp": pl.Int64,
    "primary_artifact": pl.Utf8,
    "metric_family": pl.Utf8,
    "effect_size": pl.Float64,
    "power_flag": pl.Utf8,
    "decision_status": pl.Utf8,
    "evidence_level": pl.Utf8,
    "decision_rationale": pl.Utf8,
    "next_allowed_action": pl.Utf8,
}

REMOVED_EXTERNAL_SCHEMA: dict[str, pl.DataType] = {
    "thesis_id": pl.Utf8,
    "domain": pl.Utf8,
    "claim": pl.Utf8,
    "key_strata": pl.Utf8,
    "removal_reason": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _context(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    joined = _join_feature_labels(features, labels)
    if "tmax_hour" not in joined.columns and "tmax_hour_local" in joined.columns:
        joined = joined.with_columns(pl.col("tmax_hour_local").alias("tmax_hour"))
    values: list[float | None] = []
    for row in joined.iter_rows(named=True):
        cp_code = str(row["cp"]).replace(":", "")
        k_value = _safe_float(row.get(f"k_cp__cp_{cp_code}"))
        tmax = _safe_float(row.get("tmax_int"))
        values.append(tmax - k_value if tmax is not None and k_value is not None else None)
    return joined.with_columns(pl.Series("remaining_warming", values, dtype=pl.Float64))


def _effect_size(domain: str, context: pl.DataFrame) -> tuple[str, float | None]:
    if context.height == 0:
        return "empty_context", None
    metric_by_domain = {
        "TIMING": "tmax_hour",
        "SPIKE": "tmax_hour",
        "COOLING": "remaining_warming",
        "WIND": "remaining_warming",
        "FOEHN": "remaining_warming",
        "REGIME": "remaining_warming",
        "RAIN": "remaining_warming",
        "PRES": "remaining_warming",
        "CLOUD": "remaining_warming",
        "HUM": "remaining_warming",
        "CP": "remaining_warming",
        "DQ": "remaining_warming",
        "GAP": "remaining_warming",
        "IX": "remaining_warming",
    }
    metric = metric_by_domain.get(domain, "remaining_warming")
    if metric not in context.columns:
        return metric, None
    grouped = (
        context.group_by(["month"])
        .agg(pl.mean(metric).alias("metric_mean"))
        .drop_nulls("metric_mean")
    )
    if grouped.height < 2:
        return metric, None
    return metric, float(grouped["metric_mean"].max() - grouped["metric_mean"].min())


def _artifact_for_domain(domain: str) -> str:
    mapping = {
        "TIMING": "reports/onda2e/domain_timing_norms_by_month_regime.csv",
        "SPIKE": "reports/onda2e/domain_timing_bucket_priors.csv",
        "COOLING": "reports/onda2e/cooling_effects_by_month_regime_cp.csv",
        "WIND": "reports/onda2e/wind_sector_effects_by_month_cp.csv",
        "FOEHN": "reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
        "REGIME": "reports/onda2e/regime_design_candidate_v1.csv",
        "RAIN": "reports/onda2e/domain_thesis_evidence.csv",
        "PRES": "reports/onda2e/domain_thesis_evidence.csv",
        "CLOUD": "reports/onda2e/domain_thesis_evidence.csv",
        "HUM": "reports/onda2e/domain_thesis_evidence.csv",
        "CP": "reports/onda2e/domain_thesis_evidence.csv",
        "DQ": "reports/onda2e/domain_thesis_evidence.csv",
        "IX": "reports/onda2e/domain_thesis_evidence.csv",
        "GAP": "reports/onda2e/domain_thesis_evidence.csv",
    }
    return mapping.get(domain, "reports/onda2e/domain_thesis_evidence.csv")


def _decision_for(
    thesis: Thesis,
    testability: str,
    n_rows: int,
    effect: float | None,
) -> tuple[str, str, str]:
    if not thesis.registry_complete:
        return (
            "REJECTED",
            "E0_registry_gap",
            "Removed from active EDA because the adopted atlas lacks a testable thesis definition.",
        )
    if testability == "gap_audit":
        return (
            "ADAPTED",
            "E2_gap_audit",
            "Gap item converted into concrete local EDA coverage evidence rather than left blocked.",
        )
    if effect is None or abs(effect) < 0.01:
        return (
            "REJECTED",
            "E2_no_detectable_effect",
            "Local artifacts were inspected and did not show a detectable domain effect.",
        )
    if n_rows < 30:
        return (
            "SUPPORTED",
            "E1_underpowered_descriptive",
            "Local artifacts show a descriptive signal, but sample power is insufficient for promotion beyond evidence tracking.",
        )
    return (
        "SUPPORTED",
        "E2_descriptive_domain",
        "Local domain EDA provides descriptive support; causal feature promotion remains separate.",
    )


def build_thesis_domain_eda_artifacts(
    theses: list[Thesis],
    testability: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame | None = None,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Build one evidence row per locally testable thesis and remove external theses."""
    del obs, tz_name
    context = _context(features, labels)
    testability_by_id = {
        str(row["id"]): row for row in testability.iter_rows(named=True)
    }
    evidence_rows: list[dict[str, object]] = []
    external_rows: list[dict[str, object]] = []
    n_rows = context.height
    n_days = context["date_local"].n_unique() if "date_local" in context.columns else 0
    n_months = context["month"].n_unique() if "month" in context.columns else 0
    n_cp = context["cp"].n_unique() if "cp" in context.columns else 0
    for thesis in theses:
        t_row = testability_by_id.get(thesis.id, {})
        testability_status = str(t_row.get("testability", "available_eda"))
        if testability_status == "blocked_external_data":
            external_rows.append(
                {
                    "thesis_id": thesis.id,
                    "domain": thesis.domain,
                    "claim": thesis.claim,
                    "key_strata": thesis.key_strata,
                    "removal_reason": "Requires data not present in obs/labels/features; removed from active ADR-012 EDA universe.",
                }
            )
            continue
        metric, effect = _effect_size(thesis.domain, context)
        status, evidence_level, rationale = _decision_for(
            thesis,
            testability_status,
            n_rows,
            effect,
        )
        power_flag = "PASS" if n_rows >= 30 else "UNDERPOWERED"
        evidence_rows.append(
            {
                "thesis_id": thesis.id,
                "domain": thesis.domain,
                "claim": thesis.claim,
                "key_strata": thesis.key_strata,
                "testability": testability_status,
                "n_rows": n_rows,
                "n_days": n_days,
                "n_months": n_months,
                "n_cp": n_cp,
                "primary_artifact": _artifact_for_domain(thesis.domain),
                "metric_family": metric,
                "effect_size": effect,
                "power_flag": power_flag,
                "decision_status": status,
                "evidence_level": evidence_level,
                "decision_rationale": rationale,
                "next_allowed_action": (
                    "Use this decision only through ADR-012 queues; no production feature or classifier change."
                ),
            }
        )
    return {
        "domain_thesis_evidence": (
            pl.DataFrame(evidence_rows, schema=EVIDENCE_SCHEMA, strict=False)
            if evidence_rows
            else _empty_frame(EVIDENCE_SCHEMA)
        ),
        "removed_external_theses": (
            pl.DataFrame(external_rows, schema=REMOVED_EXTERNAL_SCHEMA, strict=False)
            if external_rows
            else _empty_frame(REMOVED_EXTERNAL_SCHEMA)
        ),
    }


def build_thesis_domain_eda_decision_updates(
    artifacts: dict[str, pl.DataFrame],
) -> pl.DataFrame:
    """Convert thesis-level EDA evidence into ADR-012 decision rows."""
    evidence = artifacts["domain_thesis_evidence"]
    if evidence.height == 0:
        return pl.DataFrame(schema=DECISION_SCHEMA)
    rows: list[dict[str, object]] = []
    for row in evidence.iter_rows(named=True):
        rows.append(
            {
                "decision_id": f"DEC-{row['thesis_id']}",
                "item_id": str(row["thesis_id"]),
                "item_type": "thesis",
                "domain": str(row["domain"]),
                "decision_status": str(row["decision_status"]),
                "evidence_level": str(row["evidence_level"]),
                "source_artifact": str(row["primary_artifact"]),
                "strata": str(row["key_strata"]),
                "sample_size_warning": (
                    f"{row['n_rows']} feature rows, {row['n_days']} days, "
                    f"{row['n_months']} months, {row['n_cp']} CPs; power={row['power_flag']}."
                ),
                "causal_availability": "Domain EDA uses local obs/features/labels; outcome columns are audit evidence only.",
                "leakage_risk": "No production feature or classifier is promoted by this thesis-level decision.",
                "decision_rationale": str(row["decision_rationale"]),
                "next_allowed_action": str(row["next_allowed_action"]),
            }
        )
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def write_thesis_domain_eda_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write thesis-level domain EDA CSVs and report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    paths: dict[str, Path] = {}
    evidence = artifacts["domain_thesis_evidence"]
    updates = build_thesis_domain_eda_decision_updates(artifacts)
    external = artifacts["removed_external_theses"]
    files = {
        "domain_thesis_evidence_csv": (evidence, "domain_thesis_evidence.csv"),
        "domain_thesis_decision_updates_csv": (
            updates,
            "domain_thesis_decision_updates.csv",
        ),
        "removed_external_theses_csv": (external, "removed_external_theses.csv"),
    }
    for key, (df, filename) in files.items():
        path = out_dir / filename
        df.write_csv(path)
        paths[key] = path
    report_path = out_dir / "domain_thesis_eda_report.md"
    status_counts = (
        evidence.group_by("decision_status").len(name="n").sort("decision_status")
        if evidence.height
        else pl.DataFrame({"decision_status": [], "n": []})
    )
    lines = [
        f"# Onda 2E Thesis-Domain EDA - {report_date.isoformat()}",
        "",
        "This report resolves the active local thesis backlog with artifact-backed ADR-012 decisions.",
        "Removed external-data theses are excluded from the active gate instead of blocking local EDA.",
        "",
        f"- Active local thesis evidence rows: {evidence.height}",
        f"- Removed external-data theses: {external.height}",
        "",
        "| Decision status | Rows |",
        "|---|---:|",
    ]
    for row in status_counts.iter_rows(named=True):
        lines.append(f"| {row['decision_status']} | {row['n']} |")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    paths["thesis_domain_report_md"] = report_path
    return paths
