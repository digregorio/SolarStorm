# P2 Calibrated Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the P2 calibrated-distribution iteration (`solarstorm/distribution/` + `p2-distribution-iteration` CLI): two pre-registered candidates (`dist_residual_dressing`, `dist_truncnorm_emos`) scored by member CRPS against the climatological null distribution, judged by frozen gates D1-D4.

**Architecture:** Every predictive distribution is a 199-member quantile vector on the Tmax scale (`Tmax = k_cp + rw`). One scoring path (empirical-member CRPS) for candidates and null. Folds reuse the P1 hybrid matrix and ridge point model; within each fold a chronological inner 80/20 split provides out-of-sample calibration residuals. Gates and decision follow the P0 frozen-gate pattern.

**Tech Stack:** Python 3.12, Polars, NumPy, SciPy (new declared dependency), Typer, pytest, Ruff. Run everything with `uv run` and `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache'` (bash) or `$env:UV_CACHE_DIR='...'` (PowerShell).

**Spec:** `docs/superpowers/specs/2026-06-12-p2-distribution-design.md`
**Depends on:** P0 (`solarstorm/honest_eval/`) and P1 (`solarstorm/onda3/_hybrid_iteration.py`) implemented; P1 decision `READY_FOR_P2_DISTRIBUTION_DESIGN`.

---

## Guardrails

- Every generated row carries `production_status = EXPERIMENT_ONLY`; reports
  carry the freeze line.
- Walk-forward only; the inner 80/20 split is chronological; the null refits
  per fold on years strictly before the test year. Nothing from the test
  year enters any fit, encoding, residual pool, or the null.
- Gate thresholds, candidate set, and decision matrix are frozen in the
  spec. Record whatever happens; tune nothing.
- Write only `reports/p2-distribution/`. No mutation of `data/*.parquet` or
  of P0/P1 artifacts.
- Fixed seed 7 for any randomness. Tests must not hit the network.

## File Structure

- Create: `solarstorm/distribution/__init__.py` — public exports.
- Create: `solarstorm/distribution/_constants.py` — names, statuses, freeze line.
- Create: `solarstorm/distribution/_quantiles.py` — canonical levels, member helpers.
- Create: `solarstorm/distribution/_crps.py` — vectorized member CRPS.
- Create: `solarstorm/distribution/_null.py` — climatological null distribution.
- Create: `solarstorm/distribution/_dressing.py` — residual-dressing candidate.
- Create: `solarstorm/distribution/_emos.py` — truncated-normal EMOS candidate.
- Create: `solarstorm/distribution/_coverage.py` — coverage, brackets, floor audit.
- Create: `solarstorm/distribution/_review.py` — gates D1-D4 + decision.
- Create: `solarstorm/distribution/_iteration.py` — fold orchestration + aggregates.
- Create: `solarstorm/distribution/_artifacts.py` — CSV/MD writer + report.
- Modify: `solarstorm/__main__.py` — add `p2-distribution-iteration`.
- Modify: `pyproject.toml` — declare `scipy>=1.11`.
- Create: `tests/test_p2_distribution.py` — unit tests.
- Create: `tests/test_p2_distribution_cli.py` — CLI smoke test.

All test commands below assume bash syntax; on PowerShell replace the env
prefix with `$env:UV_CACHE_DIR='...'; `. Prefix python output-heavy commands
with `PYTHONIOENCODING=utf-8` on Windows consoles.

---

### Task 1: Package skeleton — constants and canonical quantiles

**Files:**
- Create: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/__init__.py`
- Create: `solarstorm/distribution/_constants.py`
- Create: `solarstorm/distribution/_quantiles.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_p2_distribution.py`:

```python
"""Tests for the P2 calibrated distribution package."""
from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from solarstorm.distribution import (
    canonical_levels,
    empirical_member_quantiles,
    interpolated_cdf,
    interpolated_quantile,
)


def test_canonical_levels_are_midpoint_grid():
    levels = canonical_levels()

    assert levels.shape == (199,)
    assert levels[0] == pytest.approx(0.5 / 199)
    assert levels[-1] == pytest.approx(198.5 / 199)
    assert float(levels.mean()) == pytest.approx(0.5)


def test_empirical_member_quantiles_match_numpy():
    rng = np.random.default_rng(7)
    sample = rng.normal(0.0, 1.0, 500)

    members = empirical_member_quantiles(sample)

    assert members.shape == (199,)
    assert members[99] == pytest.approx(np.quantile(sample, 99.5 / 199))
    assert np.all(np.diff(members) >= 0)


def test_empirical_member_quantiles_reject_empty_sample():
    with pytest.raises(ValueError, match="empty"):
        empirical_member_quantiles(np.array([]))


def test_interpolated_quantile_and_cdf_round_trip():
    members = np.linspace(10.0, 20.0, 199)

    q30 = interpolated_quantile(members, 0.30)

    assert 10.0 < q30 < 20.0
    assert interpolated_cdf(members, q30) == pytest.approx(0.30, abs=1e-9)
    assert interpolated_cdf(members, 9.0) == 0.0
    assert interpolated_cdf(members, 21.0) == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'solarstorm.distribution'`

- [ ] **Step 3: Implement constants and quantile helpers**

`solarstorm/distribution/_constants.py`:

```python
"""Shared constants for the P2 calibrated distribution package."""
from __future__ import annotations

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
FREEZE_LINE = (
    "No production, EV, pricing, shadow trading, or execution work is unlocked."
)
N_MEMBERS = 199
CANDIDATE_DRESSING = "dist_residual_dressing"
CANDIDATE_EMOS = "dist_truncnorm_emos"
NULL_NAME = "dist_climatology_null"
SURFACE_GATING = "covered_om"
SURFACE_INFORMATIONAL = "local_all"
MIN_CELL_ROWS = 60
RANDOM_SEED = 7
```

`solarstorm/distribution/_quantiles.py`:

```python
"""Canonical quantile levels and member-vector helpers."""
from __future__ import annotations

import numpy as np

from solarstorm.distribution._constants import N_MEMBERS


def canonical_levels(n_members: int = N_MEMBERS) -> np.ndarray:
    """Levels ``(i - 0.5) / n`` for ``i = 1..n``."""
    return (np.arange(1, n_members + 1) - 0.5) / n_members


def empirical_member_quantiles(
    values: np.ndarray, n_members: int = N_MEMBERS
) -> np.ndarray:
    """Empirical quantiles of ``values`` at the canonical levels."""
    flat = np.asarray(values, dtype=np.float64).ravel()
    if flat.size == 0:
        raise ValueError("cannot take quantiles of an empty sample")
    return np.quantile(flat, canonical_levels(n_members))


def interpolated_quantile(members: np.ndarray, level: float) -> float:
    """Linear interpolation of the member quantile function at ``level``."""
    ordered = np.sort(np.asarray(members, dtype=np.float64))
    return float(np.interp(level, canonical_levels(ordered.size), ordered))


def interpolated_cdf(members: np.ndarray, x: float) -> float:
    """Empirical CDF with linear interpolation between sorted members."""
    ordered = np.sort(np.asarray(members, dtype=np.float64))
    return float(
        np.interp(x, ordered, canonical_levels(ordered.size), left=0.0, right=1.0)
    )
```

`solarstorm/distribution/__init__.py`:

```python
"""P2 calibrated distribution iteration (EXPERIMENT_ONLY)."""
from solarstorm.distribution._quantiles import (
    canonical_levels,
    empirical_member_quantiles,
    interpolated_cdf,
    interpolated_quantile,
)

__all__ = [
    "canonical_levels",
    "empirical_member_quantiles",
    "interpolated_cdf",
    "interpolated_quantile",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): canonical 199-quantile representation"
```

### Task 2: Empirical-member CRPS

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_crps.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import crps_members


def test_crps_of_point_mass_is_absolute_error():
    members = np.full((2, 199), 15.0)

    crps = crps_members(members, np.array([17.0, 15.0]))

    assert crps[0] == pytest.approx(2.0)
    assert crps[1] == pytest.approx(0.0)


def test_crps_matches_brute_force_double_sum():
    rng = np.random.default_rng(7)
    members = rng.normal(0.0, 2.0, size=(5, 23))
    actual = rng.normal(0.0, 2.0, size=5)

    crps = crps_members(members, actual)

    for row in range(5):
        m = members[row]
        brute = np.abs(m - actual[row]).mean() - 0.5 * np.abs(
            m[:, None] - m[None, :]
        ).mean()
        assert crps[row] == pytest.approx(brute)


def test_crps_rejects_non_matrix_members():
    with pytest.raises(ValueError, match="2-D"):
        crps_members(np.zeros(199), np.array([1.0]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k crps`
