from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e import (
    build_foundation_experiment_results,
    write_foundation_experiment_result_artifacts,
)

runner = CliRunner()


def _catalog() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "experiment_id": "BEXP-L2-MONTH-REGIME-001",
                "experiment_family": "baseline",
                "domain": "BASELINE",
                "source_decision_id": "ADR-012-BASELINE-L2",
                "source_artifacts": "reports/regime-design/regime_candidate_assignments_v1.csv",
                "weakness_target": "high_mae",
                "candidate_surface": "baseline_ladder",
                "implementation_kind": "new_baseline",
                "input_columns_or_artifacts": "month; candidate_regime_label; tmax_int",
                "strata": "month x candidate regime",
                "causal_status": "outcome_only",
                "leakage_risk": "train only",
                "power_warning": "min cell rows",
                "baseline_comparator": "L2",
                "success_metric": "mae_delta",
                "acceptance_gate": "ci_lo >= 0",
                "stop_condition": "degrades",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "run",
            },
            {
                "experiment_id": "BEXP-L4-MONTH-CP-REGIME-001",
                "experiment_family": "baseline",
                "domain": "BASELINE",
                "source_decision_id": "ADR-012-BASELINE-L4",
                "source_artifacts": "reports/regime-design/regime_candidate_assignments_v1.csv",
                "weakness_target": "high_mae",
                "candidate_surface": "baseline_ladder",
                "implementation_kind": "baseline_variant",
                "input_columns_or_artifacts": "month; CP; candidate_regime_label; remaining_warming",
                "strata": "month x CP x candidate regime",
                "causal_status": "outcome_only",
                "leakage_risk": "train only",
                "power_warning": "min cell rows",
                "baseline_comparator": "L4",
                "success_metric": "mae_delta",
                "acceptance_gate": "effect > 0",
                "stop_condition": "degrades",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "run",
            },
            {
                "experiment_id": "REXP-DEAD-MARITIME-001",
                "experiment_family": "regime",
                "domain": "REGIME",
                "source_decision_id": "candidate_maritime_cloudy",
                "source_artifacts": "reports/regime-design/regime_candidate_r2_validation.csv",
                "weakness_target": "dead_regime",
                "candidate_surface": "regime_assignment",
                "implementation_kind": "regime_revision",
                "input_columns_or_artifacts": "candidate_regime_label",
                "strata": "candidate regime family x CP",
                "causal_status": "causal_available",
                "leakage_risk": "offline only",
                "power_warning": "dead",
                "baseline_comparator": "RULE_ONDA2R_PHYSICAL_REGIME_FAMILY",
                "success_metric": "dead_regime_count",
                "acceptance_gate": "dead count decreases",
                "stop_condition": "dead",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "repair",
            },
        ]
    )


def _catalog_with_mixed_dead_regime() -> pl.DataFrame:
    mixed = (
        _catalog()
        .filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001")
        .with_columns(
            pl.lit("REXP-DEAD-MIXED-001").alias("experiment_id"),
            pl.lit("candidate_mixed_or_transition").alias("source_decision_id"),
        )
    )
    return pl.concat([_catalog(), mixed], how="vertical")


def _catalog_with_foehn_feature_probe() -> pl.DataFrame:
    foehn = pl.DataFrame(
        [
            {
                "experiment_id": "FEXP-FOEHN-CONTINUOUS-001",
                "experiment_family": "feature",
                "domain": "FOEHN",
                "source_decision_id": "WCT-FOEHN-001",
                "source_artifacts": "reports/onda2e/domain_foehn_score_bins_by_month_cp.csv",
                "weakness_target": "fixed_threshold",
                "candidate_surface": "feature_builder",
                "implementation_kind": "feature_probe",
                "input_columns_or_artifacts": "foehn_score; wind sector; dewpoint_depression; month; CP",
                "strata": "month x CP x foehn_score bin",
                "causal_status": "causal_available",
                "leakage_risk": "Use pre-CP score only.",
                "power_warning": "Synthetic test fixture.",
                "baseline_comparator": "RULE_FOEHN_SCORE_FIXED_60",
                "success_metric": "mae_delta",
                "acceptance_gate": "Continuous or binned score improves validation.",
                "stop_condition": "Effect disappears.",
                "production_status": "EXPERIMENT_ONLY",
                "next_action": "Test continuous and binned foehn_score variants.",
            }
        ]
    )
    return pl.concat([_catalog(), foehn], how="vertical")


