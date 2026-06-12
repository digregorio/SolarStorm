"""Tests for the P1 horizon hybrid model iteration."""
from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from solarstorm.onda3._hybrid_iteration import (
    build_hybrid_matrix,
    build_onda3_hybrid_iteration,
    judge_hybrid_candidates,
    run_hybrid_fold,
    write_onda3_hybrid_artifacts,
)


def _features_fixture(n_days: int = 8) -> pl.DataFrame:
    rows = []
    for i in range(n_days):
        date = dt.date(2022, 1, 1) + dt.timedelta(days=i)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "cloud_cover_suppression": float(i % 3),
                    "foehn_score": float(i % 5),
                }
            )
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def _labels_fixture(n_days: int = 8) -> pl.DataFrame:
    rows = []
    for i in range(n_days):
        rows.append(
            {
                "date_local": dt.date(2022, 1, 1) + dt.timedelta(days=i),
                "tmax_int": 20 + (i % 4),
                "k_cp__cp_2000": 16 + (i % 4),
                "k_cp__cp_2100": 17 + (i % 4),
                "k_cp__cp_2200": 18 + (i % 4),
                "k_cp__cp_2300": 19 + (i % 4),
            }
        )
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def _open_meteo_fixture(n_days: int = 8) -> pl.DataFrame:
    rows = []
    for i in range(n_days):
        date = dt.date(2022, 1, 1) + dt.timedelta(days=i)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "om_prev_d1_day_max_c": 21.0 + (i % 4),
                }
            )
    return pl.DataFrame(rows, strict=False)


def test_hybrid_matrix_builds_rw_target_and_om_anchor_per_cp():
    matrix = build_hybrid_matrix(
        features=_features_fixture(),
        labels=_labels_fixture(),
        open_meteo=_open_meteo_fixture(),
    )

    row = matrix.filter(
        (pl.col("date_local") == dt.date(2022, 1, 1)) & (pl.col("cp") == "20:00")
    ).row(0, named=True)
    assert row["k_cp"] == 16
    assert row["remaining_warming"] == 4
    assert row["om_anchor_max"] == 21.0
    assert row["om_anchor_delta"] == pytest.approx(5.0)
    assert row["cp_lead_rank"] == 3
    assert row["om_anchor_delta_x_lead"] == pytest.approx(5.0)

    late = matrix.filter(
        (pl.col("date_local") == dt.date(2022, 1, 1)) & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert late["cp_lead_rank"] == 0
    assert late["om_anchor_delta"] == pytest.approx(2.0)
    assert late["om_anchor_delta_x_lead"] == pytest.approx(0.0)


def test_hybrid_matrix_without_open_meteo_has_null_anchor_columns():
    matrix = build_hybrid_matrix(
        features=_features_fixture(),
        labels=_labels_fixture(),
        open_meteo=None,
    )

    assert matrix["om_anchor_max"].null_count() == matrix.height
    assert matrix["remaining_warming"].null_count() == 0


def test_hybrid_matrix_rejects_duplicate_open_meteo_keys():
    duplicated = pl.concat([_open_meteo_fixture(), _open_meteo_fixture().head(1)])

    with pytest.raises(ValueError, match="duplicate"):
        build_hybrid_matrix(
            features=_features_fixture(),
            labels=_labels_fixture(),
            open_meteo=duplicated,
        )


def _fold_matrix() -> pl.DataFrame:
    rng = np.random.default_rng(11)
    rows = []
    for i in range(200):
        date = dt.date(2021, 1, 1) + dt.timedelta(days=i)
        for cp_i, cp in enumerate(("20:00", "21:00", "22:00", "23:00")):
            signal = float(rng.normal(0.0, 1.0))
            rw = max(0, round(2.0 + signal - cp_i * 0.5))
            k_cp = 15 + (i % 5) + cp_i
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "k_cp": k_cp,
                    "tmax_int": k_cp + rw,
                    "remaining_warming": rw,
                    "signal_feature": signal,
                    "cp_lead_rank": 3 - cp_i,
                }
            )
    return pl.DataFrame(rows, strict=False)


