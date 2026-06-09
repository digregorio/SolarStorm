from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e import (
    build_foundation_experiment_catalog,
    load_foundation_experiment_inputs,
    write_foundation_experiment_catalog_artifacts,
)

runner = CliRunner()


def _decision_register() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-REGIME-016",
                "item_id": "WCT-REGIME-016",
                "item_type": "thesis",
                "domain": "REGIME",
                "decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "evidence_level": "E2_regime_architecture_candidate",
                "source_artifact": "reports/onda2e/regime_design_candidate_v1.csv",
                "strata": "month and season x k=6 cluster",
                "sample_size_warning": "0/96 candidate rows have smallest k=6 cluster support below 30.",
                "causal_availability": "Design-only artifact.",
                "leakage_risk": "No production classifier change before Onda 4.",
                "decision_rationale": "k=6 wins approximate BIC.",
                "next_allowed_action": "Enter regime_design_queue only.",
            },
            {
                "decision_id": "DEC-WCT-REJECTED",
                "item_id": "WCT-REJECTED",
                "item_type": "thesis",
                "domain": "TIMING",
                "decision_status": "REJECTED",
                "evidence_level": "E2_rejected",
                "source_artifact": "reports/onda2e/rejected.csv",
                "strata": "month",
                "sample_size_warning": "none",
                "causal_availability": "none",
                "leakage_risk": "none",
                "decision_rationale": "Rejected by evidence.",
                "next_allowed_action": "Do not use.",
            },
        ],
    )


def _queue() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "queue_id": "RDQ-001",
                "rule_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
                "source_item_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
                "source_item_type": "rule",
                "domain": "COOLING",
                "source_decision_status": "QUARANTINED_BASELINE",
                "source_artifact": "reports/onda2e/quarantined_baseline_register.csv",
                "evidence_gap": "Fixed cooling threshold is not calibrated.",
                "next_action": "Use cooling taxonomy EDA.",
            },
            {
                "queue_id": "RDQ-008",
                "rule_id": "",
                "source_item_id": "WCT-REGIME-016",
                "source_item_type": "thesis",
                "domain": "REGIME",
                "source_decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "source_artifact": "reports/onda2e/regime_design_candidate_v1.csv",
                "evidence_gap": "k=6 wins approximate BIC but still needs Onda 4.",
                "next_action": "Run Onda 4 robustness.",
            },
        ],
    )


def _quarantined_baselines() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "rule_id": "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
                "domain": "COOLING",
                "rule_name": "Fixed material cooling threshold",
                "affected_surface": "cooling taxonomy",
                "hardcoded_value": "min_delta_t_per_h < -2.0",
                "decision_status": "QUARANTINED_BASELINE",
                "source_artifact": "reports/regime/cooling-rule-experiment.md",
                "evidence_gap": "Cooling has not been calibrated by month or mechanism.",
                "decision_rationale": "Threshold mixes physical mechanisms.",
                "next_allowed_action": "Use cooling taxonomy EDA.",
            },
            {
                "rule_id": "RULE_FOEHN_SCORE_FIXED_60",
                "domain": "FOEHN",
                "rule_name": "Fixed foehn score threshold",
                "affected_surface": "strong_nw_foehn trigger",
                "hardcoded_value": "foehn_score > 60.0",
                "decision_status": "QUARANTINED_BASELINE",
                "source_artifact": "reports/onda2e/thesis_atlas_v1.md",
                "evidence_gap": "Foehn threshold is not calibrated.",
                "decision_rationale": "Keep as audit threshold.",
                "next_allowed_action": "Run foehn-domain EDA.",
            },
        ],
    )


def _rejections() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-REJECTED",
                "item_id": "WCT-REJECTED",
                "domain": "TIMING",
                "source_artifact": "reports/onda2e/rejected.csv",
                "decision_rationale": "Rejected by evidence.",
                "reentry_condition": "Only with new local evidence.",
            }
        ],
    )


