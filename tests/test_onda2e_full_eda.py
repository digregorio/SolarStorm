from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda2e import (
    apply_decision_updates,
    build_decision_gate_artifacts,
    build_full_eda_artifacts,
    build_regime_design_decision_updates,
    build_thesis_domain_eda_artifacts,
    build_thesis_domain_eda_decision_updates,
    parse_thesis_atlas,
    refresh_full_eda_decision_review,
    thesis_testability_audit,
    write_full_eda_artifacts,
    write_thesis_domain_eda_artifacts,
)


def _feature_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in (2024, 2025):
        for month in (1, 2):
            for day in range(1, 8):
                date_local = dt.date(year, month, day)
                rows.append(
                    {
                        "date_local": date_local,
                        "cp": "20:00",
                        "regime_label": "southerly_disrupted" if day % 2 else "standard_nw",
                        "slope_3h": float(day % 3),
                        "dewpoint_depression": float(4 + day),
                        "pressure_trend_3h": float(day - 3),
                        "cloud_cover_suppression": float(day % 4),
                        "precip_disruption": 1 if day == 3 else 0,
                        "foehn_score": float(day * 10),
                        "warming_rate_06_09": float(day) / 2.0,
                    }
                )
    return pl.DataFrame(rows)


def _label_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in (2024, 2025):
        for month in (1, 2):
            for day in range(1, 8):
                date_local = dt.date(year, month, day)
                rows.append(
                    {
                        "date_local": date_local,
                        "tmax_int": 20 + month + day + (year - 2024),
                        "tmax_hour": 14 + (day % 4),
                        "k_cp__cp_2000": 17 + day,
                    }
                )
    return pl.DataFrame(rows)


def _obs_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in (2024, 2025):
        for month in (1, 2):
            for day in range(1, 8):
                date_local = dt.date(year, month, day)
                for hour in (0, 3, 6, 9):
                    rows.append(
                        {
                            "date_local": date_local,
                            "valid": dt.datetime(year, month, day, hour, tzinfo=dt.UTC),
                            "ts_local": dt.datetime(year, month, day, hour),
                            "tmp_c_int": 12 + day + hour // 3,
                            "dwp_c_int": 8 + day,
                            "dw_depression_c_int": 4 + hour // 3,
                            "drct": float((day * 35 + hour * 4) % 360),
                            "sknt": float(5 + day),
                            "relh": float(60 + day),
                            "alti": float(29.7 + day / 100),
                            "p01i": 0.01 if day == 3 else 0.0,
                            "wxcodes": "RA" if day == 3 else "",
                            "skyc1": "BKN" if day % 2 else "CLR",
                        }
                    )
    return pl.DataFrame(rows)


def _single_year_feature_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for month in (1, 2):
        for day in range(1, 8):
            date_local = dt.date(2025, month, day)
            rows.append(
                {
                    "date_local": date_local,
                    "cp": "20:00",
                    "regime_label": "southerly_disrupted" if day % 2 else "standard_nw",
                    "slope_3h": float(day % 3),
                    "dewpoint_depression": float(4 + day),
                    "pressure_trend_3h": float(day - 3),
                    "cloud_cover_suppression": float(day % 4),
                    "precip_disruption": 1 if day == 3 else 0,
                    "foehn_score": float(day * 10),
                    "warming_rate_06_09": float(day) / 2.0,
                }
            )
    return pl.DataFrame(rows)


def _single_year_label_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for month in (1, 2):
        for day in range(1, 8):
            date_local = dt.date(2025, month, day)
            rows.append(
                {
                    "date_local": date_local,
                    "tmax_int": 20 + month + day,
                    "tmax_hour": 14 + (day % 4),
                    "k_cp__cp_2000": 17 + day,
                }
            )
    return pl.DataFrame(rows)


def _single_year_obs_rows() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for month in (1, 2):
        for day in range(1, 8):
            date_local = dt.date(2025, month, day)
            for hour in (0, 3, 6, 9):
                rows.append(
                    {
                        "date_local": date_local,
                        "valid": dt.datetime(2025, month, day, hour, tzinfo=dt.UTC),
                        "ts_local": dt.datetime(2025, month, day, hour),
                        "tmp_c_int": 12 + day + hour // 3,
                        "dwp_c_int": 8 + day,
                        "dw_depression_c_int": 4 + hour // 3,
                        "drct": float((day * 35 + hour * 4) % 360),
                        "sknt": float(5 + day),
                        "relh": float(60 + day),
                        "alti": float(29.7 + day / 100),
                        "p01i": 0.01 if day == 3 else 0.0,
                        "wxcodes": "RA" if day == 3 else "",
                        "skyc1": "BKN" if day % 2 else "CLR",
                    }
                )
    return pl.DataFrame(rows)


