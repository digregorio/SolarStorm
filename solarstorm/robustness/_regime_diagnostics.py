"""Regime trigger diagnostics for Onda 2R follow-up."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc
from solarstorm.features.builder import _annotate_obs


def _empty_audit() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.Utf8,
            "regime_label": pl.Utf8,
            "n_obs": pl.Int64,
            "primary_trigger": pl.Utf8,
            "precip_sum": pl.Float64,
            "precip_trigger": pl.Boolean,
            "cooling_trigger": pl.Boolean,
            "southerly_trigger": pl.Boolean,
            "foehn_trigger": pl.Boolean,
            "standard_nw_trigger": pl.Boolean,
            "min_delta_t_per_h": pl.Float64,
            "max_delta_t_per_h": pl.Float64,
            "nw_share": pl.Float64,
            "southerly_share": pl.Float64,
            "southerly_speed": pl.Float64,
            "foehn_score": pl.Float64,
        }
    )


def _primary_trigger(
    *,
    precip_trigger: bool,
    cooling_trigger: bool,
    southerly_trigger: bool,
    foehn_trigger: bool,
    standard_nw_trigger: bool,
    regime_label: str,
) -> str:
    if precip_trigger:
        return "precip"
    if cooling_trigger:
        return "cooling"
    if southerly_trigger:
        return "southerly"
    if foehn_trigger:
        return "foehn"
    if standard_nw_trigger:
        return "standard_nw"
    if regime_label == "calm_radiative":
        return "residual_calm"
    if regime_label == "insufficient":
        return "insufficient"
    return "untriggered"


def _diagnose_slice(slice_df: pl.DataFrame, regime_label: str) -> dict:
    if slice_df.height < 3:
        return {
            "n_obs": int(slice_df.height),
            "primary_trigger": "insufficient",
            "precip_sum": 0.0,
            "precip_trigger": False,
            "cooling_trigger": False,
            "southerly_trigger": False,
            "foehn_trigger": False,
            "standard_nw_trigger": False,
            "min_delta_t_per_h": 0.0,
            "max_delta_t_per_h": 0.0,
            "nw_share": 0.0,
            "southerly_share": 0.0,
            "southerly_speed": 0.0,
            "foehn_score": 0.0,
        }

    obs = slice_df.sort("ts_local").with_columns(
        (
            pl.col("tmp_c_int").diff().cast(pl.Float64)
            / pl.col("ts_local").diff().dt.total_hours().cast(pl.Float64)
        ).alias("delta_t_per_h")
    )

    precip_sum = float(obs["p01i"].sum() or 0.0)
    min_delta = float(obs["delta_t_per_h"].min() or 0.0)
    max_delta = float(obs["delta_t_per_h"].max() or 0.0)
    dwp_depression = (obs["tmp_c_int"] - obs["dwp_c_int"]).mean()
    mean_dir = obs["wind_dir_deg"].mean()

    in_nw = obs.filter(
        (pl.col("wind_dir_deg") >= 270) | (pl.col("wind_dir_deg") <= 45)
    )
    nw_flow_strength = float(in_nw["sknt"].mean() or 0.0) if in_nw.height else 0.0
    nw_share = float(in_nw.height / obs.height) if obs.height else 0.0

    in_southerly = obs.filter(
        (pl.col("wind_dir_deg") >= 135) & (pl.col("wind_dir_deg") <= 225)
    )
    southerly_share = float(in_southerly.height / obs.height) if obs.height else 0.0
    southerly_speed = (
        float(in_southerly["sknt"].mean() or 0.0) if in_southerly.height else 0.0
    )
    foehn_score = nw_flow_strength * (
        float(dwp_depression) if dwp_depression is not None else 0.0
    )

    precip_trigger = precip_sum > 0.01
    cooling_trigger = min_delta < -2.0
    southerly_trigger = southerly_share >= 0.5 and southerly_speed >= 12.0
    foehn_trigger = foehn_score > 60.0
    standard_nw_trigger = nw_share >= 0.4 or (
        mean_dir is not None and (mean_dir >= 270 or mean_dir <= 45)
    )

    return {
        "n_obs": int(obs.height),
        "primary_trigger": _primary_trigger(
            precip_trigger=precip_trigger,
            cooling_trigger=cooling_trigger,
            southerly_trigger=southerly_trigger,
            foehn_trigger=foehn_trigger,
            standard_nw_trigger=standard_nw_trigger,
            regime_label=regime_label,
        ),
        "precip_sum": precip_sum,
        "precip_trigger": precip_trigger,
        "cooling_trigger": cooling_trigger,
        "southerly_trigger": southerly_trigger,
        "foehn_trigger": foehn_trigger,
        "standard_nw_trigger": standard_nw_trigger,
        "min_delta_t_per_h": min_delta,
        "max_delta_t_per_h": max_delta,
        "nw_share": nw_share,
        "southerly_share": southerly_share,
        "southerly_speed": southerly_speed,
        "foehn_score": float(foehn_score),
    }


def regime_trigger_audit(
    obs: pl.DataFrame,
    features: pl.DataFrame,
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    tz_name: str = TZ_NAME,
) -> pl.DataFrame:
    """Reconstruct regime trigger evidence for each feature row."""
    if features.height == 0 or "regime_label" not in features.columns:
        return _empty_audit()

    annotated = (
        _annotate_obs(obs)
        .filter(pl.col("dq_tmp_c_int") != "missing")
        .sort(["date_local", "valid"])
    )
    obs_by_date: dict[dt.date, pl.DataFrame] = {}
    for key, day_df in annotated.partition_by(
        "date_local",
        as_dict=True,
        maintain_order=True,
    ).items():
        date_key = key[0] if isinstance(key, tuple) else key
        obs_by_date[date_key] = day_df

    rows: list[dict] = []
    for feature_row in features.select(["date_local", "cp", "regime_label"]).iter_rows(named=True):
        cp = str(feature_row["cp"])
        if cp not in cp_set:
            continue
        date_local = feature_row["date_local"]
        regime_label = str(feature_row.get("regime_label") or "unknown")
        cp_utc = cp_to_utc(date_local, cp, tz_name).astimezone(dt.UTC)
        day_df = obs_by_date.get(date_local)
        slice_df = (
            day_df.filter(pl.col("valid") < cp_utc)
            if day_df is not None
            else annotated.head(0)
        )
        rows.append(
            {
                "date_local": date_local,
                "cp": cp,
                "regime_label": regime_label,
                **_diagnose_slice(slice_df, regime_label),
            }
        )

    return pl.DataFrame(rows, strict=False) if rows else _empty_audit()


def summarize_regime_trigger_audit(audit: pl.DataFrame) -> pl.DataFrame:
    """Aggregate trigger counts by regime and primary trigger."""
    if audit.height == 0:
        return pl.DataFrame(
            schema={
                "regime_label": pl.Utf8,
                "primary_trigger": pl.Utf8,
                "n_rows": pl.Int64,
                "share": pl.Float64,
            }
        )
    counts = audit.group_by(["regime_label", "primary_trigger"]).len(name="n_rows")
    totals = audit.group_by("regime_label").len(name="total_rows")
    return (
        counts.join(totals, on="regime_label")
        .with_columns((pl.col("n_rows") / pl.col("total_rows")).alias("share"))
        .select(["regime_label", "primary_trigger", "n_rows", "share"])
        .sort(["regime_label", "n_rows"], descending=[False, True])
    )


def _candidate_regime(row: dict, *, allow_cooling: bool) -> str:
    if row["n_obs"] < 3:
        return "insufficient"
    if (
        row["precip_trigger"]
        or (allow_cooling and row["cooling_trigger"])
        or row["southerly_trigger"]
    ):
        return "southerly_disrupted"
    if row["foehn_trigger"]:
        return "strong_nw_foehn"
    if row["standard_nw_trigger"]:
        return "standard_nw"
    return "calm_radiative"


def cooling_rule_experiment(audit: pl.DataFrame) -> pl.DataFrame:
    """Simulate candidate cooling-trigger variants from audit evidence.

    This is an offline diagnostic. It does not change the production classifier.
    """
    if audit.height == 0:
        return pl.DataFrame(
            schema={
                "variant": pl.Utf8,
                "date_local": pl.Date,
                "cp": pl.Utf8,
                "current_regime": pl.Utf8,
                "candidate_regime": pl.Utf8,
            }
        )

    rows: list[dict] = []
    for row in audit.iter_rows(named=True):
        current = str(row["regime_label"])
        variants = {
            "current": current,
            "south_gated_cooling": _candidate_regime(
                row,
                allow_cooling=bool(row["southerly_trigger"]),
            ),
            "no_cooling_only_trigger": _candidate_regime(row, allow_cooling=False),
        }
        for variant, candidate in variants.items():
            rows.append(
                {
                    "variant": variant,
                    "date_local": row["date_local"],
                    "cp": row["cp"],
                    "current_regime": current,
                    "candidate_regime": candidate,
                }
            )
    return pl.DataFrame(rows, strict=False)


def summarize_cooling_rule_experiment(experiment: pl.DataFrame) -> pl.DataFrame:
    """Aggregate candidate-regime counts by experiment variant."""
    if experiment.height == 0:
        return pl.DataFrame(
            schema={
                "variant": pl.Utf8,
                "candidate_regime": pl.Utf8,
                "n_rows": pl.Int64,
                "share": pl.Float64,
            }
        )
    counts = experiment.group_by(["variant", "candidate_regime"]).len(name="n_rows")
    totals = experiment.group_by("variant").len(name="total_rows")
    return (
        counts.join(totals, on="variant")
        .with_columns((pl.col("n_rows") / pl.col("total_rows")).alias("share"))
        .select(["variant", "candidate_regime", "n_rows", "share"])
        .sort(["variant", "n_rows"], descending=[False, True])
    )


def write_regime_trigger_audit(
    audit: pl.DataFrame,
    summary: pl.DataFrame,
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> tuple[Path, Path]:
    """Write JSON and markdown diagnostic artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    json_path = out_dir / f"{report_date.isoformat()}-regime-trigger-audit.json"
    md_path = out_dir / f"{report_date.isoformat()}-regime-trigger-audit.md"

    records = []
    for row in audit.iter_rows(named=True):
        record = dict(row)
        value = record.get("date_local")
        if hasattr(value, "isoformat"):
            record["date_local"] = value.isoformat()
        records.append(record)
    json_path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        f"# Regime Trigger Audit - {report_date.isoformat()}",
        "",
        "Diagnostic artifact only. This does not change the regime classifier or R2 gates.",
        "",
        f"Rows audited: {audit.height}",
        "",
        "| Regime | Primary trigger | Rows | Share |",
        "|--------|-----------------|------|-------|",
    ]
    for row in summary.iter_rows(named=True):
        lines.append(
            f"| {row['regime_label']} | {row['primary_trigger']} | "
            f"{row['n_rows']} | {float(row['share']):.3f} |"
        )

    if audit.height:
        trigger_cols = [
            "precip_trigger",
            "cooling_trigger",
            "southerly_trigger",
            "foehn_trigger",
            "standard_nw_trigger",
        ]
        lines += ["", "## Trigger Totals", "", "| Trigger | Rows |", "|---------|------|"]
        for col in trigger_cols:
            lines.append(f"| {col} | {int(audit[col].sum())} |")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def write_cooling_rule_experiment(
    experiment: pl.DataFrame,
    summary: pl.DataFrame,
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> tuple[Path, Path]:
    """Write offline cooling-rule experiment artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    json_path = out_dir / f"{report_date.isoformat()}-cooling-rule-experiment.json"
    md_path = out_dir / f"{report_date.isoformat()}-cooling-rule-experiment.md"

    records = []
    for row in experiment.iter_rows(named=True):
        record = dict(row)
        value = record.get("date_local")
        if hasattr(value, "isoformat"):
            record["date_local"] = value.isoformat()
        records.append(record)
    json_path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        f"# Cooling Rule Experiment - {report_date.isoformat()}",
        "",
        "Offline diagnostic only. This does not change the production regime classifier, labels, or R2 gates.",
        "",
        "Variants:",
        "",
        "- `current`: current `regime_label` as stored in the feature artifact.",
        "- `south_gated_cooling`: cooling can support disruption only with southerly evidence.",
        "- `no_cooling_only_trigger`: cooling is ignored as a standalone disruption trigger.",
        "",
        f"Rows simulated: {experiment.height}",
        "",
        "| Variant | Candidate regime | Rows | Share |",
        "|---------|------------------|------|-------|",
    ]
    for row in summary.iter_rows(named=True):
        lines.append(
            f"| {row['variant']} | {row['candidate_regime']} | "
            f"{row['n_rows']} | {float(row['share']):.3f} |"
        )

    if experiment.height:
        current = experiment.filter(pl.col("variant") == "current").select(
            ["date_local", "cp", "candidate_regime"]
        )
        current = current.rename({"candidate_regime": "current_candidate_regime"})
        moves = (
            experiment.filter(pl.col("variant") != "current")
            .join(current, on=["date_local", "cp"])
            .filter(pl.col("candidate_regime") != pl.col("current_candidate_regime"))
            .group_by(["variant", "current_candidate_regime", "candidate_regime"])
            .len(name="n_rows")
            .sort(["variant", "n_rows"], descending=[False, True])
        )
        lines += [
            "",
            "## Reclassification Moves",
            "",
            "| Variant | From | To | Rows |",
            "|---------|------|----|------|",
        ]
        if moves.height:
            for row in moves.iter_rows(named=True):
                lines.append(
                    f"| {row['variant']} | {row['current_candidate_regime']} | "
                    f"{row['candidate_regime']} | {row['n_rows']} |"
                )
        else:
            lines.append("| none | none | none | 0 |")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