def _labels_and_assignments() -> tuple[pl.DataFrame, pl.DataFrame]:
    label_rows: list[dict[str, object]] = []
    assignment_rows: list[dict[str, object]] = []
    train_start = dt.date(2020, 1, 1)
    for i in range(366):
        day = train_start + dt.timedelta(days=i)
        regime = "candidate_warm" if i % 2 == 0 else "candidate_cool"
        tmax = 25 if regime == "candidate_warm" else 15
        label_rows.append(
            {
                "date_local": day,
                "day_complete": True,
                "tmax_int": tmax,
                "k_cp__cp_2000": 18,
                "tmax_hour": 15,
            }
        )
        assignment_rows.append(
            {
                "date_local": day,
                "cp": "20:00",
                "candidate_regime_label": regime,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )

    test_start = dt.date(2021, 1, 1)
    for i in range(20):
        day = test_start + dt.timedelta(days=i)
        regime = "candidate_warm" if i % 2 == 0 else "candidate_cool"
        tmax = 25 if regime == "candidate_warm" else 15
        label_rows.append(
            {
                "date_local": day,
                "day_complete": True,
                "tmax_int": tmax,
                "k_cp__cp_2000": 18,
                "tmax_hour": 15,
            }
        )
        assignment_rows.append(
            {
                "date_local": day,
                "cp": "20:00",
                "candidate_regime_label": regime,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )

    return pl.DataFrame(label_rows), pl.DataFrame(assignment_rows)


def _foehn_feature_probe_frames() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    label_rows: list[dict[str, object]] = []
    assignment_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []

    for year in (2020, 2021):
        start = dt.date(year, 1, 1)
        n_days = 366 if year == 2020 else 20
        for i in range(n_days):
            day = start + dt.timedelta(days=i)
            high_bin = i % 2 == 0
            foehn_score = 50.0 if high_bin else 25.0
            tmax = 30 if high_bin else 20
            label_rows.append(
                {
                    "date_local": day,
                    "day_complete": True,
                    "tmax_int": tmax,
                    "k_cp__cp_2000": 20,
                    "tmax_hour": 15,
                }
            )
            assignment_rows.append(
                {
                    "date_local": day,
                    "cp": "20:00",
                    "candidate_regime_label": "candidate_nw_or_foehn",
                    "causal_window": "valid < CP",
                    "production_status": "NOT_PRODUCTION",
                }
            )
            feature_rows.append(
                {
                    "date_local": day,
                    "cp": "20:00",
                    "foehn_score": foehn_score,
                    "dewpoint_depression": 8.0 if high_bin else 2.0,
                    "dewpoint_collapse_rate_3h": 1.0 if high_bin else 0.0,
                    "nw_sector_not_foehn": 0,
                }
            )

    return (
        pl.DataFrame(label_rows),
        pl.DataFrame(assignment_rows),
        pl.DataFrame(feature_rows),
    )


def test_build_foundation_experiment_results_runs_priority_baselines():
    labels, assignments = _labels_and_assignments()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    results = artifacts["foundation_experiment_results"]
    l2 = results.filter(pl.col("experiment_id") == "BEXP-L2-MONTH-REGIME-001").row(
        0,
        named=True,
    )
    l4 = results.filter(pl.col("experiment_id") == "BEXP-L4-MONTH-CP-REGIME-001").row(
        0,
        named=True,
    )
    regime = results.filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001").row(
        0,
        named=True,
    )

    assert l2["run_id"] == "test-run"
    assert l2["status"] in {"passed", "failed"}
    assert l2["n_rows"] == 20
    assert l2["candidate_mae"] < l2["baseline_mae"]
    assert l2["effect_size"] > 0
    assert set(results.get_column("production_status")) == {"EXPERIMENT_ONLY"}
    assert l4["candidate_mae"] < l4["baseline_mae"]
    assert regime["status"] == "not_run"
    assert "runner implemented" in regime["notes"]


def test_foehn_continuous_feature_probe_runs_experiment_only():
    labels, assignments, features = _foehn_feature_probe_frames()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog_with_foehn_feature_probe(),
        labels=labels,
        candidate_assignments=assignments,
        features=features,
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    result = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id") == "FEXP-FOEHN-CONTINUOUS-001"
    ).row(0, named=True)

    assert result["status"] == "passed"
    assert result["production_status"] == "EXPERIMENT_ONLY"
    assert result["candidate_mae"] < result["baseline_mae"]
    assert result["effect_size"] > 0
    assert result["n_rows"] == 20
    assert "binned foehn_score" in result["notes"]
    assert "RULE_FOEHN_SCORE_FIXED_60" in result["notes"]


