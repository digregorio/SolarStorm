from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.onda2e import (
    build_regime_candidate_artifacts,
    build_regime_candidate_v2_assignment_artifacts,
    compare_regime_candidate_r2,
    compare_regime_candidate_v2_v21,
    validate_regime_candidate_r2,
    write_regime_candidate_v2_validation_artifacts,
    write_regime_candidate_v21_validation_artifacts,
    write_regime_candidate_validation_artifacts,
)

runner = CliRunner()


def _candidate_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v1",
                "candidate_id": "RDC-V1-MONTH-1-C00",
                "thesis_id": "WCT-REGIME-016",
                "candidate_name": "test",
                "stratum_type": "month",
                "stratum_value": "1",
                "k": 6,
                "cluster_id": 0,
                "n_rows": 40,
                "candidate_regime_family": "southerly_disrupted_candidate",
                "proposed_regime_label": "month_1_k6_c0_southerly",
                "physical_signature": "southerly_flow;windy",
                "interpretability_score": 0.7,
                "promotion_readiness": "design_evidence_only",
                "wind_dir_deg_mean": 180.0,
                "wind_speed_mean": 15.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp_mean": -0.4,
                "production_status": "NOT_PRODUCTION",
                "next_gate_action": "Run Onda 4.",
            },
            {
                "candidate_version": "v1",
                "candidate_id": "RDC-V1-MONTH-1-C01",
                "thesis_id": "WCT-REGIME-016",
                "candidate_name": "test",
                "stratum_type": "month",
                "stratum_value": "1",
                "k": 6,
                "cluster_id": 1,
                "n_rows": 50,
                "candidate_regime_family": "nw_or_foehn_candidate",
                "proposed_regime_label": "month_1_k6_c1_nw",
                "physical_signature": "northerly_nw_flow;dry_air",
                "interpretability_score": 0.6,
                "promotion_readiness": "design_evidence_only",
                "wind_dir_deg_mean": 350.0,
                "wind_speed_mean": 17.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp_mean": 0.5,
                "production_status": "NOT_PRODUCTION",
                "next_gate_action": "Run Onda 4.",
            },
        ],
        strict=False,
    )


def _feature_rows(n_days: int = 30) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(n_days):
        rows.append(
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=i),
                "cp": "20:00",
                "regime_label": "quarantined_baseline",
                "feat_signal": float(i),
            }
        )
    return pl.DataFrame(rows)


def _label_rows(n_days: int = 30) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(n_days):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=i)
        rows.append(
            {
                "date_local": day,
                "day_complete": True,
                "tmax_int": 20 + (i % 5),
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            }
        )
    return pl.DataFrame(rows)


def _obs_rows(n_days: int = 30) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(n_days):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=i)
        is_southerly = i % 2 == 0
        for hour in (0, 3, 6, 9):
            rows.append(
                {
                    "date_local": day,
                    "valid": dt.datetime(2025, 1, 1, hour, tzinfo=dt.UTC)
                    + dt.timedelta(days=i),
                    "ts_local": dt.datetime.combine(day, dt.time(hour)),
                    "tmp_c_int": 16 - hour // 3 if is_southerly else 12 + hour // 3,
                    "dwp_c_int": 14 if is_southerly else 4,
                    "dw_depression_c_int": 2 if is_southerly else 8,
                    "drct": 180.0 if is_southerly else 350.0,
                    "sknt": 15.0 if is_southerly else 17.0,
                    "relh": 85.0 if is_southerly else 60.0,
                    "alti": 29.74 if is_southerly else 29.88,
                    "p01i": 0.0,
                    "skyc1": "BKN" if is_southerly else "CLR",
                    "dq_tmp_c_int": "ok",
                }
            )
    return pl.DataFrame(rows)


def test_candidate_assignment_uses_month_centroids():
    artifacts = build_regime_candidate_artifacts(
        _candidate_rows(),
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
    )

    ontology = artifacts["regime_candidate_ontology"]
    assignments = artifacts["regime_candidate_assignments"]
    audit = artifacts["regime_candidate_assignment_audit"]

    assert ontology.height == 2
    assert assignments.height == 30
    assert set(assignments["production_status"]) == {"NOT_PRODUCTION"}
    assert "candidate_regime_label" in assignments.columns
    assert assignments.filter(pl.col("candidate_regime_family").is_null()).height == 0
    assert audit.filter(pl.col("audit_item") == "null_assignments").row(0, named=True)[
        "status"
    ] == "PASS"


