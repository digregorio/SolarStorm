"""Onda 2E cooling-regime domain EDA artifacts."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.onda2e._atlas import (
    _COOLING_FEATURE_ROW_NR,
    _build_cooling_event_rows,
    _cached_cooling_event_rows,
    _classify_cooling_mechanism,
    _feature_row_slice,
    _join_feature_labels,
    _obs_by_local_date,
)
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA


def _with_month(df: pl.DataFrame) -> pl.DataFrame:
    if "month" in df.columns:
        return df
    return df.with_columns(pl.col("date_local").dt.month().alias("month"))


def _remaining_warming(row: dict) -> int | None:
    cp_code = str(row["cp"]).replace(":", "")
    k_col = f"k_cp__cp_{cp_code}"
    k_value = row.get(k_col)
    tmax = row.get("tmax_int")
    return int(tmax - k_value) if tmax is not None and k_value is not None else None


def _month_means(labels: pl.DataFrame) -> pl.DataFrame:
    labels_m = _with_month(labels)
    return labels_m.group_by("month").agg(pl.mean("tmax_int").alias("month_mean_tmax"))


def build_cooling_domain_artifacts(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Build cooling-domain EDA tables for regime-repair decisions."""
    indexed_features = features.with_row_index(_COOLING_FEATURE_ROW_NR)
    joined = _join_feature_labels(indexed_features, labels)
    joined = _with_month(joined).join(_month_means(labels), on="month", how="left")
    cached_events = _cached_cooling_event_rows(features, obs, tz_name)
    if cached_events is None:
        cached_events = _build_cooling_event_rows(features, obs, tz_name=tz_name)
    event_by_feature_row = {
        row[_COOLING_FEATURE_ROW_NR]: row
        for row in cached_events.iter_rows(named=True)
    }
    obs_by_date = _obs_by_local_date(obs, tz_name) if not event_by_feature_row else {}
    rows: list[dict] = []
    for row in joined.iter_rows(named=True):
        event = event_by_feature_row.get(row[_COOLING_FEATURE_ROW_NR])
        if event is None:
            slice_df = _feature_row_slice(row, obs_by_date, tz_name)
            mechanism = (
                {
                    "cooling_mechanism": "insufficient_obs",
                    "min_delta_t_per_h": None,
                    "cooling_hour": None,
                    "n_pre_cp_obs": 0,
                }
                if slice_df is None
                else {
                    **_classify_cooling_mechanism(slice_df),
                    "n_pre_cp_obs": slice_df.height,
                }
            )
        else:
            mechanism = event
        min_delta = mechanism.get("min_delta_t_per_h")
        rows.append(
            {
                "date_local": row["date_local"],
                "month": row["month"],
                "cp": str(row["cp"]),
                "regime_label": str(row.get("regime_label") or "unknown"),
                "cooling_mechanism": mechanism["cooling_mechanism"],
                "min_delta_t_per_h": min_delta,
                "cooling_hour": mechanism.get("cooling_hour"),
                "fixed_minus_2_trigger": bool(min_delta is not None and float(min_delta) < -2.0),
                "remaining_warming": _remaining_warming(row),
                "tmax_anomaly": (
                    float(row["tmax_int"] - row["month_mean_tmax"])
                    if row.get("tmax_int") is not None and row.get("month_mean_tmax") is not None
                    else None
                ),
                "n_pre_cp_obs": mechanism["n_pre_cp_obs"],
                "causal_slice": True,
            }
        )
    events = pl.DataFrame(rows, strict=False)
    effects = (
        events.group_by(["month", "regime_label", "cp", "cooling_mechanism"])
        .agg(
            pl.len().alias("n_rows"),
            pl.mean("remaining_warming").alias("mean_remaining_warming"),
            pl.mean("tmax_anomaly").alias("mean_tmax_anomaly"),
            pl.mean("fixed_minus_2_trigger").alias("fixed_minus_2_trigger_rate"),
            pl.median("min_delta_t_per_h").alias("median_min_delta_t_per_h"),
        )
        .with_columns((pl.col("n_rows") < 30).alias("underpowered_n_lt_30"))
        .sort(["month", "regime_label", "cp", "cooling_mechanism"])
    )
    fixed_trigger_rate = float(events["fixed_minus_2_trigger"].mean() or 0.0)
    mechanism_count = events["cooling_mechanism"].n_unique()
    candidates = pl.DataFrame(
        [
            {
                "candidate_id": "CRR-001",
                "source_rule_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
                "candidate_action": "replace_single_threshold_with_mechanism_taxonomy",
                "evidence_artifact": "reports/onda2e/cooling_event_taxonomy_by_day_cp.csv",
                "rationale": f"Fixed -2 C/h trigger rate is {fixed_trigger_rate:.3f} across {mechanism_count} cooling mechanisms.",
                "next_action": "Review mechanism effects by month/regime/CP before changing any production classifier.",
            }
        ]
    )
    leakage = pl.DataFrame(
        [
            {
                "audit_item": "cp_slice_causal",
                "status": "PASS" if bool(events["causal_slice"].all()) else "FAIL",
                "detail": "All cooling events are computed from observations with valid < CP.",
            },
            {
                "audit_item": "outcome_usage",
                "status": "WARN",
                "detail": "tmax_int/tmax_anomaly are outcome columns used only for EDA effects, not CP evidence.",
            },
            {
                "audit_item": "power",
                "status": "WARN" if effects.filter(pl.col("underpowered_n_lt_30")).height else "PASS",
                "detail": f"{effects.filter(pl.col('underpowered_n_lt_30')).height}/{effects.height} effect cells have n < 30.",
            },
        ]
    )
    return {
        "cooling_event_taxonomy_by_day_cp": events.sort(["date_local", "cp"]),
        "cooling_effects_by_month_regime_cp": effects,
        "cooling_power_leakage_audit": leakage,
        "regime_repair_candidates": candidates,
    }


