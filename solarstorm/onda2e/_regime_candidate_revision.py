"""Regime-design candidate revision artifacts for Ontology v2."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

REQUIRED_CANDIDATE_V1_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "candidate_regime_family",
    "stratum_type",
    "stratum_value",
    "n_rows",
    "interpretability_score",
    "physical_signature",
    "wind_dir_deg_mean",
    "wind_speed_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum_mean",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp_mean",
    "dominant_current_regime",
    "production_status",
)

PHYSICAL_CENTROID_COLUMNS: tuple[str, ...] = (
    "wind_dir_deg_mean",
    "wind_speed_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum_mean",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp_mean",
)

REGIME_DESIGN_CANDIDATE_V2_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "candidate_id": pl.Utf8,
    "source_candidate_ids": pl.Utf8,
    "source_strategy": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "latent_component_id": pl.Utf8,
    "component_family_prior": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "n_source_rows": pl.Int64,
    "mean_interpretability_score": pl.Float64,
    "physical_signature": pl.Utf8,
    "wind_dir_deg_mean": pl.Float64,
    "wind_speed_mean": pl.Float64,
    "qnh_hpa_mean": pl.Float64,
    "relh_mean": pl.Float64,
    "dewpoint_depression_mean": pl.Float64,
    "precip_pre_cp_sum_mean": pl.Float64,
    "cloud_cover_score_mean": pl.Float64,
    "temp_slope_pre_cp_mean": pl.Float64,
    "dominant_current_regime": pl.Utf8,
    "design_rationale": pl.Utf8,
    "causal_inputs": pl.Utf8,
    "production_status": pl.Utf8,
    "next_gate_action": pl.Utf8,
}

CAUSAL_INPUTS = (
    "pre-CP physical centroids: wind direction, wind speed, pressure, humidity, "
    "dewpoint depression, precipitation, cloud cover, and pre-CP temperature slope"
)
NEXT_GATE_ACTION = (
    "Keep in regime-design review; run Onda 4 robustness and final physical "
    "interpretation before any production classifier change."
)


def _empty_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=REGIME_DESIGN_CANDIDATE_V2_SCHEMA)


def _validate_candidate_v1(candidate_v1: pl.DataFrame) -> None:
    missing = [
        column
        for column in REQUIRED_CANDIDATE_V1_COLUMNS
        if column not in candidate_v1.columns
    ]
    if missing:
        raise ValueError(f"candidate_v1 missing required columns: {', '.join(missing)}")

    invalid_status = candidate_v1.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid_status.height:
        ids = ", ".join(str(value) for value in invalid_status["candidate_id"].to_list())
        raise ValueError(
            "candidate_v1 production_status must be NOT_PRODUCTION for every row; "
            f"invalid candidate_id(s): {ids}"
        )


def _family_labels(family: object) -> tuple[str, str]:
    normalized = str(family)
    if normalized in {"mixed_or_transition", "mixed_or_transition_candidate"}:
        return "macro_light_marine_or_residual", "subtype_transition_low_confidence"
    if normalized == "maritime_cloudy_candidate":
        return "macro_light_marine_or_residual", "subtype_maritime_cloudy"
    if "nw" in normalized or "foehn" in normalized:
        return "macro_nw_continuum", f"subtype_{normalized.removesuffix('_candidate')}"
    if "southerly" in normalized or "cooling" in normalized:
        return "macro_southerly_flow", f"subtype_{normalized.removesuffix('_candidate')}"
    return "macro_light_marine_or_residual", f"subtype_{normalized.removesuffix('_candidate')}"


def _rationale(
    *,
    family: object,
    macro_regime_label: str,
    subtype_label: str,
) -> str:
    return (
        f"Recast v1 family {family} as {macro_regime_label} / {subtype_label}; "
        "dead or low-confidence families remain subtypes rather than promoted macros."
    )


def build_regime_design_candidate_v2(candidate_v1: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Build the Ontology v2 design-candidate table from v1 centroids."""
    _validate_candidate_v1(candidate_v1)
    if candidate_v1.height == 0:
        return {"regime_design_candidate_v2": _empty_frame()}

    rows: list[dict[str, object]] = []
    for row in candidate_v1.iter_rows(named=True):
        macro_regime_label, subtype_label = _family_labels(row["candidate_regime_family"])
        rows.append(
            {
                "candidate_version": "v2",
                "candidate_id": str(row["candidate_id"]),
                "source_candidate_ids": str(row["candidate_id"]),
                "source_strategy": "v1_centroid_revision",
                "macro_regime_label": macro_regime_label,
                "subtype_label": subtype_label,
                "latent_component_id": str(row["candidate_id"]),
                "component_family_prior": str(row["candidate_regime_family"]),
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "n_source_rows": int(row["n_rows"]),
                "mean_interpretability_score": float(row["interpretability_score"]),
                "physical_signature": str(row["physical_signature"]),
                **{column: float(row[column]) for column in PHYSICAL_CENTROID_COLUMNS},
                "dominant_current_regime": str(row["dominant_current_regime"]),
                "design_rationale": _rationale(
                    family=row["candidate_regime_family"],
                    macro_regime_label=macro_regime_label,
                    subtype_label=subtype_label,
                ),
                "causal_inputs": CAUSAL_INPUTS,
                "production_status": "NOT_PRODUCTION",
                "next_gate_action": NEXT_GATE_ACTION,
            }
        )
    return {
        "regime_design_candidate_v2": pl.DataFrame(
            rows,
            schema=REGIME_DESIGN_CANDIDATE_V2_SCHEMA,
            strict=False,
        )
    }