def test_candidate_assignment_imputes_missing_causal_inputs():
    obs = _obs_rows().with_columns(pl.lit(None).cast(pl.Float64).alias("alti"))

    artifacts = build_regime_candidate_artifacts(
        _candidate_rows(),
        _feature_rows(),
        _label_rows(),
        obs,
        tz_name="UTC",
    )

    assignments = artifacts["regime_candidate_assignments"]
    audit = artifacts["regime_candidate_assignment_audit"]

    assert assignments.filter(pl.col("candidate_regime_label").is_null()).height == 0
    imputation = audit.filter(pl.col("audit_item") == "missing_input_imputation").row(
        0,
        named=True,
    )
    assert imputation["status"] == "WARN"


def test_candidate_r2_validation_uses_feature_copy():
    features = _feature_rows()
    artifacts = build_regime_candidate_artifacts(
        _candidate_rows(),
        features,
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
    )
    validation = validate_regime_candidate_r2(
        features,
        _label_rows(),
        artifacts["regime_candidate_assignments"],
        [Hypothesis(id="H_SIG", feature_column="feat_signal", description="signal")],
        cp_set=("20:00",),
        test_starts=[dt.date(2025, 1, 1)],
    )

    assert features.get_column("regime_label").unique().to_list() == ["quarantined_baseline"]
    assert "regime_candidate_r2_validation" in validation
    assert "dead_candidate_regimes" in validation
    assert "regime_candidate_validation_scope" in validation
    assert {"regime", "hypothesis_id", "cp", "passes", "n_days"}.issubset(
        validation["regime_candidate_r2_validation"].columns
    )
    scope = validation["regime_candidate_validation_scope"]
    assert scope.filter(pl.col("audit_item") == "r2_test_starts").row(0, named=True)[
        "detail"
    ] == "2025-01-01"


