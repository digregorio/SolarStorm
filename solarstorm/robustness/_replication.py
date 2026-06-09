"""Per-year replication for validated feature hypotheses."""
from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Sequence

import polars as pl

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.eda._validate import HypothesisResult, validate_hypotheses


def _empty_year_matrix() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "year": pl.Int64,
            "hypothesis_id": pl.Utf8,
            "feature_column": pl.Utf8,
            "cp": pl.Utf8,
            "regime": pl.Utf8,
            "effect_size": pl.Float64,
            "ci_lo": pl.Float64,
            "ci_hi": pl.Float64,
            "p_value": pl.Float64,
            "passes_g1_g5": pl.Boolean,
            "best_null_name": pl.Utf8,
            "best_null_mae": pl.Float64,
            "challenger_mae": pl.Float64,
            "n_days": pl.Int64,
            "status": pl.Utf8,
        }
    )


def _cp_sort_key(cp: str) -> tuple[int, int]:
    hour, minute = cp.split(":")
    return int(hour), int(minute)


def hypotheses_from_contract(contract: dict) -> tuple[list[Hypothesis], tuple[str, ...]]:
    """Build unique hypotheses and CP set from a validated feature contract.

    Regime-specific rows are intentionally ignored here; Onda 4 replication
    first asks whether the pooled validated feature still holds by year.
    """
    hypotheses: list[Hypothesis] = []
    seen_features: set[str] = set()
    cps: set[str] = set()

    for row in contract.get("validated_features", []):
        if row.get("regime", "all") != "all":
            continue
        feature_column = row.get("feature_column")
        cp = row.get("cp")
        if not feature_column or not cp:
            continue
        cps.add(str(cp))
        if feature_column in seen_features:
            continue
        seen_features.add(str(feature_column))
        hypotheses.append(
            Hypothesis(
                id=str(row.get("id") or feature_column),
                feature_column=str(feature_column),
                description=f"Onda 4 replication for {feature_column}",
                source="validated_feature_contract",
            )
        )

    return hypotheses, tuple(sorted(cps, key=_cp_sort_key))


def _result_to_row(year: int, result: HypothesisResult) -> dict:
    challenger_mae = None
    if result.best_null_mae is not None and result.effect_size is not None:
        challenger_mae = result.best_null_mae - result.effect_size

    gates_pass = bool(result.gate_results) and all(g.passed for g in result.gate_results.values())
    passes_g1_g5 = result.status == "validated" and bool(result.fdr_adjusted) and gates_pass

    return {
        "year": year,
        "hypothesis_id": result.id,
        "feature_column": result.feature_column,
        "cp": result.cp,
        "regime": result.regime,
        "effect_size": result.effect_size,
        "ci_lo": result.ci_lo,
        "ci_hi": result.ci_hi,
        "p_value": result.p_value,
        "passes_g1_g5": passes_g1_g5,
        "best_null_name": result.best_null_name,
        "best_null_mae": result.best_null_mae,
        "challenger_mae": challenger_mae,
        "n_days": result.n_days,
        "status": result.status,
    }


def per_year_replication(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    hypotheses: Sequence[Hypothesis],
    *,
    test_years: Iterable[int] | None = None,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    seed: int = 42,
) -> tuple[pl.DataFrame, dict]:
    """Run the validation harness independently for each test year."""
    labels_ok = labels.filter(pl.col("day_complete"))
    if labels_ok.height == 0 or not hypotheses:
        return _empty_year_matrix(), {
            "n_years_tested": 0,
            "years_with_passing_feature": [],
            "errors": {},
        }

    if test_years is None:
        min_year = max(labels_ok["date_local"].min().year + 5, 2014)
        max_year = min(labels_ok["date_local"].max().year, 2025)
        test_years = range(min_year, max_year + 1)

    rows: list[dict] = []
    errors: dict[int, str] = {}

    for year in test_years:
        test_start = dt.date(int(year), 1, 1)
        try:
            results, _contract = validate_hypotheses(
                features,
                labels,
                list(hypotheses),
                cp_set=cp_set,
                test_starts=[test_start],
                seed=seed,
            )
        except ValueError as exc:
            errors[int(year)] = str(exc)
            continue

        for result in results:
            if result.regime != "all":
                continue
            rows.append(_result_to_row(int(year), result))

    matrix = pl.DataFrame(rows) if rows else _empty_year_matrix()
    years_with_passing = (
        sorted(matrix.filter(pl.col("passes_g1_g5"))["year"].unique().to_list())
        if matrix.height
        else []
    )
    years_tested = sorted(matrix["year"].unique().to_list()) if matrix.height else []

    return matrix, {
        "n_years_tested": len(years_tested),
        "years_tested": years_tested,
        "years_with_passing_feature": years_with_passing,
        "errors": errors,
    }