def test_hybrid_fold_reconstructs_tmax_with_floor_by_construction():
    matrix = _fold_matrix()
    train = matrix.filter(pl.col("date_local") < dt.date(2021, 6, 1))
    test = matrix.filter(pl.col("date_local") >= dt.date(2021, 6, 1))

    predictions = run_hybrid_fold(
        train,
        test,
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
        model_name="hybrid_local_only",
    )

    assert predictions.height == test.height
    joined = predictions.join(
        test.select(["date_local", "cp", "k_cp"]),
        on=["date_local", "cp"],
    )
    assert joined.filter(pl.col("prediction") < pl.col("k_cp")).is_empty()
    row = predictions.row(0, named=True)
    assert row["absolute_error"] == pytest.approx(abs(row["actual"] - row["prediction"]))
    assert row["model_name"] == "hybrid_local_only"
    assert row["production_status"] == "EXPERIMENT_ONLY"


def _two_year_matrix() -> pl.DataFrame:
    rng = np.random.default_rng(23)
    rows = []
    for i in range(500):
        date = dt.date(2021, 1, 1) + dt.timedelta(days=i)
        for cp_i, cp in enumerate(("20:00", "21:00", "22:00", "23:00")):
            signal = float(rng.normal(0.0, 1.0))
            anchor_noise = float(rng.normal(0.0, 0.3))
            rw = max(0, round(2.0 + signal - cp_i * 0.5))
            k_cp = 15 + (i % 5) + cp_i
            om = float(k_cp + rw) + anchor_noise if date >= dt.date(2021, 7, 1) else None
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "k_cp": k_cp,
                    "tmax_int": k_cp + rw,
                    "remaining_warming": rw,
                    "signal_feature": signal,
                    "cp_lead_rank": 3 - cp_i,
                    "om_anchor_max": om,
                    "om_anchor_delta": (om - k_cp) if om is not None else None,
                    "om_anchor_delta_x_lead": (
                        (om - k_cp) * (3 - cp_i) / 3.0 if om is not None else None
                    ),
                }
            )
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def test_hybrid_iteration_runs_three_candidate_surfaces():
    artifacts = build_onda3_hybrid_iteration(
        _two_year_matrix(),
        test_years=[2022],
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
    )

    results = artifacts["onda3_hybrid_model_results_v1"]
    assert set(results["model_name"].to_list()) == {
        "hybrid_local_only",
        "hybrid_om_augmented",
        "hybrid_local_only_covered_rows",
    }
    om_rows = results.filter(pl.col("model_name") == "hybrid_om_augmented")
    ref_rows = results.filter(pl.col("model_name") == "hybrid_local_only_covered_rows")
    assert om_rows["n_test"].to_list() == ref_rows["n_test"].to_list()
    assert om_rows["mae"].to_list()[0] < ref_rows["mae"].to_list()[0]


def _labels_for_judgement() -> pl.DataFrame:
    matrix = _two_year_matrix()
    wide = matrix.filter(pl.col("cp") == "20:00").select(["date_local", "tmax_int"])
    for cp, column in (
        ("20:00", "k_cp__cp_2000"),
        ("21:00", "k_cp__cp_2100"),
        ("22:00", "k_cp__cp_2200"),
        ("23:00", "k_cp__cp_2300"),
    ):
        wide = wide.join(
            matrix.filter(pl.col("cp") == cp).select(
                ["date_local", pl.col("k_cp").alias(column)]
            ),
            on="date_local",
            how="left",
        )
    return wide.with_columns(pl.col("tmax_int").cast(pl.Float64))