def test_write_regime_candidate_validation_artifacts(tmp_path: Path):
    artifacts = build_regime_candidate_artifacts(
        _candidate_rows(),
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
    )
    validation = validate_regime_candidate_r2(
        _feature_rows(),
        _label_rows(),
        artifacts["regime_candidate_assignments"],
        [Hypothesis(id="H_SIG", feature_column="feat_signal", description="signal")],
        cp_set=("20:00",),
        test_starts=[dt.date(2025, 1, 1)],
    )

    paths = write_regime_candidate_validation_artifacts(
        {**artifacts, **validation},
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "regime_candidate_assignments_v1.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v1.csv").exists()
    assert (tmp_path / "regime_candidate_assignment_audit.csv").exists()
    assert (tmp_path / "regime_candidate_validation_scope.csv").exists()
    assert (tmp_path / "regime_candidate_r2_validation.csv").exists()
    assert (tmp_path / "regime_candidate_validation_report.md").exists()
    assert (tmp_path / "regime_candidate_decision_update.csv").exists()
    decision = pl.read_csv(tmp_path / "regime_candidate_decision_update.csv")
    assert decision.row(0, named=True)["decision_status"] == "PROMOTED_TO_REGIME_DESIGN"
    assert "not a production classifier" in paths["validation_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Validation Scope" in paths["validation_report_md"].read_text(
        encoding="utf-8"
    )


def test_regime_design_validate_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    candidate_path = tmp_path / "candidate.csv"
    queue_path = tmp_path / "queue.csv"
    output_dir = tmp_path / "regime-design"
    features = _feature_rows()
    features.write_parquet(features_path)
    _label_rows().write_parquet(labels_path)
    _obs_rows().write_parquet(obs_path)
    _candidate_rows().write_csv(candidate_path)
    pl.DataFrame(
        [
            {
                "queue_id": "RDQ-001",
                "rule_id": "",
                "source_item_id": "WCT-REGIME-016",
                "source_item_type": "thesis",
                "domain": "REGIME",
                "source_decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "source_artifact": str(candidate_path),
                "evidence_gap": "test",
                "next_action": "validate candidate",
            }
        ]
    ).write_csv(queue_path)

    result = runner.invoke(
        app,
        [
            "regime-design-validate",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--candidate-path",
            str(candidate_path),
            "--queue-path",
            str(queue_path),
            "--output-dir",
            str(output_dir),
            "--tz-name",
            "UTC",
            "--cp-set",
            "20:00",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_candidate_assignments_v1.csv").exists()
    assert (output_dir / "regime_candidate_validation_report.md").exists()
    scope = pl.read_csv(output_dir / "regime_candidate_validation_scope.csv")
    assert scope.filter(pl.col("audit_item") == "r2_validation_mode").row(0, named=True)[
        "status"
    ] == "WARN"
    assert scope.filter(pl.col("audit_item") == "r2_test_starts").row(0, named=True)[
        "detail"
    ] == "2025-01-01"
    persisted = pl.read_parquet(features_path)
    assert persisted.shape == features.shape
    assert persisted.to_dicts() == features.to_dicts()


def test_regime_design_validate_cli_uses_default_candidate_path(
    tmp_path: Path,
    monkeypatch,
):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    queue_path = tmp_path / "queue.csv"
    output_dir = tmp_path / "regime-design"
    default_candidate_dir = tmp_path / "reports" / "onda2e"
    default_candidate_dir.mkdir(parents=True)
    default_candidate_path = default_candidate_dir / "regime_design_candidate_v1.csv"
    features = _feature_rows()
    features.write_parquet(features_path)
    _label_rows().write_parquet(labels_path)
    _obs_rows().write_parquet(obs_path)
    _candidate_rows().write_csv(default_candidate_path)
    pl.DataFrame(
        [
            {
                "queue_id": "RDQ-001",
                "rule_id": "",
                "source_item_id": "WCT-REGIME-016",
                "source_item_type": "thesis",
                "domain": "REGIME",
                "source_decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "source_artifact": str(default_candidate_path),
                "evidence_gap": "test",
                "next_action": "validate candidate",
            }
        ]
    ).write_csv(queue_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "regime-design-validate",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--queue-path",
            str(queue_path),
            "--output-dir",
            str(output_dir),
            "--tz-name",
            "UTC",
            "--cp-set",
            "20:00",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_candidate_assignments_v1.csv").exists()


def test_compare_regime_candidate_r2_reports_per_macro_gate_metrics():
    v1 = pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            },
            {
                "regime": "candidate_nw_or_foehn",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 10,
                "status": "validated",
            },
        ]
    )
    v2 = pl.DataFrame(
        [
            {
                "regime": "macro_light_marine_or_residual",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 20,
                "status": "validated",
            },
            {
                "regime": "macro_nw_continuum",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": True,
                "n_days": 10,
                "status": "validated",
            },
        ]
    )
    assignments_v2 = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "low_confidence_flag": False,
                "component_entropy": 0.10,
                "component_margin": 0.80,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "low_confidence_flag": True,
                "component_entropy": 0.40,
                "component_margin": 0.20,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "low_confidence_flag": False,
                "component_entropy": 0.20,
                "component_margin": 0.70,
            },
            {
                "date_local": dt.date(2025, 1, 4),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "low_confidence_flag": False,
                "component_entropy": 0.30,
                "component_margin": 0.60,
            },
        ]
    )

    artifacts = compare_regime_candidate_r2(
        v1_r2=v1,
        v2_r2=v2,
        v2_assignments=assignments_v2,
        v1_regimes=("candidate_maritime_cloudy", "candidate_nw_or_foehn"),
        v2_regimes=("macro_light_marine_or_residual", "macro_nw_continuum"),
        protected_v2_regimes=("macro_nw_continuum",),
        min_assignment_rows=2,
    )

    comparison = artifacts["regime_candidate_v1_v2_comparison"]
    light = comparison.filter(
        pl.col("macro_regime_label") == "macro_light_marine_or_residual"
    ).row(0, named=True)

    assert comparison.height == 2
    assert light["candidate_version"] == "v2"
    assert light["assignment_rows"] == 2
    assert light["r2_pass_rows"] == 1
    assert light["r2_dead_status"] == "PASS"
    assert light["protected_regression_flag"] is False
    assert light["low_confidence_share"] == 0.5
    assert light["smallest_cp_support"] == 2
    assert light["v1_dead_regimes"] == 1
    assert light["v2_dead_regimes"] == 0
    assert light["decision_update"] == "READY_FOR_FULL_ONDA4_RERUN"
    assert light["production_status"] == "EXPERIMENT_ONLY"


