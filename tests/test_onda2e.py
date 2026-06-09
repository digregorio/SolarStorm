from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e import (
    apply_decision_updates,
    build_cooling_decision_updates,
    build_cooling_domain_artifacts,
    build_decision_gate_artifacts,
    build_prerequisite_artifacts,
    build_timing_decision_updates,
    build_timing_domain_artifacts,
    parse_thesis_atlas,
    remove_decision_items,
    thesis_testability_audit,
    write_cooling_domain_artifacts,
    write_decision_gate_artifacts,
    write_timing_domain_artifacts,
)

runner = CliRunner()


def test_parse_thesis_atlas_reads_official_251_theses():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))

    assert len(theses) == 251
    assert theses[0].id == "WCT-REGIME-001"
    assert theses[-1].id == "WCT-GAP-050"
    assert {t.domain for t in theses} >= {"REGIME", "COOLING", "WIND", "IX", "GAP"}
    spike = next(t for t in theses if t.id == "WCT-SPIKE-001")
    assert "q90_train(tmax_hour | month, regime)" in spike.claim
    assert spike.key_strata == "month, regime, q90 threshold"
    assert spike.status == "E0_candidate"


def test_testability_audit_flags_external_blocks_from_official_atlas():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))

    audit = thesis_testability_audit(theses)
    blocked = set(
        audit.filter(pl.col("testability") == "blocked_external_data")
        .get_column("id")
        .to_list()
    )
    missing_detail = set(
        audit.filter(pl.col("testability") == "registry_missing_detail")
        .get_column("id")
        .to_list()
    )

    assert len(audit) == 251
    assert "WCT-PRES-008" in blocked
    assert "WCT-GAP-024" in blocked
    assert "WCT-GAP-047" in blocked
    assert len(missing_detail) == 22
    assert "WCT-IX-001" in missing_detail
    assert "WCT-TIMING-017" in missing_detail


def test_prerequisite_artifacts_produce_power_and_timing_tables():
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "cp": "20:00", "regime_label": "standard_nw"},
            {"date_local": dt.date(2025, 1, 1), "cp": "21:00", "regime_label": "standard_nw"},
            {"date_local": dt.date(2025, 1, 2), "cp": "20:00", "regime_label": "calm_radiative"},
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "tmax_int": 24,
                "tmin_int": 14,
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
                "k_cp__cp_2100": 19,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "tmax_int": 21,
                "tmin_int": 12,
                "tmax_hour": 17,
                "k_cp__cp_2000": 16,
                "k_cp__cp_2100": 16,
            },
        ]
    )

    artifacts = build_prerequisite_artifacts(features, labels)

    assert artifacts["power_map"].height == 3
    assert artifacts["regime_frequency"].height == 3
    assert artifacts["tmax_hour_distribution"].height == 2
    assert artifacts["remaining_warming_distribution"].height == 3
    assert artifacts["tmax_anomaly_by_month"].height == 1


def test_prerequisite_artifacts_produce_wind_rose_and_cooling_taxonomy_with_obs():
    d = dt.date(2025, 1, 1)
    features = pl.DataFrame(
        [
            {"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"},
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": d,
                "tmax_int": 24,
                "tmin_int": 10,
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            },
        ]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "hour_local": 0,
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 3),
                "hour_local": 3,
                "tmp_c_int": 17,
                "dwp_c_int": 12,
                "drct": 20.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 6, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 6),
                "hour_local": 6,
                "tmp_c_int": 10,
                "dwp_c_int": 9,
                "drct": 30.0,
                "sknt": 4.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )

    artifacts = build_prerequisite_artifacts(features, labels, obs=obs, tz_name="UTC")

    assert artifacts["monthly_wind_rose"].height >= 1
    wind_row = artifacts["monthly_wind_rose"].row(0, named=True)
    assert {"month", "cp", "wind_sector", "n_obs", "share"}.issubset(wind_row)
    assert wind_row["wind_sector"] == "N"

    taxonomy = artifacts["cooling_mechanism_taxonomy"]
    assert taxonomy.height == 1
    row = taxonomy.row(0, named=True)
    assert row["cooling_mechanism"] == "radiative_pre_dawn"
    assert row["n_rows"] == 1
    assert row["underpowered_n_lt_30"] is True