def test_full_eda_artifacts_review_all_theses_and_manifest_inputs():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)

    artifacts = build_full_eda_artifacts(
        theses,
        testability,
        gate["evidence_decision_register"],
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
    )

    review = artifacts["full_thesis_review"]
    assert review.height == 251
    assert review["thesis_id"].n_unique() == 251
    assert {"BLOCKED_EXTERNAL_DATA", "REGIME_ARCHITECTURE_REQUIRED"} <= set(
        review.get_column("review_status")
    )
    assert (
        review.filter(pl.col("thesis_id") == "WCT-REGIME-016")
        .get_column("implementation_path")
        .item()
        == "regime_architecture_experiment"
    )

    manifest = artifacts["regime_cluster_input_manifest"]
    assert {"drct_sin_mean", "drct_cos_mean", "sknt_mean", "qnh_hpa_mean"} <= set(
        manifest.get_column("feature")
    )
    excluded = manifest.filter(~pl.col("included_in_clustering"))
    assert "tmax_int" in set(excluded.get_column("feature"))
    assert "regime_label" in set(excluded.get_column("feature"))

    next_experiments = artifacts["domain_eda_next_experiments"]
    blocked_review = review.filter(pl.col("decision_status") == "BLOCKED")
    assert next_experiments.height == blocked_review.height
    assert {
        "thesis_id",
        "domain",
        "blocker",
        "required_artifact",
        "recommended_experiment",
    }.issubset(next_experiments.columns)
    regime_016 = next_experiments.filter(pl.col("thesis_id") == "WCT-REGIME-016").row(
        0,
        named=True,
    )
    assert regime_016["domain"] == "REGIME"
    assert regime_016["required_artifact"] == "reports/onda2e/regime_design_candidate_v1.csv"


def test_regime_architecture_sweep_emits_month_and_season_rows():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)

    artifacts = build_full_eda_artifacts(
        theses,
        testability,
        gate["evidence_decision_register"],
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
        k_values=(2, 3),
        min_cluster_rows=2,
    )

    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    assert {"month", "season"} <= set(sweep.get_column("stratum_type"))
    assert {2, 3} <= set(sweep.get_column("k"))
    assert {"silhouette_mean", "bic_approx", "eta2_tmax_anomaly"} <= set(sweep.columns)

    profiles = artifacts["regime_cluster_profiles"]
    assert profiles.height > 0
    assert {"wind_speed_mean", "qnh_hpa_mean", "tmax_anomaly_mean"} <= set(profiles.columns)


def test_write_full_eda_artifacts_exports_csvs_and_reports(tmp_path: Path):
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)
    artifacts = build_full_eda_artifacts(
        theses,
        testability,
        gate["evidence_decision_register"],
        _single_year_feature_rows(),
        _single_year_label_rows(),
        _single_year_obs_rows(),
        tz_name="UTC",
        k_values=(2,),
        min_cluster_rows=2,
    )

    paths = write_full_eda_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "full_thesis_review.csv").exists()
    assert (tmp_path / "regime_cluster_sweep_by_month_season.csv").exists()
    assert (tmp_path / "regime_cluster_stability_by_year_bootstrap.csv").exists()
    assert (tmp_path / "regime_cluster_physical_interpretation.csv").exists()
    assert (tmp_path / "regime_design_candidate_v1.csv").exists()
    assert (tmp_path / "regime_design_candidate_v1.md").exists()
    assert (tmp_path / "domain_eda_next_experiments.csv").exists()
    assert (tmp_path / "onda2e_full_eda_report.md").exists()
    assert (tmp_path / "regime_architecture_sprint_report.md").exists()
    report = paths["full_eda_report_md"].read_text(encoding="utf-8")
    assert "Onda 2E Full EDA Sprint Report" in report
    assert "251" in report
    assert "No production feature, model, or regime classifier is promoted" in report
    candidate_report = paths["regime_design_candidate_md"].read_text(encoding="utf-8")
    assert "Regime Design Candidate v1" in candidate_report
    assert "not a production classifier" in candidate_report


