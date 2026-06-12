# P1 Horizon Hybrid Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the P1 horizon hybrid model: ridge on `remaining_warming = tmax_int - k_cp`, reconstruction `tmax = k_cp + max(0, rw_pred)`, lead-aware NWP anchor blending, judged by the P0 honest harness (gates H1-H4) per CP and per stratum.

**Architecture:** One new module `solarstorm/onda3/_hybrid_iteration.py` reusing Onda 3F building blocks (`add_pooled_temporal_features`, `_encode_features`, `_ridge_predict`, binary-macro interactions) and the P0 package (`build_kcp_long`, `fit_honest_null`, `predict_honest_null`, `assign_remaining_warming_strata`, `build_honest_comparison`, `build_honest_gates`). Two candidates: `hybrid_local_only` and `hybrid_om_augmented`, compared same-row on the OM-covered subset.

**Tech Stack:** Python 3.12, Polars, NumPy, Typer, pytest, Ruff; `uv run` with `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'`.

**Spec:** `docs/superpowers/specs/2026-06-12-p1-horizon-hybrid-model-design.md`
**Depends on:** P0 plan fully implemented (`solarstorm/honest_eval/` exists and its tests pass).

---

## Guardrails

- Every generated row carries `production_status = EXPERIMENT_ONLY`.
- Walk-forward per test year; nothing from the test year enters training,
  encoding categories, or the honest null.
- OM input is only `data/open_meteo_features_2022_2025.parquet` (gated GFS
  pilot). No new providers, no new calibration formulas.
- Write only `reports/onda3-hybrid/`. No mutation of `data/*.parquet`.
- Success criteria are pre-registered in the spec; do not adjust after
  seeing results.
- Tests must not hit the network.

## File Structure

- Create: `solarstorm/onda3/_hybrid_iteration.py` — matrix builder, fold
  runner, candidate orchestration, honest judgement, writer.
- Modify: `solarstorm/__main__.py` — add `onda3-hybrid-model-iteration`.
- Create: `tests/test_onda3_hybrid_iteration.py` — unit tests.
- Create: `tests/test_onda3_hybrid_cli.py` — CLI smoke test.

---

### Task 1: Hybrid matrix builder

**Files:**
- Create: `tests/test_onda3_hybrid_iteration.py`
- Create: `solarstorm/onda3/_hybrid_iteration.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_onda3_hybrid_iteration.py`:

