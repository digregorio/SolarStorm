"""Tests for the P0 honest evaluation harness."""
from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from solarstorm.honest_eval import (
    PERSISTENCE_BLOCK,
    apply_physical_floor,
    assign_remaining_warming_strata,
    build_floor_violation_audit,
    build_honest_comparison,
    build_honest_gates,
    build_kcp_long,
    fit_honest_null,
    predict_honest_null,
    run_persistence_ablation,
    write_honest_eval_artifacts,
)


def _labels_fixture() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [dt.date(2022, 1, 1), dt.date(2022, 1, 2)],
            "tmax_int": [20, 18],
            "k_cp__cp_2000": [17, None],
            "k_cp__cp_2100": [18, 15],
            "k_cp__cp_2200": [19, 16],
            "k_cp__cp_2300": [20, 17],
        }
    )


def test_kcp_long_view_unpivots_labels() -> None:
    long = build_kcp_long(_labels_fixture())

    assert set(long.columns) == {"date_local", "cp", "k_cp"}
    assert long.height == 7
    row = long.filter(
        (pl.col("date_local") == dt.date(2022, 1, 1)) & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert row["k_cp"] == 20
    assert set(long["cp"].unique().to_list()) == {"20:00", "21:00", "22:00", "23:00"}


def _null_train_labels() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [dt.date(2021, 1, d) for d in (1, 2, 3)]
            + [dt.date(2023, 1, 4)],
            "tmax_int": [18, 19, 20, 30],
            "k_cp__cp_2000": [17, 17, 17, 10],
            "k_cp__cp_2100": [17, 17, 17, 10],
            "k_cp__cp_2200": [17, 17, 17, 10],
            "k_cp__cp_2300": [18, 19, 20, 10],
        }
    )


def test_honest_null_fits_train_only_monthly_medians() -> None:
    table = fit_honest_null(_null_train_labels(), train_end_year=2022)

    jan_20 = table.filter((pl.col("month") == 1) & (pl.col("cp") == "20:00"))
    assert jan_20.row(0, named=True)["rw_median"] == 2.0
    assert table.filter(pl.col("rw_median") >= 10).is_empty()
    assert not table.filter((pl.col("month") == 0) & (pl.col("cp") == "20:00")).is_empty()


def test_honest_null_predicts_kcp_plus_median_with_fallback() -> None:
    table = fit_honest_null(_null_train_labels(), train_end_year=2022)
    rows = pl.DataFrame(
        {
            "date_local": [dt.date(2023, 1, 10), dt.date(2023, 6, 10)],
            "cp": ["20:00", "20:00"],
            "k_cp": [14, 14],
        }
    )

    out = predict_honest_null(rows, table)

    jan = out.filter(pl.col("date_local") == dt.date(2023, 1, 10)).row(0, named=True)
    assert jan["null_prediction"] == 16.0
    jun = out.filter(pl.col("date_local") == dt.date(2023, 6, 10)).row(0, named=True)
    assert jun["null_prediction"] == 16.0


def _floor_fixture() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [dt.date(2023, 1, 1)] * 3,
            "cp": ["20:00", "21:00", "22:00"],
            "k_cp": [15, 16, 17],
            "prediction": [14.2, 16.0, 18.5],
            "actual": [17, 17, 19],
        }
    )


def test_apply_physical_floor_clamps_predictions_below_kcp() -> None:
    out = apply_physical_floor(_floor_fixture())

    assert out["prediction_floored"].to_list() == [15.0, 16.0, 18.5]
    assert out["floor_violation"].to_list() == [True, False, False]


def test_floor_violation_audit_reports_raw_and_clamped_rates_per_cp() -> None:
    audit = build_floor_violation_audit(apply_physical_floor(_floor_fixture()))

    overall = audit.filter(pl.col("cp") == "ALL").row(0, named=True)
    assert overall["n_rows"] == 3
    assert overall["n_raw_violations"] == 1
    assert overall["raw_violation_pct"] == pytest.approx(100.0 / 3.0)
    assert overall["n_clamped_violations"] == 0
    assert overall["clamped_violation_pct"] == 0.0
    assert overall["production_status"] == "EXPERIMENT_ONLY"


