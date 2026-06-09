"""Onda 2E timing-domain EDA artifacts."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda2e._atlas import _join_feature_labels, _quantile_expr
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA


def _with_month(df: pl.DataFrame) -> pl.DataFrame:
    if "month" in df.columns:
        return df
    return df.with_columns(pl.col("date_local").dt.month().alias("month"))


def _timing_context(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    joined = _join_feature_labels(features, labels)
    if "tmax_hour" not in joined.columns and "tmax_hour_local" in joined.columns:
        joined = joined.with_columns(pl.col("tmax_hour_local").alias("tmax_hour"))
    return _with_month(joined).select(
        ["date_local", "month", "regime_label", "cp", "tmax_int", "tmax_hour"]
    )


def build_timing_domain_artifacts(
    features: pl.DataFrame,
    labels: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Build timing-domain EDA tables for WCT-TIMING-001.

    These tables use full-day Tmax timing as evaluation evidence and as a
    future train-only prior. They are not causal CP features.
    """
    context = _timing_context(features, labels)
    by_day = context.unique(["date_local", "month", "regime_label", "tmax_int", "tmax_hour"])
    norms = (
        by_day.group_by(["month", "regime_label"])
        .agg(
            pl.len().alias("n_context_days"),
            _quantile_expr("tmax_hour", 0.10, "p10_tmax_hour"),
            _quantile_expr("tmax_hour", 0.25, "p25_tmax_hour"),
            _quantile_expr("tmax_hour", 0.50, "p50_tmax_hour"),
            _quantile_expr("tmax_hour", 0.75, "p75_tmax_hour"),
            _quantile_expr("tmax_hour", 0.90, "p90_tmax_hour"),
            pl.mean("tmax_hour").alias("mean_tmax_hour"),
        )
        .with_columns((pl.col("n_context_days") < 30).alias("underpowered_n_lt_30"))
        .sort(["month", "regime_label"])
    )
    context_with_norms = context.join(
        norms.select(["month", "regime_label", "p90_tmax_hour"]),
        on=["month", "regime_label"],
        how="left",
    ).with_columns(
        (pl.col("tmax_hour") >= 18).alias("fixed_18_late"),
        (pl.col("tmax_hour") > pl.col("p90_tmax_hour")).alias("q90_late"),
    )
    sensitivity = (
        context_with_norms.group_by(["month", "regime_label", "cp"])
        .agg(
            pl.len().alias("n_rows"),
            pl.mean("fixed_18_late").alias("fixed_18_late_rate"),
            pl.mean("q90_late").alias("q90_late_rate"),
            ((pl.col("fixed_18_late") != pl.col("q90_late")).cast(pl.Float64))
            .mean()
            .alias("late_rule_disagree_rate"),
        )
        .with_columns((pl.col("n_rows") < 30).alias("underpowered_n_lt_30"))
        .sort(["month", "regime_label", "cp"])
    )
    bucket_priors = (
        context.with_columns(
            pl.when(pl.col("tmax_hour") < 13)
            .then(pl.lit("before_13"))
            .when(pl.col("tmax_hour") <= 17)
            .then(pl.lit("between_13_17"))
            .otherwise(pl.lit("after_17"))
            .alias("tmax_hour_bucket")
        )
        .group_by(["month", "regime_label", "cp", "tmax_hour_bucket"])
        .agg(pl.len().alias("n_rows"))
        .join(
            context.group_by(["month", "regime_label", "cp"]).len(name="total_rows"),
            on=["month", "regime_label", "cp"],
        )
        .with_columns(
            (pl.col("n_rows") / pl.col("total_rows")).alias("bucket_share"),
            (pl.col("total_rows") < 30).alias("underpowered_n_lt_30"),
        )
        .sort(["month", "regime_label", "cp", "tmax_hour_bucket"])
    )
    return {
        "timing_norms_by_month_regime": norms,
        "timing_fixed_18_sensitivity": sensitivity,
        "timing_bucket_priors": bucket_priors,
    }


def _power_warning(norms: pl.DataFrame) -> str:
    underpowered = norms.filter(pl.col("underpowered_n_lt_30")).height
    return f"{underpowered}/{norms.height} month x regime timing cells have n < 30."