def test_write_full_eda_candidate_report_tolerates_null_optional_metrics(tmp_path: Path):
    artifacts = {
        "full_thesis_review": pl.DataFrame(
            {
                "thesis_id": ["WCT-REGIME-016"],
                "review_status": ["READY_FOR_REGIME_DESIGN_REVIEW"],
            }
        ),
        "regime_cluster_input_manifest": pl.DataFrame({"feature": []}),
        "regime_cluster_sweep_by_month_season": pl.DataFrame(
            [
                {
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "k": 6,
                    "n_rows": 40,
                    "smallest_cluster_rows": 30,
                    "bic_approx": 100.0,
                    "silhouette_mean": None,
                    "eta2_tmax_anomaly": None,
                    "underpowered_cluster": False,
                }
            ]
        ),
        "regime_cluster_profiles": pl.DataFrame({"placeholder": []}),
        "regime_cluster_outcome_audit": pl.DataFrame({"placeholder": []}),
        "regime_cluster_stability_by_year_bootstrap": pl.DataFrame({"placeholder": []}),
        "regime_cluster_physical_interpretation": pl.DataFrame({"placeholder": []}),
        "regime_cluster_leakage_audit": pl.DataFrame(
            {"audit_item": ["candidate_report"], "status": ["PASS"], "detail": ["null-safe"]}
        ),
        "regime_design_candidate_v1": pl.DataFrame({"placeholder": []}),
        "domain_eda_next_experiments": pl.DataFrame({"placeholder": []}),
    }

    paths = write_full_eda_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    candidate_report = paths["regime_design_candidate_md"].read_text(encoding="utf-8")
    assert "| month=1 | 6 | 40 | 30 | 100.0 |  |  |" in candidate_report


def test_regime_architecture_stability_and_physical_interpretation_are_reported():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)

    artifacts = build_full_eda_artifacts(
        theses,
        testability,
        gate["evidence_decision_register"],
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
        k_values=(2, 3),
        min_cluster_rows=2,
    )

    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    assert stability.height > 0
    assert {"year", "best_k_by_bic", "best_k_matches_all_year"}.issubset(stability.columns)
    assert {2024, 2025} <= set(stability.get_column("year"))

    interpretation = artifacts["regime_cluster_physical_interpretation"]
    assert interpretation.height > 0
    assert {
        "physical_signature",
        "interpretability_score",
        "candidate_regime_family",
        "promotion_readiness",
    }.issubset(interpretation.columns)
    assert set(interpretation.get_column("promotion_readiness")) <= {
        "design_evidence_only",
        "underpowered",
    }


def test_regime_design_candidate_promotes_k6_to_design_gate_only():
    artifacts = {
        "regime_cluster_sweep_by_month_season": pl.DataFrame(
            [
                {
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "k": 4,
                    "n_rows": 120,
                    "n_features": 8,
                    "min_cluster_rows": 30,
                    "smallest_cluster_rows": 24,
                    "underpowered_cluster": True,
                    "sse": 180.0,
                    "aic_approx": 240.0,
                    "bic_approx": 260.0,
                    "silhouette_mean": 0.21,
                    "eta2_tmax_anomaly": 0.10,
                    "eta2_remaining_warming": 0.08,
                    "converged": True,
                },
                {
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "k": 6,
                    "n_rows": 120,
                    "n_features": 8,
                    "min_cluster_rows": 30,
                    "smallest_cluster_rows": 31,
                    "underpowered_cluster": False,
                    "sse": 120.0,
                    "aic_approx": 180.0,
                    "bic_approx": 190.0,
                    "silhouette_mean": 0.29,
                    "eta2_tmax_anomaly": 0.18,
                    "eta2_remaining_warming": 0.16,
                    "converged": True,
                },
                {
                    "stratum_type": "season",
                    "stratum_value": "DJF",
                    "k": 5,
                    "n_rows": 220,
                    "n_features": 8,
                    "min_cluster_rows": 30,
                    "smallest_cluster_rows": 34,
                    "underpowered_cluster": False,
                    "sse": 260.0,
                    "aic_approx": 310.0,
                    "bic_approx": 330.0,
                    "silhouette_mean": 0.24,
                    "eta2_tmax_anomaly": 0.14,
                    "eta2_remaining_warming": 0.11,
                    "converged": True,
                },
                {
                    "stratum_type": "season",
                    "stratum_value": "DJF",
                    "k": 6,
                    "n_rows": 220,
                    "n_features": 8,
                    "min_cluster_rows": 30,
                    "smallest_cluster_rows": 38,
                    "underpowered_cluster": False,
                    "sse": 190.0,
                    "aic_approx": 250.0,
                    "bic_approx": 270.0,
                    "silhouette_mean": 0.30,
                    "eta2_tmax_anomaly": 0.19,
                    "eta2_remaining_warming": 0.15,
                    "converged": True,
                },
            ]
        ),
        "regime_cluster_stability_by_year_bootstrap": pl.DataFrame(
            [
                {
                    "stratum_type": "month",
                    "stratum_value": "1",
                    "year": 2024,
                    "best_k_by_bic": 6,
                    "all_year_best_k_by_bic": 6,
                    "best_k_matches_all_year": True,
                    "n_rows": 60,
                    "smallest_cluster_rows": 30,
                    "eta2_tmax_anomaly": 0.17,
                    "stability_note": "Year best-k matches all-year best-k.",
                },
                {
                    "stratum_type": "season",
                    "stratum_value": "DJF",
                    "year": 2024,
                    "best_k_by_bic": 6,
                    "all_year_best_k_by_bic": 6,
                    "best_k_matches_all_year": True,
                    "n_rows": 110,
                    "smallest_cluster_rows": 35,
                    "eta2_tmax_anomaly": 0.18,
                    "stability_note": "Year best-k matches all-year best-k.",
                },
            ]
        ),
        "regime_cluster_physical_interpretation": pl.DataFrame(
            [
                {
                    "stratum_type": "season",
                    "stratum_value": "DJF",
                    "k": 6,
                    "cluster_id": cluster_id,
                    "n_rows": 38,
                    "physical_signature": "northerly_nw_flow;dry_air",
                    "candidate_regime_family": "strong_nw_foehn_candidate",
                    "interpretability_score": 0.65,
                    "dominant_current_regime": "standard_nw",
                    "promotion_readiness": "design_evidence_only",
                }
                for cluster_id in range(6)
            ]
        ),
        "regime_cluster_profiles": pl.DataFrame(
            [{"stratum_type": "season", "stratum_value": "DJF", "k": 6, "cluster_id": i}
             for i in range(6)]
        ),
    }

    updates = build_regime_design_decision_updates(artifacts)

    assert updates.height == 1
    update = updates.row(0, named=True)
    assert update["item_id"] == "WCT-REGIME-016"
    assert update["decision_status"] == "PROMOTED_TO_REGIME_DESIGN"
    assert "regime_design_candidate_v1.csv" in update["source_artifact"]
    assert "k=6" in update["decision_rationale"]
    assert "Onda 4" in update["next_allowed_action"]

    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)
    updated_gate = apply_decision_updates(gate, updates)
    decision = updated_gate["evidence_decision_register"].filter(
        pl.col("item_id") == "WCT-REGIME-016"
    ).row(0, named=True)
    assert decision["decision_status"] == "PROMOTED_TO_REGIME_DESIGN"
    assert "WCT-REGIME-016" in set(
        updated_gate["regime_design_queue"].get_column("source_item_id")
    )


