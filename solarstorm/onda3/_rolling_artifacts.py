from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

ONDA3_ROLLING_FILENAMES = {
    "onda3_rolling_feature_manifest_v1": "onda3_rolling_feature_manifest_v1.csv",
    "onda3_rolling_model_results_v1": "onda3_rolling_model_results_v1.csv",
    "onda3_rolling_predictions_v1": "onda3_rolling_predictions_v1.csv",
    "onda3_rolling_slice_diagnostics_v1": "onda3_rolling_slice_diagnostics_v1.csv",
    "onda3_rolling_uncertainty_abstention_v1": (
        "onda3_rolling_uncertainty_abstention_v1.csv"
    ),
    "onda3_rolling_temporal_diagnostics_v1": "onda3_rolling_temporal_diagnostics_v1.csv",
    "onda3_rolling_decision_update_v1": "onda3_rolling_decision_update_v1.csv",
}


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 30) -> str:
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


def write_onda3_rolling_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in ONDA3_ROLLING_FILENAMES.items():
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            f"# {artifact_name}\n\n{_markdown_table(artifacts[artifact_name])}\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name}_md"] = md_path

    report_path = output_dir / "onda3_rolling_model_report_v1.md"
    report = "\n\n".join(
        [
            "# Onda 3C Rolling Temporal Model Iteration Report",
            f"Generated: {today.isoformat()}",
            "## Decision",
            _markdown_table(artifacts["onda3_rolling_decision_update_v1"]),
            "## Temporal Diagnostics",
            _markdown_table(artifacts["onda3_rolling_temporal_diagnostics_v1"]),
            "## Model Results",
            _markdown_table(artifacts["onda3_rolling_model_results_v1"]),
            "## Uncertainty and Abstention",
            _markdown_table(artifacts["onda3_rolling_uncertainty_abstention_v1"]),
            "## Scope",
            "All outputs are EXPERIMENT_ONLY.",
        ]
    )
    report_path.write_text(report + "\n", encoding="utf-8")
    paths["onda3_rolling_report_md"] = report_path
    return paths