def test_result_report_includes_feature_probe_section(tmp_path: Path):
    labels, assignments, features = _foehn_feature_probe_frames()
    artifacts = build_foundation_experiment_results(
        catalog=_catalog_with_foehn_feature_probe(),
        labels=labels,
        candidate_assignments=assignments,
        features=features,
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    paths = write_foundation_experiment_result_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    report = paths["foundation_experiment_results_md"].read_text(encoding="utf-8")
    assert "Feature Probe Results" in report
    assert "FEXP-FOEHN-CONTINUOUS-001" in report
    assert "RULE_FOEHN_SCORE_FIXED_60" in report


def test_runner_rejects_non_experiment_only_catalog_rows():
    labels, assignments = _labels_and_assignments()
    catalog = _catalog().with_columns(
        pl.when(pl.col("experiment_id") == "BEXP-L2-MONTH-REGIME-001")
        .then(pl.lit("PROMOTED"))
        .otherwise(pl.col("production_status"))
        .alias("production_status")
    )

    with pytest.raises(ValueError, match="EXPERIMENT_ONLY"):
        build_foundation_experiment_results(
            catalog=catalog,
            labels=labels,
            candidate_assignments=assignments,
            cp_set=("20:00",),
            test_starts=[dt.date(2021, 1, 1)],
            test_length_days=20,
            min_cell_rows=2,
            n_bootstrap=100,
            run_id="test-run",
        )


def test_runner_rejects_null_candidate_assignments():
    labels, assignments = _labels_and_assignments()
    assignments = assignments.with_columns(
        pl.when(pl.col("date_local") == dt.date(2021, 1, 1))
        .then(pl.lit(None))
        .otherwise(pl.col("candidate_regime_label"))
        .alias("candidate_regime_label")
    )

    with pytest.raises(ValueError, match="null candidate_regime_label"):
        build_foundation_experiment_results(
            catalog=_catalog(),
            labels=labels,
            candidate_assignments=assignments,
            cp_set=("20:00",),
            test_starts=[dt.date(2021, 1, 1)],
            test_length_days=20,
            min_cell_rows=2,
            n_bootstrap=100,
            run_id="test-run",
        )


def test_runner_rejects_duplicate_candidate_assignments():
    labels, assignments = _labels_and_assignments()
    assignments = pl.concat([assignments, assignments.head(1)])

    with pytest.raises(ValueError, match="duplicate candidate assignment"):
        build_foundation_experiment_results(
            catalog=_catalog(),
            labels=labels,
            candidate_assignments=assignments,
            cp_set=("20:00",),
            test_starts=[dt.date(2021, 1, 1)],
            test_length_days=20,
            min_cell_rows=2,
            n_bootstrap=100,
            run_id="test-run",
        )


def test_runner_rejects_assignment_contract_violations():
    labels, assignments = _labels_and_assignments()
    bad_status = assignments.with_columns(
        pl.lit("PROMOTED").alias("production_status")
    )

    with pytest.raises(ValueError, match="NOT_PRODUCTION"):
        build_foundation_experiment_results(
            catalog=_catalog(),
            labels=labels,
            candidate_assignments=bad_status,
            cp_set=("20:00",),
            test_starts=[dt.date(2021, 1, 1)],
            test_length_days=20,
            min_cell_rows=2,
            n_bootstrap=100,
            run_id="test-run",
        )

    bad_window = assignments.with_columns(
        pl.lit("valid <= CP").alias("causal_window")
    )
    with pytest.raises(ValueError, match="causal_window"):
        build_foundation_experiment_results(
            catalog=_catalog(),
            labels=labels,
            candidate_assignments=bad_window,
            cp_set=("20:00",),
            test_starts=[dt.date(2021, 1, 1)],
            test_length_days=20,
            min_cell_rows=2,
            n_bootstrap=100,
            run_id="test-run",
        )


def test_l4_support_uses_train_split_only(monkeypatch: pytest.MonkeyPatch):
    import solarstorm.onda2e._foundation_experiment_results as result_module

    label_rows: list[dict[str, object]] = []
    assignment_rows: list[dict[str, object]] = []
    for i in range(366):
        day = dt.date(2020, 1, 1) + dt.timedelta(days=i)
        label_rows.append(
            {
                "date_local": day,
                "day_complete": True,
                "tmax_int": 20,
                "k_cp__cp_2000": 18,
                "tmax_hour": 15,
            }
        )
        assignment_rows.append(
            {
                "date_local": day,
                "cp": "20:00",
                "candidate_regime_label": "candidate_train",
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )

    label_rows.append(
        {
            "date_local": dt.date(2021, 1, 1),
            "day_complete": True,
            "tmax_int": 5,
            "k_cp__cp_2000": 18,
            "tmax_hour": 15,
        }
    )
    assignment_rows.append(
        {
            "date_local": dt.date(2021, 1, 1),
            "cp": "20:00",
            "candidate_regime_label": "candidate_train",
            "causal_window": "valid < CP",
            "production_status": "NOT_PRODUCTION",
        }
    )
    captured_support: list[list[int]] = []

    class FakeEmpirical:
        def predict_dist(
            self,
            *,
            month: int,
            cp: str,
            k_cp: int,
            support_k: list[int],
        ) -> tuple[dict[int, float], str]:
            captured_support.append(list(support_k))
            return {support_k[0]: 1.0}, "test"

    def fake_fit_empirical_conditional(
        labels: pl.DataFrame,
        *,
        train_window: tuple[dt.date, dt.date],
    ) -> FakeEmpirical:
        return FakeEmpirical()

    monkeypatch.setattr(
        result_module,
        "fit_empirical_conditional",
        fake_fit_empirical_conditional,
    )

    build_foundation_experiment_results(
        catalog=_catalog(),
        labels=pl.DataFrame(label_rows),
        candidate_assignments=pl.DataFrame(assignment_rows),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=1,
        min_cell_rows=1,
        n_bootstrap=10,
        run_id="test-run",
    )

    assert captured_support
    assert all(support == [20] for support in captured_support)


def _dead_r2_rows(
    *,
    maritime_passes: bool = False,
    mixed_passes: bool = False,
    nw_passes: bool = True,
    southerly_passes: bool = True,
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for regime, passes in (
        ("candidate_maritime_cloudy", maritime_passes),
        ("candidate_mixed_or_transition", mixed_passes),
        ("candidate_nw_or_foehn", nw_passes),
        ("candidate_southerly_disrupted", southerly_passes),
    ):
        rows.append(
            {
                "regime": regime,
                "hypothesis_id": "H_TEST",
                "feature_column": "feat_signal",
                "cp": "20:00",
                "passes": passes,
                "n_days": 10 if passes else 0,
                "status": "validated" if passes else "rejected",
            }
        )
    return pl.DataFrame(rows)


def _v2_comparison_rows(
    *,
    production_status: str = "EXPERIMENT_ONLY",
    v2_dead_regimes: int = 0,
    protected_regressions: str = "",
    decision_update: str = "READY_FOR_FULL_ONDA4_RERUN",
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "production_status": production_status,
                "v2_dead_regimes": v2_dead_regimes,
                "protected_regressions": protected_regressions,
                "decision_update": decision_update,
            }
        ]
    )


def _v21_comparison_rows(
    *,
    production_status: str = "EXPERIMENT_ONLY",
    v21_dead_regimes: int = 0,
    protected_regression_flag: bool = False,
    decision_update: str = "READY_FOR_FULL_ONDA4_RERUN",
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "production_status": production_status,
                "v21_dead_regimes": v21_dead_regimes,
                "protected_regression_flag": protected_regression_flag,
                "decision_update": decision_update,
            }
        ]
    )