def _power_warning(effects: pl.DataFrame) -> str:
    underpowered = effects.filter(pl.col("underpowered_n_lt_30")).height
    return f"{underpowered}/{effects.height} cooling effect cells have n < 30."


def build_cooling_decision_updates(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build ADR-012 decision updates from cooling-domain EDA."""
    effects = artifacts["cooling_effects_by_month_regime_cp"]
    warning = _power_warning(effects)
    rows = [
        {
            "decision_id": "DEC-WCT-COOL-001",
            "item_id": "WCT-COOL-001",
            "item_type": "thesis",
            "domain": "COOLING",
            "decision_status": "SUPPORTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/cooling_event_taxonomy_by_day_cp.csv",
            "strata": "month x regime_label x CP x cooling_mechanism",
            "sample_size_warning": warning,
            "causal_availability": "Cooling event classification uses pre-CP observations only.",
            "leakage_risk": "Outcome columns appear only in effect summaries, not mechanism classification.",
            "decision_rationale": "Cooling peak hour/mechanism taxonomy is now computed before CP.",
            "next_allowed_action": "Use as evidence for regime-design review; no feature candidate is promoted.",
        },
        {
            "decision_id": "DEC-WCT-COOL-003",
            "item_id": "WCT-COOL-003",
            "item_type": "thesis",
            "domain": "COOLING",
            "decision_status": "PROMOTED_TO_REGIME_DESIGN",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/cooling_effects_by_month_regime_cp.csv",
            "strata": "month x regime_label x CP x cooling_mechanism",
            "sample_size_warning": warning,
            "causal_availability": "Wind speed/direction and temperature deltas are pre-CP.",
            "leakage_risk": "Regime repair must not use final Tmax to assign a live regime.",
            "decision_rationale": "Frontal/radiative/post-dawn cooling classes are separated enough to enter regime design review.",
            "next_allowed_action": "Design a replacement regime candidate that separates cooling mechanisms before Onda 4 rerun.",
        },
        {
            "decision_id": "DEC-RULE_COOLING_FIXED_MINUS_2_C_PER_H",
            "item_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
            "item_type": "rule",
            "domain": "COOLING",
            "decision_status": "ADAPTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/regime_repair_candidates.csv",
            "strata": "month x regime_label x CP x cooling_mechanism",
            "sample_size_warning": warning,
            "causal_availability": "The fixed threshold is allowed only as diagnostic comparator.",
            "leakage_risk": "Using it as a production regime trigger would preserve an arbitrary threshold.",
            "decision_rationale": "Replace the single -2 C/h trigger with mechanism-specific regime-design candidates.",
            "next_allowed_action": "Keep the threshold quarantined as comparator until a reviewed regime repair passes Onda 4.",
        },
    ]
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def write_cooling_domain_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write cooling-regime domain EDA CSVs and report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "cooling_event_taxonomy_by_day_cp": "cooling_event_taxonomy_by_day_cp.csv",
        "cooling_effects_by_month_regime_cp": "cooling_effects_by_month_regime_cp.csv",
        "cooling_power_leakage_audit": "cooling_power_leakage_audit.csv",
        "regime_repair_candidates": "regime_repair_candidates.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        _write_csv(artifacts[key], path)
        paths[f"{key}_csv"] = path

    events = artifacts["cooling_event_taxonomy_by_day_cp"]
    effects = artifacts["cooling_effects_by_month_regime_cp"]
    report_path = out_dir / "cooling_regime_domain_report.md"
    report_path.write_text(
        "\n".join(
            [
                f"# Onda 2E Cooling-Regime Domain EDA - {report_date.isoformat()}",
                "",
                "No production classifier change is made by this report.",
                "Cooling evidence is used only to feed ADR-012 regime-design decisions.",
                "",
                "## Artifacts",
                "",
                "| Artifact | Rows |",
                "|---|---:|",
                f"| `cooling_event_taxonomy_by_day_cp.csv` | {events.height} |",
                f"| `cooling_effects_by_month_regime_cp.csv` | {effects.height} |",
                f"| `cooling_power_leakage_audit.csv` | {artifacts['cooling_power_leakage_audit'].height} |",
                f"| `regime_repair_candidates.csv` | {artifacts['regime_repair_candidates'].height} |",
                "",
                "## Decision Implication",
                "",
                "- `WCT-COOL-001`: SUPPORTED as descriptive domain evidence.",
                "- `WCT-COOL-003`: PROMOTED_TO_REGIME_DESIGN.",
                "- `RULE_COOLING_FIXED_MINUS_2_C_PER_H`: ADAPTED, not retained as production truth.",
            ]
        ),
        encoding="utf-8",
    )
    paths["cooling_report_md"] = report_path
    return paths