```python
"""Tests for the P1 horizon hybrid model iteration."""
from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from solarstorm.onda3._hybrid_iteration import build_hybrid_matrix


def _features_fixture(n_days: int = 8) -> pl.DataFrame:
    rows = []
    for i in range(n_days):
        date = dt.date(2022, 1, 1) + dt.timedelta(days=i)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            rows.append(
                {"date_local": date, "cp": cp,
                 "cloud_cover_suppression": float(i % 3),
                 "foehn_score": float(i % 5)}
            )
    return pl.DataFrame(rows)


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
    return pl.DataFrame(rows)


def _open_meteo_fixture(n_days: int = 8) -> pl.DataFrame:
    rows = []
    for i in range(n_days):
        date = dt.date(2022, 1, 1) + dt.timedelta(days=i)
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            rows.append(
                {"date_local": date, "cp": cp,
                 "om_prev_d1_day_max_c": 21.0 + (i % 4)}
            )
    return pl.DataFrame(rows)


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
    assert row["remaining_warming"] == 4  # tmax 20 - k_cp 16
    assert row["om_anchor_max"] == 21.0
    assert row["om_anchor_delta"] == pytest.approx(5.0)  # 21 - 16
    assert row["cp_lead_rank"] == 3
    assert row["om_anchor_delta_x_lead"] == pytest.approx(5.0)

    late = matrix.filter(
        (pl.col("date_local") == dt.date(2022, 1, 1)) & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert late["cp_lead_rank"] == 0
    assert late["om_anchor_delta"] == pytest.approx(2.0)  # 21 - 19
    assert late["om_anchor_delta_x_lead"] == pytest.approx(0.0)


def test_hybrid_matrix_without_open_meteo_has_null_anchor_columns():
    matrix = build_hybrid_matrix(
        features=_features_fixture(), labels=_labels_fixture(), open_meteo=None
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the matrix builder**

`solarstorm/onda3/_hybrid_iteration.py`:

```python
"""P1 horizon hybrid model: ridge on remaining warming with NWP anchor blend."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.honest_eval import build_kcp_long
from solarstorm.onda3._baseline_model import _ridge_predict
from solarstorm.onda3._interactions import add_binary_macro_interaction_features
from solarstorm.onda3._pooled_iteration import (
    CP_INDEX,
    _encode_features,
    _markdown_table,
    add_pooled_temporal_features,
    normalize_pooled_cp_column,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
HYBRID_ITERATION_ID = "onda3_p1_horizon_hybrid"
OM_ANCHOR_SOURCE = "om_prev_d1_day_max_c"
OM_FEATURE_COLUMNS = ("om_anchor_max", "om_anchor_delta", "om_anchor_delta_x_lead")
DECISION_READY_P2 = "READY_FOR_P2_DISTRIBUTION_DESIGN"
DECISION_LOCAL_REFERENCE = "KEEP_HYBRID_LOCAL_AS_REFERENCE"
DECISION_KEEP_REVIEW = "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"


def build_hybrid_matrix(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None = None,
    open_meteo: pl.DataFrame | None = None,
) -> pl.DataFrame:
    features = normalize_pooled_cp_column(features)
    kcp = build_kcp_long(labels)
    matrix = (
        features.join(kcp, on=["date_local", "cp"], how="inner")
        .join(labels.select(["date_local", "tmax_int"]), on="date_local", how="inner")
        .with_columns(
            (pl.col("tmax_int") - pl.col("k_cp")).alias("remaining_warming"),
            pl.col("cp")
            .replace_strict(
                {cp: 3 - index for cp, index in CP_INDEX.items()}, default=None
            )
            .alias("cp_lead_rank"),
        )
    )
    if assignments is not None and not assignments.is_empty():
        assignments = normalize_pooled_cp_column(assignments)
        matrix = matrix.join(
            assignments.select(["date_local", "cp", "binary_macro_regime_label"]),
            on=["date_local", "cp"],
            how="left",
        )
    if open_meteo is not None and not open_meteo.is_empty():
        open_meteo = normalize_pooled_cp_column(open_meteo)
        keys = open_meteo.select(["date_local", "cp"])
        if keys.height != keys.unique().height:
            raise ValueError("duplicate (date_local, cp) keys in open_meteo frame")
        matrix = matrix.join(
            open_meteo.select(
                ["date_local", "cp", pl.col(OM_ANCHOR_SOURCE).alias("om_anchor_max")]
            ),
            on=["date_local", "cp"],
            how="left",
        )
    else:
        matrix = matrix.with_columns(pl.lit(None, dtype=pl.Float64).alias("om_anchor_max"))
    return matrix.with_columns(
        (pl.col("om_anchor_max") - pl.col("k_cp")).alias("om_anchor_delta"),
    ).with_columns(
        (pl.col("om_anchor_delta") * pl.col("cp_lead_rank") / 3.0).alias(
            "om_anchor_delta_x_lead"
        )
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/onda3/_hybrid_iteration.py tests/test_onda3_hybrid_iteration.py
git commit -m "feat(p1): hybrid matrix with rw target and lead-aware NWP anchor"
```

### Task 2: Fold runner with floor-by-construction reconstruction

**Files:**
- Modify: `tests/test_onda3_hybrid_iteration.py`
- Modify: `solarstorm/onda3/_hybrid_iteration.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_onda3_hybrid_iteration.py`:

```python
import numpy as np

from solarstorm.onda3._hybrid_iteration import run_hybrid_fold


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
                    "date_local": date, "cp": cp, "k_cp": k_cp,
                    "tmax_int": k_cp + rw, "remaining_warming": rw,
                    "signal_feature": signal,
                    "cp_lead_rank": 3 - cp_i,
                }
            )
    return pl.DataFrame(rows)


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
    # Floor by construction: tmax prediction never below k_cp.
    joined = predictions.join(
        test.select(["date_local", "cp", "k_cp"]), on=["date_local", "cp"]
    )
    assert joined.filter(pl.col("prediction") < pl.col("k_cp")).is_empty()
    # Errors are on the Tmax scale.
    row = predictions.row(0, named=True)
    assert row["absolute_error"] == pytest.approx(
        abs(row["actual"] - row["prediction"])
    )
    assert row["model_name"] == "hybrid_local_only"
    assert row["production_status"] == "EXPERIMENT_ONLY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q -k fold`
Expected: FAIL with `ImportError: cannot import name 'run_hybrid_fold'`

- [ ] **Step 3: Implement the fold runner**

Append to `solarstorm/onda3/_hybrid_iteration.py`:

```python
def run_hybrid_fold(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    model_name: str,
) -> pl.DataFrame:
    """Ridge on remaining_warming; reconstruct tmax = k_cp + max(0, rw_pred)."""
    train_x, test_x = _encode_features(
        train,
        test,
        numeric_feature_columns=numeric_feature_columns,
        categorical_feature_columns=categorical_feature_columns,
    )
    rw_prediction = _ridge_predict(
        train_x, train["remaining_warming"].to_numpy(), test_x
    )
    rw_clamped = np.maximum(rw_prediction, 0.0)
    tmax_prediction = test["k_cp"].to_numpy() + rw_clamped
    actual = test["tmax_int"].to_numpy()
    return test.select(["date_local", "cp"]).with_columns(
        pl.Series("actual", actual.astype(np.float64)),
        pl.Series("prediction", tmax_prediction),
        pl.Series("rw_prediction_raw", rw_prediction),
        pl.Series("absolute_error", np.abs(actual - tmax_prediction)),
        pl.lit(model_name).alias("model_name"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/onda3/_hybrid_iteration.py tests/test_onda3_hybrid_iteration.py
git commit -m "feat(p1): hybrid fold runner with floor-by-construction"
```

### Task 3: Candidate orchestration (walk-forward, same-row OM comparison)

**Files:**
- Modify: `tests/test_onda3_hybrid_iteration.py`
- Modify: `solarstorm/onda3/_hybrid_iteration.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_onda3_hybrid_iteration.py`:

```python
from solarstorm.onda3._hybrid_iteration import build_onda3_hybrid_iteration


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
            # OM anchor covers 2021-07 onward, so the covered subset has both
            # train (2021-H2) and test (2022) rows for test_year 2022.
            om = (
                float(k_cp + rw) + anchor_noise
                if date >= dt.date(2021, 7, 1)
                else None
            )
            rows.append(
                {
                    "date_local": date, "cp": cp, "k_cp": k_cp,
                    "tmax_int": k_cp + rw, "remaining_warming": rw,
                    "signal_feature": signal, "cp_lead_rank": 3 - cp_i,
                    "om_anchor_max": om,
                    "om_anchor_delta": (om - k_cp) if om is not None else None,
                    "om_anchor_delta_x_lead": (
                        (om - k_cp) * (3 - cp_i) / 3.0 if om is not None else None
                    ),
                }
            )
    return pl.DataFrame(rows)


def test_hybrid_iteration_runs_three_candidate_surfaces():
    artifacts = build_onda3_hybrid_iteration(
        _two_year_matrix(),
        test_years=[2022],
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
    )

    results = artifacts["onda3_hybrid_model_results_v1"]
    names = set(results["model_name"].to_list())
    assert names == {
        "hybrid_local_only",
        "hybrid_om_augmented",
        "hybrid_local_only_covered_rows",
    }
    # OM-augmented and covered-rows reference share identical row counts.
    om_rows = results.filter(pl.col("model_name") == "hybrid_om_augmented")
    ref_rows = results.filter(
        pl.col("model_name") == "hybrid_local_only_covered_rows"
    )
    assert om_rows["n_test"].to_list() == ref_rows["n_test"].to_list()
    # The OM anchor is nearly the answer in this fixture, so it must win.
    assert (
        om_rows["mae"].to_list()[0] < ref_rows["mae"].to_list()[0]
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q -k candidate`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement the orchestration**

Append to `solarstorm/onda3/_hybrid_iteration.py`:

```python
def _walk_forward_predictions(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    model_name: str,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    prediction_frames: list[pl.DataFrame] = []
    result_rows: list[dict[str, object]] = []
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    for test_year in test_years:
        train = dated.filter(pl.col("_year") < test_year).drop("_year")
        test = dated.filter(pl.col("_year") == test_year).drop("_year")
        if train.is_empty() or test.is_empty():
            continue
        predictions = run_hybrid_fold(
            train,
            test,
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
            model_name=model_name,
        ).with_columns(pl.lit(test_year).alias("test_year"))
        prediction_frames.append(predictions)
        result_rows.append(
            {
                "test_year": test_year,
                "model_name": model_name,
                "n_train": train.height,
                "n_test": test.height,
                "mae": float(predictions["absolute_error"].mean()),
                "exact_rate": float(
                    (predictions["prediction"].round(0) == predictions["actual"]).mean()
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else pl.DataFrame()
    )
    return predictions, result_rows


def build_onda3_hybrid_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> dict[str, pl.DataFrame]:
    matrix = add_pooled_temporal_features(matrix)
    if "binary_macro_regime_label" in matrix.columns:
        matrix, interaction_columns = add_binary_macro_interaction_features(matrix)
    else:
        interaction_columns = []
    local_numeric = [
        c
        for c in [
            *numeric_feature_columns,
            "k_cp",
            "cp_sin", "cp_cos", "month_sin", "month_cos", "doy_sin", "doy_cos",
            *interaction_columns,
        ]
        if c in matrix.columns and matrix.schema[c].is_numeric()
    ]
    # De-duplicate while preserving order.
    local_numeric = list(dict.fromkeys(local_numeric))
    om_numeric = list(
        dict.fromkeys([*local_numeric, *[c for c in OM_FEATURE_COLUMNS if c in matrix.columns]])
    )
    covered = matrix.drop_nulls(list(OM_FEATURE_COLUMNS))

    local_predictions, local_results = _walk_forward_predictions(
        matrix,
        test_years=test_years,
        numeric_feature_columns=local_numeric,
        categorical_feature_columns=categorical_feature_columns,
        model_name="hybrid_local_only",
    )
    om_predictions, om_results = _walk_forward_predictions(
        covered,
        test_years=test_years,
        numeric_feature_columns=om_numeric,
        categorical_feature_columns=categorical_feature_columns,
        model_name="hybrid_om_augmented",
    )
    reference_predictions, reference_results = _walk_forward_predictions(
        covered,
        test_years=test_years,
        numeric_feature_columns=local_numeric,
        categorical_feature_columns=categorical_feature_columns,
        model_name="hybrid_local_only_covered_rows",
    )

    predictions = pl.concat(
        [f for f in (local_predictions, om_predictions, reference_predictions) if not f.is_empty()],
        how="diagonal_relaxed",
    )
    results = pl.DataFrame(
        [*local_results, *om_results, *reference_results], strict=False
    )
    feature_audit = pl.DataFrame(
        [
            {"feature": c, "candidate": "hybrid_om_augmented",
             "production_status": PRODUCTION_STATUS}
            for c in om_numeric
        ]
        + [
            {"feature": c, "candidate": "hybrid_local_only",
             "production_status": PRODUCTION_STATUS}
            for c in local_numeric
        ],
        strict=False,
    )
    return {
        "onda3_hybrid_model_results_v1": results,
        "onda3_hybrid_predictions_v1": predictions,
        "onda3_hybrid_feature_audit_v1": feature_audit,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/onda3/_hybrid_iteration.py tests/test_onda3_hybrid_iteration.py
git commit -m "feat(p1): hybrid candidate orchestration with same-row OM comparison"
```

### Task 4: Honest judgement and decision

**Files:**
- Modify: `tests/test_onda3_hybrid_iteration.py`
- Modify: `solarstorm/onda3/_hybrid_iteration.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_onda3_hybrid_iteration.py`:

```python
from solarstorm.onda3._hybrid_iteration import judge_hybrid_candidates


def _labels_for_judgement() -> pl.DataFrame:
    # Build wide labels covering all matrix dates so the honest null can fit.
    matrix = _two_year_matrix()
    wide = matrix.filter(pl.col("cp") == "20:00").select(["date_local", "tmax_int"])
    for cp, col in (
        ("20:00", "k_cp__cp_2000"), ("21:00", "k_cp__cp_2100"),
        ("22:00", "k_cp__cp_2200"), ("23:00", "k_cp__cp_2300"),
    ):
        kcp = matrix.filter(pl.col("cp") == cp).select(
            ["date_local", pl.col("k_cp").alias(col)]
        )
        wide = wide.join(kcp, on="date_local", how="left")
    return wide


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q -k judgement`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement the judgement**

Append to `solarstorm/onda3/_hybrid_iteration.py`:

```python
from solarstorm.honest_eval import (  # noqa: E402 (grouped with module imports in practice)
    apply_physical_floor,
    assign_remaining_warming_strata,
    build_floor_violation_audit,
    build_honest_comparison,
    build_honest_gates,
    fit_honest_null,
    predict_honest_null,
)


def judge_hybrid_candidates(
    *,
    predictions: pl.DataFrame,
    labels: pl.DataFrame,
    train_end_year: int,
) -> dict[str, pl.DataFrame]:
    """Score every candidate with the P0 honest harness; emit gates + decision."""
    kcp = build_kcp_long(labels)
    null_table = fit_honest_null(labels, train_end_year=train_end_year)
    gate_frames: list[pl.DataFrame] = []
    comparison_frames: list[pl.DataFrame] = []
    passed: dict[str, bool] = {}
    for model_name in predictions["model_name"].unique().sort().to_list():
        rows = (
            predictions.filter(pl.col("model_name") == model_name)
            .select(["date_local", "cp", "actual", "prediction"])
            .join(kcp, on=["date_local", "cp"], how="inner")
        )
        scored = assign_remaining_warming_strata(
            apply_physical_floor(predict_honest_null(rows, null_table))
        )
        comparison = build_honest_comparison(scored)
        gates, decision = build_honest_gates(
            by_cp=comparison["by_cp"],
            by_stratum_cp=comparison["by_stratum_cp"],
            floor_audit=build_floor_violation_audit(scored),
        )
        passed[model_name] = (
            decision.row(0, named=True)["decision_status"]
            == "HONEST_EVALUATION_PASSED"
        )
        gate_frames.append(gates.with_columns(pl.lit(model_name).alias("model_name")))
        comparison_frames.append(
            comparison["by_cp"].with_columns(pl.lit(model_name).alias("model_name"))
        )

    if passed.get("hybrid_om_augmented", False):
        decision_status = DECISION_READY_P2
    elif passed.get("hybrid_local_only", False):
        decision_status = DECISION_LOCAL_REFERENCE
    else:
        decision_status = DECISION_KEEP_REVIEW
    decision = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "decision_rationale": (
                    "P1 hybrid candidates judged by the P0 honest harness; "
                    "success criteria pre-registered in "
                    "docs/superpowers/specs/2026-06-12-p1-horizon-hybrid-model-design.md."
                ),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )
    return {
        "onda3_hybrid_gates_v1": pl.concat(gate_frames, how="diagonal_relaxed"),
        "onda3_hybrid_honest_by_cp_v1": pl.concat(
            comparison_frames, how="diagonal_relaxed"
        ),
        "onda3_hybrid_decision_v1": decision,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/onda3/_hybrid_iteration.py tests/test_onda3_hybrid_iteration.py
git commit -m "feat(p1): honest judgement of hybrid candidates"
```

### Task 5: Artifact writer and report

**Files:**
- Modify: `tests/test_onda3_hybrid_iteration.py`
- Modify: `solarstorm/onda3/_hybrid_iteration.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_onda3_hybrid_iteration.py`:

```python
from solarstorm.onda3._hybrid_iteration import write_onda3_hybrid_artifacts


def test_writer_emits_csv_md_and_report(tmp_path):
    frame = pl.DataFrame({"model_name": ["hybrid_local_only"],
                          "production_status": ["EXPERIMENT_ONLY"]})
    artifacts = {
        "onda3_hybrid_model_results_v1": frame,
        "onda3_hybrid_predictions_v1": frame,
        "onda3_hybrid_feature_audit_v1": frame,
        "onda3_hybrid_gates_v1": frame,
        "onda3_hybrid_honest_by_cp_v1": frame,
        "onda3_hybrid_decision_v1": pl.DataFrame(
            [{"decision_status": "KEEP_IN_ONDA3_EXPERIMENT_REVIEW",
              "production_status": "EXPERIMENT_ONLY"}]
        ),
    }

    paths = write_onda3_hybrid_artifacts(
        artifacts, output_dir=tmp_path, today=dt.date(2026, 6, 12)
    )

    assert (tmp_path / "onda3_hybrid_decision_v1.csv").exists()
    report = (tmp_path / "onda3_hybrid_model_report_v1.md").read_text(encoding="utf-8")
    assert "EXPERIMENT_ONLY" in report
    assert "No production, EV, pricing, shadow trading, or execution work is unlocked." in report
    assert "onda3_hybrid_report_md" in paths
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q -k writer`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement the writer**

Append to `solarstorm/onda3/_hybrid_iteration.py`:

```python
HYBRID_FILENAMES = {
    "onda3_hybrid_model_results_v1": "onda3_hybrid_model_results_v1.csv",
    "onda3_hybrid_predictions_v1": "onda3_hybrid_predictions_v1.csv",
    "onda3_hybrid_feature_audit_v1": "onda3_hybrid_feature_audit_v1.csv",
    "onda3_hybrid_gates_v1": "onda3_hybrid_gates_v1.csv",
    "onda3_hybrid_honest_by_cp_v1": "onda3_hybrid_honest_by_cp_v1.csv",
    "onda3_hybrid_decision_v1": "onda3_hybrid_decision_v1.csv",
}
FREEZE_LINE = (
    "No production, EV, pricing, shadow trading, or execution work is unlocked."
)


def render_onda3_hybrid_report(
    artifacts: dict[str, pl.DataFrame], *, today: dt.date
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Onda 3 P1 Horizon Hybrid Model Report",
            f"Generated: {today.isoformat()}",
            "All outputs remain EXPERIMENT_ONLY.",
            FREEZE_LINE,
            "## Decision",
            _markdown_table(frame("onda3_hybrid_decision_v1")),
            "## Honest Gates per Candidate",
            _markdown_table(frame("onda3_hybrid_gates_v1"), max_rows=40),
            "## Model vs Honest Null by CP per Candidate",
            _markdown_table(frame("onda3_hybrid_honest_by_cp_v1"), max_rows=40),
            "## Model Results",
            _markdown_table(frame("onda3_hybrid_model_results_v1"), max_rows=40),
            "## Feature Audit",
            _markdown_table(frame("onda3_hybrid_feature_audit_v1"), max_rows=60),
        ]
    ) + "\n"


def write_onda3_hybrid_artifacts(
    artifacts: dict[str, pl.DataFrame], *, output_dir: Path, today: dt.date
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in HYBRID_FILENAMES.items():
        if artifact_name not in artifacts:
            continue
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            f"# {artifact_name}\n\n{_markdown_table(artifacts[artifact_name])}\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name}_md"] = md_path
    report_path = output_dir / "onda3_hybrid_model_report_v1.md"
    report_path.write_text(
        render_onda3_hybrid_report(artifacts, today=today), encoding="utf-8"
    )
    paths["onda3_hybrid_report_md"] = report_path
    return paths
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/onda3/_hybrid_iteration.py tests/test_onda3_hybrid_iteration.py
git commit -m "feat(p1): hybrid artifact writer and report"
```

### Task 6: CLI command

**Files:**
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_onda3_hybrid_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

`tests/test_onda3_hybrid_cli.py`:

```python
"""CLI smoke test for onda3-hybrid-model-iteration (fixtures, no network)."""
from __future__ import annotations

import datetime as dt

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app


def _write_fixtures(tmp_path):
    n_days = 500
    feature_rows, label_rows, om_rows = [], [], []
    for i in range(n_days):
        date = dt.date(2021, 1, 1) + dt.timedelta(days=i)
        tmax = 18 + (i % 6)
        label_rows.append(
            {
                "date_local": date, "tmax_int": tmax,
                "k_cp__cp_2000": tmax - 4, "k_cp__cp_2100": tmax - 3,
                "k_cp__cp_2200": tmax - 2, "k_cp__cp_2300": tmax - 1,
            }
        )
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            feature_rows.append(
                {"date_local": date, "cp": cp,
                 "cloud_cover_suppression": float(i % 3),
                 "foehn_score": float(i % 7)}
            )
            if date >= dt.date(2021, 7, 1):
                om_rows.append(
                    {"date_local": date, "cp": cp,
                     "om_prev_d1_day_max_c": float(tmax) + 0.3}
                )
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    om_path = tmp_path / "open_meteo.parquet"
    pl.DataFrame(feature_rows).write_parquet(features_path)
    pl.DataFrame(label_rows).write_parquet(labels_path)
    pl.DataFrame(om_rows).write_parquet(om_path)
    return features_path, labels_path, om_path


def test_hybrid_cli_writes_artifacts(tmp_path):
    features_path, labels_path, om_path = _write_fixtures(tmp_path)
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(
        app,
        [
            "onda3-hybrid-model-iteration",
            "--features-path", str(features_path),
            "--labels-path", str(labels_path),
            "--open-meteo-path", str(om_path),
            "--binary-assignments-path", str(tmp_path / "missing.csv"),
            "--output-dir", str(output_dir),
            "--test-years", "2022",
            "--train-end-year", "2021",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "onda3_hybrid_decision_v1.csv").exists()
    assert (output_dir / "onda3_hybrid_model_report_v1.md").exists()
    assert "EXPERIMENT_ONLY" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_cli.py -q`
Expected: FAIL with `No such command`

- [ ] **Step 3: Implement the CLI command**

Add to `solarstorm/__main__.py` (imports at top with the other onda3 imports):

```python
from solarstorm.onda3._hybrid_iteration import (
    build_hybrid_matrix,
    build_onda3_hybrid_iteration,
    judge_hybrid_candidates,
    write_onda3_hybrid_artifacts,
)
```

```python
@app.command("onda3-hybrid-model-iteration")
def onda3_hybrid_model_iteration(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    open_meteo_path: str = typer.Option("./data/open_meteo_features_2022_2025.parquet"),
    binary_assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv"
    ),
    output_dir: str = typer.Option("./reports/onda3-hybrid"),
    test_years: str = typer.Option("2023,2024,2025"),
    train_end_year: int = typer.Option(2022),
):
    """P1: horizon hybrid model on remaining warming, judged by honest gates."""
    features = pl.read_parquet(features_path)
    labels = pl.read_parquet(labels_path)
    if features.schema.get("date_local") == pl.Utf8:
        features = features.with_columns(pl.col("date_local").str.to_date())
    if labels.schema.get("date_local") != pl.Date:
        labels = labels.with_columns(pl.col("date_local").cast(pl.Date))
    om_file = Path(open_meteo_path)
    open_meteo = pl.read_parquet(om_file) if om_file.exists() else None
    assignments_file = Path(binary_assignments_path)
    assignments = None
    if assignments_file.exists():
        assignments = pl.read_csv(assignments_file)
        if assignments.schema.get("date_local") == pl.Utf8:
            assignments = assignments.with_columns(pl.col("date_local").str.to_date())

    matrix = build_hybrid_matrix(
        features=features, labels=labels, assignments=assignments, open_meteo=open_meteo
    )
    manifest = build_onda3_feature_manifest(features)
    numeric_features = [
        row["feature"]
        for row in manifest.filter(pl.col("included_in_onda3")).iter_rows(named=True)
        if row["feature"] in matrix.columns
        and matrix.schema[row["feature"]].is_numeric()
    ]
    categorical_features = [
        c for c in ["binary_macro_regime_label"] if c in matrix.columns
    ]
    parsed_test_years = [int(y.strip()) for y in test_years.split(",") if y.strip()]

    artifacts = build_onda3_hybrid_iteration(
        matrix,
        test_years=parsed_test_years,
        numeric_feature_columns=numeric_features,
        categorical_feature_columns=categorical_features,
    )
    artifacts.update(
        judge_hybrid_candidates(
            predictions=artifacts["onda3_hybrid_predictions_v1"],
            labels=labels,
            train_end_year=train_end_year,
        )
    )
    paths = write_onda3_hybrid_artifacts(
        artifacts, output_dir=Path(output_dir), today=dt.date.today()
    )
    decision = artifacts["onda3_hybrid_decision_v1"].row(0, named=True)
    print(f"Onda 3 P1 hybrid iteration complete: {decision['decision_status']}")
    print("production_status: EXPERIMENT_ONLY")
    print(f"Report: {paths['onda3_hybrid_report_md']}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_cli.py tests/test_onda3_hybrid_iteration.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solarstorm/__main__.py tests/test_onda3_hybrid_cli.py
git commit -m "feat(p1): onda3-hybrid-model-iteration CLI"
```

### Task 7: Verification and first real run

**Files:**
- No new files; generated reports under `reports/onda3-hybrid/`.

- [ ] **Step 1: Run the focused suites + neighbors**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_onda3_hybrid_iteration.py tests/test_onda3_hybrid_cli.py tests/test_honest_eval.py tests/test_honest_eval_cli.py tests/test_onda3_pooled_iteration.py -q`
Expected: PASS

- [ ] **Step 2: Run Ruff**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run ruff check solarstorm/onda3/_hybrid_iteration.py solarstorm/__main__.py tests/test_onda3_hybrid_iteration.py tests/test_onda3_hybrid_cli.py`
Expected: no findings

- [ ] **Step 3: Generate the first real artifact**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run tmax onda3-hybrid-model-iteration`
Expected: completes; decision is one of the three pre-registered statuses.
Success per spec: `hybrid_local_only` closes the CP 22:00/23:00 gap vs the
honest null (H1), and `hybrid_om_augmented` passes H1+H2 on covered rows and
beats `hybrid_local_only_covered_rows` overall MAE. Record whatever happens;
do not tune thresholds.

- [ ] **Step 4: Confirm freeze strings and physical floor**

Run: `grep -c "EXPERIMENT_ONLY" reports/onda3-hybrid/onda3_hybrid_model_report_v1.md`
Expected: >= 1

Run (floor check on the generated predictions, must print 0):

```bash
UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -c "
import polars as pl
from solarstorm.honest_eval import build_kcp_long
pred = pl.read_csv('reports/onda3-hybrid/onda3_hybrid_predictions_v1.csv').with_columns(pl.col('date_local').str.to_date())
kcp = build_kcp_long(pl.read_parquet('data/labels.parquet'))
j = pred.join(kcp, on=['date_local','cp'], how='inner')
print(j.filter(pl.col('prediction') < pl.col('k_cp')).height)
"
```

- [ ] **Step 5: Update CHANGELOG.md and ROADMAP.md with the generated decision, then commit**

```bash
git add reports/onda3-hybrid CHANGELOG.md ROADMAP.md
git commit -m "milestone(p1): horizon hybrid model first honest-judged run"
```

## Self-Review Checklist

- [ ] Spec coverage: rw target, floor-by-construction reconstruction,
  k_cp as feature, OM anchor + per-CP delta + lead interaction, three
  candidate surfaces with same-row OM comparison, honest judgement H1-H4,
  pre-registered decision matrix, CLI, first real run — all present.
- [ ] Placeholder scan: no TBD/TODO; all code steps show complete code.
- [ ] Type consistency: `build_hybrid_matrix(*, features, labels,
  assignments=None, open_meteo=None)`, `run_hybrid_fold(train, test, *,
  numeric_feature_columns, categorical_feature_columns, model_name)`,
  `build_onda3_hybrid_iteration(matrix, *, test_years,
  numeric_feature_columns, categorical_feature_columns)`,
  `judge_hybrid_candidates(*, predictions, labels, train_end_year)`,
  `write_onda3_hybrid_artifacts(artifacts, *, output_dir, today)` match
  across tasks; artifact keys match `HYBRID_FILENAMES`.