def test_dead_regime_results_can_use_v21_comparison_pass():
    labels, assignments = _labels_and_assignments()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog_with_mixed_dead_regime(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_v21_comparison=_v21_comparison_rows(),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    dead_results = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id").is_in(
            ["REXP-DEAD-MARITIME-001", "REXP-DEAD-MIXED-001"]
        )
    )

    assert dead_results.height == 2
    assert set(dead_results.get_column("status")) == {"passed"}
    assert set(dead_results.get_column("decision_update")) == {
        "READY_FOR_FULL_ONDA4_RERUN"
    }


def test_dead_regime_results_can_use_v2_comparison_pass():
    labels, assignments = _labels_and_assignments()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog_with_mixed_dead_regime(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_v2_comparison=_v2_comparison_rows(),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    dead_results = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id").is_in(
            ["REXP-DEAD-MARITIME-001", "REXP-DEAD-MIXED-001"]
        )
    )

    assert dead_results.height == 2
    assert set(dead_results.get_column("status")) == {"passed"}
    assert set(dead_results.get_column("r2_dead_regimes")) == {0}
    assert set(dead_results.get_column("decision_update")) == {
        "READY_FOR_FULL_ONDA4_RERUN"
    }
    assert all(
        "v2 comparison ready for full Onda 4 rerun" in notes
        for notes in dead_results.get_column("notes")
    )


