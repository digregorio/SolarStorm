"""Regime sensitivity checks for Onda 4."""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import polars as pl

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.eda._regimes import PHYSICAL_REGIMES
from solarstorm.eda._validate import HypothesisResult, validate_hypotheses

REGIMES: tuple[str, ...] = PHYSICAL_REGIMES


def _empty_regime_table() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "regime": pl.Utf8,
            "hypothesis_id": pl.Utf8,
            "feature_column": pl.Utf8,
            "cp": pl.Utf8,
            "passes": pl.Boolean,
            "n_days": pl.Int64,
            "status": pl.Utf8,
        }
    )


def _rows_from_results(results: Sequence[HypothesisResult]) -> list[dict]:
    rows: list[dict] = []
    for result in results:
        if result.regime in ("all", "unknown", ""):
            continue
        gates_pass = bool(result.gate_results) and all(g.passed for g in result.gate_results.values())
        rows.append(
            {
                "regime": result.regime,
                "hypothesis_id": result.id,
                "feature_column": result.feature_column,
                "cp": result.cp,
                "passes": result.status == "validated" and gates_pass,
                "n_days": result.n_days,
                "status": result.status,
            }
        )
    return rows


def _rows_from_regime_run(regime: str, results: Sequence[HypothesisResult]) -> list[dict]:
    rows: list[dict] = []
    for result in results:
        if result.regime != "all":
            continue
        gates_pass = bool(result.gate_results) and all(g.passed for g in result.gate_results.values())
        rows.append(
            {
                "regime": regime,
                "hypothesis_id": result.id,
                "feature_column": result.feature_column,
                "cp": result.cp,
                "passes": result.status == "validated" and gates_pass,
                "n_days": result.n_days,
                "status": result.status,
            }
        )
    return rows


def regime_sensitivity(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    hypotheses_or_results: Sequence[Hypothesis | HypothesisResult],
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    test_starts: list[dt.date] | None = None,
    seed: int = 42,
) -> pl.DataFrame:
    """Cross-tabulate validation status by physical regime."""
    if not hypotheses_or_results:
        return _empty_regime_table()

    first = hypotheses_or_results[0]
    if isinstance(first, HypothesisResult):
        rows = _rows_from_results(hypotheses_or_results)  # type: ignore[arg-type]
    else:
        rows = []
        if "regime_label" not in features.columns:
            return _empty_regime_table()
        regimes = sorted(
            str(regime)
            for regime in features["regime_label"].drop_nulls().unique().to_list()
            if str(regime) not in ("all", "unknown", "")
        )
        for regime in regimes:
            regime_features = features.filter(pl.col("regime_label") == regime)
            try:
                results, _contract = validate_hypotheses(
                    regime_features,
                    labels,
                    list(hypotheses_or_results),
                    cp_set=cp_set,
                    test_starts=test_starts,
                    seed=seed,
                )
            except ValueError:
                continue
            rows.extend(_rows_from_regime_run(regime, results))

    return pl.DataFrame(rows) if rows else _empty_regime_table()


def detect_dead_regimes(
    regime_cross_tab: pl.DataFrame,
    *,
    regimes: Sequence[str] = REGIMES,
) -> list[str]:
    """Return regimes with no passing feature rows."""
    dead: list[str] = []
    for regime in sorted(regimes):
        if regime_cross_tab.height == 0 or "regime" not in regime_cross_tab.columns:
            dead.append(regime)
            continue
        subset = regime_cross_tab.filter(pl.col("regime") == regime)
        has_pass = subset.height > 0 and bool(subset["passes"].fill_null(False).any())
        if not has_pass:
            dead.append(regime)
    return dead
