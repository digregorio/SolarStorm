# P0 Honest Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the P0 honest-evaluation harness (`solarstorm/honest_eval/` + `honest-evaluation` CLI) that scores any prediction artifact against the honest null `k_cp + train-only climatological remaining warming`, stratified by lead, with frozen gates H1-H4.

**Architecture:** A small evaluation-only package: k_cp unpivot, train-only null, physical-floor audit, remaining-warming strata, gate matrix, persistence ablation (reusing `build_onda3_pooled_iteration`), and a CSV+MD artifact writer following the Onda 3F pattern. No model training beyond the ablation rerun; no mutation of existing artifacts.

**Tech Stack:** Python 3.12, Polars, NumPy, Typer, pytest, Ruff. Run everything with `uv run` and `$env:UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'` (PowerShell) or `UV_CACHE_DIR=... ` (bash).

**Spec:** `docs/superpowers/specs/2026-06-12-p0-honest-evaluation-design.md`

---

## Guardrails

- Every generated row carries `production_status = EXPERIMENT_ONLY`.
- Null fit uses only `year <= train_end_year` rows.
- Gate thresholds are frozen in the spec; do not adjust after seeing results.
- Do not modify `solarstorm/robustness/_model_review.py` (M1-M8 stay frozen
  for reproducibility) or any `data/*.parquet`.
- Tests must not hit the network.

## File Structure

- Create: `solarstorm/honest_eval/__init__.py` — public exports.
- Create: `solarstorm/honest_eval/_kcp.py` — k_cp wide→long unpivot.
- Create: `solarstorm/honest_eval/_null.py` — honest null fit/predict.
- Create: `solarstorm/honest_eval/_floor.py` — physical floor clamp + audit.
- Create: `solarstorm/honest_eval/_strata.py` — lead strata + comparison tables.
- Create: `solarstorm/honest_eval/_review.py` — gates H1-H4 + decision.
- Create: `solarstorm/honest_eval/_ablation.py` — persistence ablation runner.
- Create: `solarstorm/honest_eval/_artifacts.py` — CSV/MD writer + report.
- Modify: `solarstorm/__main__.py` — add `honest-evaluation` command.
- Create: `tests/test_honest_eval.py` — unit tests.
- Create: `tests/test_honest_eval_cli.py` — CLI smoke test.

All test commands below assume bash syntax; on PowerShell replace the env
prefix with `$env:UV_CACHE_DIR='...'; `.

---

### Task 1: k_cp long view