def test_dead_regime_experiments_record_failed_current_r2():
    labels, assignments = _labels_and_assignments()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=_dead_r2_rows(),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    results = artifacts["foundation_experiment_results"]
    dead = results.filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001").row(
        0,
        named=True,
    )

    assert dead["status"] == "failed"
    assert dead["r2_dead_regimes"] == 2
    assert dead["n_rows"] == 0
    assert dead["baseline_mae"] is None
    assert dead["candidate_mae"] is None
    assert dead["effect_size"] is None
    assert dead["production_status"] == "EXPERIMENT_ONLY"
    assert "candidate_maritime_cloudy remains dead" in dead["notes"]


def test_dead_regime_experiment_passes_only_when_target_repairs_without_regression():
    labels, assignments = _labels_and_assignments()
    assignments = assignments.with_columns(
        pl.lit("candidate_maritime_cloudy").alias("candidate_regime_label")
    )

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=_dead_r2_rows(maritime_passes=True),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    maritime = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id") == "REXP-DEAD-MARITIME-001"
    ).row(0, named=True)

    assert maritime["status"] == "passed"
    assert maritime["r2_dead_regimes"] == 1
    assert maritime["n_rows"] == assignments.height


def test_dead_regime_experiment_fails_if_protected_family_regresses():
    labels, assignments = _labels_and_assignments()

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=_dead_r2_rows(
            maritime_passes=True,
            mixed_passes=True,
            nw_passes=False,
        ),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    maritime = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id") == "REXP-DEAD-MARITIME-001"
    ).row(0, named=True)

    assert maritime["status"] == "failed"
    assert maritime["r2_dead_regimes"] == 1
    assert "protected passing family regressed" in maritime["notes"]


def test_dead_regime_experiment_fails_if_target_family_disappears():
    labels, assignments = _labels_and_assignments()
    r2_without_maritime = _dead_r2_rows().filter(
        pl.col("regime") != "candidate_maritime_cloudy"
    )

    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=r2_without_maritime,
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    maritime = artifacts["foundation_experiment_results"].filter(
        pl.col("experiment_id") == "REXP-DEAD-MARITIME-001"
    ).row(0, named=True)

    assert maritime["status"] == "failed"
    assert maritime["r2_dead_regimes"] == 2
    assert "target_passes=0/0" in maritime["notes"]


def test_write_foundation_experiment_result_artifacts(tmp_path: Path):
    labels, assignments = _labels_and_assignments()
    artifacts = build_foundation_experiment_results(
        catalog=_catalog(),
        labels=labels,
        candidate_assignments=assignments,
        regime_candidate_r2_validation=_dead_r2_rows(),
        cp_set=("20:00",),
        test_starts=[dt.date(2021, 1, 1)],
        test_length_days=20,
        min_cell_rows=2,
        n_bootstrap=100,
        run_id="test-run",
    )

    paths = write_foundation_experiment_result_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 7),
    )

    assert (tmp_path / "foundation_experiment_results_v1.csv").exists()
    assert (tmp_path / "foundation_experiment_results_v1.md").exists()
    report = paths["foundation_experiment_results_md"].read_text(encoding="utf-8")
    assert "Foundation Experiment Results - 2026-06-07" in report
    assert "experiment-only" in report
    assert "BEXP-L2-MONTH-REGIME-001" in report
    assert "Regime R2 Results" in report
    assert "REXP-DEAD-MARITIME-001" in report
    persisted = pl.read_csv(tmp_path / "foundation_experiment_results_v1.csv")
    assert set(persisted.get_column("result_artifact")) == {
        str(tmp_path / "foundation_experiment_results_v1.csv")
    }


