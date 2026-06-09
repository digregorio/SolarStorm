"""Onda 2E FOEHN-domain EDA artifacts."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda2e._atlas import _join_feature_labels
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA


def _with_month(df: pl.DataFrame) -> pl.DataFrame:
    if "month" in df.columns:
        return df
    return df.with_columns(pl.col("date_local").dt.month().alias("month"))


def _remaining_warming(row: dict) -> float | None:
    cp_code = str(row["cp"]).replace(":", "")
    k_col = f"k_cp__cp_{cp_code}"
    k_value = row.get(k_col)
    tmax = row.get("tmax_int")
    return float(tmax - k_value) if tmax is not None and k_value is not None else None


def _month_means(labels: pl.DataFrame) -> pl.DataFrame:
    labels_m = _with_month(labels)
    return labels_m.group_by("month").agg(pl.mean("tmax_int").alias("month_mean_tmax"))


def _ensure_columns(df: pl.DataFrame, columns: dict[str, pl.DataType]) -> pl.DataFrame:
    expressions = [
        pl.lit(None, dtype=dtype).alias(name)
        for name, dtype in columns.items()
        if name not in df.columns
    ]
    if not expressions:
        return df
    return df.with_columns(expressions)


def _foehn_context(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    has_nw_sector_not_foehn = "nw_sector_not_foehn" in features.columns
    has_regime_label = "regime_label" in features.columns
    joined = _join_feature_labels(features, labels)
    joined = _ensure_columns(
        joined,
        {
            "foehn_score": pl.Float64,
            "regime_label": pl.Utf8,
            "nw_sector_not_foehn": pl.Int64,
            "dewpoint_depression": pl.Float64,
            "dewpoint_collapse_rate_3h": pl.Float64,
        },
    )
    joined = _with_month(joined).join(_month_means(labels), on="month", how="left")
    remaining = [_remaining_warming(row) for row in joined.iter_rows(named=True)]
    return joined.with_columns(
        [
            pl.Series("remaining_warming", remaining, dtype=pl.Float64),
            (pl.col("tmax_int") - pl.col("month_mean_tmax")).alias("tmax_anomaly"),
            pl.lit(has_nw_sector_not_foehn).alias("has_nw_sector_not_foehn"),
            pl.lit(has_regime_label).alias("has_regime_label"),
        ]
    )


def _score_bin_expr() -> pl.Expr:
    return (
        pl.when(pl.col("foehn_score").is_null())
        .then(pl.lit("missing"))
        .when(pl.col("foehn_score") < 20.0)
        .then(pl.lit("lt_20"))
        .when(pl.col("foehn_score") < 40.0)
        .then(pl.lit("20_40"))
        .when(pl.col("foehn_score") < 60.0)
        .then(pl.lit("40_60"))
        .when(pl.col("foehn_score") < 80.0)
        .then(pl.lit("60_80"))
        .otherwise(pl.lit("gte_80"))
        .alias("foehn_score_bin")
    )


def _build_score_bins(context: pl.DataFrame) -> pl.DataFrame:
    return (
        context.with_columns(_score_bin_expr())
        .group_by(["month", "cp", "foehn_score_bin"])
        .agg(
            pl.len().alias("n_rows"),
            pl.mean("foehn_score").alias("mean_foehn_score"),
            pl.mean("dewpoint_depression").alias("mean_dewpoint_depression"),
            pl.mean("dewpoint_collapse_rate_3h").alias(
                "mean_dewpoint_collapse_rate_3h"
            ),
            pl.mean("tmax_anomaly").alias("mean_tmax_anomaly"),
            pl.mean("remaining_warming").alias("mean_remaining_warming"),
        )
        .with_columns((pl.col("n_rows") < 30).alias("underpowered_n_lt_30"))
        .sort(["month", "cp", "foehn_score_bin"])
    )


def _build_false_positive_audit(context: pl.DataFrame) -> pl.DataFrame:
    audited = context.with_columns(
        [
            (pl.col("foehn_score") > 60.0).fill_null(False).alias("fixed_60_trigger"),
            (pl.col("nw_sector_not_foehn").fill_null(0).cast(pl.Int64) > 0).alias(
                "nw_sector_not_foehn_flag"
            ),
            pl.col("regime_label")
            .fill_null("unknown")
            .str.to_lowercase()
            .str.contains("foehn")
            .fill_null(False)
            .alias("regime_mentions_foehn"),
        ]
    ).with_columns(
        (pl.col("fixed_60_trigger") & pl.col("nw_sector_not_foehn_flag")).alias(
            "fixed_60_nw_sector_not_foehn"
        ),
        (pl.col("fixed_60_trigger") & ~pl.col("regime_mentions_foehn")).alias(
            "fixed_60_non_foehn_regime"
        ),
    )
    grouped = (
        audited.group_by(["month", "cp"])
        .agg(
            pl.len().alias("n_rows"),
            pl.sum("fixed_60_trigger").cast(pl.Int64).alias("n_fixed_60_trigger"),
            pl.mean("fixed_60_trigger").alias("fixed_60_trigger_rate"),
            pl.sum("fixed_60_nw_sector_not_foehn")
            .cast(pl.Int64)
            .alias("n_fixed_60_nw_sector_not_foehn"),
            pl.sum("fixed_60_non_foehn_regime")
            .cast(pl.Int64)
            .alias("n_fixed_60_non_foehn_regime"),
            pl.any("has_nw_sector_not_foehn").alias("has_nw_sector_not_foehn"),
            pl.any("has_regime_label").alias("has_regime_label"),
        )
        .with_columns(
            pl.when(pl.col("n_fixed_60_trigger") > 0)
            .then(
                pl.col("n_fixed_60_nw_sector_not_foehn")
                / pl.col("n_fixed_60_trigger")
            )
            .otherwise(None)
            .alias("fixed_60_nw_sector_not_foehn_share"),
            pl.when(pl.col("n_fixed_60_trigger") > 0)
            .then(
                pl.col("n_fixed_60_non_foehn_regime")
                / pl.col("n_fixed_60_trigger")
            )
            .otherwise(None)
            .alias("fixed_60_non_foehn_regime_share"),
            pl.lit(
                "Audit comparator only: nw_sector_not_foehn/regime_label flag possible fixed-threshold false positives, not final truth."
            ).alias("audit_interpretation"),
        )
        .sort(["month", "cp"])
    )
    return grouped


def _build_regime_repair_candidates(bins: pl.DataFrame, audit: pl.DataFrame) -> pl.DataFrame:
    underpowered = bins.filter(pl.col("underpowered_n_lt_30")).height
    max_audit_share = (
        audit["fixed_60_nw_sector_not_foehn_share"].max()
        if audit.height and "fixed_60_nw_sector_not_foehn_share" in audit.columns
        else None
    )
    audit_text = (
        "Fixed-60 false-positive share could not be estimated."
        if max_audit_share is None
        else f"Max fixed-60 NW-sector-not-foehn share is {max_audit_share:.3f}."
    )
    return pl.DataFrame(
        [
            {
                "candidate_id": "FRR-001",
                "source_rule_id": "RULE_FOEHN_SCORE_FIXED_60",
                "candidate_action": "calibrate_by_month_cp_or_replace_with_binned_continuous_score",
                "evidence_artifact": "reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
                "rationale": (
                    "Fixed foehn_score > 60 is retained only as an audit comparator. "
                    f"{audit_text} {underpowered}/{bins.height} score-bin cells have n < 30."
                ),
                "next_action": "Review month/CP bins and continuous-score calibration before changing any production regime classifier.",
            }
        ]
    )


def _build_power_leakage_audit(bins: pl.DataFrame) -> pl.DataFrame:
    underpowered = bins.filter(pl.col("underpowered_n_lt_30")).height
    return pl.DataFrame(
        [
            {
                "audit_item": "outcome_usage",
                "status": "WARN",
                "detail": "tmax_int, tmax_anomaly, and remaining_warming are labels used only for EDA effects, not CP evidence.",
            },
            {
                "audit_item": "future_observation_use",
                "status": "PASS",
                "detail": "FOEHN artifacts are built by joining feature rows to labels only; no future observation table is read.",
            },
            {
                "audit_item": "power",
                "status": "WARN" if underpowered else "PASS",
                "detail": f"{underpowered}/{bins.height} FOEHN score-bin cells have n < 30.",
            },
        ]
    )


def build_foehn_domain_artifacts(
    features: pl.DataFrame,
    labels: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Build FOEHN-domain EDA tables for score calibration decisions."""
    context = _foehn_context(features, labels)
    bins = _build_score_bins(context)
    false_positive = _build_false_positive_audit(context)
    return {
        "foehn_score_bins_by_month_cp": bins,
        "foehn_false_positive_audit": false_positive,
        "foehn_power_leakage_audit": _build_power_leakage_audit(bins),
        "foehn_regime_repair_candidates": _build_regime_repair_candidates(
            bins,
            false_positive,
        ),
    }


