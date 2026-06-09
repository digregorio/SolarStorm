"""Onda 2E wind-domain EDA artifacts."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.onda2e._atlas import (
    _feature_row_slice,
    _join_feature_labels,
    _obs_by_local_date,
    _wind_sector,
)
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA

EFFECTS_SCHEMA: dict[str, pl.DataType] = {
    "month": pl.Int8,
    "cp": pl.Utf8,
    "wind_sector": pl.Utf8,
    "n_obs": pl.Int64,
    "n_days": pl.Int64,
    "mean_tmax_anomaly": pl.Float64,
    "mean_remaining_warming": pl.Float64,
    "mean_sknt": pl.Float64,
    "underpowered_n_lt_30": pl.Boolean,
}

RELIABILITY_SCHEMA: dict[str, pl.DataType] = {
    "date_local": pl.Date,
    "month": pl.Int8,
    "cp": pl.Utf8,
    "n_pre_cp_obs": pl.Int64,
    "n_sectors_observed": pl.Int64,
    "dominant_sector": pl.Utf8,
    "dominant_share": pl.Float64,
    "southerly_obs_count": pl.Int64,
    "direction_churn_flag": pl.Boolean,
}

AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

CANDIDATE_SCHEMA: dict[str, pl.DataType] = {
    "candidate_id": pl.Utf8,
    "source_rule_id": pl.Utf8,
    "candidate_action": pl.Utf8,
    "evidence_artifact": pl.Utf8,
    "rationale": pl.Utf8,
    "next_action": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _with_month(df: pl.DataFrame) -> pl.DataFrame:
    if "month" in df.columns:
        return df
    return df.with_columns(pl.col("date_local").dt.month().alias("month"))


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _remaining_warming(row: dict[str, object]) -> float | None:
    cp_code = str(row["cp"]).replace(":", "")
    k_col = f"k_cp__cp_{cp_code}"
    k_value = _safe_float(row.get(k_col))
    tmax = _safe_float(row.get("tmax_int"))
    return tmax - k_value if tmax is not None and k_value is not None else None


def _tmax_anomaly(row: dict[str, object]) -> float | None:
    tmax = _safe_float(row.get("tmax_int"))
    month_mean = _safe_float(row.get("month_mean_tmax"))
    return tmax - month_mean if tmax is not None and month_mean is not None else None


def _month_means(labels: pl.DataFrame) -> pl.DataFrame:
    labels_m = _with_month(labels)
    return labels_m.group_by("month").agg(pl.mean("tmax_int").alias("month_mean_tmax"))


def _obs_value(obs_row: dict[str, object], *names: str) -> object:
    for name in names:
        if name in obs_row:
            return obs_row[name]
    return None


def _is_southerly_sector(sector: str) -> bool:
    return sector in {"S", "SE", "SW"}


def _dominant_sector(sector_counts: dict[str, int]) -> tuple[str | None, float]:
    n_obs = sum(sector_counts.values())
    if n_obs == 0:
        return None, 0.0
    sector, count = sorted(sector_counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return sector, count / n_obs


def _context(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    joined = _join_feature_labels(features, labels)
    return _with_month(joined).join(_month_means(labels), on="month", how="left")


def build_wind_domain_artifacts(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Build wind-domain EDA tables from pre-CP observations only."""
    if features.height == 0 or labels.height == 0 or obs.height == 0:
        effects = _empty_frame(EFFECTS_SCHEMA)
        reliability = _empty_frame(RELIABILITY_SCHEMA)
        return {
            "wind_sector_effects_by_month_cp": effects,
            "wind_direction_reliability_by_day_cp": reliability,
            "wind_power_leakage_audit": _leakage_audit(effects),
            "wind_regime_repair_candidates": _regime_repair_candidates(effects, reliability),
        }

    joined = _context(features, labels)
    obs_by_date = _obs_by_local_date(obs, tz_name)
    wind_rows: list[dict[str, object]] = []
    reliability_rows: list[dict[str, object]] = []

    for row in joined.iter_rows(named=True):
        slice_df = _feature_row_slice(row, obs_by_date, tz_name)
        month = int(row["month"])
        date_local = row["date_local"]
        cp = str(row["cp"])
        sector_counts: dict[str, int] = {}
        n_pre_cp_obs = 0
        southerly_obs_count = 0

        if slice_df is not None and slice_df.height > 0:
            n_pre_cp_obs = slice_df.height
            rw = _remaining_warming(row)
            anomaly = _tmax_anomaly(row)
            for obs_row in slice_df.iter_rows(named=True):
                sector = _wind_sector(_obs_value(obs_row, "drct", "wind_dir_deg"))
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
                if _is_southerly_sector(sector):
                    southerly_obs_count += 1
                wind_rows.append(
                    {
                        "date_local": date_local,
                        "month": month,
                        "cp": cp,
                        "wind_sector": sector,
                        "tmax_anomaly": anomaly,
                        "remaining_warming": rw,
                        "sknt": _safe_float(obs_row.get("sknt")),
                    }
                )

        dominant_sector, dominant_share = _dominant_sector(sector_counts)
        known_sectors = {sector for sector in sector_counts if sector != "unknown"}
        reliability_rows.append(
            {
                "date_local": date_local,
                "month": month,
                "cp": cp,
                "n_pre_cp_obs": n_pre_cp_obs,
                "n_sectors_observed": len(known_sectors),
                "dominant_sector": dominant_sector,
                "dominant_share": dominant_share,
                "southerly_obs_count": southerly_obs_count,
                "direction_churn_flag": len(known_sectors) > 1,
            }
        )

    effects = _sector_effects(wind_rows)
    reliability = (
        pl.DataFrame(reliability_rows, schema=RELIABILITY_SCHEMA, strict=False)
        if reliability_rows
        else _empty_frame(RELIABILITY_SCHEMA)
    )
    return {
        "wind_sector_effects_by_month_cp": effects,
        "wind_direction_reliability_by_day_cp": reliability.sort(["date_local", "cp"]),
        "wind_power_leakage_audit": _leakage_audit(effects),
        "wind_regime_repair_candidates": _regime_repair_candidates(effects, reliability),
    }