def test_cooling_taxonomy_ignores_duplicate_timestamp_temperature_deltas():
    d = dt.date(2025, 1, 1)
    features = pl.DataFrame(
        [
            {"date_local": d, "cp": "20:00", "regime_label": "standard_nw"},
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": d,
                "tmax_int": 24,
                "tmin_int": 10,
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            },
        ]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "hour_local": 0,
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 3),
                "hour_local": 3,
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 3),
                "hour_local": 3,
                "tmp_c_int": 12,
                "dwp_c_int": 10,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 6, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 6),
                "hour_local": 6,
                "tmp_c_int": 11,
                "dwp_c_int": 10,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )

    artifacts = build_prerequisite_artifacts(features, labels, obs=obs, tz_name="UTC")

    row = artifacts["cooling_mechanism_taxonomy"].row(0, named=True)
    assert row["cooling_mechanism"] == "no_material_cooling"
    assert row["median_min_delta_t_per_h"] == -1 / 3


def test_cooling_taxonomy_uses_fractional_hours_for_half_hour_metars():
    d = dt.date(2025, 1, 1)
    features = pl.DataFrame(
        [
            {"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"},
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": d,
                "tmax_int": 24,
                "tmin_int": 10,
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            },
        ]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0, 0),
                "hour_local": 0,
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, 30, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0, 30),
                "hour_local": 0,
                "tmp_c_int": 16,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 1, 0),
                "hour_local": 1,
                "tmp_c_int": 16,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )

    artifacts = build_prerequisite_artifacts(features, labels, obs=obs, tz_name="UTC")

    row = artifacts["cooling_mechanism_taxonomy"].row(0, named=True)
    assert row["cooling_mechanism"] == "radiative_pre_dawn"
    assert row["median_min_delta_t_per_h"] == -4.0


def test_decision_gate_blocks_theses_and_quarantines_legacy_rules():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)

    gate = build_decision_gate_artifacts(theses, audit)

    decision_register = gate["evidence_decision_register"]
    thesis_decisions = decision_register.filter(pl.col("item_type") == "thesis")
    promoted = thesis_decisions.filter(
        pl.col("decision_status").is_in(
            ["SUPPORTED", "PROMOTED_TO_REGIME_DESIGN", "PROMOTED_TO_FEATURE_CANDIDATE"]
        )
    )
    quarantined = gate["quarantined_baseline_register"]
    regime_queue = gate["regime_design_queue"]

    assert thesis_decisions.height == 251
    assert set(decision_register.get_column("decision_status").unique()) <= {
        "BLOCKED",
        "QUARANTINED_BASELINE",
    }
    assert promoted.height == 0
    assert "WCT-IX-001" in set(
        thesis_decisions.filter(pl.col("decision_status") == "BLOCKED")
        .get_column("item_id")
        .to_list()
    )
    assert set(quarantined.get_column("rule_id")) >= {
        "REGIME_CLASSIFIER_CURRENT",
        "RULE_LATE_WARMING_FIXED_18",
        "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
        "RULE_FOEHN_SCORE_FIXED_60",
    }
    assert set(regime_queue.get_column("rule_id")) >= {
        "REGIME_CLASSIFIER_CURRENT",
        "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
    }