**Files:**
- Create: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/__init__.py`
- Create: `solarstorm/honest_eval/_kcp.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for the P0 honest evaluation harness."""
from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from solarstorm.honest_eval import build_kcp_long


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


def test_kcp_long_view_unpivots_labels():
    long = build_kcp_long(_labels_fixture())

    assert set(long.columns) == {"date_local", "cp", "k_cp"}
    assert long.height == 7  # 8 cells minus 1 null
    row = long.filter(
        (pl.col("date_local") == dt.date(2022, 1, 1)) & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert row["k_cp"] == 20
    assert set(long["cp"].unique().to_list()) == {"20:00", "21:00", "22:00", "23:00"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py::test_kcp_long_view_unpivots_labels -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'solarstorm.honest_eval'`

- [ ] **Step 3: Implement `_kcp.py` and the package init**

`solarstorm/honest_eval/_kcp.py`:

```python
"""k_cp wide-to-long view over the labels table."""
from __future__ import annotations

import polars as pl

KCP_PREFIX = "k_cp__cp_"


def build_kcp_long(labels: pl.DataFrame) -> pl.DataFrame:
    """Unpivot ``k_cp__cp_HHMM`` columns into (date_local, cp, k_cp) rows."""
    kcp_columns = [c for c in labels.columns if c.startswith(KCP_PREFIX)]
    if not kcp_columns:
        raise ValueError("labels frame has no k_cp__cp_* columns")
    long = labels.select(["date_local", *kcp_columns]).unpivot(
        index="date_local", on=kcp_columns, variable_name="kcol", value_name="k_cp"
    )
    return (
        long.drop_nulls("k_cp")
        .with_columns(
            (
                pl.col("kcol").str.slice(len(KCP_PREFIX), 2)
                + pl.lit(":")
                + pl.col("kcol").str.slice(len(KCP_PREFIX) + 2, 2)
            ).alias("cp")
        )
        .select(["date_local", "cp", "k_cp"])
    )
```

`solarstorm/honest_eval/__init__.py`:

```python
"""P0 honest evaluation harness (EXPERIMENT_ONLY)."""
from solarstorm.honest_eval._kcp import build_kcp_long

__all__ = ["build_kcp_long"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py::test_kcp_long_view_unpivots_labels -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): k_cp wide-to-long view for honest evaluation"
```

### Task 2: Honest null fit and predict

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_null.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_honest_eval.py`:

```python
from solarstorm.honest_eval import fit_honest_null, predict_honest_null


def _null_train_labels() -> pl.DataFrame:
    # Three january days, cp 20:00: remaining warming 1, 2, 3 -> median 2.
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


def test_honest_null_fits_train_only_monthly_medians():
    table = fit_honest_null(_null_train_labels(), train_end_year=2022)

    jan_20 = table.filter((pl.col("month") == 1) & (pl.col("cp") == "20:00"))
    assert jan_20.row(0, named=True)["rw_median"] == 2.0
    # 2023 row (rw 20) is excluded by train_end_year.
    assert table.filter(pl.col("rw_median") >= 10).is_empty()
    # Per-CP fallback rows use month == 0.
    assert not table.filter((pl.col("month") == 0) & (pl.col("cp") == "20:00")).is_empty()


def test_honest_null_predicts_kcp_plus_median_with_fallback():
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
    assert jan["null_prediction"] == 16.0  # 14 + median 2
    jun = out.filter(pl.col("date_local") == dt.date(2023, 6, 10)).row(0, named=True)
    assert jun["null_prediction"] == 16.0  # june unseen -> cp fallback median 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k honest_null`
Expected: FAIL with `ImportError: cannot import name 'fit_honest_null'`

- [ ] **Step 3: Implement `_null.py`**

```python
"""Honest null: k_cp + train-only climatological median remaining warming."""
from __future__ import annotations

import polars as pl

from solarstorm.honest_eval._kcp import build_kcp_long

FALLBACK_MONTH = 0


def fit_honest_null(labels: pl.DataFrame, *, train_end_year: int) -> pl.DataFrame:
    """Median remaining warming per (month, cp) on train rows only.

    Returns columns (month, cp, rw_median, n_train_rows). ``month == 0`` rows
    are the per-CP global fallback for months unseen in training.
    """
    long = build_kcp_long(labels).join(
        labels.select(["date_local", "tmax_int"]), on="date_local", how="inner"
    )
    train = long.filter(
        pl.col("date_local").dt.year() <= train_end_year
    ).with_columns(
        (pl.col("tmax_int") - pl.col("k_cp")).alias("rw"),
        pl.col("date_local").dt.month().alias("month"),
    )
    if train.is_empty():
        raise ValueError("no train rows at or before train_end_year")
    monthly = train.group_by(["month", "cp"]).agg(
        pl.col("rw").median().alias("rw_median"), pl.len().alias("n_train_rows")
    )
    fallback = train.group_by("cp").agg(
        pl.col("rw").median().alias("rw_median"), pl.len().alias("n_train_rows")
    ).with_columns(pl.lit(FALLBACK_MONTH).cast(pl.Int8).alias("month"))
    return pl.concat(
        [monthly.with_columns(pl.col("month").cast(pl.Int8)), fallback],
        how="diagonal_relaxed",
    ).select(["month", "cp", "rw_median", "n_train_rows"])


def predict_honest_null(rows: pl.DataFrame, null_table: pl.DataFrame) -> pl.DataFrame:
    """Add ``null_prediction = k_cp + round(rw_median)`` to (date_local, cp, k_cp) rows."""
    monthly = null_table.filter(pl.col("month") != FALLBACK_MONTH)
    fallback = null_table.filter(pl.col("month") == FALLBACK_MONTH).select(
        ["cp", pl.col("rw_median").alias("rw_median_fallback")]
    )
    out = (
        rows.with_columns(pl.col("date_local").dt.month().cast(pl.Int8).alias("month"))
        .join(monthly.select(["month", "cp", "rw_median"]), on=["month", "cp"], how="left")
        .join(fallback, on="cp", how="left")
        .with_columns(
            pl.coalesce([pl.col("rw_median"), pl.col("rw_median_fallback")]).alias("_rw")
        )
    )
    if out["_rw"].null_count() > 0:
        raise ValueError("honest null has no fallback for at least one cp")
    return out.with_columns(
        (pl.col("k_cp") + pl.col("_rw").round(0)).alias("null_prediction")
    ).drop(["month", "rw_median", "rw_median_fallback", "_rw"])
```

Update `solarstorm/honest_eval/__init__.py`:

```python
"""P0 honest evaluation harness (EXPERIMENT_ONLY)."""
from solarstorm.honest_eval._kcp import build_kcp_long
from solarstorm.honest_eval._null import fit_honest_null, predict_honest_null

__all__ = ["build_kcp_long", "fit_honest_null", "predict_honest_null"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): honest null fit/predict with train-only monthly medians"
```

### Task 3: Physical floor clamp and violation audit

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_floor.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_honest_eval.py`:

```python
from solarstorm.honest_eval import apply_physical_floor, build_floor_violation_audit


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


def test_apply_physical_floor_clamps_predictions_below_kcp():
    out = apply_physical_floor(_floor_fixture())

    assert out["prediction_floored"].to_list() == [15.0, 16.0, 18.5]
    assert out["floor_violation"].to_list() == [True, False, False]


def test_floor_violation_audit_reports_rates_per_cp():
    audit = build_floor_violation_audit(apply_physical_floor(_floor_fixture()))

    overall = audit.filter(pl.col("cp") == "ALL").row(0, named=True)
    assert overall["n_rows"] == 3
    assert overall["n_violations"] == 1
    assert overall["violation_pct"] == pytest.approx(100.0 / 3.0)
    assert overall["production_status"] == "EXPERIMENT_ONLY"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k floor`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_floor.py`**

```python
"""Physical floor: Tmax can never be below the already-observed maximum."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"