def _sector_effects(rows: list[dict[str, object]]) -> pl.DataFrame:
    if not rows:
        return _empty_frame(EFFECTS_SCHEMA)

    wind = pl.DataFrame(rows, strict=False)
    return (
        wind.group_by(["month", "cp", "wind_sector"])
        .agg(
            pl.len().alias("n_obs"),
            pl.col("date_local").n_unique().alias("n_days"),
            pl.mean("tmax_anomaly").alias("mean_tmax_anomaly"),
            pl.mean("remaining_warming").alias("mean_remaining_warming"),
            pl.mean("sknt").alias("mean_sknt"),
        )
        .with_columns((pl.col("n_obs") < 30).alias("underpowered_n_lt_30"))
        .select(list(EFFECTS_SCHEMA))
        .sort(["month", "cp", "wind_sector"])
    )


def _leakage_audit(effects: pl.DataFrame) -> pl.DataFrame:
    underpowered = (
        effects.filter(pl.col("underpowered_n_lt_30")).height
        if effects.height and "underpowered_n_lt_30" in effects.columns
        else 0
    )
    power_status = "WARN" if effects.height == 0 or underpowered else "PASS"
    power_detail = (
        "No wind sector effect cells were available."
        if effects.height == 0
        else f"{underpowered}/{effects.height} wind sector effect cells have n_obs < 30."
    )
    rows = [
        {
            "audit_item": "cp_slice_causal",
            "status": "PASS",
            "detail": "Wind sectors are computed only from observations with valid < CP.",
        },
        {
            "audit_item": "outcome_usage",
            "status": "WARN",
            "detail": "tmax_int, tmax_anomaly, and remaining_warming are outcome summaries used only after sector assignment.",
        },
        {
            "audit_item": "power",
            "status": power_status,
            "detail": power_detail,
        },
    ]
    return pl.DataFrame(rows, schema=AUDIT_SCHEMA)


def _regime_repair_candidates(effects: pl.DataFrame, reliability: pl.DataFrame) -> pl.DataFrame:
    sector_count = effects["wind_sector"].n_unique() if effects.height else 0
    southerly_rows = (
        reliability.filter(pl.col("southerly_obs_count") > 0).height
        if reliability.height and "southerly_obs_count" in reliability.columns
        else 0
    )
    rows = [
        {
            "candidate_id": "WRR-001",
            "source_rule_id": "REGIME_CLASSIFIER_CURRENT",
            "candidate_action": "review_wind_sector_split_for_regime_design",
            "evidence_artifact": "reports/onda2e/wind_sector_effects_by_month_cp.csv; reports/onda2e/wind_direction_reliability_by_day_cp.csv",
            "rationale": f"Pre-CP wind evidence spans {sector_count} sectors; {southerly_rows}/{reliability.height} day/CP rows have southerly-sector observations.",
            "next_action": "Review wind-sector and southerly-count splits before changing the production regime classifier.",
        }
    ]
    return pl.DataFrame(rows, schema=CANDIDATE_SCHEMA)