Expected: FAIL with `ImportError: cannot import name 'crps_members'`

- [ ] **Step 3: Implement `_crps.py`**

```python
"""Vectorized empirical-member CRPS."""
from __future__ import annotations

import numpy as np


def crps_members(members: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """CRPS of each (row, members) pair against the matching actual.

    ``CRPS = mean|x_i - y| - 0.5 * mean|x_i - x_j|``; the pairwise term uses
    the sorted prefix identity ``sum_ij |x_i - x_j| = 2 sum_j x_(j)(2j-n-1)``.
    """
    members = np.asarray(members, dtype=np.float64)
    if members.ndim != 2:
        raise ValueError("members must be a 2-D (rows, members) matrix")
    actual = np.asarray(actual, dtype=np.float64).ravel()
    if members.shape[0] != actual.shape[0]:
        raise ValueError("members and actual row counts differ")
    n_members = members.shape[1]
    term_abs = np.abs(members - actual[:, None]).mean(axis=1)
    ordered = np.sort(members, axis=1)
    ranks = 2.0 * np.arange(1, n_members + 1) - n_members - 1.0
    term_spread = (ordered * ranks).sum(axis=1) / (n_members * n_members)
    return term_abs - term_spread
```

Add `crps_members` to `__init__.py` imports and `__all__`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): vectorized empirical-member CRPS"
```

### Task 3: Climatological null distribution

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_null.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import fit_null_distribution, predict_null_members
from solarstorm.distribution._null import FALLBACK_MONTH


def _null_train_frame() -> pl.DataFrame:
    # 70 January rows (>= 60: monthly cell exists) and 20 March rows
    # (< 60: falls back) for one CP; rw alternates 1/3.
    rows = []
    for i in range(70):
        rows.append(
            {
                "date_local": dt.date(2021 + i % 2, 1, 1 + (i // 2) % 28),
                "cp": "23:00",
                "remaining_warming": 1 + 2 * (i % 2),
            }
        )
    for i in range(20):
        rows.append(
            {
                "date_local": dt.date(2021, 3, 1 + i),
                "cp": "23:00",
                "remaining_warming": 5,
            }
        )
    return pl.DataFrame(rows)


def test_null_distribution_builds_monthly_cells_with_fallback():
    table = fit_null_distribution(_null_train_frame())

    assert (1, "23:00") in table
    assert (3, "23:00") not in table  # only 20 rows -> below MIN_CELL_ROWS
    assert (FALLBACK_MONTH, "23:00") in table
    january = table[(1, "23:00")]
    assert january.min() >= 1.0 and january.max() <= 3.0


def test_null_members_locate_at_kcp_and_use_fallback():
    table = fit_null_distribution(_null_train_frame())
    rows = pl.DataFrame(
        {
            "date_local": [dt.date(2023, 1, 10), dt.date(2023, 6, 10)],
            "cp": ["23:00", "23:00"],
            "k_cp": [14, 20],
        }
    )

    members = predict_null_members(rows, table)

    assert members.shape == (2, 199)
    assert members[0].min() >= 14.0  # k_cp + rw >= k_cp
    # June is unseen -> per-CP fallback (pooled rw includes the 5s).
    assert members[1].max() == pytest.approx(20 + 5.0)


def test_null_distribution_rejects_empty_train():
    with pytest.raises(ValueError, match="no train rows"):
        fit_null_distribution(_null_train_frame().head(0))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k null`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_null.py`**

```python
"""Climatological null distribution: train-only realized rw quantiles."""
from __future__ import annotations

import numpy as np
import polars as pl

from solarstorm.distribution._constants import MIN_CELL_ROWS, N_MEMBERS
from solarstorm.distribution._quantiles import empirical_member_quantiles

FALLBACK_MONTH = 0


def fit_null_distribution(
    train: pl.DataFrame,
    *,
    n_members: int = N_MEMBERS,
    min_cell_rows: int = MIN_CELL_ROWS,
) -> dict[tuple[int, str], np.ndarray]:
    """Quantile members of realized rw per (month, cp) on train rows only.

    ``train`` needs columns date_local, cp, remaining_warming. ``month == 0``
    keys hold the per-CP fallback; monthly cells below ``min_cell_rows`` are
    omitted so prediction falls back.
    """
    if train.is_empty():
        raise ValueError("no train rows to fit the null distribution")
    dated = train.with_columns(pl.col("date_local").dt.month().alias("_month"))
    table: dict[tuple[int, str], np.ndarray] = {}
    for cp in dated["cp"].unique().sort().to_list():
        cp_rows = dated.filter(pl.col("cp") == cp)
        table[(FALLBACK_MONTH, cp)] = empirical_member_quantiles(
            cp_rows["remaining_warming"].to_numpy(), n_members
        )
        for month in cp_rows["_month"].unique().sort().to_list():
            month_rows = cp_rows.filter(pl.col("_month") == month)
            if month_rows.height >= min_cell_rows:
                table[(int(month), cp)] = empirical_member_quantiles(
                    month_rows["remaining_warming"].to_numpy(), n_members
                )
    return table


def predict_null_members(
    rows: pl.DataFrame, table: dict[tuple[int, str], np.ndarray]
) -> np.ndarray:
    """Tmax member matrix ``k_cp + rw_quantiles`` for (date_local, cp, k_cp) rows."""
    months = rows["date_local"].dt.month().to_list()
    cps = rows["cp"].to_list()
    kcps = rows["k_cp"].to_numpy().astype(np.float64)
    n_members = next(iter(table.values())).size
    members = np.empty((rows.height, n_members))
    for index, (month, cp) in enumerate(zip(months, cps)):
        quantiles = table.get((int(month), cp))
        if quantiles is None:
            quantiles = table.get((FALLBACK_MONTH, cp))
        if quantiles is None:
            raise ValueError(f"null distribution has no fallback for cp {cp}")
        members[index] = kcps[index] + quantiles
    return members
```

Add `fit_null_distribution` and `predict_null_members` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): climatological null distribution"
```

### Task 4: Residual-dressing candidate

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_dressing.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import fit_residual_dressing, predict_dressing_members
from solarstorm.distribution._dressing import POOLED_CP


def _calibration_frame() -> pl.DataFrame:
    # 80 rows at 22:00 (per-CP cell) with residual +2; 10 rows at 23:00
    # (below MIN_CELL_ROWS -> pooled fallback) with residual -1.
    rows = []
    for i in range(80):
        rows.append(
            {
                "date_local": dt.date(2021, 1, 1) + dt.timedelta(days=i),
                "cp": "22:00",
                "remaining_warming": 4.0,
                "rw_pred_raw": 2.0,
                "cp_lead_rank": 1,
            }
        )
    for i in range(10):
        rows.append(
            {
                "date_local": dt.date(2021, 4, 1) + dt.timedelta(days=i),
                "cp": "23:00",
                "remaining_warming": 1.0,
                "rw_pred_raw": 2.0,
                "cp_lead_rank": 0,
            }
        )
    return pl.DataFrame(rows)


def test_dressing_builds_per_cp_table_with_pooled_fallback():
    table = fit_residual_dressing(_calibration_frame())

    assert "22:00" in table
    assert "23:00" not in table  # 10 rows < MIN_CELL_ROWS
    assert POOLED_CP in table
    assert table["22:00"][99] == pytest.approx(2.0)  # median residual +2


def test_dressing_members_floor_at_kcp():
    table = fit_residual_dressing(_calibration_frame())
    rows = pl.DataFrame(
        {
            "date_local": [dt.date(2022, 1, 5)],
            "cp": ["22:00"],
            "k_cp": [15],
            "rw_pred_raw": [-6.0],  # raw prediction far below zero
        }
    )

    members = predict_dressing_members(rows, table)

    assert members.shape == (1, 199)
    assert members.min() >= 15.0  # max(0, rw) keeps Tmax at or above k_cp


def test_dressing_rejects_empty_calibration():
    with pytest.raises(ValueError, match="calibration"):
        fit_residual_dressing(_calibration_frame().head(0))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k dressing`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_dressing.py`**

