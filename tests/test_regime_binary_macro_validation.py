"""Tests for the offline regime binary macro validation pipeline."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from unittest.mock import patch

import numpy as np
import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_binary_macro_validation import (
    DECISION_SCHEMA,
    validate_binary_macro_regimes,
    write_binary_validation_reports,
)

runner = CliRunner()


def _mock_assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=i),
                "cp": "20:00",
                "binary_macro_regime_label": "macro_southerly_flow" if i % 2 == 0 else "macro_non_southerly",
                "source_macro_regime_label": "macro_southerly_flow" if i % 2 == 0 else "macro_nw_continuum",
                "production_status": "EXPERIMENT_ONLY",
            }
            for i in range(10)
        ],
        strict=False,
    )


def _mock_cluster_matrix() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=i),
                "cp": "20:00",
                "drct_sin_mean": 0.1 * i,
                "drct_cos_mean": -0.1 * i,
                "sknt_mean": 10.0 + i,
                "qnh_hpa_mean": 1010.0 - i,
                "relh_mean": 60.0 + i,
                "dewpoint_depression_mean": 5.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.5,
                "regime_label": "macro_southerly_flow" if i < 5 else "macro_nw_continuum",
                "month": 1,
            }
            for i in range(10)
        ],
        strict=False,
    )


@pytest.fixture
def mock_validation_dependencies():
    """Fixture to mock all complex mathematical/R2 dependencies."""
    cols = [
        "drct_sin_mean",
        "drct_cos_mean",
        "sknt_mean",
        "qnh_hpa_mean",
        "relh_mean",
        "dewpoint_depression_mean",
        "precip_pre_cp_sum",
        "cloud_cover_score_mean",
        "temp_slope_pre_cp",
    ]
    audit_df = pl.DataFrame({"feature": cols, "included_in_classifiability": [True] * 9})

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation._build_cluster_matrix",
        return_value=_mock_cluster_matrix(),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation.select_physical_classifiability_features",
        return_value=(cols, audit_df),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_gmm",
        return_value=(
            ["macro_southerly_flow"] * 5 + ["macro_non_southerly"] * 5,
            [0] * 5 + [1] * 5,
            np.array([[0.9, 0.1]] * 10),
            np.array([0.1] * 10),
            np.array([0.8] * 10),
            np.array([0.1] * 10),
        ),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._map_by_train_centroids",
        return_value=(
            ["macro_southerly_flow"] * 5 + ["macro_non_southerly"] * 5,
            np.array([0.1] * 10),
            np.array([0.8] * 10),
        ),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation.roc_auc_score",
        return_value=0.95,
    ):
        yield


def test_validation_gate_passes(mock_validation_dependencies):
    # Mock validation R2 to pass
    cross_tab_pass = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_pass},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.85),
    ):
        artifacts = validate_binary_macro_regimes(
            assignments=_mock_assignments(),
            features=pl.DataFrame(),
            labels=pl.DataFrame(),
            obs=pl.DataFrame(),
            train_end=dt.date(2025, 1, 8),
            test_start=dt.date(2025, 1, 9),
        )

        decision = artifacts["regime_binary_macro_decision_update_v1"]
        assert decision.height == 1
        assert decision.row(0, named=True)["decision_status"] == "READY_FOR_ONDA3_DESIGN_REVIEW"
        assert artifacts["dead_candidate_regimes"].filter(pl.col("status") == "DEAD").height == 0


def test_validation_gate_fails_due_to_dead_regime(mock_validation_dependencies):
    # Mock validation R2 where macro_non_southerly is DEAD
    cross_tab_fail = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": False, "n_days": 10, "status": "rejected"}
    ])

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_fail},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.85),
    ):
        artifacts = validate_binary_macro_regimes(
            assignments=_mock_assignments(),
            features=pl.DataFrame(),
            labels=pl.DataFrame(),
            obs=pl.DataFrame(),
            train_end=dt.date(2025, 1, 8),
            test_start=dt.date(2025, 1, 9),
        )

        decision = artifacts["regime_binary_macro_decision_update_v1"]
        assert decision.row(0, named=True)["decision_status"] == "BLOCKED_WITH_CONCRETE_FAILURE"
        dead_regimes = artifacts["dead_candidate_regimes"]
        assert dead_regimes.filter(pl.col("candidate_regime_family") == "macro_non_southerly").row(0, named=True)["status"] == "DEAD"


def test_validation_gate_fails_due_to_low_auc(mock_validation_dependencies):
    cross_tab_pass = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_pass},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation.roc_auc_score",
        return_value=0.75,  # below threshold 0.80
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.85),
    ):
        artifacts = validate_binary_macro_regimes(
            assignments=_mock_assignments(),
            features=pl.DataFrame(),
            labels=pl.DataFrame(),
            obs=pl.DataFrame(),
            train_end=dt.date(2025, 1, 8),
            test_start=dt.date(2025, 1, 9),
        )

        decision = artifacts["regime_binary_macro_decision_update_v1"]
        assert decision.row(0, named=True)["decision_status"] == "BLOCKED_WITH_CONCRETE_FAILURE"


def test_validation_gate_fails_when_auc_has_insufficient_class_variation(mock_validation_dependencies):
    cross_tab_pass = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])
    assignments = _mock_assignments().with_columns(
        pl.when(pl.col("date_local") >= dt.date(2025, 1, 9))
        .then(pl.lit("macro_southerly_flow"))
        .otherwise(pl.col("binary_macro_regime_label"))
        .alias("binary_macro_regime_label")
    )

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_pass},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.85),
    ):
        artifacts = validate_binary_macro_regimes(
            assignments=assignments,
            features=pl.DataFrame(),
            labels=pl.DataFrame(),
            obs=pl.DataFrame(),
            train_end=dt.date(2025, 1, 8),
            test_start=dt.date(2025, 1, 9),
        )

        class_row = (
            artifacts["regime_binary_macro_classifiability_v1"]
            .filter(pl.col("method") == "distance_softmax_binary")
            .row(0, named=True)
        )
        decision = artifacts["regime_binary_macro_decision_update_v1"].row(0, named=True)

        assert class_row["predictive_auc"] == 0.0
        assert decision["decision_status"] == "BLOCKED_INSUFFICIENT_CLASS_VARIATION"
        assert "insufficient class variation" in decision["decision_rationale"]


def test_validation_gate_fails_due_to_low_stability(mock_validation_dependencies):
    cross_tab_pass = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_pass},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.5),  # Stability score = 0.5 < 0.7
    ):
        artifacts = validate_binary_macro_regimes(
            assignments=_mock_assignments(),
            features=pl.DataFrame(),
            labels=pl.DataFrame(),
            obs=pl.DataFrame(),
            train_end=dt.date(2025, 1, 8),
            test_start=dt.date(2025, 1, 9),
        )

        decision = artifacts["regime_binary_macro_decision_update_v1"]
        assert decision.row(0, named=True)["decision_status"] == "BLOCKED_WITH_CONCRETE_FAILURE"


def test_write_binary_validation_reports(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    cross_tab = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])
    class_df = pl.DataFrame([
        {
            "method": "distance_softmax_binary",
            "candidate_version": "binary_v1",
            "macro_count": 2,
            "dead_regimes": 0,
            "low_confidence_share": 0.0,
            "classifiability_score": 0.25,
            "predictive_auc": 0.95,
            "stability_score": 0.85,
            "temporal_stability": 0.8,
            "decision_update": "READY_FOR_ONDA3_DESIGN_REVIEW",
            "production_status": "EXPERIMENT_ONLY",
        }
    ])
    decision_df = pl.DataFrame([
        {
            "decision_id": "REGIME-BINARY-MACRO-VALIDATION-001",
            "item_id": "WCT-BINARY-MACRO",
            "item_type": "thesis",
            "domain": "REGIME",
            "decision_status": "READY_FOR_ONDA3_DESIGN_REVIEW",
            "evidence_level": "E3_candidate_r2_validation",
            "source_artifact": "reports/regime-design/regime_binary_macro_r2_validation_v1.md",
            "strata": "binary macro family x CP",
            "sample_size_warning": "none",
            "causal_availability": "ok",
            "leakage_risk": "EXPERIMENT_ONLY",
            "decision_rationale": "mock rationale",
            "next_allowed_action": "proceed",
        }
    ])
    r2_summary = pl.DataFrame([
        {"candidate_regime_family": "macro_southerly_flow", "status": "PASS"},
        {"candidate_regime_family": "macro_non_southerly", "status": "PASS"},
    ])

    artifacts = {
        "regime_binary_macro_r2_validation_v1": cross_tab,
        "regime_binary_macro_classifiability_v1": class_df,
        "regime_binary_macro_decision_update_v1": decision_df,
        "dead_candidate_regimes": r2_summary,
    }

    # Set up mock register file relative to tmp_path
    register_dir = Path("reports/onda2e")
    register_dir.mkdir(parents=True, exist_ok=True)
    register_path = register_dir / "evidence_decision_register.csv"
    pl.DataFrame(schema=DECISION_SCHEMA).write_csv(register_path)

    paths = write_binary_validation_reports(artifacts, output_dir=tmp_path, today=dt.date(2026, 6, 9))

    assert paths["regime_binary_macro_r2_validation_csv"].exists()
    assert paths["regime_binary_macro_r2_validation_md"].exists()
    assert paths["regime_binary_macro_classifiability_csv"].exists()
    assert paths["regime_binary_macro_classifiability_md"].exists()
    assert paths["regime_binary_macro_decision_update_csv"].exists()

    # Verify that register is updated
    updated_register = pl.read_csv(register_path)
    assert updated_register.height == 1
    assert updated_register.row(0, named=True)["decision_id"] == "REGIME-BINARY-MACRO-VALIDATION-001"


def test_cli_command(tmp_path: Path, monkeypatch, mock_validation_dependencies):
    monkeypatch.chdir(tmp_path)

    # Create directories
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("reports/regime-design").mkdir(parents=True, exist_ok=True)
    Path("reports/onda2e").mkdir(parents=True, exist_ok=True)

    # Set up mock input files
    assignments_path = "reports/regime-design/regime_binary_macro_assignments_v1.csv"
    features_path = "data/features.parquet"
    labels_path = "data/labels.parquet"
    obs_path = "data/obs.parquet"

    _mock_assignments().write_csv(assignments_path)
    pl.DataFrame().write_parquet(features_path)
    pl.DataFrame().write_parquet(labels_path)
    pl.DataFrame().write_parquet(obs_path)

    # Create empty register file
    register_path = Path("reports/onda2e/evidence_decision_register.csv")
    pl.DataFrame(schema=DECISION_SCHEMA).write_csv(register_path)

    cross_tab_pass = pl.DataFrame([
        {"regime": "macro_southerly_flow", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"},
        {"regime": "macro_non_southerly", "hypothesis_id": "H1", "feature_column": "feat", "cp": "20:00", "passes": True, "n_days": 10, "status": "validated"}
    ])

    with patch(
        "solarstorm.onda2e._regime_binary_macro_validation.validate_regime_candidate_r2",
        return_value={"regime_candidate_r2_validation": cross_tab_pass},
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._compute_clustering_metrics",
        return_value=(0.25, 0.0, 0.0),
    ), patch(
        "solarstorm.onda2e._regime_binary_macro_validation._run_michelangeli_stability",
        return_value=(0.8, 0.85),
    ):
        result = runner.invoke(
            app,
            [
                "regime-binary-macro-validation",
                "--assignments-path",
                assignments_path,
                "--features-path",
                features_path,
                "--labels-path",
                labels_path,
                "--obs-path",
                obs_path,
                "--output-dir",
                "reports/regime-design",
                "--train-end",
                "2025-01-08",
                "--test-start",
                "2025-01-09",
                "--cp-set",
                "20:00",
            ],
        )

        assert result.exit_code == 0, result.output
        assert "Regime binary macro validation complete" in result.output
        assert "Decision Status: READY_FOR_ONDA3_DESIGN_REVIEW" in result.output


def test_cli_command_missing_inputs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "regime-binary-macro-validation",
            "--assignments-path",
            "nonexistent.csv",
        ],
    )
    assert result.exit_code == 2
    assert "ERROR: missing input files" in result.output