def _report_lines(candidate_v2: pl.DataFrame, report_date: dt.date) -> list[str]:
    lines = [
        f"# Regime Design Candidate v2 - {report_date.isoformat()}",
        "",
        "Every row is design evidence only and keeps `production_status = NOT_PRODUCTION`.",
        "",
        "## Summary",
        "",
        f"- Candidate rows: {candidate_v2.height}",
        "- Production status: NOT_PRODUCTION",
        "",
        "## Macro Counts",
        "",
        "| Macro regime | Rows |",
        "|---|---:|",
    ]
    counts = (
        candidate_v2.group_by("macro_regime_label").len(name="n").sort("macro_regime_label")
        if candidate_v2.height
        else pl.DataFrame({"macro_regime_label": [], "n": []})
    )
    for row in counts.iter_rows(named=True):
        lines.append(f"| `{row['macro_regime_label']}` | {row['n']} |")

    lines += [
        "",
        "## Candidate Rows",
        "",
        "| Candidate | Macro | Subtype | Source rows | Status |",
        "|---|---|---|---:|---|",
    ]
    for row in candidate_v2.iter_rows(named=True):
        lines.append(
            f"| `{row['candidate_id']}` | `{row['macro_regime_label']}` | "
            f"`{row['subtype_label']}` | {row['n_source_rows']} | "
            f"{row['production_status']} |"
        )
    lines += [
        "",
        "## Next Action",
        "",
        NEXT_GATE_ACTION,
    ]
    return lines


def write_regime_design_candidate_v2_artifacts(
    artifacts: dict[str, pl.DataFrame],
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write Regime Ontology v2 design-candidate CSV and markdown artifacts."""
    candidate_v2 = artifacts["regime_design_candidate_v2"]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()

    csv_path = out_dir / "regime_design_candidate_v2.csv"
    candidate_v2.write_csv(csv_path)
    report_path = out_dir / "regime_design_candidate_v2.md"
    report_path.write_text(
        "\n".join(_report_lines(candidate_v2, report_date)),
        encoding="utf-8",
    )
    return {
        "regime_design_candidate_v2_csv": csv_path,
        "regime_design_candidate_v2_md": report_path,
    }