def test_refresh_full_eda_decision_review_updates_blocked_matrix_after_gate_change():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, testability)
    artifacts = build_full_eda_artifacts(
        theses,
        testability,
        gate["evidence_decision_register"],
        _single_year_feature_rows(),
        _single_year_label_rows(),
        _single_year_obs_rows(),
        tz_name="UTC",
        k_values=(2,),
        min_cluster_rows=2,
    )
    assert "WCT-REGIME-016" in set(
        artifacts["domain_eda_next_experiments"].get_column("thesis_id")
    )
    updates = pl.DataFrame(
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
                "sample_size_warning": "design-only",
                "causal_availability": "pre-CP only",
                "leakage_risk": "no production classifier change",
                "decision_rationale": "k=6 candidate enters design review.",
                "next_allowed_action": "Enter regime_design_queue only.",
            }
        ]
    )
    updated_gate = apply_decision_updates(gate, updates)

    refreshed = refresh_full_eda_decision_review(
        artifacts,
        theses,
        testability,
        updated_gate["evidence_decision_register"],
    )

    regime_016 = refreshed["full_thesis_review"].filter(
        pl.col("thesis_id") == "WCT-REGIME-016"
    ).row(0, named=True)
    assert regime_016["review_status"] == "READY_FOR_REGIME_DESIGN_REVIEW"
    assert "WCT-REGIME-016" not in set(
        refreshed["domain_eda_next_experiments"].get_column("thesis_id")
    )


def test_thesis_domain_eda_removes_external_and_resolves_local_theses(tmp_path: Path):
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    testability = thesis_testability_audit(theses)
    artifacts = build_thesis_domain_eda_artifacts(
        theses,
        testability,
        _feature_rows(),
        _label_rows(),
        _obs_rows(),
        tz_name="UTC",
    )
    updates = build_thesis_domain_eda_decision_updates(artifacts)

    evidence = artifacts["domain_thesis_evidence"]
    external = artifacts["removed_external_theses"]
    assert external.height == 6
    assert evidence.height == 245
    assert updates.height == 245
    assert updates.filter(pl.col("decision_status") == "BLOCKED").height == 0
    assert set(updates.get_column("decision_status")) >= {"SUPPORTED", "REJECTED"}
    assert "WCT-PRES-008" not in set(updates.get_column("item_id"))

    paths = write_thesis_domain_eda_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )
    assert (tmp_path / "domain_thesis_evidence.csv").exists()
    assert (tmp_path / "domain_thesis_decision_updates.csv").exists()
    assert (tmp_path / "removed_external_theses.csv").exists()
    assert "Removed external-data theses: 6" in paths["thesis_domain_report_md"].read_text(
        encoding="utf-8"
    )