def _power_warning(effects: pl.DataFrame) -> str:
    underpowered = effects.filter(pl.col("underpowered_n_lt_30")).height if effects.height else 0
    return f"{underpowered}/{effects.height} wind sector effect cells have n_obs < 30."


def build_wind_decision_updates(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build ADR-012 decision updates from wind-domain EDA."""
    effects = artifacts["wind_sector_effects_by_month_cp"]
    reliability = artifacts["wind_direction_reliability_by_day_cp"]
    warning = _power_warning(effects)
    max_southerly = (
        int(reliability["southerly_obs_count"].max() or 0)
        if reliability.height and "southerly_obs_count" in reliability.columns
        else 0
    )
    southerly_status = (
        "PROMOTED_TO_REGIME_DESIGN" if max_southerly > 0 else "SUPPORTED"
    )
    rows = [
        {
            "decision_id": "DEC-WCT-WIND-006",
            "item_id": "WCT-WIND-006",
            "item_type": "thesis",
            "domain": "WIND",
            "decision_status": "SUPPORTED",
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/wind_sector_effects_by_month_cp.csv",
            "strata": "month x CP x wind_sector",
            "sample_size_warning": warning,
            "causal_availability": "Wind sectors are assigned from pre-CP observations only.",
            "leakage_risk": "Tmax anomaly and remaining warming appear only in descriptive effect summaries.",
            "decision_rationale": "The mandatory artifact-backed wind-sector table now exists by month and CP.",
            "next_allowed_action": "Use as prerequisite wind evidence for regime design review; no feature candidate is promoted.",
        },
        {
            "decision_id": "DEC-WCT-WIND-019",
            "item_id": "WCT-WIND-019",
            "item_type": "thesis",
            "domain": "WIND",
            "decision_status": southerly_status,
            "evidence_level": "E2_descriptive_domain",
            "source_artifact": "reports/onda2e/wind_direction_reliability_by_day_cp.csv",
            "strata": "date x CP with month/sector context",
            "sample_size_warning": warning,
            "causal_availability": "Southerly observation count is computed from valid < CP observations.",
            "leakage_risk": "Remaining warming can evaluate the split but must not assign a live regime.",
            "decision_rationale": f"Pre-CP southerly-sector counts are artifact-backed; max southerly count by day/CP is {max_southerly}.",
            "next_allowed_action": "Evaluate southerly-count/depth as a regime-design split, not as a promoted model feature.",
        },
    ]
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def _write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def write_wind_domain_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write wind-domain CSV artifacts and a compact markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "wind_sector_effects_by_month_cp": "wind_sector_effects_by_month_cp.csv",
        "wind_direction_reliability_by_day_cp": "wind_direction_reliability_by_day_cp.csv",
        "wind_power_leakage_audit": "wind_power_leakage_audit.csv",
        "wind_regime_repair_candidates": "wind_regime_repair_candidates.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        _write_csv(artifacts[key], path)
        paths[f"{key}_csv"] = path

    effects = artifacts["wind_sector_effects_by_month_cp"]
    reliability = artifacts["wind_direction_reliability_by_day_cp"]
    underpowered = effects.filter(pl.col("underpowered_n_lt_30")).height if effects.height else 0
    report_path = out_dir / "wind_domain_report.md"
    report_path.write_text(
        "\n".join(
            [
                f"# Onda 2E Wind Domain EDA - {report_date.isoformat()}",
                "",
                "No production classifier change is made by this report.",
                "No feature candidate is promoted by wind-domain EDA.",
                "",
                "## Artifacts",
                "",
                "| Artifact | Rows |",
                "|---|---:|",
                f"| `wind_sector_effects_by_month_cp.csv` | {effects.height} |",
                f"| `wind_direction_reliability_by_day_cp.csv` | {reliability.height} |",
                f"| `wind_power_leakage_audit.csv` | {artifacts['wind_power_leakage_audit'].height} |",
                f"| `wind_regime_repair_candidates.csv` | {artifacts['wind_regime_repair_candidates'].height} |",
                "",
                "## Power",
                "",
                f"- Underpowered wind-sector cells (`n_obs < 30`): {underpowered}/{effects.height}.",
                "",
                "## Decision Implication",
                "",
                "- `WCT-WIND-006`: SUPPORTED as descriptive wind-sector evidence.",
                "- `WCT-WIND-019`: eligible only for regime-design review when southerly counts are present.",
            ]
        ),
        encoding="utf-8",
    )
    paths["wind_report_md"] = report_path
    return paths