def test_timing_domain_artifacts_resolve_q90_prerequisite_and_fixed_18_rule():
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "cp": "20:00", "regime_label": "summer_foehn"},
            {"date_local": dt.date(2025, 1, 1), "cp": "21:00", "regime_label": "summer_foehn"},
            {"date_local": dt.date(2025, 1, 2), "cp": "20:00", "regime_label": "summer_foehn"},
            {"date_local": dt.date(2025, 1, 3), "cp": "20:00", "regime_label": "summer_foehn"},
            {"date_local": dt.date(2025, 6, 1), "cp": "20:00", "regime_label": "winter_calm"},
            {"date_local": dt.date(2025, 6, 2), "cp": "20:00", "regime_label": "winter_calm"},
            {"date_local": dt.date(2025, 6, 3), "cp": "20:00", "regime_label": "winter_calm"},
        ]
    )
    labels = pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "tmax_int": 25, "tmax_hour": 15},
            {"date_local": dt.date(2025, 1, 2), "tmax_int": 27, "tmax_hour": 18},
            {"date_local": dt.date(2025, 1, 3), "tmax_int": 28, "tmax_hour": 19},
            {"date_local": dt.date(2025, 6, 1), "tmax_int": 12, "tmax_hour": 12},
            {"date_local": dt.date(2025, 6, 2), "tmax_int": 13, "tmax_hour": 13},
            {"date_local": dt.date(2025, 6, 3), "tmax_int": 15, "tmax_hour": 14},
        ]
    )

    artifacts = build_timing_domain_artifacts(features, labels)
    norms = artifacts["timing_norms_by_month_regime"]
    sensitivity = artifacts["timing_fixed_18_sensitivity"]
    updates = build_timing_decision_updates(artifacts)

    assert norms.height == 2
    assert norms.filter(pl.col("regime_label") == "summer_foehn").row(0, named=True)[
        "n_context_days"
    ] == 3
    assert "fixed_18_late_rate" in sensitivity.columns
    assert sensitivity.filter(pl.col("regime_label") == "winter_calm").row(0, named=True)[
        "late_rule_disagree_rate"
    ] == 0.0
    assert set(updates.get_column("item_id")) == {
        "WCT-TIMING-001",
        "RULE_LATE_WARMING_FIXED_18",
    }
    assert updates.filter(pl.col("item_id") == "WCT-TIMING-001").row(0, named=True)[
        "decision_status"
    ] == "SUPPORTED"
    assert updates.filter(pl.col("item_id") == "RULE_LATE_WARMING_FIXED_18").row(
        0,
        named=True,
    )["decision_status"] == "ADAPTED"


def test_timing_decision_updates_replace_initial_gate_rows(tmp_path: Path):
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, audit)
    updates = pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-TIMING-001",
                "item_id": "WCT-TIMING-001",
                "item_type": "thesis",
                "domain": "TIMING",
                "decision_status": "SUPPORTED",
                "evidence_level": "E2_descriptive_domain",
                "source_artifact": "reports/onda2e/domain_timing_norms_by_month_regime.csv",
                "strata": "month x regime_label",
                "sample_size_warning": "1/2 cells have n < 30.",
                "causal_availability": "Evaluation target and train-only prior only.",
                "leakage_risk": "Would leak if computed from holdout/live labels.",
                "decision_rationale": "Timing norms table exists.",
                "next_allowed_action": "Use as prerequisite only.",
            }
        ]
    )

    updated_gate = apply_decision_updates(gate, updates)
    paths = write_decision_gate_artifacts(
        updated_gate,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )
    register = updated_gate["evidence_decision_register"]
    timing_decision = register.filter(pl.col("item_id") == "WCT-TIMING-001").row(
        0,
        named=True,
    )

    assert timing_decision["decision_status"] == "SUPPORTED"
    assert register.filter(pl.col("decision_status") == "BLOCKED").height == 250
    report_text = paths["decision_report_md"].read_text(encoding="utf-8")
    assert "SUPPORTED | 1" in report_text
    assert "Baseline-register entries: 5" in report_text


