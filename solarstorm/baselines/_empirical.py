"""L4: Empirical conditional baseline — P(k_eod | month, CP, k_cp).

REBAIXADO: This is a baseline ONLY. It must never serve as production forecast.
The old project's collapse (92.9% fallback, p50 collapse) is the cautionary tale.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import polars as pl


def cp_key(cp: str) -> str:
    """Normalize CP string to canonical form (no colons).

    ``"23:00"`` and ``"2300"`` both map to ``"2300"``.
    This bridges the L4 mismatch between column-name keys (``k_cp__cp_2300``)
    and user-facing CP strings (``"23:00"``).
    """
    return cp.replace(":", "")


def _dist_p50(dist: dict[int, float]) -> int:
    """Median (p50) of a discrete probability distribution via CDF.

    Returns the smallest value whose cumulative probability >= 0.5.
    Falls back to the mode if no value reaches 0.5 (degenerate case).
    """
    cum = 0.0
    for k in sorted(dist):
        cum += dist[k]
        if cum >= 0.5:
            return k
    return max(dist, key=dist.get)  # fallback


@dataclass
class EmpiricalConditional:
    cond: dict[tuple[int, str, int], dict[int, int]] = field(default_factory=dict)
    marginal: dict[tuple[int, str], dict[int, int]] = field(default_factory=dict)
    n_min_bucket: int = 30
    laplace_alpha: float = 1.0
    train_window: tuple[dt.date, dt.date] | None = None
    _fallback_rate: float = 0.0

    @property
    def fallback_rate(self) -> float:
        return self._fallback_rate

    def predict_dist(
        self, *, month: int, cp: str, k_cp: int, support_k: list[int]
    ) -> tuple[dict[int, float], str]:
        cp = cp_key(cp)  # normalize "23:00" → "2300" (Fix #4)
        counts = self.cond.get((month, cp, k_cp))
        if counts is not None and sum(counts.values()) >= self.n_min_bucket:
            source = "conditional"
            total = sum(counts.values()) + self.laplace_alpha * len(support_k)
            dist = {k: (counts.get(k, 0) + self.laplace_alpha) / total for k in support_k}
        else:
            source = "fallback_marginal"
            marginal_counts = self.marginal.get((month, cp), {})
            if marginal_counts:
                total = sum(marginal_counts.values()) + self.laplace_alpha * len(support_k)
                dist = {k: (marginal_counts.get(k, 0) + self.laplace_alpha) / total for k in support_k}
            else:
                source = "uniform"
                dist = {k: 1.0 / len(support_k) for k in support_k}

        # Re-normalise defensively
        total = sum(dist.values())
        return {k: v / total for k, v in dist.items()}, source


def fit_empirical_conditional(
    labels: pl.DataFrame,
    *,
    train_window: tuple[dt.date, dt.date] | None = None,
    n_min_bucket: int = 30,
    laplace_alpha: float = 1.0,
) -> EmpiricalConditional:
    if train_window is None:
        raise ValueError("train_window is required — no silent epoch default")

    train = labels.filter(
        pl.col("date_local").is_between(train_window[0], train_window[1])
        & pl.col("day_complete")
    )
    train = train.with_columns(pl.col("date_local").dt.month().alias("month"))

    kcp_cols = [c for c in train.columns if c.startswith("k_cp__cp_")]
    cond: dict[tuple[int, str, int], dict[int, int]] = {}
    marginal: dict[tuple[int, str], dict[int, int]] = {}

    for row in train.iter_rows(named=True):
        m = row["month"]
        keod = row["tmax_int"]
        for col in kcp_cols:
            cp = cp_key(col.replace("k_cp__cp_", ""))
            kcp = row[col]
            if kcp is None:
                continue
            cond.setdefault((m, cp, kcp), {}).setdefault(keod, 0)
            cond[(m, cp, kcp)][keod] += 1
            marginal.setdefault((m, cp), {}).setdefault(keod, 0)
            marginal[(m, cp)][keod] += 1

    return EmpiricalConditional(
        cond=cond, marginal=marginal,
        n_min_bucket=n_min_bucket, laplace_alpha=laplace_alpha,
        train_window=train_window,
    )
