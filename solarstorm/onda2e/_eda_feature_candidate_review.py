"""Experiment-only bridge from Onda 2E EDA evidence to feature experiments."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

EDA_FEATURE_REVIEW_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "domain": pl.Utf8,
    "source_decision_id": pl.Utf8,
    "source_artifacts": pl.Utf8,
    "candidate_surface": pl.Utf8,
    "implementation_kind": pl.Utf8,
    "eda_feature_disposition": pl.Utf8,
    "runner_status": pl.Utf8,
    "feature_queue_status": pl.Utf8,
    "result_status": pl.Utf8,
    "production_status": pl.Utf8,
    "required_artifact": pl.Utf8,
    "recommended_experiment": pl.Utf8,
    "rationale": pl.Utf8,
}


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _feature_queue_ids(feature_candidate_queue: pl.DataFrame | None) -> set[str]:
    if feature_candidate_queue is None or feature_candidate_queue.height == 0:
        return set()
    for column in ("experiment_id", "source_experiment_id", "feature_id", "candidate_id"):
        if column in feature_candidate_queue.columns:
            return set(
                str(value)
                for value in feature_candidate_queue.get_column(column).drop_nulls().to_list()
            )
    return set()


def _disposition(row: dict[str, object]) -> str:
    family = str(row.get("experiment_family", "")).lower()
    surface = str(row.get("candidate_surface", "")).lower()
    kind = str(row.get("implementation_kind", "")).lower()
    if family == "feature" or surface == "feature_builder" or kind == "feature_probe":
        return "feature_ready_experiment"
    if family == "baseline":
        return "baseline_only"
    if family == "threshold":
        return "threshold_calibration_only"
    if family == "regime":
        return "regime_design_only"
    return "blocked_until_runner"


def _runner_status(disposition: str, result_status: str) -> str:
    if disposition != "feature_ready_experiment":
        return "not_feature_runner_scope"
    if result_status in {"passed", "failed", "blocked"}:
        return "runner_available"
    return "blocked_until_runner"


def _required_artifact(disposition: str) -> str:
    if disposition == "feature_ready_experiment":
        return "feature_probe_result + validated_feature_contract.json after gates"
    if disposition == "baseline_only":
        return "foundation_experiment_results_v1.csv"
    if disposition == "regime_design_only":
        return "regime design validation + Onda 4 robustness review"
    if disposition == "threshold_calibration_only":
        return "threshold calibration result with train-only assignment"
    return "foundation experiment runner"


def _rationale(
    *,
    disposition: str,
    queue_status: str,
    result_status: str,
    power_warning: object,
) -> str:
    warning = str(power_warning).rstrip(".")
    if disposition == "feature_ready_experiment":
        return (
            "Catalog authorizes an experiment-only feature probe, but "
            f"{queue_status}; result_status={result_status}; "
            f"power_warning={warning}."
        )
    return (
        "EDA evidence is valuable for experiment design, but this catalog row is "
        f"{disposition}, not a direct feature promotion."
    )


def build_eda_feature_candidate_review(
    *,
    catalog: pl.DataFrame,
    results: pl.DataFrame | None = None,
    feature_candidate_queue: pl.DataFrame | None = None,
) -> dict[str, pl.DataFrame]:
    """Classify EDA-derived catalog rows by how they may feed feature work."""
    if catalog.height == 0:
        return {"eda_feature_candidate_review": _empty_frame(EDA_FEATURE_REVIEW_SCHEMA)}
    if "production_status" not in catalog.columns:
        raise ValueError("catalog missing production_status column")
    invalid = catalog.filter(pl.col("production_status") != "EXPERIMENT_ONLY")
    if invalid.height:
        ids = ", ".join(str(value) for value in invalid.get_column("experiment_id").to_list())
        raise ValueError(f"EDA feature review only accepts EXPERIMENT_ONLY rows: {ids}")

    result_status_by_id: dict[str, str] = {}
    if results is not None and results.height and "experiment_id" in results.columns:
        status_column = "status" if "status" in results.columns else None
        if status_column:
            result_status_by_id = {
                str(row["experiment_id"]): str(row[status_column])
                for row in results.iter_rows(named=True)
            }
    queue_ids = _feature_queue_ids(feature_candidate_queue)
    queue_empty = not queue_ids

    rows: list[dict[str, object]] = []
    for row in catalog.sort("experiment_id").iter_rows(named=True):
        experiment_id = str(row["experiment_id"])
        disposition = _disposition(row)
        result_status = result_status_by_id.get(experiment_id, "not_run")
        if queue_empty:
            queue_status = "queue_empty"
        elif experiment_id in queue_ids:
            queue_status = "queued"
        else:
            queue_status = "not_queued"
        rows.append(
            {
                "experiment_id": experiment_id,
                "domain": str(row.get("domain", "")),
                "source_decision_id": str(row.get("source_decision_id", "")),
                "source_artifacts": str(row.get("source_artifacts", "")),
                "candidate_surface": str(row.get("candidate_surface", "")),
                "implementation_kind": str(row.get("implementation_kind", "")),
                "eda_feature_disposition": disposition,
                "runner_status": _runner_status(disposition, result_status),
                "feature_queue_status": queue_status,
                "result_status": result_status,
                "production_status": "EXPERIMENT_ONLY",
                "required_artifact": _required_artifact(disposition),
                "recommended_experiment": str(row.get("next_action", "")),
                "rationale": _rationale(
                    disposition=disposition,
                    queue_status=queue_status,
                    result_status=result_status,
                    power_warning=row.get("power_warning", ""),
                ),
            }
        )

    return {
        "eda_feature_candidate_review": pl.DataFrame(
            rows,
            schema=EDA_FEATURE_REVIEW_SCHEMA,
            strict=False,
        )
    }


def _md(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "/")


def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    review = artifacts["eda_feature_candidate_review"]
    lines = [
        f"# EDA Feature Candidate Review - {report_date.isoformat()}",
        "",
        "This artifact is an experiment-only bridge. It does not promote features, baselines, regimes, or thresholds to production.",
        "",
        f"- Reviewed rows: {review.height}",
        f"- Feature-ready experiments: {review.filter(pl.col('eda_feature_disposition') == 'feature_ready_experiment').height}",
        f"- Direct feature queue rows: {review.filter(pl.col('feature_queue_status') == 'queued').height}",
        "",
        "## Disposition Counts",
        "",
        "| Disposition | Rows |",
        "|---|---:|",
    ]
    for row in (
        review.group_by("eda_feature_disposition")
        .len(name="n")
        .sort("eda_feature_disposition")
        .iter_rows(named=True)
    ):
        lines.append(f"| {_md(row['eda_feature_disposition'])} | {row['n']} |")
    lines += [
        "",
        "## Review Matrix",
        "",
        "| Experiment | Domain | Disposition | Runner | Queue | Result | Required Artifact | Recommended Experiment |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in review.sort("experiment_id").iter_rows(named=True):
        lines.append(
            "| "
            f"{_md(row['experiment_id'])} | {_md(row['domain'])} | "
            f"{_md(row['eda_feature_disposition'])} | {_md(row['runner_status'])} | "
            f"{_md(row['feature_queue_status'])} | {_md(row['result_status'])} | "
            f"{_md(row['required_artifact'])} | {_md(row['recommended_experiment'])} |"
        )
    return lines


def write_eda_feature_candidate_review_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write EDA-to-feature review CSV and markdown artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "eda_feature_candidate_review_v1.csv"
    artifacts["eda_feature_candidate_review"].write_csv(review_path)
    report_path = out_dir / "eda_feature_candidate_review_v1.md"
    report_path.write_text(
        "\n".join(_report_lines(artifacts, today or dt.date.today())),
        encoding="utf-8",
    )
    return {
        "eda_feature_candidate_review_csv": review_path,
        "eda_feature_candidate_review_md": report_path,
    }
