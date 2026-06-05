"""Empirical conditional prob_dist baseline (design section 8 - baselines contract).

Replaces any "ingenious gaussian" baseline. Trained train-only.

P(k_eod = k | month, cp, k_cp) -- empirical with Laplace smoothing alpha=1.
Fallback to marginal P(k_eod = k | month, cp) when bucket has n < n_min_bucket.
Truncated to ``support_K`` (design 4.5.1) at predict time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

import polars as pl


@dataclass(frozen=True)
class EmpiricalConditional:
    """Frozen empirical conditional distribution for prob_dist."""

    # P(k_eod=k | month, cp, k_cp) as nested dicts.
    cond: dict[tuple[int, str, int], dict[int, int]] = field(default_factory=dict)
    # P(k_eod=k | month, cp) marginal (fallback).
    marginal: dict[tuple[int, str], dict[int, int]] = field(default_factory=dict)
    n_min_bucket: int = 30
    laplace_alpha: float = 1.0
    # train_window=None means "not yet fitted" - reviewers should not see Unix epoch
    # in a freshly constructed dataclass (review #12).
    train_window: tuple[date, date] | None = None

    def predict_dist(
        self,
        *,
        month: int,
        cp: str,
        k_cp: int,
        support_k: Iterable[int],
    ) -> tuple[dict[int, float], str]:
        """Return ``(prob_dist, source)`` where source in ``{'conditional','fallback_marginal','uniform'}``.

        Truncates and normalises to ``support_k``.
        """
        sup = list(support_k)
        if not sup:
            raise ValueError("support_k is empty")
        bucket = self.cond.get((month, cp, k_cp))
        used = "conditional"
        if bucket is None or sum(bucket.values()) < self.n_min_bucket:
            bucket = self.marginal.get((month, cp))
            used = "fallback_marginal"
        if bucket is None or sum(bucket.values()) == 0:
            # Last resort: uniform
            p = {k: 1.0 / len(sup) for k in sup}
            return p, "uniform"
        # Laplace smoothing only over support
        a = self.laplace_alpha
        counts = {k: bucket.get(k, 0) for k in sup}
        denom = sum(counts.values()) + a * len(sup)
        p = {k: (counts[k] + a) / denom for k in sup}
        # Re-normalise (defensive)
        s = sum(p.values())
        return {k: v / s for k, v in p.items()}, used


def fit_empirical_conditional(
    train_panel: pl.DataFrame,
    *,
    cp_col_template: str = "k_cp__cp_",
    laplace_alpha: float = 1.0,
    n_min_bucket: int = 30,
    train_window: tuple[date, date] | None = None,
) -> EmpiricalConditional:
    """Fit on a train panel of ``(date_local, month, k_eod, k_cp__cp_HH)`` columns.

    The function discovers all columns matching ``cp_col_template`` to build per-CP buckets.
    """
    needed = {"date_local", "month", "tmax_int"}
    if not needed.issubset(set(train_panel.columns)):
        missing = needed - set(train_panel.columns)
        raise ValueError(f"Missing columns: {missing}")
    cp_cols = [c for c in train_panel.columns if c.startswith(cp_col_template)]
    if not cp_cols:
        raise ValueError(f"No columns starting with '{cp_col_template}' (per-CP k_cp).")

    cond: dict[tuple[int, str, int], dict[int, int]] = {}
    marginal: dict[tuple[int, str], dict[int, int]] = {}

    df = train_panel.filter(pl.col("tmax_int").is_not_null())
    if "day_complete" in df.columns:
        df = df.filter(pl.col("day_complete"))
    for cp_col in cp_cols:
        cp = cp_col.replace(cp_col_template, "") + ":00"
        sub = df.filter(pl.col(cp_col).is_not_null()).select(
            ["month", cp_col, "tmax_int"]
        )
        for row in sub.iter_rows(named=True):
            m = int(row["month"])
            kcp = int(row[cp_col])
            keod = int(row["tmax_int"])
            cond.setdefault((m, cp, kcp), {}).setdefault(keod, 0)
            cond[(m, cp, kcp)][keod] += 1
            marginal.setdefault((m, cp), {}).setdefault(keod, 0)
            marginal[(m, cp)][keod] += 1
    return EmpiricalConditional(
        cond=cond,
        marginal=marginal,
        n_min_bucket=n_min_bucket,
        laplace_alpha=laplace_alpha,
        train_window=_validate_train_window(train_window),
    )


def _validate_train_window(tw: tuple[date, date] | None) -> tuple[date, date]:
    if tw is None:
        raise ValueError(
            "fit_empirical_conditional requires an explicit train_window=(start, end). "
            "Defaults like Unix epoch are misleading (review #12)."
        )
    start, end = tw
    if not isinstance(start, date) or not isinstance(end, date):
        raise TypeError(f"train_window must be (date, date); got {tw!r}")
    if start >= end:
        raise ValueError(f"train_window start must be < end; got {tw!r}")
    return (start, end)


__all__ = ["EmpiricalConditional", "fit_empirical_conditional"]
