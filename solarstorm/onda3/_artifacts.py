from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

ARTIFACT_FILENAMES = {
    "onda3_feature_manifest_v1": "onda3_feature_manifest_v1.csv",
    "onda3_design_matrix_audit_v1": "onda3_design_matrix_audit_v1.csv",
    "onda3_baseline_results_v1": "onda3_baseline_results_v1.csv",
    "onda3_challenger_results_v1": "onda3_challenger_results_v1.csv",
    "onda3_slice_diagnostics_v1": "onda3_slice_diagnostics_v1.csv",
    "onda3_uncertainty_abstention_v1": "onda3_uncertainty_abstention_v1.csv",
    "onda3_decision_update_v1": "onda3_decision_update_v1.csv",
}


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 20) -> str:
    if df.is_empty():
        return "_No rows._"
    columns = df.columns
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row[column]) for column in columns) + " |"
        for row in df.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *body])


def write_onda3_baseline_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in ARTIFACT_FILENAMES.items():
        frame = artifacts[artifact_name]
        path = output_dir / filename
        frame.write_csv(path)
        paths[f"{artifact_name}_csv"] = path

    report_path = output_dir / "onda3_baseline_model_report_v1.md"
    report = "\n\n".join(
        [
            "# Onda 3 Baseline Model Report",
            f"Generated: {today.isoformat()}",
            "## Decision",
            _markdown_table(artifacts["onda3_decision_update_v1"]),
            "## Baseline Results",
            _markdown_table(artifacts["onda3_baseline_results_v1"]),
            "## Challenger Results",
            _markdown_table(artifacts["onda3_challenger_results_v1"]),
            "## Slice Diagnostics",
            _markdown_table(artifacts["onda3_slice_diagnostics_v1"]),
            "## Uncertainty and Abstention",
            _markdown_table(artifacts["onda3_uncertainty_abstention_v1"]),
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")
    paths["onda3_report_md"] = report_path
    paths["onda3_decision_update_csv"] = paths["onda3_decision_update_v1_csv"]
    return paths
