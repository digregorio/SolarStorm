from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda2e._foehn import (
    build_foehn_decision_updates,
    build_foehn_domain_artifacts,
    write_foehn_domain_artifacts,
)


def _synthetic_foehn_frames() -> tuple[pl.DataFrame, pl.DataFrame]:
    features = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "20:00",
                "regime_label": "strong_nw_foehn",
                "foehn_score": 70.0,
                "dewpoint_depression": 12.0,
                "dewpoint_collapse_rate_3h": 2.5,
                "nw_sector_not_foehn": 0,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "cp": "20:00",
                "regime_label": "standard_nw",
                "foehn_score": 65.0,
                "dewpoint_depression": 5.0,
                "dewpoint_collapse_rate_3h": 0.2,
                "nw_sector_not_foehn": 1,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "cp": "20:00",
                "regime_label": "standard_nw",
                "foehn_score": 25.0,
                "dewpoint_depression": 3.0,
                "dewpoint_collapse_rate_3h": 0.0,
                "nw_sector_not_foehn": 0,
            },
            {
                "date_local": dt.date(2025, 2, 1),
                "cp": "21:00",
                "regime_label": "standard_nw",
                "foehn_score": 55.0,
                "dewpoint_depression": 8.0,
                "dewpoint_collapse_rate_3h": 1.5,
                "nw_sector_not_foehn": 0,
            },
        ]
    )
    labels = pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 1, 1),
                "tmax_int": 28,
                "k_cp__cp_2000": 22,
                "k_cp__cp_2100": 21,
            },
            {
                "date_local": dt.date(2025, 1, 2),
                "tmax_int": 20,
                "k_cp__cp_2000": 19,
                "k_cp__cp_2100": 18,
            },
            {
                "date_local": dt.date(2025, 1, 3),
                "tmax_int": 24,
                "k_cp__cp_2000": 20,
                "k_cp__cp_2100": 20,
            },
            {
                "date_local": dt.date(2025, 2, 1),
                "tmax_int": 18,
                "k_cp__cp_2000": 17,
                "k_cp__cp_2100": 16,
            },
        ]
    )
    return features, labels


def test_foehn_domain_artifacts_bin_scores_and_audit_fixed_60():
    features, labels = _synthetic_foehn_frames()

    artifacts = build_foehn_domain_artifacts(features, labels)
    bins = artifacts["foehn_score_bins_by_month_cp"]
    false_positive = artifacts["foehn_false_positive_audit"]
    leakage = artifacts["foehn_power_leakage_audit"]
    candidates = artifacts["foehn_regime_repair_candidates"]

    jan_high = bins.filter(
        (pl.col("month") == 1)
        & (pl.col("cp") == "20:00")
        & (pl.col("foehn_score_bin") == "60_80")
    ).row(0, named=True)
    assert jan_high["n_rows"] == 2
    assert jan_high["mean_tmax_anomaly"] == 0.0
    assert jan_high["mean_remaining_warming"] == 3.5
    assert jan_high["underpowered_n_lt_30"] is True

    fp_row = false_positive.filter((pl.col("month") == 1) & (pl.col("cp") == "20:00")).row(
        0,
        named=True,
    )
    assert fp_row["n_fixed_60_trigger"] == 2
    assert fp_row["n_fixed_60_nw_sector_not_foehn"] == 1
    assert fp_row["fixed_60_nw_sector_not_foehn_share"] == 0.5
    assert fp_row["n_fixed_60_non_foehn_regime"] == 1
    assert "not final truth" in fp_row["audit_interpretation"]

    assert leakage.filter(pl.col("audit_item") == "outcome_usage").row(0, named=True)[
        "status"
    ] == "WARN"
    assert leakage.filter(pl.col("audit_item") == "future_observation_use").row(0, named=True)[
        "status"
    ] == "PASS"
    assert candidates.row(0, named=True)["source_rule_id"] == "RULE_FOEHN_SCORE_FIXED_60"
    assert "continuous" in candidates.row(0, named=True)["candidate_action"]


def test_foehn_decision_updates_adapt_fixed_score_rule_without_feature_promotion():
    features, labels = _synthetic_foehn_frames()
    artifacts = build_foehn_domain_artifacts(features, labels)

    updates = build_foehn_decision_updates(artifacts)

    assert set(updates.get_column("item_id")) == {
        "WCT-FOEHN-001",
        "RULE_FOEHN_SCORE_FIXED_60",
    }
    assert updates.filter(pl.col("item_id") == "RULE_FOEHN_SCORE_FIXED_60").row(
        0,
        named=True,
    )["decision_status"] == "ADAPTED"
    assert updates.filter(pl.col("item_id") == "WCT-FOEHN-001").row(0, named=True)[
        "decision_status"
    ] == "PROMOTED_TO_REGIME_DESIGN"
    assert updates.filter(pl.col("decision_status") == "PROMOTED_TO_FEATURE_CANDIDATE").height == 0


def test_write_foehn_domain_artifacts_exports_csvs_and_report(tmp_path: Path):
    features, labels = _synthetic_foehn_frames()
    artifacts = build_foehn_domain_artifacts(features, labels)

    paths = write_foehn_domain_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "domain_foehn_score_bins_by_month_cp.csv").exists()
    assert (tmp_path / "foehn_false_positive_audit.csv").exists()
    assert (tmp_path / "foehn_power_leakage_audit.csv").exists()
    assert (tmp_path / "foehn_regime_repair_candidates.csv").exists()
    report_text = paths["foehn_report_md"].read_text(encoding="utf-8")
    assert "Onda 2E FOEHN Domain EDA" in report_text
    assert "not production truth" in report_text
