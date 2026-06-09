from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

from solarstorm.onda2e._wind import (
    build_wind_decision_updates,
    build_wind_domain_artifacts,
    write_wind_domain_artifacts,
)


def _wind_obs(
    date_local: dt.date,
    hour: int,
    *,
    drct: float,
    sknt: float,
) -> dict[str, object]:
    return {
        "date_local": date_local,
        "valid": dt.datetime.combine(
            date_local,
            dt.time(hour, tzinfo=dt.UTC),
        ),
        "ts_local": dt.datetime.combine(date_local, dt.time(hour)),
        "tmp_c_int": 18,
        "dwp_c_int": 12,
        "drct": drct,
        "sknt": sknt,
        "p01i": 0.0,
        "dq_tmp_c_int": "ok",
    }


def _synthetic_inputs() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    d1 = dt.date(2025, 1, 1)
    d2 = dt.date(2025, 1, 2)
    features = pl.DataFrame(
        [
            {"date_local": d1, "cp": "20:00", "regime_label": "standard_nw"},
            {"date_local": d2, "cp": "20:00", "regime_label": "southerly_disrupted"},
        ]
    )
    labels = pl.DataFrame(
        [
            {"date_local": d1, "tmax_int": 25, "tmax_hour": 16, "k_cp__cp_2000": 20},
            {"date_local": d2, "tmax_int": 21, "tmax_hour": 13, "k_cp__cp_2000": 17},
        ]
    )
    obs = pl.DataFrame(
        [
            _wind_obs(d1, 8, drct=350.0, sknt=10.0),
            _wind_obs(d1, 9, drct=20.0, sknt=14.0),
            _wind_obs(d1, 10, drct=100.0, sknt=6.0),
            _wind_obs(d1, 21, drct=270.0, sknt=50.0),
            _wind_obs(d2, 8, drct=180.0, sknt=18.0),
            _wind_obs(d2, 9, drct=190.0, sknt=16.0),
        ]
    )
    return features, labels, obs


def test_wind_domain_artifacts_use_pre_cp_sector_effects_and_reliability():
    features, labels, obs = _synthetic_inputs()

    artifacts = build_wind_domain_artifacts(features, labels, obs, tz_name="UTC")

    effects = artifacts["wind_sector_effects_by_month_cp"]
    assert effects.select(pl.sum("n_obs")).item() == 5
    assert "W" not in set(effects.get_column("wind_sector"))

    north = effects.filter(pl.col("wind_sector") == "N").row(0, named=True)
    assert north["month"] == 1
    assert north["cp"] == "20:00"
    assert north["n_obs"] == 2
    assert north["n_days"] == 1
    assert north["underpowered_n_lt_30"] is True
    assert math.isclose(north["mean_tmax_anomaly"], 2.0)
    assert math.isclose(north["mean_remaining_warming"], 5.0)
    assert math.isclose(north["mean_sknt"], 12.0)

    reliability = artifacts["wind_direction_reliability_by_day_cp"]
    churned = reliability.filter(pl.col("date_local") == dt.date(2025, 1, 1)).row(
        0,
        named=True,
    )
    assert churned["n_sectors_observed"] == 2
    assert churned["dominant_sector"] == "N"
    assert math.isclose(churned["dominant_share"], 2 / 3)
    assert churned["direction_churn_flag"] is True

    stable = reliability.filter(pl.col("date_local") == dt.date(2025, 1, 2)).row(
        0,
        named=True,
    )
    assert stable["n_sectors_observed"] == 1
    assert stable["dominant_sector"] == "S"
    assert stable["direction_churn_flag"] is False


def test_wind_artifacts_include_leakage_audit_and_regime_repair_candidate():
    features, labels, obs = _synthetic_inputs()

    artifacts = build_wind_domain_artifacts(features, labels, obs, tz_name="UTC")
    audit = artifacts["wind_power_leakage_audit"]
    candidates = artifacts["wind_regime_repair_candidates"]

    assert audit.filter(pl.col("audit_item") == "cp_slice_causal").row(0, named=True)[
        "status"
    ] == "PASS"
    assert audit.filter(pl.col("audit_item") == "outcome_usage").row(0, named=True)[
        "status"
    ] == "WARN"
    assert audit.filter(pl.col("audit_item") == "power").row(0, named=True)["status"] == "WARN"
    assert "REGIME_CLASSIFIER_CURRENT" in set(candidates.get_column("source_rule_id"))
    assert candidates.filter(pl.col("source_rule_id") == "REGIME_CLASSIFIER_CURRENT").row(
        0,
        named=True,
    )["candidate_action"] == "review_wind_sector_split_for_regime_design"


def test_wind_decision_updates_support_sector_artifact_and_promote_southerly_count():
    features, labels, obs = _synthetic_inputs()
    artifacts = build_wind_domain_artifacts(features, labels, obs, tz_name="UTC")

    updates = build_wind_decision_updates(artifacts)

    assert set(updates.get_column("item_id")) == {"WCT-WIND-006", "WCT-WIND-019"}
    assert updates.filter(pl.col("item_id") == "WCT-WIND-006").row(0, named=True)[
        "decision_status"
    ] == "SUPPORTED"
    assert updates.filter(pl.col("item_id") == "WCT-WIND-019").row(0, named=True)[
        "decision_status"
    ] == "PROMOTED_TO_REGIME_DESIGN"
    assert updates.filter(pl.col("decision_status") == "PROMOTED_TO_FEATURE_CANDIDATE").height == 0


def test_write_wind_domain_artifacts_exports_csvs_and_report(tmp_path: Path):
    features, labels, obs = _synthetic_inputs()
    artifacts = build_wind_domain_artifacts(features, labels, obs, tz_name="UTC")

    paths = write_wind_domain_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "wind_sector_effects_by_month_cp.csv").exists()
    assert (tmp_path / "wind_direction_reliability_by_day_cp.csv").exists()
    assert (tmp_path / "wind_power_leakage_audit.csv").exists()
    assert (tmp_path / "wind_regime_repair_candidates.csv").exists()
    report_text = paths["wind_report_md"].read_text(encoding="utf-8")
    assert "Onda 2E Wind Domain EDA" in report_text
    assert "No feature candidate is promoted" in report_text