def test_foundation_experiment_results_cli_runs_dead_regime_experiments(tmp_path: Path):
    labels, assignments = _labels_and_assignments()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v1.csv"
    r2_path = tmp_path / "regime_candidate_r2_validation.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)
    _dead_r2_rows().write_csv(r2_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--regime-candidate-r2-path",
            str(r2_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output
    persisted = pl.read_csv(output_dir / "foundation_experiment_results_v1.csv")
    dead = persisted.filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001").row(
        0,
        named=True,
    )
    assert dead["status"] == "failed"
    assert dead["r2_dead_regimes"] == 2


def test_foundation_experiment_results_cli_runs_foehn_feature_probe(tmp_path: Path):
    labels, assignments, features = _foehn_feature_probe_frames()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v1.csv"
    features_path = tmp_path / "features.parquet"
    output_dir = tmp_path / "foundation-experiments"
    _catalog_with_foehn_feature_probe().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)
    features.write_parquet(features_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--features-path",
            str(features_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output
    persisted = pl.read_csv(output_dir / "foundation_experiment_results_v1.csv")
    foehn = persisted.filter(
        pl.col("experiment_id") == "FEXP-FOEHN-CONTINUOUS-001"
    ).row(0, named=True)
    assert foehn["status"] == "passed"
    assert foehn["production_status"] == "EXPERIMENT_ONLY"


def test_foundation_experiment_results_cli_uses_v2_comparison(tmp_path: Path):
    labels, assignments = _labels_and_assignments()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v2.csv"
    r2_path = tmp_path / "regime_candidate_r2_validation_v2.csv"
    comparison_path = tmp_path / "regime_candidate_v1_v2_comparison.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)
    _dead_r2_rows().write_csv(r2_path)
    _v2_comparison_rows().write_csv(comparison_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--regime-candidate-r2-path",
            str(r2_path),
            "--regime-candidate-v2-comparison-path",
            str(comparison_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output
    persisted = pl.read_csv(output_dir / "foundation_experiment_results_v1.csv")
    dead = persisted.filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001").row(
        0,
        named=True,
    )
    assert dead["status"] == "passed"
    assert dead["r2_dead_regimes"] == 0
    assert dead["decision_update"] == "READY_FOR_FULL_ONDA4_RERUN"


def test_foundation_experiment_results_cli_uses_v21_comparison(tmp_path: Path):
    labels, assignments = _labels_and_assignments()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v2_1.csv"
    r2_path = tmp_path / "regime_candidate_r2_validation_v2_1.csv"
    comparison_path = tmp_path / "regime_candidate_v2_v21_comparison.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)
    _dead_r2_rows().write_csv(r2_path)
    _v21_comparison_rows().write_csv(comparison_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--regime-candidate-r2-path",
            str(r2_path),
            "--regime-candidate-v21-comparison-path",
            str(comparison_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output
    persisted = pl.read_csv(output_dir / "foundation_experiment_results_v1.csv")
    dead = persisted.filter(pl.col("experiment_id") == "REXP-DEAD-MARITIME-001").row(
        0,
        named=True,
    )
    assert dead["status"] == "passed"
    assert dead["r2_dead_regimes"] == 0
    assert dead["decision_update"] == "READY_FOR_FULL_ONDA4_RERUN"


def test_foundation_experiment_results_cli_rejects_missing_explicit_r2_path(
    tmp_path: Path,
):
    labels, assignments = _labels_and_assignments()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v1.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--regime-candidate-r2-path",
            str(tmp_path / "missing_r2.csv"),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 2
    assert "candidate R2 validation file not found" in result.output


def test_foundation_experiment_results_cli_writes_artifacts(tmp_path: Path):
    labels, assignments = _labels_and_assignments()
    catalog_path = tmp_path / "foundation_experiment_catalog_v1.csv"
    labels_path = tmp_path / "labels.parquet"
    assignments_path = tmp_path / "regime_candidate_assignments_v1.csv"
    output_dir = tmp_path / "foundation-experiments"
    _catalog().write_csv(catalog_path)
    labels.write_parquet(labels_path)
    assignments.write_csv(assignments_path)

    result = runner.invoke(
        app,
        [
            "foundation-experiment-results",
            "--catalog-path",
            str(catalog_path),
            "--labels-path",
            str(labels_path),
            "--assignments-path",
            str(assignments_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--test-start",
            "2021-01-01",
            "--test-length-days",
            "20",
            "--min-cell-rows",
            "2",
            "--n-bootstrap",
            "100",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "foundation_experiment_results_v1.csv").exists()
    persisted = pl.read_csv(output_dir / "foundation_experiment_results_v1.csv")
    assert "BEXP-L4-MONTH-CP-REGIME-001" in set(persisted.get_column("experiment_id"))