def test_regime_design_queue_includes_promoted_thesis_decisions():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, audit)
    updates = pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-COOL-003",
                "item_id": "WCT-COOL-003",
                "item_type": "thesis",
                "domain": "COOLING",
                "decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "evidence_level": "E2_descriptive_domain",
                "source_artifact": "reports/onda2e/cooling_effects_by_month_regime_cp.csv",
                "strata": "month x regime_label x CP",
                "sample_size_warning": "some cells underpowered",
                "causal_availability": "pre-CP classification only",
                "leakage_risk": "no live classifier change",
                "decision_rationale": "Cooling mechanisms enter regime design review.",
                "next_allowed_action": "Create regime repair candidate.",
            }
        ]
    )

    updated_gate = apply_decision_updates(gate, updates)
    queue = updated_gate["regime_design_queue"]

    assert "WCT-COOL-003" in set(queue.get_column("source_item_id"))
    assert queue.filter(pl.col("source_item_id") == "WCT-COOL-003").row(0, named=True)[
        "source_decision_status"
    ] == "PROMOTED_TO_REGIME_DESIGN"


def test_decision_updates_populate_rejection_register():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, audit)
    updates = pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-IX-001",
                "item_id": "WCT-IX-001",
                "item_type": "thesis",
                "domain": "IX",
                "decision_status": "REJECTED",
                "evidence_level": "E0_registry_gap",
                "source_artifact": "reports/onda2e/domain_thesis_evidence.csv",
                "strata": "registry",
                "sample_size_warning": "not testable",
                "causal_availability": "not available",
                "leakage_risk": "not assessed",
                "decision_rationale": "Registry lacks a testable thesis definition.",
                "next_allowed_action": "Do not use without an atlas repair and new evidence.",
            }
        ]
    )

    updated_gate = apply_decision_updates(gate, updates)
    rejection = updated_gate["rejection_register"]

    assert rejection.height == 1
    assert rejection.row(0, named=True)["item_id"] == "WCT-IX-001"


def test_remove_decision_items_recalculates_gate_queues():
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, audit)
    updates = pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-PRES-008",
                "item_id": "WCT-PRES-008",
                "item_type": "thesis",
                "domain": "PRES",
                "decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "evidence_level": "E2_descriptive_domain",
                "source_artifact": "reports/onda2e/test.csv",
                "strata": "month x CP",
                "sample_size_warning": "test",
                "causal_availability": "test",
                "leakage_risk": "test",
                "decision_rationale": "test promotion.",
                "next_allowed_action": "test queue.",
            }
        ]
    )

    promoted_gate = apply_decision_updates(gate, updates)
    trimmed_gate = remove_decision_items(
        promoted_gate,
        {"WCT-PRES-008"},
        item_type="thesis",
    )

    assert "WCT-PRES-008" not in set(
        trimmed_gate["evidence_decision_register"].get_column("item_id")
    )
    assert "WCT-PRES-008" not in set(
        trimmed_gate["regime_design_queue"].get_column("source_item_id")
    )
    assert trimmed_gate["regime_design_queue"].height == 5


def test_write_timing_domain_artifacts_exports_report(tmp_path: Path):
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "cp": "20:00", "regime_label": "standard_nw"},
        ]
    )
    labels = pl.DataFrame(
        [{"date_local": dt.date(2025, 1, 1), "tmax_int": 24, "tmax_hour": 15}]
    )
    artifacts = build_timing_domain_artifacts(features, labels)

    paths = write_timing_domain_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "domain_timing_norms_by_month_regime.csv").exists()
    assert (tmp_path / "domain_timing_fixed_18_sensitivity.csv").exists()
    assert (tmp_path / "domain_timing_bucket_priors.csv").exists()
    report_text = paths["timing_report_md"].read_text(encoding="utf-8")
    assert "Onda 2E Timing Domain EDA" in report_text
    assert "evaluation target" in report_text