```python
"""Residual-dressing candidate: empirical out-of-sample residual quantiles."""
from __future__ import annotations

import numpy as np
import polars as pl

from solarstorm.distribution._constants import MIN_CELL_ROWS, N_MEMBERS
from solarstorm.distribution._quantiles import empirical_member_quantiles

POOLED_CP = "ALL"


def fit_residual_dressing(
    calibration: pl.DataFrame,
    *,
    n_members: int = N_MEMBERS,
    min_cell_rows: int = MIN_CELL_ROWS,
) -> dict[str, np.ndarray]:
    """Residual quantiles (rw_actual - rw_pred_raw) per CP plus pooled fallback."""
    if calibration.is_empty():
        raise ValueError("calibration frame is empty")
    framed = calibration.with_columns(
        (pl.col("remaining_warming") - pl.col("rw_pred_raw")).alias("_residual")
    )
    table = {
        POOLED_CP: empirical_member_quantiles(framed["_residual"].to_numpy(), n_members)
    }
    for cp in framed["cp"].unique().sort().to_list():
        cp_rows = framed.filter(pl.col("cp") == cp)
        if cp_rows.height >= min_cell_rows:
            table[cp] = empirical_member_quantiles(
                cp_rows["_residual"].to_numpy(), n_members
            )
    return table


def predict_dressing_members(
    rows: pl.DataFrame, table: dict[str, np.ndarray]
) -> np.ndarray:
    """Tmax members ``k_cp + max(0, rw_pred_raw + e_q)`` per row."""
    kcps = rows["k_cp"].to_numpy().astype(np.float64)
    raw = rows["rw_pred_raw"].to_numpy().astype(np.float64)
    cps = rows["cp"].to_list()
    n_members = next(iter(table.values())).size
    members = np.empty((rows.height, n_members))
    for index, cp in enumerate(cps):
        residuals = table.get(cp, table[POOLED_CP])
        members[index] = kcps[index] + np.maximum(0.0, raw[index] + residuals)
    return members
```

Add `fit_residual_dressing` and `predict_dressing_members` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): residual-dressing candidate distribution"
```

### Task 5: Truncated-normal EMOS candidate (declares scipy)

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_emos.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Declare scipy in `pyproject.toml`**

In the `dependencies` list, after the `scikit-learn>=1.4` line, add:

```toml
    # P2 EMOS candidate (truncnorm quantiles + Nelder-Mead CRPS fit)
    "scipy>=1.11",
```

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv sync --extra dev`
Expected: resolves without error (scipy already present transitively).

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import fit_truncnorm_emos, predict_emos_members
from solarstorm.distribution._emos import SIGMA_MAX, SIGMA_MIN, _mu_sigma


def _emos_calibration(n: int = 240) -> pl.DataFrame:
    rng = np.random.default_rng(7)
    raw = rng.uniform(0.0, 6.0, n)
    noise = rng.normal(0.0, 1.2, n)
    return pl.DataFrame(
        {
            "date_local": [dt.date(2021, 1, 1) + dt.timedelta(days=i) for i in range(n)],
            "cp": ["21:00"] * n,
            "remaining_warming": np.maximum(0.0, raw + noise),
            "rw_pred_raw": raw,
            "cp_lead_rank": [2] * n,
        }
    )


def test_emos_members_are_sorted_and_non_negative_on_rw_scale():
    params = np.array([0.0, 1.0, 0.0, 0.0])
    rows = pl.DataFrame(
        {
            "date_local": [dt.date(2022, 1, 1)],
            "cp": ["21:00"],
            "k_cp": [12],
            "rw_pred_raw": [-2.0],  # mu below zero: truncation must hold
            "cp_lead_rank": [2],
        }
    )

    members = predict_emos_members(rows, params)

    assert members.shape == (1, 199)
    assert members.min() >= 12.0 - 1e-9
    assert np.all(np.diff(members[0]) >= 0)


def test_emos_fit_improves_on_init_and_respects_sigma_bounds():
    calibration = _emos_calibration()

    params = fit_truncnorm_emos(calibration)

    mu, sigma = _mu_sigma(
        params,
        calibration["rw_pred_raw"].to_numpy(),
        calibration["cp_lead_rank"].to_numpy().astype(np.float64),
    )
    assert np.all(sigma >= SIGMA_MIN) and np.all(sigma <= SIGMA_MAX)
    # b should stay near 1 for a well-specified synthetic relation.
    assert 0.4 <= params[1] <= 1.6
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k emos`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Implement `_emos.py`**

```python
"""Truncated-normal EMOS candidate fit by minimizing sampled CRPS."""
from __future__ import annotations

import numpy as np
import polars as pl
from scipy.optimize import minimize
from scipy.stats import truncnorm

from solarstorm.distribution._constants import N_MEMBERS
from solarstorm.distribution._crps import crps_members
from solarstorm.distribution._quantiles import canonical_levels

SIGMA_MIN = 0.1
SIGMA_MAX = 10.0


def _truncnorm_members(
    mu: np.ndarray, sigma: np.ndarray, n_members: int
) -> np.ndarray:
    """Quantiles of N(mu, sigma) truncated to [0, inf), one row per element."""
    levels = canonical_levels(n_members)
    lower = (0.0 - mu[:, None]) / sigma[:, None]
    return truncnorm.ppf(
        levels[None, :], lower, np.inf, loc=mu[:, None], scale=sigma[:, None]
    )


def _mu_sigma(
    params: np.ndarray, rw_pred_raw: np.ndarray, cp_lead_rank: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    a, b, c, d = (float(value) for value in params)
    mu = a + b * rw_pred_raw
    sigma = np.clip(np.exp(c + d * cp_lead_rank), SIGMA_MIN, SIGMA_MAX)
    return mu, sigma


def fit_truncnorm_emos(
    calibration: pl.DataFrame, *, n_members: int = N_MEMBERS
) -> np.ndarray:
    """Fit (a, b, c, d) by Nelder-Mead on mean member CRPS (rw scale)."""
    if calibration.is_empty():
        raise ValueError("calibration frame is empty")
    rw = calibration["remaining_warming"].to_numpy().astype(np.float64)
    raw = calibration["rw_pred_raw"].to_numpy().astype(np.float64)
    lead = calibration["cp_lead_rank"].to_numpy().astype(np.float64)
    residual_std = float(np.std(rw - raw))
    init = np.array([0.0, 1.0, np.log(max(residual_std, SIGMA_MIN)), 0.0])

    def objective(params: np.ndarray) -> float:
        mu, sigma = _mu_sigma(params, raw, lead)
        return float(crps_members(_truncnorm_members(mu, sigma, n_members), rw).mean())

    result = minimize(
        objective,
        init,
        method="Nelder-Mead",
        options={"maxiter": 400, "xatol": 1e-3, "fatol": 1e-4},
    )
    return np.asarray(result.x, dtype=np.float64)


def predict_emos_members(
    rows: pl.DataFrame, params: np.ndarray, *, n_members: int = N_MEMBERS
) -> np.ndarray:
    """Tmax members ``k_cp + TruncNormal(mu, sigma, lower=0)`` quantiles."""
    raw = rows["rw_pred_raw"].to_numpy().astype(np.float64)
    lead = rows["cp_lead_rank"].to_numpy().astype(np.float64)
    mu, sigma = _mu_sigma(np.asarray(params, dtype=np.float64), raw, lead)
    kcps = rows["k_cp"].to_numpy().astype(np.float64)
    return kcps[:, None] + _truncnorm_members(mu, sigma, n_members)
```

Add `fit_truncnorm_emos` and `predict_emos_members` to `__init__.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (15 tests)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): truncated-normal EMOS candidate, declare scipy"
```

### Task 6: Coverage, bracket integrity, and floor audit

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_coverage.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import (
    bracket_probability_sums,
    interval_coverage_flags,
    row_quantiles,
)


def test_row_quantiles_interpolate_each_row():
    members = np.vstack([np.linspace(0.0, 10.0, 199), np.linspace(5.0, 6.0, 199)])

    quantiles = row_quantiles(members, [0.05, 0.50, 0.95])

    assert quantiles.shape == (2, 3)
    assert quantiles[0, 1] == pytest.approx(5.0, abs=0.05)
    assert quantiles[1, 0] < quantiles[1, 2]


def test_interval_coverage_flags_inside_and_outside():
    members = np.vstack([np.linspace(10.0, 20.0, 199)] * 2)

    flags = interval_coverage_flags(members, np.array([15.0, 25.0]), 0.05, 0.95)

    assert flags.tolist() == [True, False]


def test_bracket_probability_sums_are_one():
    rng = np.random.default_rng(7)
    members = np.sort(rng.normal(18.0, 2.0, size=(3, 199)), axis=1)

    sums = bracket_probability_sums(members)

    assert np.allclose(sums, 1.0, atol=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k "row_quantiles or coverage_flags or bracket"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_coverage.py`**