def apply_physical_floor(
    frame: pl.DataFrame,
    *,
    prediction_col: str = "prediction",
    k_cp_col: str = "k_cp",
) -> pl.DataFrame:
    return frame.with_columns(
        pl.max_horizontal(pl.col(prediction_col), pl.col(k_cp_col).cast(pl.Float64))
        .alias("prediction_floored"),
        (pl.col(prediction_col) < pl.col(k_cp_col)).alias("floor_violation"),
    )


def build_floor_violation_audit(frame: pl.DataFrame) -> pl.DataFrame:
    per_cp = frame.group_by("cp").agg(
        pl.len().alias("n_rows"), pl.col("floor_violation").sum().alias("n_violations")
    )
    overall = frame.select(
        pl.lit("ALL").alias("cp"),
        pl.len().alias("n_rows"),
        pl.col("floor_violation").sum().alias("n_violations"),
    )
    return (
        pl.concat([overall, per_cp.sort("cp")], how="diagonal_relaxed")
        .with_columns(
            (pl.col("n_violations") * 100.0 / pl.col("n_rows")).alias("violation_pct"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
    )
```

Add both names to `__init__.py` imports and `__all__`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): physical floor clamp and violation audit"
```

### Task 4: Remaining-warming strata and comparison tables

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_strata.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_honest_eval.py`:

```python
from solarstorm.honest_eval import assign_remaining_warming_strata, build_honest_comparison


def _comparison_fixture() -> pl.DataFrame:
    # 4 rows at one cp: strata already_seen, small_1, forecast_2_plus x2.
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


def test_strata_assignment_buckets_realized_remaining_warming():
    out = assign_remaining_warming_strata(_comparison_fixture())

    assert out["rw_stratum"].to_list() == [
        "already_seen",
        "small_1",
        "forecast_2_plus",
        "forecast_2_plus",
    ]


def test_honest_comparison_reports_model_and_null_by_cp_and_stratum():
    tables = build_honest_comparison(assign_remaining_warming_strata(_comparison_fixture()))

    by_cp = tables["by_cp"].filter(pl.col("cp") == "23:00").row(0, named=True)
    assert by_cp["model_mae"] == pytest.approx(0.5)   # |0|+|0|+|0|+|2| / 4
    assert by_cp["null_mae"] == pytest.approx(1.25)   # 0+0+2+3 / 4
    assert by_cp["model_beats_null"] is True

    strat = tables["by_stratum_cp"].filter(
        (pl.col("rw_stratum") == "forecast_2_plus") & (pl.col("cp") == "23:00")
    ).row(0, named=True)
    assert strat["n_rows"] == 2
    assert strat["model_mae"] == pytest.approx(1.0)
    assert strat["null_mae"] == pytest.approx(2.5)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k "strata or comparison"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_strata.py`**

```python
"""Lead strata by realized remaining warming, and model-vs-null comparison."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
STRATUM_ALREADY_SEEN = "already_seen"
STRATUM_SMALL = "small_1"
STRATUM_FORECAST = "forecast_2_plus"


def assign_remaining_warming_strata(frame: pl.DataFrame) -> pl.DataFrame:
    rw = pl.col("actual") - pl.col("k_cp")
    return frame.with_columns(
        pl.when(rw <= 0)
        .then(pl.lit(STRATUM_ALREADY_SEEN))
        .when(rw <= 1)
        .then(pl.lit(STRATUM_SMALL))
        .otherwise(pl.lit(STRATUM_FORECAST))
        .alias("rw_stratum")
    )


def _summary(frame: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    return (
        frame.group_by(keys)
        .agg(
            pl.len().alias("n_rows"),
            (pl.col("prediction") - pl.col("actual")).abs().mean().alias("model_mae"),
            (pl.col("null_prediction") - pl.col("actual")).abs().mean().alias("null_mae"),
            (pl.col("prediction").round(0) == pl.col("actual"))
            .mean()
            .alias("model_exact_rate"),
            (pl.col("null_prediction").round(0) == pl.col("actual"))
            .mean()
            .alias("null_exact_rate"),
        )
        .with_columns(
            (pl.col("model_mae") < pl.col("null_mae")).alias("model_beats_null"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(keys)
    )


def build_honest_comparison(frame: pl.DataFrame) -> dict[str, pl.DataFrame]:
    return {
        "by_cp": _summary(frame, ["cp"]),
        "by_stratum": _summary(frame, ["rw_stratum"]),
        "by_stratum_cp": _summary(frame, ["rw_stratum", "cp"]),
    }
```

Add names to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): remaining-warming strata and honest comparison tables"
```

### Task 5: Gate matrix H1-H4 and decision

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_review.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_honest_eval.py`:

```python
from solarstorm.honest_eval import build_honest_gates

H2_MIN_ROWS = 30


def _gate_inputs(model_wins: bool) -> dict[str, pl.DataFrame]:
    model_mae = 0.9 if model_wins else 1.2
    by_cp = pl.DataFrame(
        {
            "cp": ["20:00", "21:00", "22:00", "23:00"],
            "n_rows": [100] * 4,
            "model_mae": [model_mae] * 4,
            "null_mae": [1.0] * 4,
            "model_beats_null": [model_wins] * 4,
        }
    )
    by_stratum_cp = pl.DataFrame(
        {
            "rw_stratum": ["forecast_2_plus"] * 4,
            "cp": ["20:00", "21:00", "22:00", "23:00"],
            "n_rows": [50] * 4,
            "model_mae": [model_mae] * 4,
            "null_mae": [1.0] * 4,
            "model_beats_null": [model_wins] * 4,
        }
    )
    floor_audit = pl.DataFrame(
        {"cp": ["ALL"], "n_rows": [400], "n_violations": [12], "violation_pct": [3.0]}
    )
    return {"by_cp": by_cp, "by_stratum_cp": by_stratum_cp, "floor_audit": floor_audit}


def test_gates_pass_and_decision_when_model_beats_null_everywhere():
    gates, decision = build_honest_gates(**_gate_inputs(model_wins=True))

    assert gates.filter(pl.col("gate_status") != "PASS").is_empty()
    assert decision.row(0, named=True)["decision_status"] == "HONEST_EVALUATION_PASSED"


def test_gates_block_when_null_wins_any_cp():
    gates, decision = build_honest_gates(**_gate_inputs(model_wins=False))

    h1 = gates.filter(pl.col("gate_id") == "H1").row(0, named=True)
    assert h1["gate_status"] == "BLOCK"
    assert (
        decision.row(0, named=True)["decision_status"]
        == "BLOCK_MODEL_PROMOTION_HONEST_NULL"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k gates`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_review.py`**

```python
"""Frozen gates H1-H4 and the honest-evaluation decision."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
H2_MIN_ROWS = 30
DECISION_PASSED = "HONEST_EVALUATION_PASSED"
DECISION_BLOCK = "BLOCK_MODEL_PROMOTION_HONEST_NULL"
DECISION_REVIEW = "KEEP_IN_HONEST_EVALUATION_REVIEW"
FORECAST_STRATUM = "forecast_2_plus"


def build_honest_gates(
    *,
    by_cp: pl.DataFrame,
    by_stratum_cp: pl.DataFrame,
    floor_audit: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    h1_fail = by_cp.filter(~pl.col("model_beats_null"))
    h1_pass = not by_cp.is_empty() and h1_fail.is_empty()

    forecast = by_stratum_cp.filter(
        (pl.col("rw_stratum") == FORECAST_STRATUM) & (pl.col("n_rows") >= H2_MIN_ROWS)
    )
    h2_fail = forecast.filter(~pl.col("model_beats_null"))
    h2_pass = not forecast.is_empty() and h2_fail.is_empty()

    h3_pass = not floor_audit.is_empty()
    h4_pass = by_stratum_cp.filter(pl.col("cp") != "ALL")["cp"].n_unique() >= 4

    def status(flag: bool) -> str:
        return "PASS" if flag else "BLOCK"

    gates = pl.DataFrame(
        [
            {
                "gate_id": "H1",
                "gate_name": "Per-CP honest lift",
                "gate_status": status(h1_pass),
                "detail": f"cps_losing_to_null={h1_fail['cp'].to_list()}",
            },
            {
                "gate_id": "H2",
                "gate_name": "Anticipation stratum (rw >= 2)",
                "gate_status": status(h2_pass),
                "detail": (
                    f"supported_cps={forecast.height}; "
                    f"cps_losing_to_null={h2_fail['cp'].to_list()}"
                ),
            },
            {
                "gate_id": "H3",
                "gate_name": "Physical floor audit",
                "gate_status": status(h3_pass),
                "detail": f"raw_violation_rows={floor_audit.filter(pl.col('cp') == 'ALL')['n_violations'].sum()}",
            },
            {
                "gate_id": "H4",
                "gate_name": "Lead degradation table",
                "gate_status": status(h4_pass),
                "detail": f"stratum_cp_rows={by_stratum_cp.height}",
            },
        ],
    ).with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))

    if not (h3_pass and h4_pass):
        decision_status = DECISION_REVIEW
    elif h1_pass and h2_pass:
        decision_status = DECISION_PASSED
    else:
        decision_status = DECISION_BLOCK
    decision = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "decision_rationale": (
                    "Honest-null gates H1-H4 evaluated; thresholds frozen in "
                    "docs/superpowers/specs/2026-06-12-p0-honest-evaluation-design.md."
                ),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )
    return gates, decision