def _power_warning(bins: pl.DataFrame) -> str:
    underpowered = bins.filter(pl.col("underpowered_n_lt_30")).height
    return f"{underpowered}/{bins.height} FOEHN score-bin cells have n < 30."


def _audit_warning(audit: pl.DataFrame) -> str:
    if audit.height == 0 or "fixed_60_nw_sector_not_foehn_share" not in audit.columns:
        return "Fixed-60 false-positive audit could not be estimated."
    max_nw_share = audit["fixed_60_nw_sector_not_foehn_share"].max()
    max_regime_share = audit["fixed_60_non_foehn_regime_share"].max()
    if max_nw_share is None or max_regime_share is None:
        return "Fixed-60 false-positive audit had no triggered rows to estimate shares."
    return (
        f"Max fixed-60 NW-sector-not-foehn share is {max_nw_share:.3f}; "
        f"max non-foehn-regime share is {max_regime_share:.3f}."
    )


def build_foehn_decision_updates(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build ADR-012 decision updates from FOEHN-domain EDA."""
    bins = artifacts["foehn_score_bins_by_month_cp"]
    audit = artifacts["foehn_false_positive_audit"]
    warning = _power_warning(bins)
    audit_text = _audit_warning(audit)
    rows = [
        {
            "decision_id": "DEC-WCT-FOEHN-001",
            "item_id": "WCT-FOEHN-001",
            "item_type": "thesis",
            "domain": "FOEHN",
            "decision_status": "PROMOTED_TO_REGIME_DESIGN",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
            "strata": "month x CP x foehn_score_bin",
            "sample_size_warning": warning,
            "causal_availability": "Foehn score and dewpoint diagnostics are feature-side inputs; Tmax effects are labels used only for EDA.",
            "leakage_risk": "Outcome effects must not be used to assign live FOEHN regimes or calibrate outside the training window.",
            "decision_rationale": "FOEHN score bins now expose month/CP effect patterns and a fixed-threshold audit for regime-design review.",
            "next_allowed_action": "Design a regime-repair candidate using month/CP calibration or continuous FOEHN score; no feature candidate is promoted.",
        },
        {
            "decision_id": "DEC-RULE_FOEHN_SCORE_FIXED_60",
            "item_id": "RULE_FOEHN_SCORE_FIXED_60",
            "item_type": "rule",
            "domain": "FOEHN",
            "decision_status": "ADAPTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/foehn_false_positive_audit.csv",
            "strata": "month x CP",
            "sample_size_warning": warning,
            "causal_availability": "foehn_score > 60 is allowed only as a diagnostic comparator while calibration is redesigned.",
            "leakage_risk": "Treating the fixed cutoff as production truth would preserve an uncalibrated heuristic.",
            "decision_rationale": (
                "Replace the fixed 60 score threshold with month/CP-calibrated bins or a continuous-score design. "
                f"{audit_text}"
            ),
            "next_allowed_action": "Keep RULE_FOEHN_SCORE_FIXED_60 quarantined as an audit threshold until Onda 4 validates a reviewed regime repair.",
        },
    ]
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def write_foehn_domain_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write FOEHN-domain CSV artifacts and markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "foehn_score_bins_by_month_cp": "domain_foehn_score_bins_by_month_cp.csv",
        "foehn_false_positive_audit": "foehn_false_positive_audit.csv",
        "foehn_power_leakage_audit": "foehn_power_leakage_audit.csv",
        "foehn_regime_repair_candidates": "foehn_regime_repair_candidates.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        _write_csv(artifacts[key], path)
        paths[f"{key}_csv"] = path

    bins = artifacts["foehn_score_bins_by_month_cp"]
    audit = artifacts["foehn_false_positive_audit"]
    underpowered = bins.filter(pl.col("underpowered_n_lt_30")).height
    report_path = out_dir / "foehn_domain_report.md"
    report_path.write_text(
        "\n".join(
            [
                f"# Onda 2E FOEHN Domain EDA - {report_date.isoformat()}",
                "",
                "No production classifier change is made by this report.",
                "`RULE_FOEHN_SCORE_FIXED_60` is adapted as an audit comparator, not production truth.",
                "",
                "## Artifacts",
                "",
                "| Artifact | Rows |",
                "|---|---:|",
                f"| `domain_foehn_score_bins_by_month_cp.csv` | {bins.height} |",
                f"| `foehn_false_positive_audit.csv` | {audit.height} |",
                f"| `foehn_power_leakage_audit.csv` | {artifacts['foehn_power_leakage_audit'].height} |",
                f"| `foehn_regime_repair_candidates.csv` | {artifacts['foehn_regime_repair_candidates'].height} |",
                "",
                "## Power",
                "",
                f"- Underpowered FOEHN score-bin cells (`n < 30`): {underpowered}/{bins.height}.",
                "",
                "## Decision Implication",
                "",
                "- `WCT-FOEHN-001`: PROMOTED_TO_REGIME_DESIGN for calibration review.",
                "- `RULE_FOEHN_SCORE_FIXED_60`: ADAPTED, not retained as production truth.",
                "- No feature candidate is promoted by this report.",
            ]
        ),
        encoding="utf-8",
    )
    paths["foehn_report_md"] = report_path
    return paths
