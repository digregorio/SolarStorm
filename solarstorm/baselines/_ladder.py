"""Baseline ladder: orchestrates degraus, computes best-null-por-CP."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class LadderResult:
    level: str
    name: str
    cp: str
    mae: float = 0.0
    rmse: float = 0.0
    bias: float = 0.0
    bracket_match: float = 0.0
    rps: float = 0.0
    crps: float = 0.0
    fallback_rate: float | None = None
    p50_mode_share: float = 0.0
    corr_diff: float | None = None
    n: int = 0


def evaluate_step(
    *,
    level: str,
    name: str,
    cp: str,
    pred: dict,
    truth: int,
    fallback_rate: float = 0.0,
) -> LadderResult:
    p50 = pred["p50"]
    error = p50 - truth
    from solarstorm.data._settlement import integer_settlement
    return LadderResult(
        level=level, name=name, cp=cp,
        mae=abs(error),
        rmse=error**2,
        bias=error,
        bracket_match=1.0 if integer_settlement(p50) == integer_settlement(truth) else 0.0,
        fallback_rate=fallback_rate,
    )


def best_null_for_cp(results: dict[str, list[LadderResult]], cp: str) -> LadderResult | None:
    """Return the baseline with lowest MAE for a given CP."""
    candidates = results.get(cp, [])
    if not candidates:
        return None
    return min(candidates, key=lambda r: r.mae)


def aggregate_results(results: list[LadderResult]) -> list[LadderResult]:
    """Aggregate per-row LadderResults by (level, name, cp).

    Each per-row result stores ``mae = abs(error)``, ``rmse = error**2``,
    ``bias = error``, ``bracket_match ∈ {0, 1}``.  This function pools all rows
    in a group and computes proper aggregate metrics:

    * mae  = mean(abs(error))
    * rmse = sqrt(mean(error**2))
    * bias = mean(error)
    * bracket_match = mean(match)
    * fallback_rate = mean(fallback_rate) across rows that have it
    * n = number of rows in the group
    """
    groups: dict[tuple[str, str, str], list[LadderResult]] = defaultdict(list)
    for r in results:
        groups[(r.level, r.name, r.cp)].append(r)

    aggregated: list[LadderResult] = []
    for (level, name, cp), group in sorted(groups.items()):
        n = len(group)
        errors = [r.mae for r in group]
        sq_errors = [r.rmse for r in group]
        biases = [r.bias for r in group]
        bms = [r.bracket_match for r in group]
        rps_vals = [r.rps for r in group if r.rps]
        fbrs = [r.fallback_rate for r in group if r.fallback_rate is not None]
        p50_shares = [r.p50_mode_share for r in group]
        corr_diffs = [r.corr_diff for r in group if r.corr_diff is not None]

        aggregated.append(LadderResult(
            level=level, name=name, cp=cp,
            mae=sum(errors) / n,
            rmse=(sum(sq_errors) / n) ** 0.5,
            bias=sum(biases) / n,
            bracket_match=sum(bms) / n,
            rps=sum(rps_vals) / len(rps_vals) if rps_vals else 0.0,
            fallback_rate=sum(fbrs) / len(fbrs) if fbrs else None,
            p50_mode_share=sum(p50_shares) / n,
            corr_diff=corr_diffs[0] if corr_diffs else None,
            n=n,
        ))

    return aggregated