```python
"""Interval coverage, integer-bracket integrity, and the distributional floor."""
from __future__ import annotations

import numpy as np

from solarstorm.distribution._quantiles import canonical_levels

SELECTED_LEVELS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)


def row_quantiles(members: np.ndarray, levels_out) -> np.ndarray:
    """Interpolated quantiles per row at ``levels_out``."""
    members = np.asarray(members, dtype=np.float64)
    levels = canonical_levels(members.shape[1])
    ordered = np.sort(members, axis=1)
    out = np.empty((members.shape[0], len(levels_out)))
    for index, row in enumerate(ordered):
        out[index] = np.interp(levels_out, levels, row)
    return out


def interval_coverage_flags(
    members: np.ndarray,
    actual: np.ndarray,
    lower_level: float,
    upper_level: float,
) -> np.ndarray:
    """True where ``actual`` falls inside [q(lower_level), q(upper_level)]."""
    bounds = row_quantiles(members, [lower_level, upper_level])
    actual = np.asarray(actual, dtype=np.float64).ravel()
    return (actual >= bounds[:, 0]) & (actual <= bounds[:, 1])


def bracket_probability_sums(members: np.ndarray) -> np.ndarray:
    """Per-row sum of integer-bracket probabilities (must be 1).

    Brackets are ``(b - 0.5, b + 0.5]`` for integers spanning the member
    range; probabilities come from the interpolated member CDF with tails
    clipped to 0 and 1.
    """
    members = np.asarray(members, dtype=np.float64)
    levels = canonical_levels(members.shape[1])
    sums = np.empty(members.shape[0])
    for index in range(members.shape[0]):
        row = np.sort(members[index])
        low = np.floor(row[0]) - 0.5
        high = np.ceil(row[-1]) + 0.5
        edges = np.arange(low, high + 1.0)
        cdf = np.interp(edges, row, levels, left=0.0, right=1.0)
        sums[index] = float(np.diff(cdf).sum())
    return sums
```

Add `SELECTED_LEVELS`, `row_quantiles`, `interval_coverage_flags`, and
`bracket_probability_sums` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): coverage, bracket integrity, floor helpers"
```

### Task 7: Gates D1-D4 and decision

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_review.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import build_p2_decision, build_p2_gates


def _gate_inputs(
    *, beats_null: bool, coverage_90: float = 90.0, floor_violations: int = 0
):
    candidate = "dist_residual_dressing"
    cps = ["20:00", "21:00", "22:00", "23:00"]
    by_cp = pl.DataFrame(
        {
            "distribution_name": [candidate] * 4,
            "cp": cps,
            "n_rows": [200] * 4,
            "candidate_crps": [0.6 if beats_null else 1.2] * 4,
            "null_crps": [1.0] * 4,
            "candidate_beats_null": [beats_null] * 4,
        }
    )
    by_stratum_cp = pl.DataFrame(
        {
            "distribution_name": [candidate] * 5,
            "rw_stratum": ["forecast_2_plus"] * 5,
            "cp": ["ALL", *cps],
            "n_rows": [400, 100, 100, 100, 100],
            "candidate_crps": [0.6 if beats_null else 1.2] * 5,
            "null_crps": [1.0] * 5,
            "candidate_beats_null": [beats_null] * 5,
        }
    )
    coverage = pl.DataFrame(
        {
            "distribution_name": [candidate],
            "coverage_90_pct": [coverage_90],
            "coverage_50_pct": [50.0],
        }
    )
    floor_audit = pl.DataFrame(
        {
            "distribution_name": [candidate],
            "cp": ["ALL"],
            "n_rows": [800],
            "n_floor_violations": [floor_violations],
            "max_bracket_deviation": [0.0],
        }
    )
    return {
        "by_cp": by_cp,
        "by_stratum_cp": by_stratum_cp,
        "coverage": coverage,
        "floor_audit": floor_audit,
        "candidate": candidate,
    }


def test_gates_all_pass_when_candidate_beats_null_and_calibrates():
    gates, summary = build_p2_gates(**_gate_inputs(beats_null=True))

    assert gates.filter(pl.col("gate_status") != "PASS").is_empty()
    assert summary == {"d123_pass": True, "d4_pass": True}


def test_gate_d1_blocks_when_null_wins():
    gates, summary = build_p2_gates(**_gate_inputs(beats_null=False))

    d1 = gates.filter(pl.col("gate_id") == "D1").row(0, named=True)
    assert d1["gate_status"] == "BLOCK"
    assert summary["d123_pass"] is False


def test_gate_d3_blocks_on_coverage_outside_bounds():
    gates, summary = build_p2_gates(**_gate_inputs(beats_null=True, coverage_90=79.0))

    d3 = gates.filter(pl.col("gate_id") == "D3").row(0, named=True)
    assert d3["gate_status"] == "BLOCK"
    assert summary["d123_pass"] is False
    assert summary["d4_pass"] is True


def test_decision_promotes_lowest_crps_passer():
    decision = build_p2_decision(
        {
            "dist_residual_dressing": {
                "d123_pass": True,
                "d4_pass": True,
                "pooled_crps": 0.71,
            },
            "dist_truncnorm_emos": {
                "d123_pass": True,
                "d4_pass": True,
                "pooled_crps": 0.66,
            },
        }
    ).row(0, named=True)

    assert decision["decision_status"] == "READY_FOR_P3_ABSTENTION_DESIGN"
    assert decision["promoted_candidate"] == "dist_truncnorm_emos"
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def test_decision_d4_failure_forces_review():
    decision = build_p2_decision(
        {
            "dist_residual_dressing": {
                "d123_pass": True,
                "d4_pass": False,
                "pooled_crps": 0.71,
            },
            "dist_truncnorm_emos": {
                "d123_pass": True,
                "d4_pass": True,
                "pooled_crps": 0.66,
            },
        }
    ).row(0, named=True)

    assert decision["decision_status"] == "KEEP_IN_P2_DISTRIBUTION_REVIEW"
    assert decision["promoted_candidate"] is None


def test_decision_no_passer_keeps_point_hybrid():
    decision = build_p2_decision(
        {
            "dist_residual_dressing": {
                "d123_pass": False,
                "d4_pass": True,
                "pooled_crps": 1.2,
            },
            "dist_truncnorm_emos": {
                "d123_pass": False,
                "d4_pass": True,
                "pooled_crps": 1.1,
            },
        }
    ).row(0, named=True)

    assert decision["decision_status"] == "KEEP_POINT_HYBRID_AS_REFERENCE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k "gates or decision"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_review.py`**

