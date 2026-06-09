from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_v22_calm_radiative import (
    build_regime_v22_calm_radiative_artifacts,
    compare_regime_candidate_v21_v22,
    write_regime_v22_calm_radiative_artifacts,
)

runner = CliRunner()


def _v21_assignment_rows(n_days: int = 4) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(n_days):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=i)
        macro = "macro_nw_continuum" if i % 2 == 0 else "macro_southerly_flow"
        rows.append(
            {
                "candidate_version": "v2.1",
                "date_local": day,
                "cp": "20:00",
                "macro_regime_label": macro,
                "subtype_label": macro,
                "candidate_regime_label": macro,
                "source_candidate_id": f"RDC-V21-{i:02d}",
                "component_argmax": f"component-{i}",
                "component_probabilities": json.dumps({f"component-{i}": 1.0}),
                "family_probabilities": json.dumps({macro: 1.0}),
                "component_entropy": 0.2,
                "component_margin": 0.7,
                "nearest_alternative_macro": "macro_southerly_flow"
                if macro == "macro_nw_continuum"
                else "macro_nw_continuum",
                "distance_to_candidate": 0.3,
                "distance_to_alternative": 1.0,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "original_macro_regime_label": macro,
                "original_subtype_label": macro,
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )
    return pl.DataFrame(rows, strict=False)


def _physical_matrix() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "sknt_mean": 4.0,
                "relh_mean": 92.0,
                "dewpoint_depression_mean": 1.0,
                "cloud_cover_score_mean": 3.5,
                "temp_slope_pre_cp": 0.0,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "sknt_mean": 5.0,
                "relh_mean": 60.0,
                "dewpoint_depression_mean": 6.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp": 0.4,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "20:00",
                "sknt_mean": 18.0,
                "relh_mean": 70.0,
                "dewpoint_depression_mean": 4.0,
                "cloud_cover_score_mean": 2.0,
                "temp_slope_pre_cp": 0.2,
            },
            {
                "date_local": dt.date(2025, 1, 4),
                "cp": "20:00",
                "sknt_mean": 16.0,
                "relh_mean": 83.0,
                "dewpoint_depression_mean": 2.5,
                "cloud_cover_score_mean": 2.4,
                "temp_slope_pre_cp": 0.1,
            },
        ]
    )


def test_v22_restores_calm_radiative_from_physical_rule():
    artifacts = build_regime_v22_calm_radiative_artifacts(
        _v21_assignment_rows(),
        _physical_matrix(),
        min_assignment_rows=1,
    )

    assignments = artifacts["regime_candidate_assignments_v2_2"]
    ontology = artifacts["regime_candidate_ontology_v2_2"]
    audit = artifacts["regime_calm_radiative_reassignment_audit"]

    assert assignments.height == 4
    assert set(assignments["candidate_version"]) == {"v2.2"}
    assert set(assignments["production_status"]) == {"NOT_PRODUCTION"}
    assert "macro_calm_radiative" in set(assignments["macro_regime_label"])

    calm = assignments.filter(
        pl.col("macro_regime_label") == "macro_calm_radiative"
    ).row(0, named=True)
    assert calm["subtype_label"] == "subtype_calm_radiative"
    assert calm["candidate_regime_label"] == "macro_calm_radiative"
    assert calm["original_v21_macro_regime_label"] == "macro_nw_continuum"
    assert calm["reassigned_to_calm_radiative"] is True
    assert calm["calm_radiative_rule_score"] >= 3
    assert calm["assignment_confidence"] >= 0.7
    assert calm["low_confidence_flag"] is False

    calm_ontology = ontology.filter(
        pl.col("macro_regime_label") == "macro_calm_radiative"
    ).row(0, named=True)
    assert calm_ontology["assignment_rows"] == 1
    assert calm_ontology["reassigned_calm_radiative_rows"] == 1

    audit_items = set(audit["diagnostic_item"])
    assert "physical_thresholds" in audit_items
    assert "calm_radiative_candidate_rows" in audit_items
    assert audit.filter(pl.col("status") == "FAIL").height == 0


