"""CSV/Markdown artifact writer for the honest evaluation harness."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda3._pooled_iteration import _markdown_table

HONEST_FILENAMES = {
    "honest_eval_null_table_v1": "honest_eval_null_table_v1.csv",
    "honest_eval_by_cp_v1": "honest_eval_by_cp_v1.csv",
    "honest_eval_by_stratum_cp_v1": "honest_eval_by_stratum_cp_v1.csv",
    "honest_eval_floor_audit_v1": "honest_eval_floor_audit_v1.csv",
    "honest_eval_ablation_v1": "honest_eval_ablation_v1.csv",
    "honest_eval_gates_v1": "honest_eval_gates_v1.csv",
    "honest_eval_decision_v1": "honest_eval_decision_v1.csv",
}
FREEZE_LINE = (
    "No production, EV, pricing, shadow trading, or execution work is unlocked."
)


def render_honest_eval_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    """Render the top-level P0 honest evaluation report."""

    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Honest Evaluation Report (P0)",
            f"Generated: {today.isoformat()}",
            "All outputs remain EXPERIMENT_ONLY.",
            FREEZE_LINE,
            "## Decision",
            _markdown_table(frame("honest_eval_decision_v1")),
            "## Gates H1-H4",
            _markdown_table(frame("honest_eval_gates_v1")),
            "## Model vs Honest Null by CP",
            _markdown_table(frame("honest_eval_by_cp_v1")),
            "## Model vs Honest Null by Stratum x CP",
            _markdown_table(frame("honest_eval_by_stratum_cp_v1"), max_rows=40),
            "## Physical Floor Audit",
            _markdown_table(frame("honest_eval_floor_audit_v1")),
            "## Persistence Ablation",
            _markdown_table(frame("honest_eval_ablation_v1")),
            "## Honest Null Table (train-only)",
            _markdown_table(frame("honest_eval_null_table_v1"), max_rows=60),
        ]
    ) + "\n"


def write_honest_eval_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    """Write honest evaluation CSV/MD pairs plus the report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in HONEST_FILENAMES.items():
        if artifact_name not in artifacts:
            continue
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            f"# {artifact_name}\n\n{_markdown_table(artifacts[artifact_name])}\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name}_md"] = md_path
    report_path = output_dir / "honest_evaluation_report_v1.md"
    report_path.write_text(
        render_honest_eval_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["honest_eval_report_md"] = report_path
    return paths