```python
"""Frozen D1-D4 gate matrix and decision for the P2 distribution iteration."""
from __future__ import annotations

import polars as pl

from solarstorm.distribution._constants import (
    CANDIDATE_DRESSING,
    CANDIDATE_EMOS,
    PRODUCTION_STATUS,
)

EXPECTED_CPS = ("20:00", "21:00", "22:00", "23:00")
FORECAST_STRATUM = "forecast_2_plus"
D2_MIN_ROWS = 30
COVERAGE_90_BOUNDS = (85.0, 95.0)
COVERAGE_50_BOUNDS = (40.0, 60.0)
BRACKET_TOLERANCE = 1e-6
DECISION_READY_P3 = "READY_FOR_P3_ABSTENTION_DESIGN"
DECISION_POINT_REFERENCE = "KEEP_POINT_HYBRID_AS_REFERENCE"
DECISION_REVIEW = "KEEP_IN_P2_DISTRIBUTION_REVIEW"


def _gate_row(gate_id: str, gate_name: str, ok: bool, detail: str) -> dict[str, object]:
    return {
        "gate_id": gate_id,
        "gate_name": gate_name,
        "gate_status": "PASS" if ok else "BLOCK",
        "gate_detail": detail,
        "production_status": PRODUCTION_STATUS,
    }


def build_p2_gates(
    *,
    by_cp: pl.DataFrame,
    by_stratum_cp: pl.DataFrame,
    coverage: pl.DataFrame,
    floor_audit: pl.DataFrame,
    candidate: str,
) -> tuple[pl.DataFrame, dict[str, bool]]:
    """Evaluate frozen D1-D4 for one candidate; returns (gates, summary)."""
    cp_rows = by_cp.filter(pl.col("distribution_name") == candidate)
    present = set(cp_rows["cp"].to_list())
    missing = [cp for cp in EXPECTED_CPS if cp not in present]
    d1_ok = not missing and cp_rows.filter(~pl.col("candidate_beats_null")).is_empty()
    d1_detail = (
        f"missing CP rows: {','.join(missing)}"
        if missing
        else (
            "candidate CRPS below null CRPS at every CP"
            if d1_ok
            else "candidate CRPS is not below null CRPS at every CP"
        )
    )

    stratum_rows = by_stratum_cp.filter(
        (pl.col("distribution_name") == candidate)
        & (pl.col("rw_stratum") == FORECAST_STRATUM)
    )
    overall = stratum_rows.filter(pl.col("cp") == "ALL")
    support = stratum_rows.filter(
        (pl.col("cp") != "ALL") & (pl.col("n_rows") >= D2_MIN_ROWS)
    )
    d2_ok = (
        not overall.is_empty()
        and bool(overall["candidate_beats_null"][0])
        and not support.is_empty()
        and support.filter(~pl.col("candidate_beats_null")).is_empty()
    )
    d2_detail = (
        f"forecast_2_plus supported_cps={support.height}; "
        f"overall_beats_null={bool(overall['candidate_beats_null'][0]) if not overall.is_empty() else False}"
    )

    coverage_row = coverage.filter(pl.col("distribution_name") == candidate)
    if coverage_row.is_empty():
        d3_ok = False
        d3_detail = "coverage row missing"
    else:
        cov90 = float(coverage_row["coverage_90_pct"][0])
        cov50 = float(coverage_row["coverage_50_pct"][0])
        d3_ok = (
            COVERAGE_90_BOUNDS[0] <= cov90 <= COVERAGE_90_BOUNDS[1]
            and COVERAGE_50_BOUNDS[0] <= cov50 <= COVERAGE_50_BOUNDS[1]
        )
        d3_detail = (
            f"coverage_90={cov90:.1f}% bounds={COVERAGE_90_BOUNDS}; "
            f"coverage_50={cov50:.1f}% bounds={COVERAGE_50_BOUNDS}"
        )

    all_row = floor_audit.filter(
        (pl.col("distribution_name") == candidate) & (pl.col("cp") == "ALL")
    )
    if all_row.is_empty():
        d4_ok = False
        d4_detail = "floor audit ALL row missing"
    else:
        violations = int(all_row["n_floor_violations"][0])
        deviation = float(all_row["max_bracket_deviation"][0])
        d4_ok = violations == 0 and deviation <= BRACKET_TOLERANCE
        d4_detail = (
            f"floor_violations={violations}; max_bracket_deviation={deviation:.2e}"
        )

    gates = pl.DataFrame(
        [
            _gate_row("D1", "CRPS lift per CP", d1_ok, d1_detail),
            _gate_row("D2", "Anticipation stratum", d2_ok, d2_detail),
            _gate_row("D3", "Central-interval calibration", d3_ok, d3_detail),
            _gate_row("D4", "Distributional floor + integrity", d4_ok, d4_detail),
        ],
        strict=False,
    ).with_columns(pl.lit(candidate).alias("distribution_name"))
    return gates, {"d123_pass": d1_ok and d2_ok and d3_ok, "d4_pass": d4_ok}


def build_p2_decision(candidate_summaries: dict[str, dict]) -> pl.DataFrame:
    """Pre-registered decision: D4 sanity, then D1+D2+D3, then lowest CRPS."""
    if any(not summary["d4_pass"] for summary in candidate_summaries.values()):
        decision_status = DECISION_REVIEW
        promoted = None
    else:
        passers = {
            name: summary
            for name, summary in candidate_summaries.items()
            if summary["d123_pass"]
        }
        if passers:
            promoted = min(passers, key=lambda name: passers[name]["pooled_crps"])
            decision_status = DECISION_READY_P3
        else:
            promoted = None
            decision_status = DECISION_POINT_REFERENCE

    def pooled(name: str) -> float | None:
        summary = candidate_summaries.get(name)
        return None if summary is None else float(summary["pooled_crps"])

    return pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "promoted_candidate": promoted,
                "dist_residual_dressing_pooled_crps": pooled(CANDIDATE_DRESSING),
                "dist_truncnorm_emos_pooled_crps": pooled(CANDIDATE_EMOS),
                "decision_rationale": (
                    "Frozen P2 gates D1-D4 plus same-row CRPS promotion, "
                    "pre-registered in "
                    "docs/superpowers/specs/2026-06-12-p2-distribution-design.md."
                ),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
```

Add `build_p2_gates` and `build_p2_decision` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (24 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): frozen gates D1-D4 and pre-registered decision"
```

### Task 8: Fold orchestration and aggregates

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_iteration.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import (
    build_p2_aggregates,
    build_p2_distribution_iteration,
)
from solarstorm.distribution._constants import (
    CANDIDATE_DRESSING,
    CANDIDATE_EMOS,
    NULL_NAME,
    SURFACE_GATING,
)
from solarstorm.distribution._iteration import _inner_split


def _p2_matrix(n_days: int = 500) -> pl.DataFrame:
    rng = np.random.default_rng(7)
    rows = []
    for i in range(n_days):
        date = dt.date(2021, 1, 1) + dt.timedelta(days=i)
        for cp_index, cp in enumerate(("20:00", "21:00", "22:00", "23:00")):
            signal = float(rng.normal(0.0, 1.0))
            rw = max(0, round(2.0 + signal - cp_index * 0.5))
            k_cp = 15 + (i % 5) + cp_index
            rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "k_cp": k_cp,
                    "tmax_int": k_cp + rw,
                    "remaining_warming": rw,
                    "signal_feature": signal,
                    "cp_lead_rank": 3 - cp_index,
                }
            )
    return pl.DataFrame(rows)


def test_inner_split_is_chronological_80_20():
    matrix = _p2_matrix(100)

    point_fit, calibration = _inner_split(matrix)

    assert point_fit.height + calibration.height == matrix.height
    assert point_fit.height == int(matrix.height * 0.8)
    assert point_fit["date_local"].max() <= calibration["date_local"].min()


def test_iteration_scores_candidates_and_null_on_identical_rows():
    artifacts = build_p2_distribution_iteration(
        _p2_matrix(),
        test_years=[2022],
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
        surface=SURFACE_GATING,
    )

    scored = artifacts["scored"]
    names = set(scored["distribution_name"].unique().to_list())
    assert names == {CANDIDATE_DRESSING, CANDIDATE_EMOS, NULL_NAME}
    keys_per_name = [
        set(
            scored.filter(pl.col("distribution_name") == name)
            .select(["date_local", "cp"])
            .iter_rows()
        )
        for name in names
    ]
    assert keys_per_name[0] == keys_per_name[1] == keys_per_name[2]
    assert scored.filter(pl.col("n_floor_violations") > 0).is_empty()
    assert scored["surface"].unique().to_list() == [SURFACE_GATING]
    results = artifacts["results"]
    assert set(results["distribution_name"].to_list()) == names


def test_iteration_skips_test_year_without_prior_train_rows():
    artifacts = build_p2_distribution_iteration(
        _p2_matrix(),
        test_years=[2021, 2022],  # 2021 has no earlier train year
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
        surface=SURFACE_GATING,
    )

    assert artifacts["scored"]["test_year"].unique().to_list() == [2022]


def test_aggregates_produce_comparison_coverage_and_floor_tables():
    artifacts = build_p2_distribution_iteration(
        _p2_matrix(),
        test_years=[2022],
        numeric_feature_columns=["signal_feature", "cp_lead_rank"],
        categorical_feature_columns=[],
        surface=SURFACE_GATING,
    )

    aggregates = build_p2_aggregates(artifacts["scored"])

    by_cp = aggregates["by_cp"]
    assert set(by_cp.columns) >= {
        "surface",
        "distribution_name",
        "cp",
        "n_rows",
        "candidate_crps",
        "null_crps",
        "candidate_beats_null",
    }
    assert by_cp["cp"].n_unique() == 4
    stratum_cps = aggregates["by_stratum_cp"]["cp"].unique().to_list()
    assert "ALL" in stratum_cps
    coverage = aggregates["coverage"]
    assert coverage.height == 2  # one row per candidate
    floor_audit = aggregates["floor_audit"]
    assert not floor_audit.filter(pl.col("cp") == "ALL").is_empty()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k "inner_split or iteration or aggregates"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_iteration.py`**