def test_v21_v22_comparison_protects_three_physical_macros():
    artifacts = build_regime_v22_calm_radiative_artifacts(
        _v21_assignment_rows(),
        _physical_matrix(),
        min_assignment_rows=1,
    )
    assignments = artifacts["regime_candidate_assignments_v2_2"]
    v21_r2 = pl.DataFrame(
        [
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )
    v22_r2 = pl.DataFrame(
        [
            {"regime": "macro_calm_radiative", "passes": True, "cp": "20:00"},
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    )

    comparison = compare_regime_candidate_v21_v22(
        v21_r2=v21_r2,
        v22_r2=v22_r2,
        v22_assignments=assignments,
        v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        v22_regimes=(
            "macro_calm_radiative",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        protected_v22_regimes=(
            "macro_calm_radiative",
            "macro_nw_continuum",
            "macro_southerly_flow",
        ),
        min_assignment_rows=1,
    )["regime_candidate_v21_v22_comparison"]

    assert comparison.height == 3
    assert set(comparison["candidate_version"]) == {"v2.2"}
    assert set(comparison["v22_dead_regimes"]) == {0}
    assert set(comparison["decision_update"]) == {"READY_FOR_FULL_ONDA4_RERUN"}
    assert set(comparison["production_status"]) == {"EXPERIMENT_ONLY"}


def test_write_regime_v22_artifacts(tmp_path: Path):
    artifacts = build_regime_v22_calm_radiative_artifacts(
        _v21_assignment_rows(),
        _physical_matrix(),
        min_assignment_rows=1,
    )
    comparison = compare_regime_candidate_v21_v22(
        v21_r2=pl.DataFrame(
            [{"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"}]
        ),
        v22_r2=pl.DataFrame(
            [{"regime": "macro_calm_radiative", "passes": True, "cp": "20:00"}]
        ),
        v22_assignments=artifacts["regime_candidate_assignments_v2_2"],
        v21_regimes=("macro_nw_continuum", "macro_southerly_flow"),
        v22_regimes=("macro_calm_radiative",),
        protected_v22_regimes=("macro_calm_radiative",),
        min_assignment_rows=1,
    )
    artifacts = {
        **artifacts,
        **comparison,
        "regime_candidate_r2_validation": pl.DataFrame(
            [{"regime": "macro_calm_radiative", "passes": True, "cp": "20:00"}]
        ),
    }

    paths = write_regime_v22_calm_radiative_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_candidate_assignments_v2_2.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v2_2.csv").exists()
    assert (
        tmp_path / "regime_calm_radiative_reassignment_audit_v1.csv"
    ).exists()
    assert (tmp_path / "regime_candidate_r2_validation_v2_2.csv").exists()
    assert (tmp_path / "regime_candidate_v21_v22_comparison.csv").exists()
    assert (tmp_path / "regime_candidate_v22_validation_report.md").exists()
    report = paths["regime_candidate_v22_validation_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Candidate v2.2 Validation - 2026-06-08" in report
    assert "not a production classifier" in report


def _feature_rows(n_days: int = 8) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=i),
                "cp": "20:00",
                "regime_label": "quarantined_baseline",
                "feat_signal": float(i),
            }
            for i in range(n_days)
        ]
    )


def _label_rows(n_days: int = 8) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1) + dt.timedelta(days=i),
                "day_complete": True,
                "tmax_int": 20 + (i % 5),
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            }
            for i in range(n_days)
        ]
    )


def _obs_rows(n_days: int = 8) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(n_days):
        day = dt.date(2025, 1, 1) + dt.timedelta(days=i)
        is_calm = i in {0, 4}
        for hour in (0, 3, 6, 9):
            rows.append(
                {
                    "date_local": day,
                    "valid": dt.datetime.combine(
                        day,
                        dt.time(hour),
                        tzinfo=dt.UTC,
                    ),
                    "ts_local": dt.datetime.combine(day, dt.time(hour)),
                    "tmp_c_int": 14 if is_calm else 16 + (hour // 3),
                    "dwp_c_int": 13 if is_calm else 8,
                    "dw_depression_c_int": 1 if is_calm else 8,
                    "drct": 20.0 if is_calm else (350.0 if i % 2 == 0 else 180.0),
                    "sknt": 4.0 if is_calm else (17.0 if i % 2 == 0 else 15.0),
                    "relh": 92.0 if is_calm else (60.0 if i % 2 == 0 else 85.0),
                    "alti": 29.90 if is_calm else 29.80,
                    "p01i": 0.0,
                    "skyc1": "BKN" if is_calm else "CLR",
                    "dq_tmp_c_int": "ok",
                }
            )
    return pl.DataFrame(rows)


def test_regime_design_v22_validate_cli_writes_artifacts(tmp_path: Path):
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    assignments_v21_path = tmp_path / "regime_candidate_assignments_v2_1.csv"
    r2_v21_path = tmp_path / "regime_candidate_r2_validation_v2_1.csv"
    output_dir = tmp_path / "regime-design"

    _feature_rows().write_parquet(features_path)
    _label_rows().write_parquet(labels_path)
    _obs_rows().write_parquet(obs_path)
    _v21_assignment_rows(n_days=8).write_csv(assignments_v21_path)
    pl.DataFrame(
        [
            {"regime": "macro_nw_continuum", "passes": True, "cp": "20:00"},
            {"regime": "macro_southerly_flow", "passes": True, "cp": "20:00"},
        ]
    ).write_csv(r2_v21_path)

    result = runner.invoke(
        app,
        [
            "regime-design-v22-validate",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--assignments-v21-path",
            str(assignments_v21_path),
            "--r2-v21-path",
            str(r2_v21_path),
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
    assert (output_dir / "regime_candidate_assignments_v2_2.csv").exists()
    assert (output_dir / "regime_candidate_ontology_v2_2.csv").exists()
    assert (output_dir / "regime_candidate_r2_validation_v2_2.csv").exists()
    assert (output_dir / "regime_candidate_v21_v22_comparison.csv").exists()
    assert (output_dir / "regime_candidate_v22_validation_report.md").exists()