def _candidate_v2_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2",
                "candidate_id": "RDC-V2-0001",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "latent_component_id": "macro_nw_continuum:subtype_standard_nw:month:1",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_source_rows": 100,
                "mean_interpretability_score": 0.6,
                "physical_signature": "northerly_nw_flow",
                "wind_dir_deg_mean": 350.0,
                "wind_speed_mean": 17.0,
                "qnh_hpa_mean": 1012.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 8.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp_mean": 0.5,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v2",
                "candidate_id": "RDC-V2-0002",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "latent_component_id": (
                    "macro_southerly_flow:subtype_frontal_southerly:month:1"
                ),
                "stratum_type": "month",
                "stratum_value": "1",
                "n_source_rows": 80,
                "mean_interpretability_score": 0.7,
                "physical_signature": "southerly_flow;windy",
                "wind_dir_deg_mean": 180.0,
                "wind_speed_mean": 15.0,
                "qnh_hpa_mean": 1007.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp_mean": -0.4,
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_v2_assignment_artifacts_use_distance_softmax_probabilities():
    artifacts = build_regime_candidate_v2_assignment_artifacts(
        _candidate_v2_rows(),
        _feature_rows(n_days=4),
        _label_rows(n_days=4),
        _obs_rows(n_days=4),
        tz_name="UTC",
    )

    assignments = artifacts["regime_candidate_assignments_v2"]
    ontology = artifacts["regime_candidate_ontology_v2"]
    audit = artifacts["regime_candidate_assignment_audit_v2"]
    row = assignments.row(0, named=True)
    component_probs = json.loads(row["component_probabilities"])
    family_probs = json.loads(row["family_probabilities"])

    assert assignments.height == 4
    assert ontology.height == 2
    assert row["component_argmax"] in component_probs
    assert abs(sum(component_probs.values()) - 1.0) < 1e-9
    assert abs(sum(family_probs.values()) - 1.0) < 1e-9
    assert row["candidate_regime_label"] == row["macro_regime_label"]
    assert row["component_entropy"] >= 0.0
    assert 0.0 <= row["component_margin"] <= 1.0
    assert 0.0 <= row["assignment_confidence"] <= 1.0
    assert row["causal_window"] == "valid < CP"
    assert row["production_status"] == "NOT_PRODUCTION"
    assert audit.filter(pl.col("audit_item") == "soft_assignment_probabilities").row(
        0,
        named=True,
    )["status"] == "PASS"