```python
"""Walk-forward fold orchestration for the P2 distribution iteration."""
from __future__ import annotations

import numpy as np
import polars as pl

from solarstorm.distribution._constants import (
    CANDIDATE_DRESSING,
    CANDIDATE_EMOS,
    NULL_NAME,
    PRODUCTION_STATUS,
)
from solarstorm.distribution._coverage import (
    SELECTED_LEVELS,
    bracket_probability_sums,
    interval_coverage_flags,
    row_quantiles,
)
from solarstorm.distribution._crps import crps_members
from solarstorm.distribution._dressing import (
    fit_residual_dressing,
    predict_dressing_members,
)
from solarstorm.distribution._emos import fit_truncnorm_emos, predict_emos_members
from solarstorm.distribution._null import fit_null_distribution, predict_null_members
from solarstorm.honest_eval import assign_remaining_warming_strata
from solarstorm.onda3._baseline_model import _ridge_predict
from solarstorm.onda3._pooled_iteration import _encode_features

INNER_TRAIN_FRACTION = 0.8


def _inner_split(train: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Chronological 80/20 split: (point-fit segment, calibration segment)."""
    ordered = train.sort("date_local")
    cutoff = int(ordered.height * INNER_TRAIN_FRACTION)
    point_fit, calibration = ordered.head(cutoff), ordered.slice(cutoff)
    if point_fit.is_empty() or calibration.is_empty():
        raise ValueError("train window too small for the inner 80/20 split")
    return point_fit, calibration


def _point_predictions(
    fit: pl.DataFrame,
    predict: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> np.ndarray:
    fit_x, predict_x = _encode_features(
        fit,
        predict,
        numeric_feature_columns=numeric_feature_columns,
        categorical_feature_columns=categorical_feature_columns,
    )
    return _ridge_predict(fit_x, fit["remaining_warming"].to_numpy(), predict_x)


def run_p2_fold(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> pl.DataFrame:
    """Score both candidates and the per-fold null on one walk-forward fold."""
    point_fit, calibration = _inner_split(train)
    calibration = calibration.with_columns(
        pl.Series(
            "rw_pred_raw",
            _point_predictions(
                point_fit,
                calibration,
                numeric_feature_columns=numeric_feature_columns,
                categorical_feature_columns=categorical_feature_columns,
            ),
        )
    )
    dressing_table = fit_residual_dressing(calibration)
    emos_params = fit_truncnorm_emos(calibration)
    null_table = fit_null_distribution(train)
    test = test.with_columns(
        pl.Series(
            "rw_pred_raw",
            _point_predictions(
                train,
                test,
                numeric_feature_columns=numeric_feature_columns,
                categorical_feature_columns=categorical_feature_columns,
            ),
        )
    )
    actual = test["tmax_int"].to_numpy().astype(np.float64)
    kcp_column = test["k_cp"].to_numpy().astype(np.float64)
    member_sets = {
        CANDIDATE_DRESSING: predict_dressing_members(test, dressing_table),
        CANDIDATE_EMOS: predict_emos_members(test, emos_params),
        NULL_NAME: predict_null_members(test, null_table),
    }
    frames: list[pl.DataFrame] = []
    for distribution_name, members in member_sets.items():
        quantiles = row_quantiles(members, list(SELECTED_LEVELS))
        frames.append(
            test.select(["date_local", "cp", "k_cp"]).with_columns(
                pl.Series("actual", actual),
                pl.lit(distribution_name).alias("distribution_name"),
                pl.Series("crps", crps_members(members, actual)),
                *[
                    pl.Series(f"q{int(level * 100):02d}", quantiles[:, position])
                    for position, level in enumerate(SELECTED_LEVELS)
                ],
                pl.Series(
                    "covered_90", interval_coverage_flags(members, actual, 0.05, 0.95)
                ),
                pl.Series(
                    "covered_50", interval_coverage_flags(members, actual, 0.25, 0.75)
                ),
                pl.Series(
                    "n_floor_violations",
                    (members < kcp_column[:, None] - 1e-9).sum(axis=1),
                ),
                pl.Series(
                    "bracket_probability_sum", bracket_probability_sums(members)
                ),
                pl.lit(PRODUCTION_STATUS).alias("production_status"),
            )
        )
    return pl.concat(frames, how="vertical")


def build_p2_distribution_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    surface: str,
) -> dict[str, pl.DataFrame]:
    """Walk-forward over ``test_years``; returns scored rows + fold results."""
    scored_frames: list[pl.DataFrame] = []
    result_rows: list[dict[str, object]] = []
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    for test_year in test_years:
        train = dated.filter(pl.col("_year") < test_year).drop("_year")
        test = dated.filter(pl.col("_year") == test_year).drop("_year")
        if train.is_empty() or test.is_empty():
            continue
        scored = run_p2_fold(
            train,
            test,
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
        ).with_columns(
            pl.lit(test_year).alias("test_year"),
            pl.lit(surface).alias("surface"),
        )
        scored_frames.append(scored)
        for distribution_name in (CANDIDATE_DRESSING, CANDIDATE_EMOS, NULL_NAME):
            fold_rows = scored.filter(
                pl.col("distribution_name") == distribution_name
            )
            result_rows.append(
                {
                    "surface": surface,
                    "test_year": test_year,
                    "distribution_name": distribution_name,
                    "n_train": train.height,
                    "n_test": test.height,
                    "mean_crps": float(fold_rows["crps"].mean()),
                    "production_status": PRODUCTION_STATUS,
                }
            )
    scored_all = (
        pl.concat(scored_frames, how="vertical")
        if scored_frames
        else pl.DataFrame()
    )
    return {
        "scored": scored_all,
        "results": pl.DataFrame(result_rows, strict=False),
    }


def build_p2_aggregates(scored: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Comparison, coverage, and floor tables from scored per-row frames."""
    null_rows = scored.filter(pl.col("distribution_name") == NULL_NAME).select(
        ["surface", "test_year", "date_local", "cp", pl.col("crps").alias("null_crps")]
    )
    candidates = (
        scored.filter(pl.col("distribution_name") != NULL_NAME)
        .join(null_rows, on=["surface", "test_year", "date_local", "cp"], how="inner")
    )
    candidates = assign_remaining_warming_strata(candidates)

    def summary(keys: list[str]) -> pl.DataFrame:
        return (
            candidates.group_by(["surface", "distribution_name", *keys])
            .agg(
                pl.len().alias("n_rows"),
                pl.col("crps").mean().alias("candidate_crps"),
                pl.col("null_crps").mean().alias("null_crps"),
            )
            .with_columns(
                (pl.col("candidate_crps") < pl.col("null_crps")).alias(
                    "candidate_beats_null"
                ),
                pl.lit(PRODUCTION_STATUS).alias("production_status"),
            )
            .sort(["surface", "distribution_name", *keys])
        )

    by_stratum_cp = pl.concat(
        [
            summary(["rw_stratum", "cp"]),
            summary(["rw_stratum"]).with_columns(pl.lit("ALL").alias("cp")),
        ],
        how="diagonal_relaxed",
    ).sort(["surface", "distribution_name", "rw_stratum", "cp"])

    coverage = (
        candidates.group_by(["surface", "distribution_name"])
        .agg(
            pl.len().alias("n_rows"),
            (pl.col("covered_90").mean() * 100.0).alias("coverage_90_pct"),
            (pl.col("covered_50").mean() * 100.0).alias("coverage_50_pct"),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort(["surface", "distribution_name"])
    )

    floor_per_cp = (
        scored.group_by(["surface", "distribution_name", "cp"])
        .agg(
            pl.len().alias("n_rows"),
            pl.col("n_floor_violations").sum().alias("n_floor_violations"),
            (pl.col("bracket_probability_sum") - 1.0)
            .abs()
            .max()
            .alias("max_bracket_deviation"),
        )
        .sort(["surface", "distribution_name", "cp"])
    )
    floor_overall = (
        scored.group_by(["surface", "distribution_name"])
        .agg(
            pl.len().alias("n_rows"),
            pl.col("n_floor_violations").sum().alias("n_floor_violations"),
            (pl.col("bracket_probability_sum") - 1.0)
            .abs()
            .max()
            .alias("max_bracket_deviation"),
        )
        .with_columns(pl.lit("ALL").alias("cp"))
        .select(floor_per_cp.columns)
    )
    floor_audit = pl.concat([floor_overall, floor_per_cp], how="vertical").with_columns(
        pl.lit(PRODUCTION_STATUS).alias("production_status")
    )

    return {
        "by_cp": summary(["cp"]),
        "by_stratum_cp": by_stratum_cp,
        "coverage": coverage,
        "floor_audit": floor_audit,
    }
```

