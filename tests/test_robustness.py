"""Tests for Onda 4 robustness hardening."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc
from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.robustness._causal_audit import reaudit_causality
from solarstorm.robustness._config import (
    R1_BLOCK_YEARS,
    R1_MIN_PASSING_YEARS,
    R4_TREND_ALPHA,
    ROBUSTNESS_CONFIG_VERSION,
)
from solarstorm.robustness._drift import compute_drift_trend, write_drift_snapshot
from solarstorm.robustness._late_spike import (
    find_late_spike_candidates,
    write_late_spike_candidates,
)
from solarstorm.robustness._lead_time import (
    detect_nowcast_only,
    lead_time_analysis,
)
from solarstorm.robustness._regime_analysis import detect_dead_regimes, regime_sensitivity
from solarstorm.robustness._replication import (
    hypotheses_from_contract,
    per_year_replication,
)
from solarstorm.robustness._report import evaluate_go_nogo, render_robustness_report
from solarstorm.robustness._tmax_hour import (
    detect_fixed_cp_artifact,
    has_late_tmax_risk_baseline,
    tmax_hour_stratification,
)


def _tmax_utc(d: dt.date, local_hour: int) -> dt.datetime:
    local = dt.datetime(d.year, d.month, d.day, local_hour, tzinfo=dt.timezone(dt.timedelta(hours=13)))
    return local.astimezone(dt.UTC)


def _make_signal_dataset(
    *,
    n_years: int = 7,
    start_year: int = 2018,
    seed: int = 42,
    cp_set: tuple[str, ...] = ("20:00",),
) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    doy = np.arange(n_days)
    tmax = np.round(20 + 8 * np.sin(2 * np.pi * doy / 365) + rng.normal(0, 0.3, n_days)).astype(int)
    remaining = rng.normal(0, 3, n_days)
    remaining -= remaining.mean()
    remaining_i = np.round(remaining).astype(int)
    signal = remaining_i.astype(float) + rng.normal(0, 0.1, n_days)

    labels_rows: list[dict] = []
    feature_rows: list[dict] = []
    for i, d in enumerate(dates):
        label_row: dict = {
            "date_local": d,
            "tmax_int": int(tmax[i]),
            "day_complete": True,
            "tmax_hour": 14,
            "tmax_hour_utc": _tmax_utc(d, 14),
        }
        for cp in cp_set:
            label_row[f"k_cp__cp_{cp.replace(':', '')}"] = int(tmax[i] - remaining_i[i])
            feature_rows.append(
                {
                    "date_local": d,
                    "cp": cp,
                    "regime_label": "calm_radiative" if i % 2 == 0 else "standard_nw",
                    "feat_signal": float(signal[i]),
                }
            )
        labels_rows.append(label_row)

    return pl.DataFrame(feature_rows), pl.DataFrame(labels_rows)


def _validated_entry(
    *,
    feature_column: str = "feat_signal",
    cp: str = "20:00",
    hypothesis_id: str = "H_SIG",
) -> dict:
    return {
        "id": hypothesis_id,
        "feature_column": feature_column,
        "cp": cp,
        "regime": "all",
        "effect_size": 0.5,
        "ci_lo": 0.1,
        "ci_hi": 0.9,
        "p_value": 0.001,
        "best_null_name": "L0_persistence",
        "best_null_mae": 2.0,
    }


def test_config_constants_are_frozen_and_typed():
    assert isinstance(ROBUSTNESS_CONFIG_VERSION, str)
    assert R1_MIN_PASSING_YEARS > R1_BLOCK_YEARS >= 0
    assert 0 < R4_TREND_ALPHA < 1


def test_hypotheses_from_contract_deduplicates_validated_features():
    contract = {
        "validated_features": [
            _validated_entry(cp="20:00"),
            _validated_entry(cp="21:00"),
            _validated_entry(feature_column="other_signal", hypothesis_id="H_OTHER"),
            {**_validated_entry(feature_column="regime_signal"), "regime": "calm_radiative"},
        ]
    }

    hypotheses, cp_set = hypotheses_from_contract(contract)

    assert cp_set == ("20:00", "21:00")
    assert [(h.id, h.feature_column) for h in hypotheses] == [
        ("H_SIG", "feat_signal"),
        ("H_OTHER", "other_signal"),
    ]


def test_per_year_replication_reports_passing_years():
    features, labels = _make_signal_dataset()
    hypothesis = Hypothesis(
        id="H_SIG",
        feature_column="feat_signal",
        description="Known remaining-warming signal",
    )

    matrix, summary = per_year_replication(
        features,
        labels,
        [hypothesis],
        test_years=(2023, 2024),
        cp_set=("20:00",),
        seed=42,
    )

    assert {"year", "hypothesis_id", "cp", "passes_g1_g5", "challenger_mae"}.issubset(matrix.columns)
    assert set(matrix["year"].unique().to_list()) == {2023, 2024}
    assert summary["n_years_tested"] == 2
    assert set(summary["years_with_passing_feature"]) == {2023, 2024}


def test_regime_sensitivity_detects_dead_regimes_from_result_rows():
    rows = pl.DataFrame(
        [
            {"regime": "calm_radiative", "hypothesis_id": "H1", "cp": "20:00", "passes": True, "n_days": 50},
            {"regime": "standard_nw", "hypothesis_id": "H1", "cp": "20:00", "passes": False, "n_days": 50},
        ]
    )

    dead = detect_dead_regimes(rows, regimes=("calm_radiative", "standard_nw", "strong_nw_foehn"))

    assert dead == ["standard_nw", "strong_nw_foehn"]


def test_dead_regime_default_uses_physical_regime_family():
    rows = pl.DataFrame(
        [
            {"regime": "calm_radiative", "hypothesis_id": "H1", "cp": "20:00", "passes": True, "n_days": 50},
            {"regime": "standard_nw", "hypothesis_id": "H1", "cp": "20:00", "passes": True, "n_days": 50},
            {"regime": "strong_nw_foehn", "hypothesis_id": "H1", "cp": "20:00", "passes": True, "n_days": 50},
            {"regime": "southerly_disrupted", "hypothesis_id": "H1", "cp": "20:00", "passes": True, "n_days": 50},
        ]
    )

    assert detect_dead_regimes(rows) == []


def test_regime_sensitivity_accepts_validation_result_objects():
    features, labels = _make_signal_dataset()
    hypothesis = Hypothesis(id="H_SIG", feature_column="feat_signal", description="Known signal")

    cross_tab = regime_sensitivity(
        features,
        labels,
        [hypothesis],
        cp_set=("20:00",),
        test_starts=[dt.date(2024, 1, 1)],
        seed=42,
    )

    assert {"regime", "hypothesis_id", "cp", "passes", "n_days"}.issubset(cross_tab.columns)
    assert cross_tab.filter(pl.col("regime") == "calm_radiative").height >= 1


def test_drift_trend_warns_on_significant_decline(tmp_path: Path):
    matrix = pl.DataFrame(
        {
            "year": [2019, 2020, 2021, 2022, 2023],
            "effect_size": [5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )

    trend = compute_drift_trend(matrix)

    assert trend["trend_direction"] == "decreasing"
    assert trend["warning"] is True

    path = tmp_path / "drift.json"
    write_drift_snapshot(trend, path)
    assert json.loads(path.read_text(encoding="utf-8"))["warning"] is True


def test_causal_reaudit_flags_future_timestamp_columns():
    d = dt.date(2024, 1, 5)
    cp = "20:00"
    cp_utc = cp_to_utc(d, cp, TZ_NAME)
    features = pl.DataFrame(
        [
            {
                "date_local": d,
                "cp": cp,
                "clean_feature": 1.0,
                "clean_feature_max_obs_utc": cp_utc - dt.timedelta(minutes=5),
                "leaky_feature": 2.0,
                "leaky_feature_max_obs_utc": cp_utc + dt.timedelta(minutes=5),
            }
        ]
    )

    clean, violating = reaudit_causality(features, ["clean_feature", "leaky_feature"])

    assert clean == ["clean_feature"]
    assert violating == ["leaky_feature"]


def test_lead_time_analysis_separates_prediction_from_nowcast():
    labels = pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 1, 1),
                "tmax_int": 20,
                "day_complete": True,
                "tmax_hour": 14,
                "tmax_hour_utc": _tmax_utc(dt.date(2024, 1, 1), 14),
            },
            {
                "date_local": dt.date(2024, 1, 2),
                "tmax_int": 21,
                "day_complete": True,
                "tmax_hour": 8,
                "tmax_hour_utc": _tmax_utc(dt.date(2024, 1, 2), 8),
            },
        ]
    )
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2024, 1, 1), "cp": "20:00", "feat_signal": 1.0},
            {"date_local": dt.date(2024, 1, 2), "cp": "20:00", "feat_signal": 2.0},
        ]
    )

    table = lead_time_analysis(features, labels, [_validated_entry()])

    assert {"already_seen", "4h_plus"}.issubset(set(table["lead_time_bucket"].to_list()))
    assert detect_nowcast_only(table) is False
    assert detect_nowcast_only(table.filter(pl.col("tmax_already_seen"))) is True


def test_tmax_hour_stratification_marks_fixed_cp_artifacts():
    labels = pl.DataFrame(
        [
            {"date_local": dt.date(2024, 1, 1), "day_complete": True, "tmax_hour": 14},
            {"date_local": dt.date(2024, 1, 2), "day_complete": True, "tmax_hour": 15},
            {"date_local": dt.date(2024, 1, 3), "day_complete": True, "tmax_hour": 8},
        ]
    )
    features = pl.DataFrame(
        [
            {"date_local": dt.date(2024, 1, 1), "cp": "20:00", "regime_label": "calm_radiative", "feat_signal": 1.0},
            {"date_local": dt.date(2024, 1, 2), "cp": "20:00", "regime_label": "calm_radiative", "feat_signal": 2.0},
            {"date_local": dt.date(2024, 1, 3), "cp": "20:00", "regime_label": "calm_radiative", "feat_signal": 3.0},
        ]
    )

    table = tmax_hour_stratification(features, labels, [_validated_entry()], min_days=1)

    assert {"midday_12_14", "afternoon_15_18", "morning_before_12"}.issubset(
        set(table["tmax_hour_bucket"].to_list())
    )
    assert detect_fixed_cp_artifact(table) is False

    artifact_table = table.with_columns(pl.lit(1.0).alias("tmax_seen_share"))
    assert detect_fixed_cp_artifact(artifact_table) is True


def test_late_tmax_baseline_is_month_regime_relative_not_bucket_relative():
    labels = pl.DataFrame(
        [
            {"date_local": dt.date(2024, 1, 1), "day_complete": True, "tmax_hour": 11},
            {"date_local": dt.date(2024, 1, 2), "day_complete": True, "tmax_hour": 13},
            {"date_local": dt.date(2024, 1, 3), "day_complete": True, "tmax_hour": 16},
            {"date_local": dt.date(2024, 1, 4), "day_complete": True, "tmax_hour": 20},
        ]
    )
    features = pl.DataFrame(
        [
            {"date_local": d, "cp": "20:00", "regime_label": "standard_nw", "feat_signal": float(i)}
            for i, d in enumerate(labels["date_local"].to_list(), start=1)
        ]
    )

    table = tmax_hour_stratification(features, labels, [_validated_entry()], min_days=1)
    thresholds = table.select("late_tmax_baseline_threshold").unique().to_series().to_list()

    assert thresholds == [16.0]
    assert has_late_tmax_risk_baseline(table) is True


def test_tmax_hour_stratification_handles_regime_label_as_validated_feature():
    labels = pl.DataFrame(
        [{"date_local": dt.date(2024, 1, 1), "day_complete": True, "tmax_hour": 14}]
    )
    features = pl.DataFrame(
        [{"date_local": dt.date(2024, 1, 1), "cp": "20:00", "regime_label": "calm_radiative"}]
    )

    table = tmax_hour_stratification(
        features,
        labels,
        [_validated_entry(feature_column="regime_label", hypothesis_id="H_REGIME")],
        min_days=1,
    )

    assert table.height == 1
    assert table.row(0, named=True)["feature_column"] == "regime_label"


def test_late_spike_candidates_are_written_as_json(tmp_path: Path):
    labels = pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 1, 1),
                "tmax_int": 21,
                "day_complete": True,
                "k_cp__cp_2000": 19,
                "tmax_hour": 15,
            },
            {
                "date_local": dt.date(2024, 1, 2),
                "tmax_int": 20,
                "day_complete": True,
                "k_cp__cp_2000": 20,
                "tmax_hour": 11,
            },
        ]
    )

    candidates = find_late_spike_candidates(labels, cp_set=("20:00",), min_delta=1)

    assert candidates.height == 1
    assert candidates.row(0, named=True)["delta_after_cp"] == 2

    path = tmp_path / "late_spikes.json"
    write_late_spike_candidates(candidates, path)
    assert json.loads(path.read_text(encoding="utf-8"))[0]["delta_after_cp"] == 2


def test_report_go_nogo_includes_r6_r7_r8_r9(tmp_path: Path):
    year_matrix = pl.DataFrame(
        [
            {
                "year": 2020,
                "hypothesis_id": "H_SIG",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "regime": "all",
                "effect_size": 0.4,
                "ci_lo": 0.1,
                "ci_hi": 0.8,
                "passes_g1_g5": True,
                "best_null_name": "L0",
                "best_null_mae": 2.0,
                "challenger_mae": 1.6,
                "n_days": 365,
                "status": "validated",
            }
        ]
    )
    regime_tab = pl.DataFrame(
        [
            {"regime": "calm_radiative", "hypothesis_id": "H_SIG", "cp": "20:00", "passes": True, "n_days": 365},
            {"regime": "standard_nw", "hypothesis_id": "H_SIG", "cp": "20:00", "passes": True, "n_days": 365},
            {"regime": "strong_nw_foehn", "hypothesis_id": "H_SIG", "cp": "20:00", "passes": True, "n_days": 365},
            {"regime": "southerly_disrupted", "hypothesis_id": "H_SIG", "cp": "20:00", "passes": True, "n_days": 365},
        ]
    )
    drift = {"trend_statistic": 0.0, "p_value": 1.0, "warning": False, "per_year_gaps": {2020: 0.4}}
    lead_table = pl.DataFrame(
        [
            {
                "hypothesis_id": "H_SIG",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "lead_time_bucket": "4h_plus",
                "tmax_already_seen": False,
                "n_days": 365,
                "passes": True,
            }
        ]
    )
    tmax_tab = pl.DataFrame(
        [
            {
                "hypothesis_id": "H_SIG",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "regime": "calm_radiative",
                "month": 1,
                "tmax_hour_bucket": "afternoon_15_18",
                "n_days": 365,
                "tmax_seen_share": 0.0,
                "passes": True,
                "late_tmax_baseline_name": "month_regime_q90",
                "late_tmax_baseline_threshold": 17.0,
            }
        ]
    )
    late_spikes = pl.DataFrame(
        [{"date_local": dt.date(2024, 1, 1), "cp": "20:00", "delta_after_cp": 2}]
    )

    verdict = evaluate_go_nogo(
        {
            "n_passing_years": 3,
            "dead_regimes": [],
            "causal_violations": [],
            "gates_rerun_pass": True,
            "lead_time_ok": True,
            "fixed_cp_artifact": False,
            "late_spike_artifact_produced": True,
            "late_tmax_risk_baseline_exists": True,
        }
    )
    assert verdict == "GO"

    report_path = render_robustness_report(
        output_dir=tmp_path,
        year_matrix=year_matrix,
        regime_cross_tab=regime_tab,
        drift_result=drift,
        causal_clean=["feat_signal"],
        causal_violating=[],
        lead_time_table=lead_table,
        tmax_hour_table=tmax_tab,
        late_spike_candidates=late_spikes,
        gates_rerun_pass=True,
        today=dt.date(2026, 6, 6),
    )
    text = Path(report_path).read_text(encoding="utf-8")
    assert "R6: Anti-nowcast lead-time" in text
    assert "R7: Month/regime Tmax timing norms" in text
    assert "R8: Late-spike evidence pack" in text
    assert "R9: Late-Tmax risk baseline" in text