def _r2_validation() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H1",
                "feature_column": "slope_3h",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H2",
                "feature_column": "dewpoint_depression",
                "cp": "21:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_mixed_or_transition",
                "hypothesis_id": "H1",
                "feature_column": "slope_3h",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_nw_or_foehn",
                "hypothesis_id": "H1",
                "feature_column": "slope_3h",
                "cp": "20:00",
                "passes": True,
                "n_days": 20,
                "status": "validated",
            },
        ],
    )


def test_catalog_builds_baseline_regime_and_dead_family_experiments():
    artifacts = build_foundation_experiment_catalog(
        decision_register=_decision_register(),
        regime_design_queue=_queue(),
        quarantined_baselines=_quarantined_baselines(),
        rejection_register=_rejections(),
        regime_candidate_r2_validation=_r2_validation(),
    )

    catalog = artifacts["foundation_experiment_catalog"]

    assert "BEXP-L2-MONTH-REGIME-001" in set(catalog.get_column("experiment_id"))
    assert "BEXP-L4-MONTH-CP-REGIME-001" in set(catalog.get_column("experiment_id"))
    assert "REXP-DEAD-MARITIME-001" in set(catalog.get_column("experiment_id"))
    assert "REXP-DEAD-MIXED-001" in set(catalog.get_column("experiment_id"))
    assert "FEXP-FOEHN-CONTINUOUS-001" in set(catalog.get_column("experiment_id"))
    assert "TEXP-COOLING-MECHANISM-001" in set(catalog.get_column("experiment_id"))
    assert not catalog.filter(pl.col("source_decision_id") == "WCT-REJECTED").height
    assert set(catalog.get_column("production_status")) == {"EXPERIMENT_ONLY"}
    assert catalog.filter(pl.col("baseline_comparator") == "").height == 0
    assert catalog.filter(pl.col("success_metric") == "").height == 0
    assert catalog.filter(pl.col("acceptance_gate") == "").height == 0
    assert catalog.filter(pl.col("stop_condition") == "").height == 0
    assert catalog.filter(pl.col("source_artifacts") == "").height == 0


def test_catalog_rejects_rejected_queue_items():
    contaminated_queue = pl.DataFrame(
        [
            {
                "queue_id": "RDQ-BAD",
                "rule_id": "",
                "source_item_id": "WCT-REJECTED",
                "source_item_type": "thesis",
                "domain": "TIMING",
                "source_decision_status": "REJECTED",
                "source_artifact": "reports/onda2e/rejected.csv",
                "evidence_gap": "Rejected by evidence.",
                "next_action": "Do not use.",
            }
        ]
    )

    with pytest.raises(ValueError, match="rejected"):
        build_foundation_experiment_catalog(
            decision_register=_decision_register(),
            regime_design_queue=contaminated_queue,
            quarantined_baselines=_quarantined_baselines(),
            rejection_register=_rejections(),
            regime_candidate_r2_validation=_r2_validation(),
        )


def test_catalog_rejects_non_quarantined_baseline_register_rows():
    invalid_baselines = _quarantined_baselines().with_columns(
        pl.when(pl.col("rule_id") == "RULE_FOEHN_SCORE_FIXED_60")
        .then(pl.lit("SUPPORTED"))
        .otherwise(pl.col("decision_status"))
        .alias("decision_status")
    )

    with pytest.raises(ValueError, match="QUARANTINED_BASELINE"):
        build_foundation_experiment_catalog(
            decision_register=_decision_register(),
            regime_design_queue=_queue(),
            quarantined_baselines=invalid_baselines,
            rejection_register=_rejections(),
            regime_candidate_r2_validation=_r2_validation(),
        )


def test_writer_outputs_catalog_and_markdown_without_results_file(tmp_path: Path):
    artifacts = build_foundation_experiment_catalog(
        decision_register=_decision_register(),
        regime_design_queue=_queue(),
        quarantined_baselines=_quarantined_baselines(),
        rejection_register=_rejections(),
        regime_candidate_r2_validation=_r2_validation(),
        optional_artifact_warnings=pl.DataFrame(
            [
                {
                    "artifact": "reports/onda2e/domain_thesis_evidence.csv",
                    "status": "MISSING_OPTIONAL",
                    "detail": "Optional artifact not found.",
                }
            ]
        ),
    )

    paths = write_foundation_experiment_catalog_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "foundation_experiment_catalog_v1.csv").exists()
    assert (tmp_path / "foundation_experiment_catalog_v1.md").exists()
    assert not (tmp_path / "foundation_experiment_results_v1.csv").exists()
    report = paths["foundation_experiment_catalog_md"].read_text(encoding="utf-8")
    assert "Foundation Experiment Catalog - 2026-06-07" in report
    assert "not a production promotion" in report
    assert "Counts By Family" in report
    assert "Missing Optional Artifacts" in report