Add `run_p2_fold`, `build_p2_distribution_iteration`, and
`build_p2_aggregates` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (28 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): walk-forward fold orchestration and aggregates"
```

### Task 9: Artifact writer and report

**Files:**
- Modify: `tests/test_p2_distribution.py`
- Create: `solarstorm/distribution/_artifacts.py`
- Modify: `solarstorm/distribution/__init__.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_p2_distribution.py`:

```python
from solarstorm.distribution import write_p2_distribution_artifacts


def test_writer_emits_csv_md_pairs_and_report(tmp_path):
    frame = pl.DataFrame(
        {"distribution_name": ["dist_residual_dressing"],
         "production_status": ["EXPERIMENT_ONLY"]}
    )
    artifacts = {
        "p2_distribution_results_v1": frame,
        "p2_distribution_by_cp_v1": frame,
        "p2_distribution_by_stratum_cp_v1": frame,
        "p2_distribution_coverage_v1": frame,
        "p2_distribution_quantile_predictions_v1": frame,
        "p2_distribution_floor_audit_v1": frame,
        "p2_distribution_gates_v1": frame,
        "p2_distribution_decision_v1": pl.DataFrame(
            [{"decision_status": "KEEP_POINT_HYBRID_AS_REFERENCE",
              "production_status": "EXPERIMENT_ONLY"}]
        ),
    }

    paths = write_p2_distribution_artifacts(
        artifacts, output_dir=tmp_path, today=dt.date(2026, 6, 12)
    )

    assert (tmp_path / "p2_distribution_decision_v1.csv").exists()
    assert (tmp_path / "p2_distribution_gates_v1.md").exists()
    report = (tmp_path / "p2_distribution_report_v1.md").read_text(encoding="utf-8")
    assert "EXPERIMENT_ONLY" in report
    assert (
        "No production, EV, pricing, shadow trading, or execution work is unlocked."
        in report
    )
    assert "p2_distribution_report_md" in paths
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q -k writer`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement `_artifacts.py`**

```python
"""CSV/MD artifact writer for the P2 distribution iteration."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.distribution._constants import FREEZE_LINE
from solarstorm.onda3._pooled_iteration import _markdown_table

P2_FILENAMES = {
    "p2_distribution_results_v1": "p2_distribution_results_v1.csv",
    "p2_distribution_by_cp_v1": "p2_distribution_by_cp_v1.csv",
    "p2_distribution_by_stratum_cp_v1": "p2_distribution_by_stratum_cp_v1.csv",
    "p2_distribution_coverage_v1": "p2_distribution_coverage_v1.csv",
    "p2_distribution_quantile_predictions_v1": (
        "p2_distribution_quantile_predictions_v1.csv"
    ),
    "p2_distribution_floor_audit_v1": "p2_distribution_floor_audit_v1.csv",
    "p2_distribution_gates_v1": "p2_distribution_gates_v1.csv",
    "p2_distribution_decision_v1": "p2_distribution_decision_v1.csv",
}


def render_p2_distribution_report(
    artifacts: dict[str, pl.DataFrame], *, today: dt.date
) -> str:
    """Render the P2 distribution report."""

    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# P2 Calibrated Distribution Report",
            f"Generated: {today.isoformat()}",
            "All outputs remain EXPERIMENT_ONLY.",
            FREEZE_LINE,
            "## Decision",
            _markdown_table(frame("p2_distribution_decision_v1")),
            "## Gates D1-D4 per Candidate",
            _markdown_table(frame("p2_distribution_gates_v1"), max_rows=20),
            "## Candidate vs Null CRPS by CP",
            _markdown_table(frame("p2_distribution_by_cp_v1"), max_rows=40),
            "## Candidate vs Null CRPS by Stratum x CP",
            _markdown_table(frame("p2_distribution_by_stratum_cp_v1"), max_rows=60),
            "## Central-Interval Coverage",
            _markdown_table(frame("p2_distribution_coverage_v1")),
            "## Distributional Floor Audit",
            _markdown_table(frame("p2_distribution_floor_audit_v1"), max_rows=40),
            "## Fold Results",
            _markdown_table(frame("p2_distribution_results_v1"), max_rows=40),
        ]
    ) + "\n"


def write_p2_distribution_artifacts(
    artifacts: dict[str, pl.DataFrame], *, output_dir: Path, today: dt.date
) -> dict[str, Path]:
    """Write CSV/MD pairs plus the report; returns written paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in P2_FILENAMES.items():
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
    report_path = output_dir / "p2_distribution_report_v1.md"
    report_path.write_text(
        render_p2_distribution_report(artifacts, today=today), encoding="utf-8"
    )
    paths["p2_distribution_report_md"] = report_path
    return paths
```

Add `write_p2_distribution_artifacts` to `__init__.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py -q`
Expected: PASS (29 tests)

- [ ] **Step 5: Commit**

```bash
git add solarstorm/distribution tests/test_p2_distribution.py
git commit -m "feat(p2): artifact writer and report"
```

### Task 10: CLI command

**Files:**
- Modify: `solarstorm/__main__.py`
- Create: `tests/test_p2_distribution_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

`tests/test_p2_distribution_cli.py`:

```python
"""CLI smoke test for p2-distribution-iteration (fixtures, no network)."""
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
                "date_local": date,
                "tmax_int": tmax,
                "k_cp__cp_2000": tmax - 4,
                "k_cp__cp_2100": tmax - 3,
                "k_cp__cp_2200": tmax - 2,
                "k_cp__cp_2300": tmax - 1,
            }
        )
        for cp in ("20:00", "21:00", "22:00", "23:00"):
            feature_rows.append(
                {
                    "date_local": date,
                    "cp": cp,
                    "cloud_cover_suppression": float(i % 3),
                    "foehn_score": float(i % 7),
                }
            )
            if date >= dt.date(2021, 7, 1):
                om_rows.append(
                    {
                        "date_local": date,
                        "cp": cp,
                        "om_prev_d1_day_max_c": float(tmax) + 0.3,
                    }
                )
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    om_path = tmp_path / "open_meteo.parquet"
    pl.DataFrame(feature_rows).write_parquet(features_path)
    pl.DataFrame(label_rows).write_parquet(labels_path)
    pl.DataFrame(om_rows).write_parquet(om_path)
    return features_path, labels_path, om_path


def test_p2_distribution_cli_writes_artifacts(tmp_path):
    features_path, labels_path, om_path = _write_fixtures(tmp_path)
    output_dir = tmp_path / "out"

    result = CliRunner().invoke(
        app,
        [
            "p2-distribution-iteration",
            "--features-path", str(features_path),
            "--labels-path", str(labels_path),
            "--open-meteo-path", str(om_path),
            "--binary-assignments-path", str(tmp_path / "missing.csv"),
            "--output-dir", str(output_dir),
            "--gating-test-years", "2022",
            "--informational-test-years", "2022",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "p2_distribution_decision_v1.csv").exists()
    assert (output_dir / "p2_distribution_report_v1.md").exists()
    assert "EXPERIMENT_ONLY" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution_cli.py -q`
Expected: FAIL with `No such command 'p2-distribution-iteration'`

- [ ] **Step 3: Implement the CLI command**

Add to the imports at the top of `solarstorm/__main__.py` (with the other
solarstorm imports):

```python
from solarstorm.distribution import (
    build_p2_aggregates,
    build_p2_decision,
    build_p2_distribution_iteration,
    build_p2_gates,
    write_p2_distribution_artifacts,
)
from solarstorm.distribution._constants import (
    CANDIDATE_DRESSING,
    CANDIDATE_EMOS,
    SURFACE_GATING,
    SURFACE_INFORMATIONAL,
)
```

Add the command after `onda3-hybrid-model-iteration` (reuses
`build_hybrid_matrix`, `OM_FEATURE_COLUMNS`, `add_pooled_temporal_features`,
and `build_onda3_feature_manifest`, all already imported for P1):