def test_write_regime_candidate_v2_validation_artifacts(tmp_path: Path):
    artifacts = {
        "regime_candidate_assignments_v2": pl.DataFrame(
            [
                {
                    "date_local": dt.date(2025, 1, 1),
                    "cp": "20:00",
                    "macro_regime_label": "macro_nw_continuum",
                    "subtype_label": "subtype_standard_nw",
                    "candidate_regime_label": "macro_nw_continuum",
                    "source_candidate_id": "RDC-V2-0001",
                    "component_argmax": "macro_nw_continuum:subtype_standard_nw:month:1",
                    "component_probabilities": (
                        "{\"macro_nw_continuum:subtype_standard_nw:month:1\": 1.0}"
                    ),
                    "family_probabilities": "{\"macro_nw_continuum\": 1.0}",
                    "component_entropy": 0.0,
                    "component_margin": 1.0,
                    "nearest_alternative_macro": "",
                    "distance_to_candidate": 0.0,
                    "distance_to_alternative": None,
                    "assignment_confidence": 1.0,
                    "low_confidence_flag": False,
                    "causal_window": "valid < CP",
                    "production_status": "NOT_PRODUCTION",
                }
            ],
            strict=False,
        ),
        "regime_candidate_ontology_v2": pl.DataFrame(
            [
                {
                    "macro_regime_label": "macro_nw_continuum",
                    "subtype_label": "subtype_standard_nw",
                    "latent_component_id": "macro_nw_continuum:subtype_standard_nw:month:1",
                    "source_candidate_id": "RDC-V2-0001",
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "n_source_rows": 100,
                    "production_status": "NOT_PRODUCTION",
                }
            ]
        ),
        "regime_candidate_assignment_audit_v2": pl.DataFrame(
            [{"audit_item": "soft_assignment_probabilities", "status": "PASS", "detail": "ok"}]
        ),
        "regime_candidate_r2_validation": pl.DataFrame(
            [
                {
                    "regime": "macro_nw_continuum",
                    "hypothesis_id": "H",
                    "feature_column": "feat",
                    "cp": "20:00",
                    "passes": True,
                    "n_days": 10,
                    "status": "validated",
                }
            ]
        ),
        "regime_candidate_v1_v2_comparison": pl.DataFrame(
            [
                {
                    "candidate_version": "v2",
                    "macro_regime_label": "macro_nw_continuum",
                    "assignment_rows": 1,
                    "r2_rows": 1,
                    "r2_pass_rows": 1,
                    "r2_dead_status": "PASS",
                    "protected_regression_flag": False,
                    "low_confidence_share": 0.0,
                    "mean_component_entropy": 0.0,
                    "mean_component_margin": 1.0,
                    "smallest_cp_support": 1,
                    "v1_dead_regimes": 1,
                    "v2_dead_regimes": 0,
                    "protected_regressions": "",
                    "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                    "production_status": "EXPERIMENT_ONLY",
                }
            ]
        ),
    }

    paths = write_regime_candidate_v2_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "regime_candidate_assignments_v2.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v2.csv").exists()
    assert (tmp_path / "regime_candidate_assignment_audit_v2.csv").exists()
    assert (tmp_path / "regime_candidate_r2_validation_v2.csv").exists()
    assert (tmp_path / "regime_candidate_v1_v2_comparison.csv").exists()
    report = paths["regime_candidate_v2_validation_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Candidate v2 Validation - 2026-06-07" in report
    assert "not a production classifier" in report


def test_regime_design_v2_validate_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    candidate_v2_path = tmp_path / "regime_design_candidate_v2.csv"
    v1_r2_path = tmp_path / "regime_candidate_r2_validation.csv"
    output_dir = tmp_path / "regime-design"
    features = _feature_rows(n_days=4)
    features.write_parquet(features_path)
    _label_rows(n_days=4).write_parquet(labels_path)
    _obs_rows(n_days=4).write_parquet(obs_path)
    _candidate_v2_rows().write_csv(candidate_v2_path)
    pl.DataFrame(
        [
            {
                "regime": "candidate_maritime_cloudy",
                "hypothesis_id": "H",
                "feature_column": "feat",
                "cp": "20:00",
                "passes": False,
                "n_days": 0,
                "status": "rejected",
            }
        ]
    ).write_csv(v1_r2_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v2-validate",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--candidate-v2-path",
            str(candidate_v2_path),
            "--v1-r2-path",
            str(v1_r2_path),
            "--output-dir",
            str(output_dir),
            "--tz-name",
            "UTC",
            "--cp-set",
            "20:00",
            "--min-assignment-rows",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_candidate_assignments_v2.csv").exists()
    assert (output_dir / "regime_candidate_r2_validation_v2.csv").exists()
    assert (output_dir / "regime_candidate_v1_v2_comparison.csv").exists()
    assert (output_dir / "regime_candidate_v2_validation_report.md").exists()
    persisted = pl.read_parquet(features_path)
    assert persisted.shape == features.shape
    assert persisted.to_dicts() == features.to_dicts()


def _v2_assignments_for_absorption() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "subtype_label": "subtype_transition_low_confidence",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "source_candidate_id": "RDC-V1-MONTH-1-C00",
                "component_argmax": "RDC-V1-MONTH-1-C00",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-1-C00": 1.0}),
                "family_probabilities": json.dumps(
                    {"macro_light_marine_or_residual": 0.6, "macro_nw_continuum": 0.4}
                ),
                "component_entropy": 1.1,
                "component_margin": 0.1,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 0.3,
                "distance_to_alternative": 0.4,
                "assignment_confidence": 0.6,
                "low_confidence_flag": True,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "candidate_regime_label": "macro_southerly_flow",
                "source_candidate_id": "RDC-V1-MONTH-1-C01",
                "component_argmax": "RDC-V1-MONTH-1-C01",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-1-C01": 1.0}),
                "family_probabilities": json.dumps({"macro_southerly_flow": 1.0}),
                "component_entropy": 0.2,
                "component_margin": 0.8,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 0.2,
                "distance_to_alternative": 1.0,
                "assignment_confidence": 0.9,
                "low_confidence_flag": False,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_regime_design_v21_validate_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    assignments_v2_path = tmp_path / "regime_candidate_assignments_v2.csv"
    r2_v2_path = tmp_path / "regime_candidate_r2_validation_v2.csv"
    output_dir = tmp_path / "regime-design"
    features = _feature_rows(n_days=4)
    features.write_parquet(features_path)
    _label_rows(n_days=4).write_parquet(labels_path)
    _v2_assignments_for_absorption().write_csv(assignments_v2_path)
    pl.DataFrame(
        [
            {"regime": "macro_light_marine_or_residual", "passes": False, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    ).write_csv(r2_v2_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v21-validate",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--assignments-v2-path",
            str(assignments_v2_path),
            "--r2-v2-path",
            str(r2_v2_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_candidate_assignments_v2_1.csv").exists()
    assert (output_dir / "regime_candidate_r2_validation_v2_1.csv").exists()
    assert (output_dir / "regime_candidate_v2_v21_comparison.csv").exists()
    persisted = pl.read_parquet(features_path)
    assert persisted.shape == features.shape
    assert persisted.to_dicts() == features.to_dicts()


def test_compare_regime_candidate_v2_v21_reports_absorption_decision():
    v2_r2 = pl.DataFrame(
        [
            {"regime": "macro_light_marine_or_residual", "passes": False, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )
    v21_r2 = pl.DataFrame(
        [
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )
    assignments_v21 = pl.DataFrame(
        [
            {
                "macro_regime_label": "macro_nw_continuum",
                "candidate_regime_label": "macro_nw_continuum",
                "absorbed_from_residual": True,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "macro_regime_label": "macro_southerly_flow",
                "candidate_regime_label": "macro_southerly_flow",
                "absorbed_from_residual": False,
                "production_status": "NOT_PRODUCTION",
            },
        ]
    )
    diagnostics = pl.DataFrame(
        [
            {
                "diagnostic_item": "invalid_absorption_targets",
                "status": "PASS",
                "detail": "0 invalid",
                "n_rows": 0,
                "production_status": "EXPERIMENT_ONLY",
            }
        ]
    )

    artifacts = compare_regime_candidate_v2_v21(
        v2_r2=v2_r2,
        v21_r2=v21_r2,
        v21_assignments=assignments_v21,
        residual_diagnostics=diagnostics,
        v2_regimes=(
            "macro_light_marine_or_residual",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        protected_v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
    )

    comparison = artifacts["regime_candidate_v2_v21_comparison"]
    assert comparison.height == 2
    assert set(comparison["decision_update"]) == {"READY_FOR_FULL_ONDA4_RERUN"}
    assert set(comparison["v2_dead_regimes"]) == {1}
    assert set(comparison["v21_dead_regimes"]) == {0}
    assert set(comparison["production_status"]) == {"EXPERIMENT_ONLY"}
    nw = comparison.filter(pl.col("macro_regime_label") == "macro_nw_continuum").row(
        0,
        named=True,
    )
    assert nw["absorbed_residual_rows"] == 1


def test_write_regime_candidate_v21_validation_artifacts(tmp_path: Path):
    artifacts = {
        "regime_candidate_r2_validation": pl.DataFrame(
            [
                {
                    "regime": "macro_nw_continuum",
                    "hypothesis_id": "H",
                    "feature_column": "feat",
                    "cp": "20:00",
                    "passes": True,
                    "n_days": 10,
                    "status": "validated",
                }
            ]
        ),
        "regime_candidate_v2_v21_comparison": pl.DataFrame(
            [
                {
                    "candidate_version": "v2.1",
                    "macro_regime_label": "macro_nw_continuum",
                    "assignment_rows": 2,
                    "absorbed_residual_rows": 1,
                    "r2_rows": 1,
                    "r2_pass_rows": 1,
                    "r2_dead_status": "PASS",
                    "v2_dead_regimes": 1,
                    "v21_dead_regimes": 0,
                    "protected_regression_flag": False,
                    "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                    "production_status": "EXPERIMENT_ONLY",
                }
            ]
        ),
    }

    paths = write_regime_candidate_v21_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_candidate_r2_validation_v2_1.csv").exists()
    assert (tmp_path / "regime_candidate_v2_v21_comparison.csv").exists()
    assert (tmp_path / "regime_candidate_v21_validation_report.md").exists()
    report = paths["regime_candidate_v21_validation_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Candidate v2.1 Validation - 2026-06-08" in report
    assert "not a production classifier" in report