def _write_required_inputs(onda2e_dir: Path, regime_design_dir: Path) -> None:
    onda2e_dir.mkdir(parents=True)
    regime_design_dir.mkdir(parents=True)
    _decision_register().write_csv(onda2e_dir / "evidence_decision_register.csv")
    _queue().write_csv(onda2e_dir / "regime_design_queue.csv")
    _quarantined_baselines().write_csv(onda2e_dir / "quarantined_baseline_register.csv")
    _rejections().write_csv(onda2e_dir / "rejection_register.csv")
    _r2_validation().write_csv(regime_design_dir / "regime_candidate_r2_validation.csv")


def test_loader_records_missing_optional_artifact_warnings(tmp_path: Path):
    onda2e_dir = tmp_path / "onda2e"
    regime_design_dir = tmp_path / "regime-design"
    _write_required_inputs(onda2e_dir, regime_design_dir)

    inputs = load_foundation_experiment_inputs(
        onda2e_dir=onda2e_dir,
        regime_design_dir=regime_design_dir,
    )

    warnings = inputs["optional_artifact_warnings"]
    assert warnings.filter(pl.col("status") == "MISSING_OPTIONAL").height > 0


@pytest.mark.parametrize(
    ("filename", "empty_frame"),
    [
        ("evidence_decision_register.csv", _decision_register().head(0)),
        ("regime_design_queue.csv", _queue().head(0)),
        ("quarantined_baseline_register.csv", _quarantined_baselines().head(0)),
    ],
)
def test_loader_rejects_empty_required_artifacts(
    tmp_path: Path,
    filename: str,
    empty_frame: pl.DataFrame,
):
    onda2e_dir = tmp_path / "onda2e"
    regime_design_dir = tmp_path / "regime-design"
    _write_required_inputs(onda2e_dir, regime_design_dir)
    empty_frame.write_csv(onda2e_dir / filename)

    with pytest.raises(ValueError, match="zero rows"):
        load_foundation_experiment_inputs(
            onda2e_dir=onda2e_dir,
            regime_design_dir=regime_design_dir,
        )


def test_loader_rejects_required_artifacts_with_missing_columns(tmp_path: Path):
    onda2e_dir = tmp_path / "onda2e"
    regime_design_dir = tmp_path / "regime-design"
    _write_required_inputs(onda2e_dir, regime_design_dir)
    pl.DataFrame({"decision_id": ["DEC-BROKEN"]}).write_csv(
        onda2e_dir / "evidence_decision_register.csv"
    )

    with pytest.raises(ValueError, match="missing required columns"):
        load_foundation_experiment_inputs(
            onda2e_dir=onda2e_dir,
            regime_design_dir=regime_design_dir,
        )


def test_foundation_experiments_cli_writes_artifacts(tmp_path: Path):
    onda2e_dir = tmp_path / "onda2e"
    regime_design_dir = tmp_path / "regime-design"
    output_dir = tmp_path / "foundation-experiments"
    _write_required_inputs(onda2e_dir, regime_design_dir)

    result = runner.invoke(
        app,
        [
            "foundation-experiments",
            "--onda2e-dir",
            str(onda2e_dir),
            "--regime-design-dir",
            str(regime_design_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    catalog_path = output_dir / "foundation_experiment_catalog_v1.csv"
    assert catalog_path.exists()
    assert (output_dir / "foundation_experiment_catalog_v1.md").exists()
    assert not (output_dir / "foundation_experiment_results_v1.csv").exists()
    catalog = pl.read_csv(catalog_path)
    assert "REXP-DEAD-MARITIME-001" in set(catalog.get_column("experiment_id"))