```python
@app.command("p2-distribution-iteration")
def p2_distribution_iteration(
    features_path: str = typer.Option("./data/features.parquet"),
    labels_path: str = typer.Option("./data/labels.parquet"),
    open_meteo_path: str = typer.Option("./data/open_meteo_features_2022_2025.parquet"),
    binary_assignments_path: str = typer.Option(
        "./reports/regime-design/regime_binary_macro_assignments_v1.csv"
    ),
    output_dir: str = typer.Option("./reports/p2-distribution"),
    gating_test_years: str = typer.Option("2024,2025"),
    informational_test_years: str = typer.Option("2023,2024,2025"),
    include_local_surface: bool = typer.Option(
        True, "--include-local-surface/--no-local-surface"
    ),
):
    """P2: calibrated distribution over the P1 hybrid, judged by gates D1-D4."""
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
            assignments = assignments.with_columns(
                pl.col("date_local").str.to_date()
            )

    matrix = build_hybrid_matrix(
        features=features,
        labels=labels,
        assignments=assignments,
        open_meteo=open_meteo,
    )
    matrix = add_pooled_temporal_features(matrix)
    if "binary_macro_regime_label" in matrix.columns:
        matrix, interaction_columns = add_binary_macro_interaction_features(matrix)
    else:
        interaction_columns = []
    manifest = build_onda3_feature_manifest(features)
    manifest_features = [
        row["feature"]
        for row in manifest.filter(pl.col("included_in_onda3")).iter_rows(named=True)
        if row["feature"] in matrix.columns
        and matrix.schema[row["feature"]].is_numeric()
    ]
    local_numeric = list(
        dict.fromkeys(
            [
                *manifest_features,
                "k_cp",
                "cp_sin", "cp_cos", "month_sin", "month_cos", "doy_sin", "doy_cos",
                "cp_lead_rank",
                *interaction_columns,
            ]
        )
    )
    local_numeric = [
        column
        for column in local_numeric
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]
    om_numeric = list(
        dict.fromkeys(
            [
                *local_numeric,
                *[c for c in OM_FEATURE_COLUMNS if c in matrix.columns],
            ]
        )
    )
    categorical = [
        column
        for column in ["binary_macro_regime_label"]
        if column in matrix.columns
    ]
    covered = matrix.drop_nulls(list(OM_FEATURE_COLUMNS))

    gating_run = build_p2_distribution_iteration(
        covered,
        test_years=_parse_open_meteo_csv_ints(gating_test_years),
        numeric_feature_columns=om_numeric,
        categorical_feature_columns=categorical,
        surface=SURFACE_GATING,
    )
    scored = gating_run["scored"]
    results = gating_run["results"]
    if include_local_surface:
        local_run = build_p2_distribution_iteration(
            matrix,
            test_years=_parse_open_meteo_csv_ints(informational_test_years),
            numeric_feature_columns=local_numeric,
            categorical_feature_columns=categorical,
            surface=SURFACE_INFORMATIONAL,
        )
        scored = pl.concat([scored, local_run["scored"]], how="vertical")
        results = pl.concat([results, local_run["results"]], how="vertical")

    aggregates = build_p2_aggregates(scored)
    gating_filter = pl.col("surface") == SURFACE_GATING
    gate_frames = []
    summaries: dict[str, dict] = {}
    gating_scored = scored.filter(gating_filter)
    for candidate in (CANDIDATE_DRESSING, CANDIDATE_EMOS):
        gates, summary = build_p2_gates(
            by_cp=aggregates["by_cp"].filter(gating_filter),
            by_stratum_cp=aggregates["by_stratum_cp"].filter(gating_filter),
            coverage=aggregates["coverage"].filter(gating_filter),
            floor_audit=aggregates["floor_audit"].filter(gating_filter),
            candidate=candidate,
        )
        gate_frames.append(gates)
        summary["pooled_crps"] = float(
            gating_scored.filter(pl.col("distribution_name") == candidate)[
                "crps"
            ].mean()
        )
        summaries[candidate] = summary
    decision = build_p2_decision(summaries)

    artifacts = {
        "p2_distribution_results_v1": results,
        "p2_distribution_by_cp_v1": aggregates["by_cp"],
        "p2_distribution_by_stratum_cp_v1": aggregates["by_stratum_cp"],
        "p2_distribution_coverage_v1": aggregates["coverage"],
        "p2_distribution_quantile_predictions_v1": scored,
        "p2_distribution_floor_audit_v1": aggregates["floor_audit"],
        "p2_distribution_gates_v1": pl.concat(gate_frames, how="vertical"),
        "p2_distribution_decision_v1": decision,
    }
    paths = write_p2_distribution_artifacts(
        artifacts, output_dir=Path(output_dir), today=dt.date.today()
    )
    decision_row = decision.row(0, named=True)
    print(f"P2 distribution iteration complete: {decision_row['decision_status']}")
    print("production_status: EXPERIMENT_ONLY")
    print(f"Report: {paths['p2_distribution_report_md']}")
```

Note: the command also needs `build_hybrid_matrix` and `OM_FEATURE_COLUMNS`
from `solarstorm.onda3._hybrid_iteration`, plus
`add_pooled_temporal_features` (from `solarstorm.onda3._pooled_iteration`)
and `add_binary_macro_interaction_features` (from
`solarstorm.onda3._interactions`). `build_hybrid_matrix` is already imported
for the P1 command; add any of the others that are missing to the existing
import lists at the top of `__main__.py` rather than importing twice.

- [ ] **Step 4: Run tests to verify they pass**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution_cli.py tests/test_p2_distribution.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add solarstorm/__main__.py tests/test_p2_distribution_cli.py
git commit -m "feat(p2): p2-distribution-iteration CLI"
```

### Task 11: Verification and first real run

**Files:**
- No new source files; generated reports under `reports/p2-distribution/`.

- [ ] **Step 1: Run the focused suites + neighbors**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/test_p2_distribution.py tests/test_p2_distribution_cli.py tests/test_onda3_hybrid_iteration.py tests/test_honest_eval.py -q`
Expected: PASS

- [ ] **Step 2: Run Ruff and the full suite**

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run ruff check solarstorm/distribution solarstorm/__main__.py tests/test_p2_distribution.py tests/test_p2_distribution_cli.py`
Expected: no findings

Run: `UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -m pytest tests/ -q -m "not network"`
Expected: PASS (509 + new tests)

- [ ] **Step 3: Generate the first real artifact**

Run: `PYTHONIOENCODING=utf-8 UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run tmax p2-distribution-iteration`
Expected: completes; decision is one of the three pre-registered statuses.
Whatever the outcome, do NOT adjust gate thresholds, candidate definitions,
or coverage bounds; record the result.

- [ ] **Step 4: Confirm freeze strings and the distributional floor**

Run: `grep -c "EXPERIMENT_ONLY" reports/p2-distribution/p2_distribution_report_v1.md && grep -c "No production, EV, pricing" reports/p2-distribution/p2_distribution_report_v1.md`
Expected: both counts >= 1

Run (must print 0 and a value <= 1e-6):

```bash
PYTHONIOENCODING=utf-8 UV_CACHE_DIR='D:\Downloads\Wellington\.uv-cache' uv run python -c "
import polars as pl
scored = pl.read_csv('reports/p2-distribution/p2_distribution_quantile_predictions_v1.csv')
print(scored['n_floor_violations'].sum())
print((scored['bracket_probability_sum'] - 1.0).abs().max())
"
```

- [ ] **Step 5: Update CHANGELOG.md and ROADMAP.md with the generated decision, then commit**

```bash
git add reports/p2-distribution CHANGELOG.md ROADMAP.md
git commit -m "milestone(p2): first calibrated-distribution run judged by frozen gates D1-D4"
```

## Self-Review Checklist

- [ ] Spec coverage: 199-quantile canon, empirical CRPS, climatological null
  with per-fold window, dressing + EMOS candidates with inner 80/20
  calibration, coverage/bracket/floor audits, gates D1-D4 with frozen
  bounds, pre-registered decision matrix with same-row CRPS promotion,
  two surfaces with `surface` column, writer, CLI, first real run — all
  present.
- [ ] Placeholder scan: no TBD/TODO; every code step shows complete code.
- [ ] Type consistency: `canonical_levels(n_members=199)`,
  `empirical_member_quantiles(values, n_members)`,
  `crps_members(members, actual)`, `fit_null_distribution(train)`,
  `predict_null_members(rows, table)`, `fit_residual_dressing(calibration)`,
  `predict_dressing_members(rows, table)`,
  `fit_truncnorm_emos(calibration)`, `predict_emos_members(rows, params)`,
  `row_quantiles(members, levels_out)`,
  `interval_coverage_flags(members, actual, lower_level, upper_level)`,
  `bracket_probability_sums(members)`,
  `build_p2_gates(*, by_cp, by_stratum_cp, coverage, floor_audit, candidate)`,
  `build_p2_decision(candidate_summaries)`,
  `run_p2_fold(train, test, *, numeric_feature_columns, categorical_feature_columns)`,
  `build_p2_distribution_iteration(matrix, *, test_years, numeric_feature_columns, categorical_feature_columns, surface)`,
  `build_p2_aggregates(scored)`,
  `write_p2_distribution_artifacts(artifacts, *, output_dir, today)` are
  used with the same signatures across tasks; artifact keys match
  `P2_FILENAMES`.
