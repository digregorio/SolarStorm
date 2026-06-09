"""Experiment-only result runner for the Foundation Experiment Catalog."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.baselines._climatology import fit_climatology
from solarstorm.baselines._empirical import fit_empirical_conditional
from solarstorm.data._settlement import integer_settlement
from solarstorm.eval._bootstrap import bootstrap_ci_diff
from solarstorm.eval._metrics import bias, mae, rmse
from solarstorm.eval._walkforward import expanding_walk_forward_splits
from solarstorm.robustness._regime_analysis import detect_dead_regimes

FOUNDATION_RESULT_SCHEMA: dict[str, pl.DataType] = {
    "experiment_id": pl.Utf8,
    "run_id": pl.Utf8,
    "status": pl.Utf8,
    "result_artifact": pl.Utf8,
    "baseline_mae": pl.Float64,
    "candidate_mae": pl.Float64,
    "effect_size": pl.Float64,
    "ci_lo": pl.Float64,
    "ci_hi": pl.Float64,
    "n_rows": pl.Int64,
    "n_years": pl.Int64,
    "r2_dead_regimes": pl.Int64,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
    "notes": pl.Utf8,
}

_RUNNABLE_BASELINES = frozenset(
    {
        "BEXP-L2-MONTH-REGIME-001",
        "BEXP-L4-MONTH-CP-REGIME-001",
    }
)
_RUNNABLE_FEATURE_PROBES = frozenset({"FEXP-FOEHN-CONTINUOUS-001"})
_DEAD_REGIME_EXPERIMENT_TARGETS = {
    "REXP-DEAD-MARITIME-001": "candidate_maritime_cloudy",
    "REXP-DEAD-MIXED-001": "candidate_mixed_or_transition",
}
_BASELINE_DEAD_REGIME_COUNT = len(_DEAD_REGIME_EXPERIMENT_TARGETS)
_PROTECTED_PASSING_FAMILIES = frozenset(
    {
        "candidate_nw_or_foehn",
        "candidate_southerly_disrupted",
    }
)


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _run_id() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H%M%SZ")


def _default_test_starts(labels: pl.DataFrame) -> list[dt.date]:
    complete = labels.filter(pl.col("day_complete"))
    first_complete = complete["date_local"].min() if complete.height else None
    if first_complete is None:
        return []
    first_test_year = max(first_complete.year + 5, 2014)
    last_year = min(2025, complete["date_local"].max().year)
    if first_test_year > last_year:
        return []
    return [dt.date(year, 1, 1) for year in range(first_test_year, last_year + 1)]


def _date_columns(labels: pl.DataFrame, assignments: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    labels_out = labels
    assignments_out = assignments
    if labels_out.schema.get("date_local") == pl.Utf8:
        labels_out = labels_out.with_columns(
            pl.col("date_local").str.strptime(pl.Date, strict=False)
        )
    if assignments_out.schema.get("date_local") == pl.Utf8:
        assignments_out = assignments_out.with_columns(
            pl.col("date_local").str.strptime(pl.Date, strict=False)
        )
    return labels_out, assignments_out


def _date_column(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.schema.get("date_local") == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.strptime(pl.Date, strict=False))
    return frame


def _context(labels: pl.DataFrame, assignments: pl.DataFrame, cp_set: tuple[str, ...]) -> pl.DataFrame:
    if not cp_set:
        raise ValueError("cp_set must contain at least one CP")
    labels, assignments = _date_columns(labels, assignments)
    labels_ok = labels.filter(
        pl.col("day_complete")
        & pl.col("tmax_int").is_not_null()
    )
    required_assignment_cols = {
        "date_local",
        "cp",
        "candidate_regime_label",
        "causal_window",
        "production_status",
    }
    missing = required_assignment_cols - set(assignments.columns)
    if missing:
        raise ValueError(
            "candidate_assignments missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    filtered_assignments = assignments.filter(pl.col("cp").is_in(cp_set))
    if filtered_assignments.filter(pl.col("candidate_regime_label").is_null()).height:
        raise ValueError("candidate_assignments contains null candidate_regime_label")
    invalid_status = filtered_assignments.filter(pl.col("production_status") != "NOT_PRODUCTION")
    if invalid_status.height:
        raise ValueError("candidate_assignments production_status must be NOT_PRODUCTION")
    invalid_window = filtered_assignments.filter(pl.col("causal_window") != "valid < CP")
    if invalid_window.height:
        raise ValueError("candidate_assignments causal_window must be valid < CP")
    duplicate_keys = (
        filtered_assignments.group_by(["date_local", "cp"])
        .len(name="n")
        .filter(pl.col("n") > 1)
    )
    if duplicate_keys.height:
        raise ValueError("candidate_assignments contains duplicate candidate assignment rows")
    joined = (
        filtered_assignments.select(["date_local", "cp", "candidate_regime_label"])
        .join(labels_ok, on="date_local", how="inner")
        .with_columns(pl.col("date_local").dt.month().alias("month"))
        .sort(["date_local", "cp"])
    )
    return joined


def _cp_col(cp: str) -> str:
    return f"k_cp__cp_{cp.replace(':', '')}"


def _foehn_score_bin_expr() -> pl.Expr:
    return (
        pl.when(pl.col("foehn_score").is_null())
        .then(pl.lit("missing"))
        .when(pl.col("foehn_score") < 20.0)
        .then(pl.lit("lt_20"))
        .when(pl.col("foehn_score") < 40.0)
        .then(pl.lit("20_40"))
        .when(pl.col("foehn_score") < 60.0)
        .then(pl.lit("40_60"))
        .when(pl.col("foehn_score") < 80.0)
        .then(pl.lit("60_80"))
        .otherwise(pl.lit("gte_80"))
        .alias("foehn_score_bin")
    )


def _prediction_metrics(
    *,
    baseline_pred: list[float],
    candidate_pred: list[float],
    truth: list[float],
    n_bootstrap: int,
) -> tuple[float, float, float, float, float, float, float]:
    baseline_arr = np.array(baseline_pred, dtype=float)
    candidate_arr = np.array(candidate_pred, dtype=float)
    truth_arr = np.array(truth, dtype=float)
    baseline_errors = np.abs(baseline_arr - truth_arr)
    candidate_errors = np.abs(candidate_arr - truth_arr)
    effect, ci_lo, ci_hi = bootstrap_ci_diff(
        baseline_errors,
        candidate_errors,
        n_bootstrap=n_bootstrap,
    )
    return (
        mae(baseline_arr, truth_arr),
        mae(candidate_arr, truth_arr),
        effect,
        ci_lo,
        ci_hi,
        rmse(candidate_arr, truth_arr),
        bias(candidate_arr, truth_arr),
    )


def _result_row(
    *,
    experiment_id: str,
    run_id: str,
    status: str,
    baseline_mae: float | None = None,
    candidate_mae: float | None = None,
    effect_size: float | None = None,
    ci_lo: float | None = None,
    ci_hi: float | None = None,
    n_rows: int = 0,
    n_years: int = 0,
    r2_dead_regimes: int | None = None,
    decision_update: str = "",
    notes: str = "",
) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "status": status,
        "result_artifact": "reports/foundation-experiments/foundation_experiment_results_v1.csv",
        "baseline_mae": baseline_mae,
        "candidate_mae": candidate_mae,
        "effect_size": effect_size,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "n_rows": n_rows,
        "n_years": n_years,
        "r2_dead_regimes": r2_dead_regimes,
        "decision_update": decision_update,
        "production_status": "EXPERIMENT_ONLY",
        "notes": notes,
    }


def _train_test_context(
    context: pl.DataFrame,
    *,
    train_start: dt.date,
    train_end: dt.date,
    test_start: dt.date,
    test_end: dt.date,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    train = context.filter(pl.col("date_local").is_between(train_start, train_end))
    test = context.filter(pl.col("date_local").is_between(test_start, test_end))
    return train, test


def _lookup_mean(
    frame: pl.DataFrame,
    columns: list[str],
    value_column: str,
    *,
    min_cell_rows: int,
) -> dict[tuple[object, ...], float]:
    if frame.height == 0:
        return {}
    grouped = (
        frame.group_by(columns)
        .agg(
            pl.col(value_column).mean().alias("mean_value"),
            pl.len().alias("n_rows"),
        )
        .filter(pl.col("n_rows") >= min_cell_rows)
    )
    return {
        tuple(row[column] for column in columns): float(row["mean_value"])
        for row in grouped.iter_rows(named=True)
    }


def _run_l2_month_regime(
    *,
    labels: pl.DataFrame,
    context: pl.DataFrame,
    splits: list,
    run_id: str,
    min_cell_rows: int,
    n_bootstrap: int,
) -> dict[str, object]:
    baseline_pred: list[float] = []
    candidate_pred: list[float] = []
    truth: list[float] = []
    years: set[int] = set()
    labels_ok = labels.filter(pl.col("day_complete") & pl.col("tmax_int").is_not_null())
    support_month_mean: dict[int, float] = {}

    for split in splits:
        train, test = _train_test_context(
            context,
            train_start=split.train_start,
            train_end=split.train_end,
            test_start=split.test_start,
            test_end=split.test_end,
        )
        if train.height == 0 or test.height == 0:
            continue
        climo = fit_climatology(
            labels_ok,
            train_start=split.train_start,
            train_end=split.train_end,
        )
        candidate_means = _lookup_mean(
            train,
            ["month", "candidate_regime_label"],
            "tmax_int",
            min_cell_rows=min_cell_rows,
        )
        month_means = _lookup_mean(
            train,
            ["month"],
            "tmax_int",
            min_cell_rows=1,
        )
        support_month_mean.update({int(key[0]): value for key, value in month_means.items()})

        for row in test.iter_rows(named=True):
            key = (row["month"], row["candidate_regime_label"])
            candidate = candidate_means.get(key, support_month_mean.get(int(row["month"])))
            if candidate is None:
                continue
            baseline_pred.append(float(integer_settlement(climo.tmax_dec_for(row["date_local"]))))
            candidate_pred.append(float(integer_settlement(candidate)))
            truth.append(float(row["tmax_int"]))
            years.add(row["date_local"].year)

    if not truth:
        return _result_row(
            experiment_id="BEXP-L2-MONTH-REGIME-001",
            run_id=run_id,
            status="blocked",
            notes="No evaluable rows for month/regime climatology experiment.",
        )
    baseline_mae, candidate_mae, effect, ci_lo, ci_hi, candidate_rmse, candidate_bias = (
        _prediction_metrics(
            baseline_pred=baseline_pred,
            candidate_pred=candidate_pred,
            truth=truth,
            n_bootstrap=n_bootstrap,
        )
    )
    status = "passed" if effect > 0 and ci_lo >= 0 else "failed"
    return _result_row(
        experiment_id="BEXP-L2-MONTH-REGIME-001",
        run_id=run_id,
        status=status,
        baseline_mae=baseline_mae,
        candidate_mae=candidate_mae,
        effect_size=effect,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        n_rows=len(truth),
        n_years=len(years),
        notes=(
            "Train-only month x candidate-regime climatology. "
            f"candidate_rmse={candidate_rmse:.3f}; candidate_bias={candidate_bias:.3f}."
        ),
    )


def _run_l4_month_cp_regime(
    *,
    labels: pl.DataFrame,
    context: pl.DataFrame,
    splits: list,
    run_id: str,
    min_cell_rows: int,
    n_bootstrap: int,
) -> dict[str, object]:
    baseline_pred: list[float] = []
    candidate_pred: list[float] = []
    truth: list[float] = []
    years: set[int] = set()
    labels_ok = labels.filter(pl.col("day_complete") & pl.col("tmax_int").is_not_null())

    for split in splits:
        train, test = _train_test_context(
            context,
            train_start=split.train_start,
            train_end=split.train_end,
            test_start=split.test_start,
            test_end=split.test_end,
        )
        if train.height == 0 or test.height == 0:
            continue
        train_labels = labels_ok.filter(
            pl.col("date_local").is_between(split.train_start, split.train_end)
        )
        support_k = sorted(
            int(value) for value in train_labels["tmax_int"].drop_nulls().unique()
        )
        if not support_k:
            continue
        emp = fit_empirical_conditional(
            labels_ok,
            train_window=(split.train_start, split.train_end),
        )

        train_rows: list[dict[str, object]] = []
        for row in train.iter_rows(named=True):
            cp_col = _cp_col(str(row["cp"]))
            k_cp = row.get(cp_col)
            if k_cp is None:
                continue
            train_rows.append(
                {
                    **row,
                    "remaining_warming": float(row["tmax_int"] - k_cp),
                }
            )
        train_with_rw = pl.DataFrame(train_rows) if train_rows else _empty_frame({})
        candidate_means = (
            _lookup_mean(
                train_with_rw,
                ["month", "cp", "candidate_regime_label"],
                "remaining_warming",
                min_cell_rows=min_cell_rows,
            )
            if train_with_rw.height
            else {}
        )
        fallback_means = (
            _lookup_mean(
                train_with_rw,
                ["month", "cp"],
                "remaining_warming",
                min_cell_rows=1,
            )
            if train_with_rw.height
            else {}
        )

        for row in test.iter_rows(named=True):
            cp = str(row["cp"])
            cp_col = _cp_col(cp)
            k_cp = row.get(cp_col)
            if k_cp is None:
                continue
            key = (row["month"], cp, row["candidate_regime_label"])
            fallback_key = (row["month"], cp)
            candidate_rw = candidate_means.get(key, fallback_means.get(fallback_key))
            if candidate_rw is None:
                continue
            dist, _source = emp.predict_dist(
                month=int(row["month"]),
                cp=cp,
                k_cp=int(k_cp),
                support_k=support_k,
            )
            baseline_tmax = max(dist, key=dist.get)
            baseline_pred.append(float(baseline_tmax))
            candidate_pred.append(float(integer_settlement(float(k_cp) + candidate_rw)))
            truth.append(float(row["tmax_int"]))
            years.add(row["date_local"].year)

    if not truth:
        return _result_row(
            experiment_id="BEXP-L4-MONTH-CP-REGIME-001",
            run_id=run_id,
            status="blocked",
            notes="No evaluable rows for month/CP/candidate-regime remaining-warming experiment.",
        )
    baseline_mae, candidate_mae, effect, ci_lo, ci_hi, candidate_rmse, candidate_bias = (
        _prediction_metrics(
            baseline_pred=baseline_pred,
            candidate_pred=candidate_pred,
            truth=truth,
            n_bootstrap=n_bootstrap,
        )
    )
    status = "passed" if effect > 0 and ci_lo >= 0 else "failed"
    return _result_row(
        experiment_id="BEXP-L4-MONTH-CP-REGIME-001",
        run_id=run_id,
        status=status,
        baseline_mae=baseline_mae,
        candidate_mae=candidate_mae,
        effect_size=effect,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        n_rows=len(truth),
        n_years=len(years),
        notes=(
            "Train-only month x CP x candidate-regime remaining-warming baseline. "
            f"candidate_rmse={candidate_rmse:.3f}; candidate_bias={candidate_bias:.3f}."
        ),
    )


def _normalized_r2_validation(regime_candidate_r2_validation: pl.DataFrame) -> pl.DataFrame:
    if regime_candidate_r2_validation.height == 0:
        return regime_candidate_r2_validation
    required = {"regime", "passes"}
    missing = required - set(regime_candidate_r2_validation.columns)
    if missing:
        raise ValueError(
            "regime_candidate_r2_validation missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    if regime_candidate_r2_validation.schema.get("passes") == pl.Boolean:
        return regime_candidate_r2_validation
    return regime_candidate_r2_validation.with_columns(
        pl.col("passes")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .is_in(["true", "1", "yes"])
        .alias("passes")
    )


def _assignment_support_count(
    candidate_assignments: pl.DataFrame,
    *,
    family: str,
    cp_set: tuple[str, ...],
) -> int:
    filtered = candidate_assignments.filter(pl.col("cp").is_in(cp_set))
    support_expr = pl.col("candidate_regime_label") == family
    if "candidate_regime_family" in filtered.columns:
        support_expr = support_expr | (pl.col("candidate_regime_family") == family)
    return filtered.filter(support_expr).height


def _run_dead_regime_experiment(
    *,
    experiment_id: str,
    regime_candidate_r2_validation: pl.DataFrame,
    candidate_assignments: pl.DataFrame,
    cp_set: tuple[str, ...],
    run_id: str,
) -> dict[str, object]:
    target_family = _DEAD_REGIME_EXPERIMENT_TARGETS[experiment_id]
    r2 = _normalized_r2_validation(regime_candidate_r2_validation)
    if r2.height == 0:
        return _result_row(
            experiment_id=experiment_id,
            run_id=run_id,
            status="blocked",
            notes="No candidate R2 validation rows available for dead-regime experiment.",
        )
    families = sorted(
        set(str(value) for value in r2["regime"].drop_nulls().unique())
        | set(_DEAD_REGIME_EXPERIMENT_TARGETS.values())
        | set(_PROTECTED_PASSING_FAMILIES)
    )
    dead = set(detect_dead_regimes(r2, regimes=families))
    dead_count = len(dead)
    protected_regressions = sorted(_PROTECTED_PASSING_FAMILIES & dead)
    target_rows = r2.filter(pl.col("regime") == target_family)
    target_passes = int(target_rows.filter(pl.col("passes")).height)
    support_rows = _assignment_support_count(
        candidate_assignments,
        family=target_family,
        cp_set=cp_set,
    )
    if target_family in dead:
        status = "failed"
        target_clause = f"{target_family} remains dead"
    else:
        target_clause = f"{target_family} has at least one passing R2 row"
        status = (
            "passed"
            if dead_count < _BASELINE_DEAD_REGIME_COUNT and not protected_regressions
            else "failed"
        )
    notes = (
        f"{target_clause}; target_passes={target_passes}/{target_rows.height}; "
        f"assignment_support_rows={support_rows}; global_dead_regimes={dead_count}."
    )
    if protected_regressions:
        notes += (
            " protected passing family regressed: "
            f"{', '.join(protected_regressions)}."
        )
    return _result_row(
        experiment_id=experiment_id,
        run_id=run_id,
        status=status,
        n_rows=support_rows,
        r2_dead_regimes=dead_count,
        notes=notes,
    )


def _comparison_value(row: dict[str, object], column: str) -> object:
    if column not in row:
        raise ValueError(
            "regime_candidate_v2_comparison missing required columns: "
            f"{column}"
        )
    return row[column]


def _protected_regressions_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return stripped == "" or stripped == "[]"
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    return False


def _v2_comparison_row(
    regime_candidate_v2_comparison: pl.DataFrame,
    *,
    experiment_id: str,
) -> dict[str, object]:
    required = {
        "production_status",
        "v2_dead_regimes",
        "protected_regressions",
        "decision_update",
    }
    missing = required - set(regime_candidate_v2_comparison.columns)
    if missing:
        raise ValueError(
            "regime_candidate_v2_comparison missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    invalid = regime_candidate_v2_comparison.filter(
        pl.col("production_status") != "EXPERIMENT_ONLY"
    )
    if invalid.height:
        raise ValueError("regime_candidate_v2_comparison production_status must be EXPERIMENT_ONLY")
    comparison = regime_candidate_v2_comparison
    if "experiment_id" in comparison.columns:
        matched = comparison.filter(pl.col("experiment_id") == experiment_id)
        if matched.height:
            comparison = matched
    return comparison.row(0, named=True)


def _v21_comparison_row(
    regime_candidate_v21_comparison: pl.DataFrame,
    *,
    experiment_id: str,
) -> dict[str, object]:
    required = {
        "production_status",
        "v21_dead_regimes",
        "protected_regression_flag",
        "decision_update",
    }
    missing = required - set(regime_candidate_v21_comparison.columns)
    if missing:
        raise ValueError(
            "regime_candidate_v21_comparison missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    invalid = regime_candidate_v21_comparison.filter(
        pl.col("production_status") != "EXPERIMENT_ONLY"
    )
    if invalid.height:
        raise ValueError(
            "regime_candidate_v21_comparison production_status must be EXPERIMENT_ONLY"
        )
    comparison = regime_candidate_v21_comparison
    if "experiment_id" in comparison.columns:
        matched = comparison.filter(pl.col("experiment_id") == experiment_id)
        if matched.height:
            comparison = matched
    return comparison.row(0, named=True)


def _v21_has_protected_regression(
    regime_candidate_v21_comparison: pl.DataFrame,
    *,
    experiment_id: str,
) -> bool:
    comparison = regime_candidate_v21_comparison
    if "experiment_id" in comparison.columns:
        matched = comparison.filter(pl.col("experiment_id") == experiment_id)
        if matched.height:
            comparison = matched
    flags = comparison.get_column("protected_regression_flag")
    if flags.dtype == pl.Boolean:
        return bool(flags.fill_null(False).any())
    return bool(
        flags.cast(pl.Utf8)
        .str.to_lowercase()
        .is_in(["true", "1", "yes"])
        .fill_null(False)
        .any()
    )


def _v21_comparison_value(row: dict[str, object], column: str) -> object:
    if column not in row:
        raise ValueError(
            "regime_candidate_v21_comparison missing required columns: "
            f"{column}"
        )
    return row[column]


def _run_v21_comparison_dead_regime_experiment(
    *,
    experiment_id: str,
    regime_candidate_v21_comparison: pl.DataFrame,
    run_id: str,
) -> dict[str, object]:
    row = _v21_comparison_row(
        regime_candidate_v21_comparison,
        experiment_id=experiment_id,
    )
    dead_regimes = int(_v21_comparison_value(row, "v21_dead_regimes"))
    protected_regression = _v21_has_protected_regression(
        regime_candidate_v21_comparison,
        experiment_id=experiment_id,
    )
    decision_update = str(_v21_comparison_value(row, "decision_update"))
    ready = (
        dead_regimes == 0
        and not protected_regression
        and decision_update == "READY_FOR_FULL_ONDA4_RERUN"
    )
    if ready:
        status = "passed"
        notes = "v2.1 comparison ready for full Onda 4 rerun."
    else:
        status = "failed"
        notes = "v2.1 remains in design review."
    return _result_row(
        experiment_id=experiment_id,
        run_id=run_id,
        status=status,
        r2_dead_regimes=dead_regimes,
        decision_update=decision_update,
        notes=notes,
    )


def _run_v2_comparison_dead_regime_experiment(
    *,
    experiment_id: str,
    regime_candidate_v2_comparison: pl.DataFrame,
    run_id: str,
) -> dict[str, object]:
    row = _v2_comparison_row(
        regime_candidate_v2_comparison,
        experiment_id=experiment_id,
    )
    dead_regimes = int(_comparison_value(row, "v2_dead_regimes"))
    protected_regressions = _comparison_value(row, "protected_regressions")
    decision_update = str(_comparison_value(row, "decision_update"))
    ready = (
        dead_regimes == 0
        and _protected_regressions_empty(protected_regressions)
        and decision_update == "READY_FOR_FULL_ONDA4_RERUN"
    )
    if ready:
        status = "passed"
        notes = "v2 comparison ready for full Onda 4 rerun."
    else:
        status = "failed"
        notes = "v2 remains in design review."
    return _result_row(
        experiment_id=experiment_id,
        run_id=run_id,
        status=status,
        r2_dead_regimes=dead_regimes,
        decision_update=decision_update,
        notes=notes,
    )


def _foehn_feature_context(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    cp_set: tuple[str, ...],
) -> pl.DataFrame:
    required = {"date_local", "cp", "foehn_score"}
    missing = required - set(features.columns)
    if missing:
        raise ValueError(
            "features missing required FOEHN probe columns: "
            f"{', '.join(sorted(missing))}"
        )
    features = _date_column(features)
    labels = _date_column(labels)
    labels_ok = labels.filter(pl.col("day_complete") & pl.col("tmax_int").is_not_null())
    joined = (
        features.filter(pl.col("cp").is_in(cp_set))
        .join(labels_ok, on="date_local", how="inner")
        .with_columns(
            pl.col("date_local").dt.month().alias("month"),
            _foehn_score_bin_expr(),
        )
        .sort(["date_local", "cp"])
    )
    duplicate_keys = joined.group_by(["date_local", "cp"]).len(name="n").filter(pl.col("n") > 1)
    if duplicate_keys.height:
        raise ValueError("features contains duplicate FOEHN probe rows")
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        cp = str(row["cp"])
        k_cp = row.get(_cp_col(cp))
        tmax = row.get("tmax_int")
        foehn_score = row.get("foehn_score")
        if k_cp is None or tmax is None or foehn_score is None:
            continue
        rows.append(
            {
                **row,
                "remaining_warming": float(tmax - k_cp),
                "fixed_60_trigger": float(foehn_score) > 60.0,
            }
        )
    return pl.DataFrame(rows) if rows else _empty_frame({})


def _run_foehn_continuous_probe(
    *,
    labels: pl.DataFrame,
    features: pl.DataFrame | None,
    cp_set: tuple[str, ...],
    splits: list,
    run_id: str,
    min_cell_rows: int,
    n_bootstrap: int,
) -> dict[str, object]:
    experiment_id = "FEXP-FOEHN-CONTINUOUS-001"
    if features is None:
        return _result_row(
            experiment_id=experiment_id,
            run_id=run_id,
            status="blocked",
            notes="features parquet is required to run the experiment-only FOEHN feature probe.",
        )
    context = _foehn_feature_context(features=features, labels=labels, cp_set=cp_set)
    if context.height == 0:
        return _result_row(
            experiment_id=experiment_id,
            run_id=run_id,
            status="blocked",
            notes="No evaluable FOEHN feature rows after joining features to labels.",
        )

    baseline_pred: list[float] = []
    candidate_pred: list[float] = []
    truth: list[float] = []
    years: set[int] = set()
    fallback_rows = 0

    for split in splits:
        train, test = _train_test_context(
            context,
            train_start=split.train_start,
            train_end=split.train_end,
            test_start=split.test_start,
            test_end=split.test_end,
        )
        if train.height == 0 or test.height == 0:
            continue
        fixed_means = _lookup_mean(
            train,
            ["month", "cp", "fixed_60_trigger"],
            "remaining_warming",
            min_cell_rows=min_cell_rows,
        )
        score_bin_means = _lookup_mean(
            train,
            ["month", "cp", "foehn_score_bin"],
            "remaining_warming",
            min_cell_rows=min_cell_rows,
        )
        fallback_means = _lookup_mean(
            train,
            ["month", "cp"],
            "remaining_warming",
            min_cell_rows=1,
        )
        for row in test.iter_rows(named=True):
            cp = str(row["cp"])
            k_cp = row.get(_cp_col(cp))
            if k_cp is None:
                continue
            fixed_key = (row["month"], cp, row["fixed_60_trigger"])
            bin_key = (row["month"], cp, row["foehn_score_bin"])
            fallback_key = (row["month"], cp)
            baseline_rw = fixed_means.get(fixed_key, fallback_means.get(fallback_key))
            candidate_rw = score_bin_means.get(bin_key, fallback_means.get(fallback_key))
            if baseline_rw is None or candidate_rw is None:
                continue
            if bin_key not in score_bin_means:
                fallback_rows += 1
            baseline_pred.append(float(integer_settlement(float(k_cp) + baseline_rw)))
            candidate_pred.append(float(integer_settlement(float(k_cp) + candidate_rw)))
            truth.append(float(row["tmax_int"]))
            years.add(row["date_local"].year)

    if not truth:
        return _result_row(
            experiment_id=experiment_id,
            run_id=run_id,
            status="blocked",
            notes="No evaluable rows for binned foehn_score feature probe.",
        )
    baseline_mae, candidate_mae, effect, ci_lo, ci_hi, candidate_rmse, candidate_bias = (
        _prediction_metrics(
            baseline_pred=baseline_pred,
            candidate_pred=candidate_pred,
            truth=truth,
            n_bootstrap=n_bootstrap,
        )
    )
    status = "passed" if effect > 0 and ci_lo >= 0 else "failed"
    return _result_row(
        experiment_id=experiment_id,
        run_id=run_id,
        status=status,
        baseline_mae=baseline_mae,
        candidate_mae=candidate_mae,
        effect_size=effect,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        n_rows=len(truth),
        n_years=len(years),
        notes=(
            "Experiment-only binned foehn_score probe versus "
            "RULE_FOEHN_SCORE_FIXED_60 comparator; "
            f"candidate_rmse={candidate_rmse:.3f}; candidate_bias={candidate_bias:.3f}; "
            f"fallback_rows={fallback_rows}."
        ),
    )


def build_foundation_experiment_results(
    *,
    catalog: pl.DataFrame,
    labels: pl.DataFrame,
    candidate_assignments: pl.DataFrame,
    features: pl.DataFrame | None = None,
    regime_candidate_r2_validation: pl.DataFrame | None = None,
    regime_candidate_v21_comparison: pl.DataFrame | None = None,
    regime_candidate_v2_comparison: pl.DataFrame | None = None,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    test_starts: list[dt.date] | None = None,
    test_length_days: int = 365,
    min_cell_rows: int = 30,
    n_bootstrap: int = 1000,
    run_id: str | None = None,
) -> dict[str, pl.DataFrame]:
    """Run implemented foundation experiments and mark the rest as not_run."""
    resolved_run_id = run_id or _run_id()
    if "production_status" not in catalog.columns:
        raise ValueError("catalog missing production_status column")
    invalid = catalog.filter(pl.col("production_status") != "EXPERIMENT_ONLY")
    if invalid.height:
        ids = ", ".join(str(value) for value in invalid.get_column("experiment_id").to_list())
        raise ValueError(f"Foundation experiments must remain EXPERIMENT_ONLY: {ids}")
    labels, candidate_assignments = _date_columns(labels, candidate_assignments)
    labels_ok = labels.filter(pl.col("day_complete") & pl.col("tmax_int").is_not_null())
    if labels_ok.height == 0:
        raise ValueError("labels has no complete rows with tmax_int")
    starts = test_starts or _default_test_starts(labels_ok)
    splits = expanding_walk_forward_splits(
        history_start=labels_ok["date_local"].min(),
        test_starts=starts,
        test_length_days=test_length_days,
        min_train_days=365,
    )
    if not splits:
        raise ValueError("No walk-forward splits available for foundation experiments.")
    context = _context(labels_ok, candidate_assignments, cp_set)

    result_by_id: dict[str, dict[str, object]] = {}
    if "BEXP-L2-MONTH-REGIME-001" in set(catalog.get_column("experiment_id")):
        result_by_id["BEXP-L2-MONTH-REGIME-001"] = _run_l2_month_regime(
            labels=labels_ok,
            context=context,
            splits=splits,
            run_id=resolved_run_id,
            min_cell_rows=min_cell_rows,
            n_bootstrap=n_bootstrap,
        )
    if "BEXP-L4-MONTH-CP-REGIME-001" in set(catalog.get_column("experiment_id")):
        result_by_id["BEXP-L4-MONTH-CP-REGIME-001"] = _run_l4_month_cp_regime(
            labels=labels_ok,
            context=context,
            splits=splits,
            run_id=resolved_run_id,
            min_cell_rows=min_cell_rows,
            n_bootstrap=n_bootstrap,
        )
    if "FEXP-FOEHN-CONTINUOUS-001" in set(catalog.get_column("experiment_id")):
        result_by_id["FEXP-FOEHN-CONTINUOUS-001"] = _run_foehn_continuous_probe(
            labels=labels_ok,
            features=features,
            cp_set=cp_set,
            splits=splits,
            run_id=resolved_run_id,
            min_cell_rows=min_cell_rows,
            n_bootstrap=n_bootstrap,
        )
    if (
        regime_candidate_r2_validation is not None
        or (
            regime_candidate_v21_comparison is not None
            and regime_candidate_v21_comparison.height > 0
        )
        or (
            regime_candidate_v2_comparison is not None
            and regime_candidate_v2_comparison.height > 0
        )
    ):
        catalog_ids = set(catalog.get_column("experiment_id"))
        for experiment_id in sorted(_DEAD_REGIME_EXPERIMENT_TARGETS):
            if experiment_id not in catalog_ids:
                continue
            if (
                regime_candidate_v21_comparison is not None
                and regime_candidate_v21_comparison.height > 0
            ):
                result_by_id[experiment_id] = _run_v21_comparison_dead_regime_experiment(
                    experiment_id=experiment_id,
                    regime_candidate_v21_comparison=regime_candidate_v21_comparison,
                    run_id=resolved_run_id,
                )
            elif (
                regime_candidate_v2_comparison is not None
                and regime_candidate_v2_comparison.height > 0
            ):
                result_by_id[experiment_id] = _run_v2_comparison_dead_regime_experiment(
                    experiment_id=experiment_id,
                    regime_candidate_v2_comparison=regime_candidate_v2_comparison,
                    run_id=resolved_run_id,
                )
            elif regime_candidate_r2_validation is not None:
                result_by_id[experiment_id] = _run_dead_regime_experiment(
                    experiment_id=experiment_id,
                    regime_candidate_r2_validation=regime_candidate_r2_validation,
                    candidate_assignments=candidate_assignments,
                    cp_set=cp_set,
                    run_id=resolved_run_id,
                )

    rows: list[dict[str, object]] = []
    for item in catalog.sort("experiment_id").iter_rows(named=True):
        experiment_id = str(item["experiment_id"])
        if experiment_id in result_by_id:
            rows.append(result_by_id[experiment_id])
            continue
        rows.append(
            _result_row(
                experiment_id=experiment_id,
                run_id=resolved_run_id,
                status="not_run",
                notes=(
                    "No experiment runner implemented for this catalog row in results v1."
                ),
            )
        )

    return {
        "foundation_experiment_results": pl.DataFrame(
            rows,
            schema=FOUNDATION_RESULT_SCHEMA,
            strict=False,
        )
    }


def _md(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "/")


def _result_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    results = artifacts["foundation_experiment_results"]
    lines = [
        f"# Foundation Experiment Results - {report_date.isoformat()}",
        "",
        "These are experiment-only results. They do not promote a baseline, feature, model, or regime classifier.",
        "",
        f"- Result rows: {results.height}",
        f"- Runnable rows completed: {results.filter(pl.col('status') != 'not_run').height}",
        "",
        "## Status Counts",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for row in results.group_by("status").len(name="n").sort("status").iter_rows(named=True):
        lines.append(f"| {_md(row['status'])} | {row['n']} |")
    lines += [
        "",
        "## Baseline Results",
        "",
        "| Experiment | Status | Production | Baseline MAE | Candidate MAE | Effect | CI low | CI high | Rows | Notes |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    baseline = results.filter(pl.col("experiment_id").is_in(_RUNNABLE_BASELINES))
    for row in baseline.sort("experiment_id").iter_rows(named=True):
        lines.append(
            "| "
            f"{_md(row['experiment_id'])} | {_md(row['status'])} | "
            f"{_md(row['production_status'])} | "
            f"{row['baseline_mae'] if row['baseline_mae'] is not None else ''} | "
            f"{row['candidate_mae'] if row['candidate_mae'] is not None else ''} | "
            f"{row['effect_size'] if row['effect_size'] is not None else ''} | "
            f"{row['ci_lo'] if row['ci_lo'] is not None else ''} | "
            f"{row['ci_hi'] if row['ci_hi'] is not None else ''} | "
            f"{row['n_rows']} | {_md(row['notes'])} |"
        )
    feature_probe = results.filter(pl.col("experiment_id").is_in(_RUNNABLE_FEATURE_PROBES))
    if feature_probe.height:
        lines += [
            "",
            "## Feature Probe Results",
            "",
            "| Experiment | Status | Production | Baseline MAE | Candidate MAE | Effect | CI low | CI high | Rows | Notes |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
        for row in feature_probe.sort("experiment_id").iter_rows(named=True):
            lines.append(
                "| "
                f"{_md(row['experiment_id'])} | {_md(row['status'])} | "
                f"{_md(row['production_status'])} | "
                f"{row['baseline_mae'] if row['baseline_mae'] is not None else ''} | "
                f"{row['candidate_mae'] if row['candidate_mae'] is not None else ''} | "
                f"{row['effect_size'] if row['effect_size'] is not None else ''} | "
                f"{row['ci_lo'] if row['ci_lo'] is not None else ''} | "
                f"{row['ci_hi'] if row['ci_hi'] is not None else ''} | "
                f"{row['n_rows']} | {_md(row['notes'])} |"
            )
    regime = results.filter(
        pl.col("experiment_id").is_in(list(_DEAD_REGIME_EXPERIMENT_TARGETS))
        & (pl.col("status") != "not_run")
    )
    if regime.height:
        lines += [
            "",
            "## Regime R2 Results",
            "",
            "| Experiment | Status | Production | Dead Regimes | Support Rows | Notes |",
            "|---|---|---|---:|---:|---|",
        ]
        for row in regime.sort("experiment_id").iter_rows(named=True):
            lines.append(
                "| "
                f"{_md(row['experiment_id'])} | {_md(row['status'])} | "
                f"{_md(row['production_status'])} | "
                f"{row['r2_dead_regimes'] if row['r2_dead_regimes'] is not None else ''} | "
                f"{row['n_rows']} | {_md(row['notes'])} |"
            )
    return lines


def write_foundation_experiment_result_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write foundation experiment result CSV and markdown artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    results_path = out_dir / "foundation_experiment_results_v1.csv"
    results = artifacts["foundation_experiment_results"].with_columns(
        pl.lit(str(results_path)).alias("result_artifact")
    )
    results.write_csv(results_path)
    report_path = out_dir / "foundation_experiment_results_v1.md"
    report_path.write_text(
        "\n".join(
            _result_report_lines(
                {**artifacts, "foundation_experiment_results": results},
                report_date,
            )
        ),
        encoding="utf-8",
    )
    return {
        "foundation_experiment_results_csv": results_path,
        "foundation_experiment_results_md": report_path,
    }