def test_judgement_emits_gates_per_candidate_and_decision():
    artifacts = build_onda3_hybrid_iteration(
        _two_year_matrix(),
        test_years=[2022],
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
    )

    judged = judge_hybrid_candidates(
        predictions=artifacts["onda3_hybrid_predictions_v1"],
        labels=_labels_for_judgement(),
        train_end_year=2021,
    )

    gates = judged["onda3_hybrid_gates_v1"]
    assert set(gates["model_name"].unique().to_list()) == {
        "hybrid_local_only",
        "hybrid_om_augmented",
        "hybrid_local_only_covered_rows",
    }
    decision = judged["onda3_hybrid_decision_v1"].row(0, named=True)
    assert decision["decision_status"] in {
        "READY_FOR_P2_DISTRIBUTION_DESIGN",
        "KEEP_HYBRID_LOCAL_AS_REFERENCE",
        "KEEP_IN_ONDA3_EXPERIMENT_REVIEW",
    }
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def _judgement_predictions_fixture(
    *, om_offset: float, reference_offset: float
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Labels + candidate predictions where every row is forecast_2_plus.

    rw alternates 3/5 (median 4) so the honest null predicts k_cp + 4 and
    scores MAE 1.0; candidates beat it whenever their offset is < 1.
    """
    train_dates = [dt.date(2021, 1, 1) + dt.timedelta(days=i) for i in range(120)]
    test_dates = [dt.date(2022, 1, 1) + dt.timedelta(days=i) for i in range(60)]
    label_rows = []
    for i, date in enumerate([*train_dates, *test_dates]):
        label_rows.append(
            {
                "date_local": date,
                "tmax_int": 18 + (i % 2) * 2,
                "k_cp__cp_2000": 15,
                "k_cp__cp_2100": 15,
                "k_cp__cp_2200": 15,
                "k_cp__cp_2300": 15,
            }
        )
    labels = pl.DataFrame(label_rows)
    pred_rows = []
    for i, date in enumerate(test_dates):
        actual = float(18 + ((len(train_dates) + i) % 2) * 2)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            for model_name, prediction in (
                ("hybrid_local_only", actual),
                ("hybrid_local_only_covered_rows", actual + reference_offset),
                ("hybrid_om_augmented", actual + om_offset),
            ):
                pred_rows.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "actual": actual,
                        "prediction": prediction,
                        "model_name": model_name,
                        "test_year": 2022,
                    }
                )
    return labels, pl.DataFrame(pred_rows)


def test_om_candidate_passing_gates_but_losing_same_row_mae_is_not_promoted():
    # om beats the honest null (0.5 < 1.0) so H1/H2 pass, but it loses the
    # pre-registered same-row MAE comparison against the covered-rows
    # reference (0.5 > 0.0) -> spec criterion 2 forbids READY_FOR_P2.
    labels, predictions = _judgement_predictions_fixture(
        om_offset=0.5, reference_offset=0.0
    )

    judged = judge_hybrid_candidates(
        predictions=predictions, labels=labels, train_end_year=2021
    )

    decision = judged["onda3_hybrid_decision_v1"].row(0, named=True)
    assert decision["decision_status"] == "KEEP_HYBRID_LOCAL_AS_REFERENCE"
    assert decision["om_beats_reference_same_row"] is False
    assert decision["om_same_row_mae"] == pytest.approx(0.5)
    assert decision["reference_same_row_mae"] == pytest.approx(0.0)


def test_om_candidate_winning_gates_and_same_row_mae_is_promoted():
    labels, predictions = _judgement_predictions_fixture(
        om_offset=0.0, reference_offset=0.5
    )

    judged = judge_hybrid_candidates(
        predictions=predictions, labels=labels, train_end_year=2021
    )

    decision = judged["onda3_hybrid_decision_v1"].row(0, named=True)
    assert decision["decision_status"] == "READY_FOR_P2_DISTRIBUTION_DESIGN"
    assert decision["om_beats_reference_same_row"] is True
    assert decision["om_same_row_mae"] == pytest.approx(0.0)
    assert decision["reference_same_row_mae"] == pytest.approx(0.5)


def test_judgement_rejects_test_years_inside_null_training_window():
    labels, predictions = _judgement_predictions_fixture(
        om_offset=0.0, reference_offset=0.5
    )

    with pytest.raises(ValueError, match="train_end_year"):
        judge_hybrid_candidates(
            predictions=predictions, labels=labels, train_end_year=2022
        )


def test_writer_emits_csv_md_and_report(tmp_path):
    frame = pl.DataFrame(
        {"model_name": ["hybrid_local_only"], "production_status": ["EXPERIMENT_ONLY"]}
    )
    artifacts = {
        "onda3_hybrid_model_results_v1": frame,
        "onda3_hybrid_predictions_v1": frame,
        "onda3_hybrid_feature_audit_v1": frame,
        "onda3_hybrid_gates_v1": frame,
        "onda3_hybrid_honest_by_cp_v1": frame,
        "onda3_hybrid_decision_v1": pl.DataFrame(
            [
                {
                    "decision_status": "KEEP_IN_ONDA3_EXPERIMENT_REVIEW",
                    "production_status": "EXPERIMENT_ONLY",
                }
            ]
        ),
    }

    paths = write_onda3_hybrid_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 12),
    )

    assert (tmp_path / "onda3_hybrid_decision_v1.csv").exists()
    report = (tmp_path / "onda3_hybrid_model_report_v1.md").read_text(encoding="utf-8")
    assert "EXPERIMENT_ONLY" in report
    assert "No production, EV, pricing, shadow trading, or execution work is unlocked." in report
    assert "onda3_hybrid_report_md" in paths