```

Add `build_honest_gates` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): frozen honest gates H1-H4 and decision"
```

### Task 6: Persistence ablation runner

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_ablation.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_honest_eval.py`:

```python
import numpy as np

from solarstorm.honest_eval import PERSISTENCE_BLOCK, run_persistence_ablation


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


def test_persistence_ablation_compares_full_vs_ablated_mae():
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
    # Removing a dominant persistence block must hurt: ablated MAE is larger.
    assert row["ablated_mae"] > row["full_mae"]
    assert row["production_status"] == "EXPERIMENT_ONLY"
```

Note: `test_years=[2021]` has no earlier train year, so the pooled builder
would skip the fold. The implementation must split the single year
internally (first 80% of dates train, last 20% test) when only one year
exists — see Step 3. This keeps the unit test small and network-free.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k ablation`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_ablation.py`**

```python
"""Persistence-block ablation over the Onda 3F pooled ridge."""
from __future__ import annotations

import numpy as np
import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict
from solarstorm.onda3._pooled_iteration import (
    _encode_features,
    add_pooled_temporal_features,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
PERSISTENCE_BLOCK = ("tmax_dminus1", "slope_3h", "warming_rate_06_09")


def _fold_frames(
    matrix: pl.DataFrame, test_year: int
) -> tuple[pl.DataFrame, pl.DataFrame]:
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    train = dated.filter(pl.col("_year") < test_year)
    test = dated.filter(pl.col("_year") == test_year)
    if train.is_empty() and not test.is_empty():
        # Single-year input: chronological 80/20 split inside the year.
        cutoff_index = int(test.height * 0.8)
        ordered = test.sort("date_local")
        train, test = ordered.head(cutoff_index), ordered.slice(cutoff_index)
    return train.drop("_year"), test.drop("_year")


def _fit_mae(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric: list[str],
    categorical: list[str],
    target_column: str,
) -> float:
    train_x, test_x = _encode_features(
        train, test, numeric_feature_columns=numeric, categorical_feature_columns=categorical
    )
    predictions = _ridge_predict(train_x, train[target_column].to_numpy(), test_x)
    return _mae(test[target_column].to_numpy(), predictions)


def run_persistence_ablation(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> pl.DataFrame:
    matrix = add_pooled_temporal_features(matrix)
    numeric = [
        c
        for c in [*numeric_feature_columns, "cp_sin", "cp_cos", "month_sin",
                  "month_cos", "doy_sin", "doy_cos"]
        if c in matrix.columns and matrix.schema[c].is_numeric()
    ]
    ablated_numeric = [c for c in numeric if c not in PERSISTENCE_BLOCK]
    rows: list[dict[str, object]] = []
    for test_year in test_years:
        train, test = _fold_frames(matrix, test_year)
        if train.is_empty() or test.is_empty():
            continue
        full_mae = _fit_mae(
            train, test, numeric=numeric,
            categorical=categorical_feature_columns, target_column=target_column,
        )
        ablated_mae = _fit_mae(
            train, test, numeric=ablated_numeric,
            categorical=categorical_feature_columns, target_column=target_column,
        )
        rows.append(
            {
                "test_year": test_year,
                "n_train": train.height,
                "n_test": test.height,
                "full_mae": full_mae,
                "ablated_mae": ablated_mae,
                "mae_delta_ablated_minus_full": ablated_mae - full_mae,
                "ablated_features": ",".join(PERSISTENCE_BLOCK),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)
```

Add `PERSISTENCE_BLOCK` and `run_persistence_ablation` to `__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): persistence-block ablation runner"
```

### Task 7: Artifact writer and report

**Files:**
- Modify: `tests/test_honest_eval.py`
- Create: `solarstorm/honest_eval/_artifacts.py`
- Modify: `solarstorm/honest_eval/__init__.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_honest_eval.py`:

```python
from solarstorm.honest_eval import write_honest_eval_artifacts


def test_writer_emits_csv_md_pairs_and_report(tmp_path):
    frame = pl.DataFrame({"cp": ["ALL"], "production_status": ["EXPERIMENT_ONLY"]})
    artifacts = {
        "honest_eval_null_table_v1": frame,
        "honest_eval_by_cp_v1": frame,
        "honest_eval_by_stratum_cp_v1": frame,
        "honest_eval_floor_audit_v1": frame,
        "honest_eval_ablation_v1": frame,
        "honest_eval_gates_v1": frame,
        "honest_eval_decision_v1": pl.DataFrame(
            [{"decision_status": "HONEST_EVALUATION_PASSED",
              "production_status": "EXPERIMENT_ONLY"}]
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q -k writer`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_artifacts.py`**

```python
"""CSV/MD artifact writer for the honest evaluation harness."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda3._pooled_iteration import _markdown_table

HONEST_FILENAMES = {
    "honest_eval_null_table_v1": "honest_eval_null_table_v1.csv",
    "honest_eval_by_cp_v1": "honest_eval_by_cp_v1.csv",
    "honest_eval_by_stratum_cp_v1": "honest_eval_by_stratum_cp_v1.csv",
    "honest_eval_floor_audit_v1": "honest_eval_floor_audit_v1.csv",
    "honest_eval_ablation_v1": "honest_eval_ablation_v1.csv",
    "honest_eval_gates_v1": "honest_eval_gates_v1.csv",
    "honest_eval_decision_v1": "honest_eval_decision_v1.csv",
}
FREEZE_LINE = (
    "No production, EV, pricing, shadow trading, or execution work is unlocked."
)


def render_honest_eval_report(
    artifacts: dict[str, pl.DataFrame], *, today: dt.date
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Honest Evaluation Report (P0)",
            f"Generated: {today.isoformat()}",
            "All outputs remain EXPERIMENT_ONLY.",
            FREEZE_LINE,
            "## Decision",
            _markdown_table(frame("honest_eval_decision_v1")),
            "## Gates H1-H4",
            _markdown_table(frame("honest_eval_gates_v1")),
            "## Model vs Honest Null by CP",
            _markdown_table(frame("honest_eval_by_cp_v1")),
            "## Model vs Honest Null by Stratum x CP",
            _markdown_table(frame("honest_eval_by_stratum_cp_v1"), max_rows=40),
            "## Physical Floor Audit",
            _markdown_table(frame("honest_eval_floor_audit_v1")),
            "## Persistence Ablation",
            _markdown_table(frame("honest_eval_ablation_v1")),
            "## Honest Null Table (train-only)",
            _markdown_table(frame("honest_eval_null_table_v1"), max_rows=60),
        ]
    ) + "\n"


def write_honest_eval_artifacts(
    artifacts: dict[str, pl.DataFrame], *, output_dir: Path, today: dt.date
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in HONEST_FILENAMES.items():
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
    report_path = output_dir / "honest_evaluation_report_v1.md"
    report_path.write_text(
        render_honest_eval_report(artifacts, today=today), encoding="utf-8"
    )
    paths["honest_eval_report_md"] = report_path
    return paths
```

Add `write_honest_eval_artifacts` to `__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py -q`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/honest_eval tests/test_honest_eval.py
git commit -m "feat(p0): honest evaluation artifact writer and report"
```

### Task 8: CLI command

**Files:**
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_honest_eval_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

`tests/test_honest_eval_cli.py`:

```python
"""CLI smoke test for honest-evaluation (fixture data, no network)."""
from __future__ import annotations

import datetime as dt

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app


def _write_fixtures(tmp_path):
    dates = [dt.date(2021, 1, 1) + dt.timedelta(days=i) for i in range(120)]
    labels = pl.DataFrame(
        {
            "date_local": dates,
            "tmax_int": [15 + (i % 5) for i in range(120)],
            "k_cp__cp_2000": [13 + (i % 5) for i in range(120)],
            "k_cp__cp_2100": [13 + (i % 5) for i in range(120)],
            "k_cp__cp_2200": [14 + (i % 5) for i in range(120)],
            "k_cp__cp_2300": [14 + (i % 5) for i in range(120)],
        }
    )
    labels_path = tmp_path / "labels.parquet"
    labels.write_parquet(labels_path)
    pred_rows = []
    for date in dates[90:]:
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            actual = labels.filter(pl.col("date_local") == date)["tmax_int"][0]
            pred_rows.append(
                {"date_local": date.isoformat(), "cp": cp,
                 "actual": actual, "prediction": float(actual)}
            )
    predictions_path = tmp_path / "predictions.csv"
    pl.DataFrame(pred_rows).write_csv(predictions_path)
    return labels_path, predictions_path


def test_honest_evaluation_cli_writes_artifacts(tmp_path):
    labels_path, predictions_path = _write_fixtures(tmp_path)
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(
        app,
        [
            "honest-evaluation",
            "--labels-path", str(labels_path),
            "--predictions-path", str(predictions_path),
            "--output-dir", str(output_dir),
            "--train-end-year", "2021",
            "--no-ablation",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "honest_eval_decision_v1.csv").exists()
    assert (output_dir / "honest_evaluation_report_v1.md").exists()
    assert "EXPERIMENT_ONLY" in result.output
```

Note on the fixture: all rows are in 2021, so `--train-end-year 2021` lets the
honest null fit on the full year while predictions cover the last 30 days.
The overlap is acceptable for a smoke test because the honest null is a fixed
climatology, not a fitted competitor; the real run in Task 9 uses the proper
2022 boundary.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval_cli.py -q`
Expected: FAIL with `No such command 'honest-evaluation'`

- [ ] **Step 3: Implement the CLI command**

Add to `solarstorm/__main__.py` (after the `onda3-pooled-model-iteration`
command; imports go at the top of the file with the existing onda3 imports):

```python
from solarstorm.honest_eval import (
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
```

```python
@app.command("honest-evaluation")
def honest_evaluation(
    predictions_path: str = typer.Option(
        "./reports/onda3-pooled/onda3_pooled_predictions_v1.csv"
    ),
    labels_path: str = typer.Option("./data/labels.parquet"),
    features_path: str = typer.Option("./data/features.parquet"),
    binary_assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv"
    ),
    output_dir: str = typer.Option("./reports/honest-evaluation"),
    train_end_year: int = typer.Option(2022),
    test_years: str = typer.Option("2023,2024,2025"),
    ablation: bool = typer.Option(True, "--ablation/--no-ablation"),
):
    """P0: score a prediction artifact against the honest k_cp+climatology null."""
    labels = pl.read_parquet(labels_path)
    if labels.schema.get("date_local") != pl.Date:
        labels = labels.with_columns(pl.col("date_local").cast(pl.Date))
    predictions = pl.read_csv(predictions_path)
    if predictions.schema.get("date_local") == pl.Utf8:
        predictions = predictions.with_columns(pl.col("date_local").str.to_date())
    predictions = predictions.select(["date_local", "cp", "actual", "prediction"])

    kcp = build_kcp_long(labels)
    rows = predictions.join(kcp, on=["date_local", "cp"], how="inner")
    null_table = fit_honest_null(labels, train_end_year=train_end_year)
    scored = predict_honest_null(rows, null_table)
    scored = assign_remaining_warming_strata(apply_physical_floor(scored))
    comparison = build_honest_comparison(scored)
    floor_audit = build_floor_violation_audit(scored)
    gates, decision = build_honest_gates(
        by_cp=comparison["by_cp"],
        by_stratum_cp=comparison["by_stratum_cp"],
        floor_audit=floor_audit,
    )

    ablation_frame = pl.DataFrame()
    if ablation:
        features = pl.read_parquet(features_path)
        if features.schema.get("date_local") == pl.Utf8:
            features = features.with_columns(pl.col("date_local").str.to_date())
        features = normalize_pooled_cp_column(features)
        matrix = features.join(
            labels.select(["date_local", "tmax_int"]), on="date_local", how="inner"
        )
        assignments_file = Path(binary_assignments_path)
        if assignments_file.exists():
            assignments = pl.read_csv(assignments_file)
            if assignments.schema.get("date_local") == pl.Utf8:
                assignments = assignments.with_columns(
                    pl.col("date_local").str.to_date()
                )
            assignments = normalize_pooled_cp_column(assignments)
            matrix = matrix.join(
                assignments.select(["date_local", "cp", "binary_macro_regime_label"]),
                on=["date_local", "cp"],
                how="left",
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
        ablation_frame = run_persistence_ablation(
            matrix,
            test_years=[int(y.strip()) for y in test_years.split(",") if y.strip()],
            numeric_feature_columns=numeric_features,
            categorical_feature_columns=categorical_features,
        )

    artifacts = {
        "honest_eval_null_table_v1": null_table.with_columns(
            pl.lit("EXPERIMENT_ONLY").alias("production_status")
        ),
        "honest_eval_by_cp_v1": comparison["by_cp"],
        "honest_eval_by_stratum_cp_v1": comparison["by_stratum_cp"],
        "honest_eval_floor_audit_v1": floor_audit,
        "honest_eval_ablation_v1": ablation_frame,
        "honest_eval_gates_v1": gates,
        "honest_eval_decision_v1": decision,
    }
    paths = write_honest_eval_artifacts(
        artifacts, output_dir=Path(output_dir), today=dt.date.today()
    )
    decision_row = decision.row(0, named=True)
    print(f"Honest evaluation complete: {decision_row['decision_status']}")
    print("production_status: EXPERIMENT_ONLY")
    print(f"Report: {paths['honest_eval_report_md']}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval_cli.py tests/test_honest_eval.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solarstorm/__main__.py tests/test_honest_eval_cli.py
git commit -m "feat(p0): honest-evaluation CLI command"
```

### Task 9: Verification and first real run

**Files:**
- No new files; generated reports under `reports/honest-evaluation/`.

- [ ] **Step 1: Run the full focused suite**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run pytest tests/test_honest_eval.py tests/test_honest_eval_cli.py tests/test_onda3_pooled_iteration.py -q`
Expected: PASS

- [ ] **Step 2: Run Ruff**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run ruff check solarstorm/honest_eval solarstorm/__main__.py tests/test_honest_eval.py tests/test_honest_eval_cli.py`
Expected: no findings

- [ ] **Step 3: Generate the first real artifact against Onda 3F**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run tmax honest-evaluation`
Expected: command completes; prints decision (pre-registered expectation:
`BLOCK_MODEL_PROMOTION_HONEST_NULL`, because the forensic analysis showed the
null beats Onda 3F at CP 22:00/23:00). Whatever the outcome, do NOT adjust
gate thresholds; record the result.

- [ ] **Step 4: Confirm freeze strings in generated report**

Run: `grep -c "EXPERIMENT_ONLY" reports/honest-evaluation/honest_evaluation_report_v1.md && grep -c "No production, EV, pricing" reports/honest-evaluation/honest_evaluation_report_v1.md`
Expected: both counts >= 1

- [ ] **Step 5: Update CHANGELOG.md and ROADMAP.md with the generated decision, then commit**

```bash
git add reports/honest-evaluation CHANGELOG.md ROADMAP.md
git commit -m "milestone(p0): first honest evaluation of Onda 3F vs k_cp+climatology null"
```

## Self-Review Checklist

- [ ] Spec coverage: k_cp long view, honest null (train-only + fallback),
  physical floor + audit, strata, gates H1-H4 with frozen thresholds,
  persistence ablation, writer, CLI, first real run — all present.
- [ ] Placeholder scan: no TBD/TODO; every code step shows complete code.
- [ ] Type consistency: `build_kcp_long`, `fit_honest_null(labels, *,
  train_end_year)`, `predict_honest_null(rows, null_table)`,
  `apply_physical_floor`, `build_floor_violation_audit`,
  `assign_remaining_warming_strata`, `build_honest_comparison`,
  `build_honest_gates(by_cp=, by_stratum_cp=, floor_audit=)`,
  `run_persistence_ablation`, `write_honest_eval_artifacts` are used with the
  same signatures across tasks.