def _comparison_fixture() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [dt.date(2023, 1, d) for d in (1, 2, 3, 4)],
            "cp": ["23:00"] * 4,
            "k_cp": [20, 19, 15, 15],
            "actual": [20, 20, 18, 19],
            "prediction": [20.0, 20.0, 18.0, 17.0],
            "null_prediction": [20.0, 20.0, 16.0, 16.0],
        }
    )


def test_strata_assignment_buckets_realized_remaining_warming() -> None:
    out = assign_remaining_warming_strata(_comparison_fixture())

    assert out["rw_stratum"].to_list() == [
        "already_seen",
        "small_1",
        "forecast_2_plus",
        "forecast_2_plus",
    ]


def test_honest_comparison_reports_model_and_null_by_cp_and_stratum() -> None:
    tables = build_honest_comparison(assign_remaining_warming_strata(_comparison_fixture()))

    by_cp = tables["by_cp"].filter(pl.col("cp") == "23:00").row(0, named=True)
    assert by_cp["model_mae"] == pytest.approx(0.5)
    assert by_cp["null_mae"] == pytest.approx(1.25)
    assert by_cp["model_beats_null"] is True

    forecast = tables["by_stratum"].filter(pl.col("rw_stratum") == "forecast_2_plus")
    assert forecast.row(0, named=True)["model_mae"] == pytest.approx(1.0)

    strat = tables["by_stratum_cp"].filter(
        (pl.col("rw_stratum") == "forecast_2_plus") & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert strat["n_rows"] == 2
    assert strat["model_mae"] == pytest.approx(1.0)
    assert strat["null_mae"] == pytest.approx(2.5)


def _gate_inputs(
    *,
    h1_model_wins: bool = True,
    h2_model_wins: bool = True,
    all_cps: bool = True,
) -> dict[str, pl.DataFrame]:
    cps = ["20:00", "21:00", "22:00", "23:00"] if all_cps else ["20:00", "21:00"]
    h1_model_mae = 0.9 if h1_model_wins else 1.2
    h2_model_mae = 0.9 if h2_model_wins else 1.2
    by_cp = pl.DataFrame(
        {
            "cp": cps,
            "n_rows": [100] * len(cps),
            "model_mae": [h1_model_mae] * len(cps),
            "null_mae": [1.0] * len(cps),
            "model_beats_null": [h1_model_wins] * len(cps),
        }
    )
    by_stratum = pl.DataFrame(
        {
            "rw_stratum": ["forecast_2_plus"],
            "n_rows": [50 * len(cps)],
            "model_mae": [h2_model_mae],
            "null_mae": [1.0],
            "model_beats_null": [h2_model_wins],
        }
    )
    by_stratum_cp = pl.DataFrame(
        {
            "rw_stratum": ["forecast_2_plus"] * len(cps),
            "cp": cps,
            "n_rows": [50] * len(cps),
            "model_mae": [h2_model_mae] * len(cps),
            "null_mae": [1.0] * len(cps),
            "model_beats_null": [h2_model_wins] * len(cps),
        }
    )
    floor_audit = pl.DataFrame(
        {
            "cp": ["ALL"],
            "n_rows": [400],
            "n_raw_violations": [12],
            "raw_violation_pct": [3.0],
            "n_clamped_violations": [0],
            "clamped_violation_pct": [0.0],
        }
    )
    return {
        "by_cp": by_cp,
        "by_stratum": by_stratum,
        "by_stratum_cp": by_stratum_cp,
        "floor_audit": floor_audit,
    }


def test_gates_pass_and_decision_when_model_beats_null_everywhere() -> None:
    gates, decision = build_honest_gates(**_gate_inputs())

    assert gates.filter(pl.col("gate_status") != "PASS").is_empty()
    assert decision.row(0, named=True)["decision_status"] == "HONEST_EVALUATION_PASSED"


def test_gates_block_when_null_wins_any_cp() -> None:
    gates, decision = build_honest_gates(**_gate_inputs(h1_model_wins=False))

    h1 = gates.filter(pl.col("gate_id") == "H1").row(0, named=True)
    assert h1["gate_status"] == "BLOCK"
    assert decision.row(0, named=True)["decision_status"] == "BLOCK_MODEL_PROMOTION_HONEST_NULL"


def test_gates_block_when_forecast_stratum_loses_overall() -> None:
    gates, decision = build_honest_gates(**_gate_inputs(h2_model_wins=False))

    h2 = gates.filter(pl.col("gate_id") == "H2").row(0, named=True)
    assert h2["gate_status"] == "BLOCK"
    assert decision.row(0, named=True)["decision_status"] == "BLOCK_MODEL_PROMOTION_HONEST_NULL"


def test_gates_review_when_physical_floor_instrumentation_fails() -> None:
    inputs = _gate_inputs()
    inputs["floor_audit"] = inputs["floor_audit"].with_columns(
        pl.lit(1).alias("n_clamped_violations")
    )

    gates, decision = build_honest_gates(**inputs)

    h3 = gates.filter(pl.col("gate_id") == "H3").row(0, named=True)
    assert h3["gate_status"] == "BLOCK"
    assert decision.row(0, named=True)["decision_status"] == "KEEP_IN_HONEST_EVALUATION_REVIEW"


def test_gates_review_when_lead_table_missing_cps() -> None:
    gates, decision = build_honest_gates(**_gate_inputs(all_cps=False))

    h4 = gates.filter(pl.col("gate_id") == "H4").row(0, named=True)
    assert h4["gate_status"] == "BLOCK"
    assert decision.row(0, named=True)["decision_status"] == "KEEP_IN_HONEST_EVALUATION_REVIEW"


def _ablation_matrix() -> pl.DataFrame:
    rng = np.random.default_rng(7)
    n = 400
    dates = [dt.date(2021, 1, 1) + dt.timedelta(days=i // 4) for i in range(n)]
    cps = ["20:00", "21:00", "22:00", "23:00"] * (n // 4)
    persistence = rng.normal(0.0, 2.0, n)
    other = rng.normal(0.0, 1.0, n)
    target = 15.0 + 2.0 * persistence + 0.5 * other + rng.normal(0.0, 0.2, n)
    return pl.DataFrame(
        {
            "date_local": dates,
            "cp": cps,
            "tmax_dminus1": persistence,
            "slope_3h": persistence * 0.5,
            "warming_rate_06_09": persistence * 0.2,
            "cloud_cover_suppression": other,
            "tmax_int": target,
        }
    )


def test_persistence_ablation_compares_full_vs_ablated_mae() -> None:
    out = run_persistence_ablation(
        _ablation_matrix(),
        test_years=[2021],
        numeric_feature_columns=[
            "tmax_dminus1",
            "slope_3h",
            "warming_rate_06_09",
            "cloud_cover_suppression",
        ],
        categorical_feature_columns=[],
    )

    row = out.row(0, named=True)
    assert row["test_year"] == 2021
    assert set(PERSISTENCE_BLOCK) == {"tmax_dminus1", "slope_3h", "warming_rate_06_09"}
    assert row["ablated_mae"] > row["full_mae"]
    assert row["production_status"] == "EXPERIMENT_ONLY"


def test_writer_emits_csv_md_pairs_and_report(tmp_path) -> None:
    frame = pl.DataFrame({"cp": ["ALL"], "production_status": ["EXPERIMENT_ONLY"]})
    artifacts = {
        "honest_eval_null_table_v1": frame,
        "honest_eval_by_cp_v1": frame,
        "honest_eval_by_stratum_cp_v1": frame,
        "honest_eval_floor_audit_v1": frame,
        "honest_eval_ablation_v1": frame,
        "honest_eval_gates_v1": frame,
        "honest_eval_decision_v1": pl.DataFrame(
            [
                {
                    "decision_status": "HONEST_EVALUATION_PASSED",
                    "production_status": "EXPERIMENT_ONLY",
                }
            ]
        ),
    }

    paths = write_honest_eval_artifacts(
        artifacts, output_dir=tmp_path, today=dt.date(2026, 6, 12)
    )

    assert (tmp_path / "honest_eval_gates_v1.csv").exists()
    assert (tmp_path / "honest_eval_gates_v1.md").exists()
    report = (tmp_path / "honest_evaluation_report_v1.md").read_text(encoding="utf-8")
    assert "EXPERIMENT_ONLY" in report
    assert "No production, EV, pricing, shadow trading, or execution work is unlocked." in report
    assert "honest_eval_report_md" in paths
