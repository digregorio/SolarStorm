from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e import (
    build_eda_feature_candidate_review,
    write_eda_feature_candidate_review_artifacts,
)

runner = CliRunner()


def _catalog() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "experiment_id": "FEXP-FOEHN-CONTINUOUS-001",
                "experiment_family": "feature",
                "domain": "FOEHN",
                "source_decision_id": "WCT-FOEHN-001",
                "source_artifacts": "reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
                "weakness_target": "fixed_threshold",
                "candidate_surface": "feature_builder",
                "implementation_kind": "feature_probe",
                "input_columns_or_artifacts": "foehn_score; wind sector; dewpoint_depression; month; CP",
                "strata": "month x CP x foehn_score bin",
                "causal_status": "causal_available",
                "leakage_risk": "Use pre-CP score only.",
                "power_warning": "55/272 score-bin cells may be underpowered.",
                "baseline_comparator": "RULE_FOEHN_SCORE_FIXED_60",
                "success_metric": "mae_delta",
                "acceptance_gate": "Continuous or binned score improves validation.",
                "stop_condition": "Effect disappears.",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "Test continuous and binned foehn_score variants.",
            },
            {
                "experiment_id": "BEXP-L4-MONTH-CP-REGIME-001",
                "experiment_family": "baseline",
                "domain": "BASELINE",
                "source_decision_id": "ADR-012-BASELINE-L4",
                "source_artifacts": "reports/onda2e/regime_design_candidate_v1.csv",
                "weakness_target": "high_mae",
                "candidate_surface": "baseline_ladder",
                "implementation_kind": "baseline_variant",
                "input_columns_or_artifacts": "month; CP; candidate_regime_label; remaining_warming",
                "strata": "month x CP x candidate regime",
                "causal_status": "outcome_only",
                "leakage_risk": "Use train-fold conditional means only.",
                "power_warning": "Sparse cells require fallback.",
                "baseline_comparator": "L4",
                "success_metric": "mae_delta",
                "acceptance_gate": "Candidate reduces MAE versus L4.",
                "stop_condition": "Fallback rate is high.",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "Add empirical conditional baseline variant.",
            },
            {
                "experiment_id": "REXP-WIND-RDQ-009",
                "experiment_family": "regime",
                "domain": "WIND",
                "source_decision_id": "WCT-WIND-019",
                "source_artifacts": "reports/onda2e/wind_direction_reliability_by_day_cp.csv",
                "weakness_target": "regime_design_review",
                "candidate_surface": "regime_assignment",
                "implementation_kind": "regime_revision",
                "input_columns_or_artifacts": "southerly_count; southerly_depth; month; CP",
                "strata": "month x CP x wind sector depth",
                "causal_status": "causal_available",
                "leakage_risk": "Use only pre-CP wind observations.",
                "power_warning": "28/412 cells with n_obs < 30.",
                "baseline_comparator": "REGIME_CLASSIFIER_CURRENT",
                "success_metric": "dead_regime_count",
                "acceptance_gate": "Split improves candidate R2 screen.",
                "stop_condition": "Split is unstable.",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "Evaluate as regime-design split, not production feature.",
            },
            {
                "experiment_id": "TEXP-COOLING-MECHANISM-001",
                "experiment_family": "threshold",
                "domain": "COOLING",
                "source_decision_id": "WCT-COOL-003",
                "source_artifacts": "reports/onda2e/cooling_effects_by_month_regime_cp.csv",
                "weakness_target": "fixed_threshold",
                "candidate_surface": "regime_assignment",
                "implementation_kind": "threshold_calibration",
                "input_columns_or_artifacts": "temp_slope_pre_cp; wind shift; rain; pressure",
                "strata": "month x CP x cooling mechanism",
                "causal_status": "causal_available",
                "leakage_risk": "Do not use final Tmax.",
                "power_warning": "Require per-mechanism power checks.",
                "baseline_comparator": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
                "success_metric": "dead_regime_count",
                "acceptance_gate": "Calibrated split reduces dead regimes.",
                "stop_condition": "Split remains dead.",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "Calibrate cooling thresholds.",
            },
        ]
    )