def test_cooling_domain_artifacts_classify_event_effects_and_repair_candidates():
    d1 = dt.date(2025, 1, 1)
    d2 = dt.date(2025, 1, 2)
    features = pl.DataFrame(
        [
            {"date_local": d1, "cp": "20:00", "regime_label": "southerly_disrupted"},
            {"date_local": d2, "cp": "20:00", "regime_label": "standard_nw"},
        ]
    )
    labels = pl.DataFrame(
        [
            {"date_local": d1, "tmax_int": 19, "tmax_hour": 11, "k_cp__cp_2000": 18},
            {"date_local": d2, "tmax_int": 26, "tmax_hour": 15, "k_cp__cp_2000": 20},
        ]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d1,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 180.0,
                "sknt": 18.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d1,
                "valid": dt.datetime(2025, 1, 1, 1, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 1),
                "tmp_c_int": 15,
                "dwp_c_int": 13,
                "drct": 190.0,
                "sknt": 20.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d2,
                "valid": dt.datetime(2025, 1, 2, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 2, 0),
                "tmp_c_int": 16,
                "dwp_c_int": 10,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d2,
                "valid": dt.datetime(2025, 1, 2, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 2, 3),
                "tmp_c_int": 9,
                "dwp_c_int": 10,
                "drct": 20.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )

    artifacts = build_cooling_domain_artifacts(features, labels, obs, tz_name="UTC")
    events = artifacts["cooling_event_taxonomy_by_day_cp"]
    effects = artifacts["cooling_effects_by_month_regime_cp"]
    candidates = artifacts["regime_repair_candidates"]
    leakage = artifacts["cooling_power_leakage_audit"]

    assert events.height == 2
    assert set(events.get_column("cooling_mechanism")) >= {
        "southerly_frontal",
        "radiative_pre_dawn",
    }
    assert {"mean_remaining_warming", "mean_tmax_anomaly"}.issubset(effects.columns)
    assert "RULE_COOLING_FIXED_MINUS_2_C_PER_H" in set(candidates.get_column("source_rule_id"))
    assert leakage.filter(pl.col("audit_item") == "cp_slice_causal").row(0, named=True)[
        "status"
    ] == "PASS"


def test_cooling_decision_updates_promote_regime_design_not_features():
    d = dt.date(2025, 1, 1)
    features = pl.DataFrame(
        [{"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"}]
    )
    labels = pl.DataFrame(
        [{"date_local": d, "tmax_int": 19, "tmax_hour": 11, "k_cp__cp_2000": 18}]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 180.0,
                "sknt": 18.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 1, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 1),
                "tmp_c_int": 15,
                "dwp_c_int": 13,
                "drct": 190.0,
                "sknt": 20.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )
    artifacts = build_cooling_domain_artifacts(features, labels, obs, tz_name="UTC")

    updates = build_cooling_decision_updates(artifacts)

    assert set(updates.get_column("item_id")) >= {
        "WCT-COOL-001",
        "WCT-COOL-003",
        "RULE_COOLING_FIXED_MINUS_2_C_PER_H",
    }
    assert updates.filter(pl.col("item_id") == "RULE_COOLING_FIXED_MINUS_2_C_PER_H").row(
        0,
        named=True,
    )["decision_status"] == "ADAPTED"
    assert updates.filter(pl.col("decision_status") == "PROMOTED_TO_FEATURE_CANDIDATE").height == 0
    assert updates.filter(pl.col("decision_status") == "PROMOTED_TO_REGIME_DESIGN").height >= 1


def test_write_cooling_domain_artifacts_exports_report(tmp_path: Path):
    d = dt.date(2025, 1, 1)
    features = pl.DataFrame(
        [{"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"}]
    )
    labels = pl.DataFrame(
        [{"date_local": d, "tmax_int": 19, "tmax_hour": 11, "k_cp__cp_2000": 18}]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 180.0,
                "sknt": 18.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d,
                "valid": dt.datetime(2025, 1, 1, 1, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 1),
                "tmp_c_int": 15,
                "dwp_c_int": 13,
                "drct": 190.0,
                "sknt": 20.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )
    artifacts = build_cooling_domain_artifacts(features, labels, obs, tz_name="UTC")

    paths = write_cooling_domain_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "cooling_event_taxonomy_by_day_cp.csv").exists()
    assert (tmp_path / "cooling_effects_by_month_regime_cp.csv").exists()
    assert (tmp_path / "cooling_power_leakage_audit.csv").exists()
    assert (tmp_path / "regime_repair_candidates.csv").exists()
    report_text = paths["cooling_report_md"].read_text(encoding="utf-8")
    assert "Onda 2E Cooling-Regime Domain EDA" in report_text
    assert "No production classifier change" in report_text