def build_timing_decision_updates(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build ADR-012 decision updates from timing-domain EDA."""
    norms = artifacts["timing_norms_by_month_regime"]
    sensitivity = artifacts["timing_fixed_18_sensitivity"]
    max_disagree = (
        sensitivity["late_rule_disagree_rate"].max()
        if sensitivity.height and "late_rule_disagree_rate" in sensitivity.columns
        else None
    )
    disagree_text = (
        f"Max fixed-vs-q90 disagreement rate across month/regime/CP cells is {max_disagree:.3f}."
        if max_disagree is not None
        else "Fixed-vs-q90 disagreement could not be estimated."
    )
    rows = [
        {
            "decision_id": "DEC-WCT-TIMING-001",
            "item_id": "WCT-TIMING-001",
            "item_type": "thesis",
            "domain": "TIMING",
            "decision_status": "SUPPORTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/domain_timing_norms_by_month_regime.csv",
            "strata": "month x regime_label",
            "sample_size_warning": _power_warning(norms),
            "causal_availability": "Full-day tmax_hour is an evaluation target; q90 timing norms may be used only as train-only priors.",
            "leakage_risk": "High if computed from holdout/live labels or used as a direct CP feature.",
            "decision_rationale": "The mandatory month x regime q90 tmax_hour table now exists and is power-flagged.",
            "next_allowed_action": "Allow TIMING/SPIKE EDA to reference this table as a prerequisite; no model feature is promoted.",
        },
        {
            "decision_id": "DEC-RULE_LATE_WARMING_FIXED_18",
            "item_id": "RULE_LATE_WARMING_FIXED_18",
            "item_type": "rule",
            "domain": "TIMING",
            "decision_status": "ADAPTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/domain_timing_fixed_18_sensitivity.csv",
            "strata": "month x regime_label x CP",
            "sample_size_warning": _power_warning(norms),
            "causal_availability": "Fixed 18:00 is not causal evidence; replace with train-only month/regime q90 prior for evaluation.",
            "leakage_risk": "High if q90 thresholds are computed outside the training window.",
            "decision_rationale": f"Static 18:00 late-Tmax logic is superseded by month/regime-relative q90 timing norms. {disagree_text}",
            "next_allowed_action": "Use q90_train(tmax_hour | month, regime) as the only admissible late-Tmax prior design.",
        },
    ]
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def write_timing_domain_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write timing-domain CSV artifacts and markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    paths: dict[str, Path] = {}
    filenames = {
        "timing_norms_by_month_regime": "domain_timing_norms_by_month_regime.csv",
        "timing_fixed_18_sensitivity": "domain_timing_fixed_18_sensitivity.csv",
        "timing_bucket_priors": "domain_timing_bucket_priors.csv",
    }
    for key, filename in filenames.items():
        path = out_dir / filename
        _write_csv(artifacts[key], path)
        paths[f"{key}_csv"] = path

    norms = artifacts["timing_norms_by_month_regime"]
    underpowered = norms.filter(pl.col("underpowered_n_lt_30")).height
    report_path = out_dir / "onda2e_timing_report.md"
    report_path.write_text(
        "\n".join(
            [
                f"# Onda 2E Timing Domain EDA - {report_date.isoformat()}",
                "",
                "This report resolves WCT-TIMING-001 as an evaluation target timing prior.",
                "`tmax_hour` is a full-day outcome and must never be used as direct CP evidence.",
                "Any late-Tmax prior derived from this table must be computed train-only.",
                "",
                "## Artifacts",
                "",
                "| Artifact | Rows |",
                "|---|---:|",
                f"| `domain_timing_norms_by_month_regime.csv` | {norms.height} |",
                f"| `domain_timing_fixed_18_sensitivity.csv` | {artifacts['timing_fixed_18_sensitivity'].height} |",
                f"| `domain_timing_bucket_priors.csv` | {artifacts['timing_bucket_priors'].height} |",
                "",
                "## Power",
                "",
                f"- Underpowered month x regime cells (`n < 30`): {underpowered}/{norms.height}.",
                "",
                "## Decision Implication",
                "",
                "- `WCT-TIMING-001`: SUPPORTED as prerequisite evidence.",
                "- `RULE_LATE_WARMING_FIXED_18`: ADAPTED to month/regime-relative q90 timing norms.",
                "- No feature candidate is promoted by this report.",
            ]
        ),
        encoding="utf-8",
    )
    paths["timing_report_md"] = report_path
    return paths