def _results() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "experiment_id": "FEXP-FOEHN-CONTINUOUS-001",
                "status": "not_run",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "experiment_id": "BEXP-L4-MONTH-CP-REGIME-001",
                "status": "passed",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "experiment_id": "REXP-WIND-RDQ-009",
                "status": "not_run",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "experiment_id": "TEXP-COOLING-MECHANISM-001",
                "status": "not_run",
                "production_status": "EXPERIMENT_ONLY",
            },
        ]
    )


def test_eda_feature_review_keeps_empty_feature_queue_from_promoting_features():
    artifacts = build_eda_feature_candidate_review(
        catalog=_catalog(),
        results=_results(),
        feature_candidate_queue=pl.DataFrame(),
    )

    review = artifacts["eda_feature_candidate_review"]
    by_id = {row["experiment_id"]: row for row in review.iter_rows(named=True)}

    assert by_id["FEXP-FOEHN-CONTINUOUS-001"]["eda_feature_disposition"] == (
        "feature_ready_experiment"
    )
    assert by_id["FEXP-FOEHN-CONTINUOUS-001"]["runner_status"] == "blocked_until_runner"
    assert by_id["FEXP-FOEHN-CONTINUOUS-001"]["feature_queue_status"] == "queue_empty"
    assert by_id["BEXP-L4-MONTH-CP-REGIME-001"]["eda_feature_disposition"] == "baseline_only"
    assert by_id["REXP-WIND-RDQ-009"]["eda_feature_disposition"] == "regime_design_only"
    assert by_id["TEXP-COOLING-MECHANISM-001"]["eda_feature_disposition"] == (
        "threshold_calibration_only"
    )
    assert set(review.get_column("production_status")) == {"EXPERIMENT_ONLY"}


def test_eda_feature_review_marks_failed_feature_probe_as_runner_available():
    results = _results().with_columns(
        pl.when(pl.col("experiment_id") == "FEXP-FOEHN-CONTINUOUS-001")
        .then(pl.lit("failed"))
        .otherwise(pl.col("status"))
        .alias("status")
    )

    artifacts = build_eda_feature_candidate_review(
        catalog=_catalog(),
        results=results,
        feature_candidate_queue=pl.DataFrame(),
    )

    row = artifacts["eda_feature_candidate_review"].filter(
        pl.col("experiment_id") == "FEXP-FOEHN-CONTINUOUS-001"
    ).row(0, named=True)

    assert row["runner_status"] == "runner_available"
    assert row["result_status"] == "failed"
    assert row["production_status"] == "EXPERIMENT_ONLY"


def test_write_eda_feature_review_artifacts(tmp_path: Path):
    artifacts = build_eda_feature_candidate_review(
        catalog=_catalog(),
        results=_results(),
        feature_candidate_queue=pl.DataFrame(),
    )

    paths = write_eda_feature_candidate_review_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "eda_feature_candidate_review_v1.csv").exists()
    assert (tmp_path / "eda_feature_candidate_review_v1.md").exists()
    report = paths["eda_feature_candidate_review_md"].read_text(encoding="utf-8")
    assert "EDA Feature Candidate Review - 2026-06-08" in report
    assert "FEXP-FOEHN-CONTINUOUS-001" in report
    assert "feature_ready_experiment" in report


def test_eda_feature_review_cli_writes_artifacts(tmp_path: Path):
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    results_path = tmp_path / "foundation_experiment_results_v1.csv"
    queue_path = tmp_path / "feature_candidate_queue.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    _results().write_csv(results_path)
    queue_path.write_text("", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "eda-feature-candidate-review",
            "--catalog-path",
            str(catalog_path),
            "--results-path",
            str(results_path),
            "--feature-candidate-queue-path",
            str(queue_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    persisted = pl.read_csv(output_dir / "eda_feature_candidate_review_v1.csv")
    assert "FEXP-FOEHN-CONTINUOUS-001" in set(persisted.get_column("experiment_id"))
    assert set(persisted.get_column("production_status")) == {"EXPERIMENT_ONLY"}