def test_write_decision_gate_artifacts_exports_required_registers(tmp_path: Path):
    theses = parse_thesis_atlas(Path("reports/onda2e/thesis_atlas_v1.md"))
    audit = thesis_testability_audit(theses)
    gate = build_decision_gate_artifacts(theses, audit)

    paths = write_decision_gate_artifacts(
        gate,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "evidence_decision_register.csv").exists()
    assert (tmp_path / "regime_design_queue.csv").exists()
    assert (tmp_path / "feature_candidate_queue.csv").exists()
    assert (tmp_path / "rejection_register.csv").exists()
    assert (tmp_path / "quarantined_baseline_register.csv").exists()
    assert (tmp_path / "onda2e_decision_report.md").exists()
    report_text = paths["decision_report_md"].read_text(encoding="utf-8")
    assert "No thesis is promoted by prerequisite EDA alone" in report_text
    assert "QUARANTINED_BASELINE" in report_text
    assert "Active quarantined decision rows" in report_text
    assert "## Baseline Comparator Register" in report_text
    assert "Active quarantine is counted separately" in report_text
    assert "evidence_decision_register.csv and its downstream queues" in report_text
    assert "## Quarantined Baselines" not in report_text


def test_onda2e_cli_writes_registry_and_prerequisite_artifacts(tmp_path: Path):
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2025, 1, 1), "cp": "20:00", "regime_label": "standard_nw"},
            {"date_local": dt.date(2025, 1, 2), "cp": "20:00", "regime_label": "calm_radiative"},
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "tmax_int": 24,
                "tmin_int": 14,
                "tmax_hour": 15,
                "k_cp__cp_2000": 18,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "tmax_int": 21,
                "tmin_int": 12,
                "tmax_hour": 17,
                "k_cp__cp_2000": 16,
            },
        ]
    )
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    obs_path = tmp_path / "obs.parquet"
    output_dir = tmp_path / "onda2e"
    features.write_parquet(features_path)
    labels.write_parquet(labels_path)
    pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "hour_local": 0,
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": dt.date(2025, 1, 1),
                "valid": dt.datetime(2025, 1, 1, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 3),
                "hour_local": 3,
                "tmp_c_int": 17,
                "dwp_c_int": 12,
                "drct": 20.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": dt.date(2025, 1, 1),
                "valid": dt.datetime(2025, 1, 1, 6, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 6),
                "hour_local": 6,
                "tmp_c_int": 10,
                "dwp_c_int": 9,
                "drct": 30.0,
                "sknt": 4.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    ).write_parquet(obs_path)

    result = runner.invoke(
        app,
        [
            "onda2e",
            "--atlas-path",
            "reports/onda2e/thesis_atlas_v1.md",
            "--features-path",
            str(features_path),
            "--labels-path",
            str(labels_path),
            "--obs-path",
            str(obs_path),
            "--output-dir",
            str(output_dir),
            "--tz-name",
            "UTC",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "thesis_registry.csv").exists()
    assert (output_dir / "thesis_testability_audit.csv").exists()
    assert (output_dir / "prereq_power_map.csv").exists()
    assert (output_dir / "prereq_tmax_hour_distribution.csv").exists()
    assert (output_dir / "prereq_monthly_wind_rose.csv").exists()
    assert (output_dir / "prereq_cooling_mechanism_taxonomy.csv").exists()
    assert (output_dir / "onda2e_prerequisite_report.md").exists()
    assert (output_dir / "evidence_decision_register.csv").exists()
    assert (output_dir / "regime_design_queue.csv").exists()
    assert (output_dir / "feature_candidate_queue.csv").exists()
    assert (output_dir / "rejection_register.csv").exists()
    assert (output_dir / "quarantined_baseline_register.csv").exists()
    assert (output_dir / "onda2e_decision_report.md").exists()
    assert (output_dir / "domain_timing_norms_by_month_regime.csv").exists()
    assert (output_dir / "domain_timing_fixed_18_sensitivity.csv").exists()
    assert (output_dir / "domain_timing_bucket_priors.csv").exists()
    assert (output_dir / "onda2e_timing_report.md").exists()
    assert (output_dir / "cooling_event_taxonomy_by_day_cp.csv").exists()
    assert (output_dir / "cooling_effects_by_month_regime_cp.csv").exists()
    assert (output_dir / "cooling_power_leakage_audit.csv").exists()
    assert (output_dir / "regime_repair_candidates.csv").exists()
    assert (output_dir / "cooling_regime_domain_report.md").exists()
    assert (output_dir / "full_thesis_review.csv").exists()
    assert (output_dir / "regime_cluster_input_manifest.csv").exists()
    assert (output_dir / "regime_cluster_sweep_by_month_season.csv").exists()
    assert (output_dir / "regime_cluster_profiles.csv").exists()
    assert (output_dir / "regime_cluster_outcome_audit.csv").exists()
    assert (output_dir / "regime_cluster_stability_by_year_bootstrap.csv").exists()
    assert (output_dir / "regime_cluster_physical_interpretation.csv").exists()
    assert (output_dir / "regime_cluster_leakage_audit.csv").exists()
    assert (output_dir / "regime_design_candidate_v1.csv").exists()
    assert (output_dir / "regime_design_candidate_v1.md").exists()
    assert (output_dir / "domain_eda_next_experiments.csv").exists()
    assert (output_dir / "domain_thesis_evidence.csv").exists()
    assert (output_dir / "domain_thesis_decision_updates.csv").exists()
    assert (output_dir / "removed_external_theses.csv").exists()
    assert (output_dir / "onda2e_full_eda_report.md").exists()
    assert (output_dir / "regime_architecture_sprint_report.md").exists()
    decision_register = pl.read_csv(output_dir / "evidence_decision_register.csv")
    active_theses = decision_register.filter(pl.col("item_type") == "thesis")
    assert active_theses.height == 245
    assert active_theses.filter(pl.col("decision_status") == "BLOCKED").height == 0
    assert "WCT-PRES-008" not in set(active_theses.get_column("item_id"))
    full_review = pl.read_csv(output_dir / "full_thesis_review.csv")
    next_experiments = pl.read_csv(output_dir / "domain_eda_next_experiments.csv")
    assert full_review.height == 245
    assert full_review.filter(pl.col("decision_status") == "BLOCKED").height == 0
    assert full_review.filter(pl.col("review_status").str.starts_with("BLOCKED")).height == 0
    assert "GAP_AUDIT_REQUIRED" not in set(full_review.get_column("review_status"))
    assert "WCT-PRES-008" not in set(full_review.get_column("thesis_id"))
    assert next_experiments.height == 0
    report_text = (output_dir / "onda2e_prerequisite_report.md").read_text(encoding="utf-8")
    assert "Monthly Wind Rose Totals" in report_text
    assert "Cooling Mechanism Taxonomy Totals" in report_text
    decision_report_text = (output_dir / "onda2e_decision_report.md").read_text(encoding="utf-8")
    assert "Onda 2E-Gate Decision Report" in decision_report_text
    assert "SUPPORTED" in decision_report_text
    full_report_text = (output_dir / "onda2e_full_eda_report.md").read_text(encoding="utf-8")
    assert "unresolved rows remain explicitly blocked" not in full_report_text
