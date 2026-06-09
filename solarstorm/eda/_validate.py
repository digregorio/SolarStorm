"""Hypothesis validation harness: walk-forward bootstrap CI + FDR + gates.

Each hypothesis in SEED_HYPOTHESES is tested against each CP via a walk-forward
paired bootstrap test.  Baseline is L0 persistence (k_cp).  A hypothesis is
*validated* when the 95% CI of the MAE reduction excludes zero, FDR survives,
**and** all five gates (G1--G5) pass.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import polars as pl

from solarstorm.baselines._climatology import fit_climatology
from solarstorm.baselines._empirical import _dist_p50, fit_empirical_conditional
from solarstorm.eval._bootstrap import bootstrap_ci_diff
from solarstorm.eval._gates import GateResult, apply_all_gates
from solarstorm.eval._walkforward import expanding_walk_forward_splits
from solarstorm.features.builder import BLOCKED_FEATURES

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class HypothesisResult:
    """Per-(hypothesis, CP, regime) result from the validation harness."""

    id: str
    feature_column: str
    cp: str
    regime: str
    effect_size: float | None = None
    ci_lo: float | None = None
    ci_hi: float | None = None
    p_value: float | None = None
    fdr_adjusted: bool = False
    passes: bool | None = None
    gate_results: dict[str, GateResult] = field(default_factory=dict)
    n_days: int = 0
    status: str = "pending"
    blocked_reason: str | None = None
    best_null_name: str | None = None
    best_null_mae: float | None = None


@dataclass(frozen=True)
class _OLSChallenger:
    """Small OLS model for remaining_warming, supporting numeric and one-hot features."""

    intercept: float
    slope: float | None = None
    categories: tuple[str, ...] = ()
    category_coefficients: tuple[float, ...] = ()

    @property
    def is_numeric(self) -> bool:
        return self.slope is not None

    def predict_remaining_warming(self, value: object) -> float | None:
        if value is None:
            return None
        if self.is_numeric:
            try:
                x = float(value)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(x):
                return None
            return self.intercept + self.slope * x  # type: ignore[operator]

        if not self.categories:
            return None
        key = str(value)
        if key == self.categories[0]:
            return self.intercept
        try:
            idx = self.categories.index(key) - 1
        except ValueError:
            return self.intercept
        if idx < 0 or idx >= len(self.category_coefficients):
            return self.intercept
        return self.intercept + self.category_coefficients[idx]

    def __iter__(self):
        """Backward-compatible unpacking for older numeric-only callers."""
        yield self.intercept
        yield self.slope if self.slope is not None else 0.0


_NULL_PRIORITY = (
    "L0_persistence",
    "L1_dminus1",
    "L2_climatology_doy",
    "L4_empirical_conditional",
    "calibrated_cp_mean_rw",
)

_SKILL_EPSILON = 1e-9


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _kcp_col(cp_str: str) -> str:
    """Labels column name for the k_cp at *cp_str* (e.g. '20:00' -> 'k_cp__cp_2000')."""
    return f"k_cp__cp_{cp_str.replace(':', '')}"


def _fit_ols_challenger(
    train_features: pl.DataFrame,
    train_labels: pl.DataFrame,
    feature_column: str,
    cp_str: str,
) -> _OLSChallenger | None:
    """Fit OLS: remaining_warming ~ feature_value.

    Numeric features use a univariate slope.  Categorical/string/boolean
    features are encoded as one-hot indicators with the first sorted category
    as the reference level.
    """
    k_col = _kcp_col(cp_str)
    if k_col not in train_labels.columns or feature_column not in train_features.columns:
        return None

    joined = train_features.join(train_labels, on="date_local", how="inner")

    try:
        feat_series = joined[feature_column]
    except Exception:
        return None

    tmax = joined["tmax_int"].to_numpy().astype(float)
    kcp = joined[k_col].to_numpy().astype(float)
    rw = tmax - kcp

    feat_vals = feat_series.to_numpy()
    if np.issubdtype(feat_vals.dtype, np.number):
        mask = ~(np.isnan(feat_vals) | np.isnan(rw))
        x = feat_vals[mask].astype(float)
        y = rw[mask]

        if len(x) < 5:
            return None

        design = np.vstack([np.ones_like(x), x]).T
        try:
            intercept, slope = np.linalg.lstsq(design, y, rcond=None)[0]
        except Exception:
            return None

        return _OLSChallenger(intercept=float(intercept), slope=float(slope))

    joined_non_null = joined.filter(pl.col(feature_column).is_not_null())
    if joined_non_null.height < 5:
        return None

    categories = sorted(str(v) for v in joined_non_null[feature_column].unique().to_list() if v is not None)
    if len(categories) < 2:
        return None

    y = (
        joined_non_null["tmax_int"].to_numpy().astype(float)
        - joined_non_null[k_col].to_numpy().astype(float)
    )
    cat_values = [str(v) for v in joined_non_null[feature_column].to_list()]
    if len(cat_values) < 5:
        return None

    columns: list[np.ndarray] = [np.ones(len(cat_values))]
    for category in categories[1:]:
        columns.append(np.array([1.0 if value == category else 0.0 for value in cat_values]))
    design = np.vstack(columns).T

    try:
        coefs = np.linalg.lstsq(design, y, rcond=None)[0]
    except Exception:
        return None

    return _OLSChallenger(
        intercept=float(coefs[0]),
        categories=tuple(categories),
        category_coefficients=tuple(float(c) for c in coefs[1:]),
    )


def _default_test_starts(labels: pl.DataFrame) -> list[dt.date]:
    """Generate annual Jan-1 test starts from 2014 or 5 years after first data."""
    first_complete = labels.filter(pl.col("day_complete"))["date_local"].min()
    if first_complete is None:
        raise ValueError("No complete days in labels")
    first_test_year = max(first_complete.year + 5, 2014)
    # Cap at 2025 so we don't generate future splits with no data
    last_year = 2025
    if first_test_year > last_year:
        return []
    return [dt.date(y, 1, 1) for y in range(first_test_year, last_year + 1)]


def _bootstrap_p_value(
    a: np.ndarray,
    b: np.ndarray,
    n_bootstrap: int = 9999,
    seed: int = 42,
) -> float:
    """One-sided p-value for H0: mean(a) <= mean(b) vs H1: mean(a) > mean(b).

    Uses the same paired-index resampling strategy as ``bootstrap_ci_diff``.
    """
    rng = np.random.default_rng(seed)
    n = len(a)
    count_below = 0
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        boot_diff = np.mean(a[idx]) - np.mean(b[idx])
        if boot_diff <= 0:
            count_below += 1
    return float(count_below + 1) / (n_bootstrap + 1)


def _pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation coefficient, dropping NaN pairs."""
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]
    if len(x) <= 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _mode_share(predictions: np.ndarray) -> float:
    """Fraction of predictions equal to the most common rounded value."""
    if len(predictions) == 0:
        return 0.0
    from solarstorm.data._settlement import integer_settlement

    rounded = np.array([integer_settlement(float(p)) for p in predictions])
    _, counts = np.unique(rounded, return_counts=True)
    mode_count = counts.max()
    return float(mode_count) / len(predictions)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(np.isnan(value))  # type: ignore[arg-type]
    except TypeError:
        return False


def _add_null_prediction(
    nulls: dict[str, dict[str, float]],
    name: str,
    *,
    pred: float,
    truth: float,
) -> None:
    if not np.isfinite(pred):
        return
    nulls[name] = {
        "pred": float(pred),
        "error": float(abs(pred - truth)),
    }


def _fit_cp_mean_remaining_warming(train_labels: pl.DataFrame, cp_str: str) -> float | None:
    """Train-only intercept null: mean(Tmax - k_cp) for one CP."""
    k_col = _kcp_col(cp_str)
    if k_col not in train_labels.columns:
        return None

    vals: list[float] = []
    for row in train_labels.iter_rows(named=True):
        tmax = row.get("tmax_int")
        kcp = row.get(k_col)
        if _is_missing(tmax) or _is_missing(kcp):
            continue
        vals.append(float(tmax) - float(kcp))

    if len(vals) < 5:
        return None
    return float(np.mean(vals))


def _build_split_null_predictions(
    *,
    labels_ok: pl.DataFrame,
    train_labels: pl.DataFrame,
    test_labels: pl.DataFrame,
    cp_set: tuple[str, ...],
    split_train_start: dt.date,
    split_train_end: dt.date,
) -> dict[str, dict[dt.date, dict[str, dict[str, float]]]]:
    """Compute train-only null predictions for every test day and CP."""
    nulls_by_cp_date: dict[str, dict[dt.date, dict[str, dict[str, float]]]] = {
        cp_str: {} for cp_str in cp_set
    }

    tmax_by_date: dict[dt.date, int] = {
        row["date_local"]: int(row["tmax_int"])
        for row in labels_ok.iter_rows(named=True)
        if not _is_missing(row.get("tmax_int"))
    }

    try:
        climo = fit_climatology(
            labels_ok,
            train_start=split_train_start,
            train_end=split_train_end,
        )
    except ValueError:
        climo = None

    support_k = [
        int(v)
        for v in train_labels["tmax_int"].drop_nulls().unique().sort().to_list()
    ] if "tmax_int" in train_labels.columns else []
    try:
        empirical = fit_empirical_conditional(
            labels_ok,
            train_window=(split_train_start, split_train_end),
        ) if support_k else None
    except ValueError:
        empirical = None

    mean_rw_by_cp = {
        cp_str: _fit_cp_mean_remaining_warming(train_labels, cp_str)
        for cp_str in cp_set
    }

    for row in test_labels.iter_rows(named=True):
        d = row["date_local"]
        truth = row.get("tmax_int")
        if _is_missing(truth):
            continue
        truth_f = float(truth)

        for cp_str in cp_set:
            k_col = _kcp_col(cp_str)
            nulls: dict[str, dict[str, float]] = {}

            kcp = row.get(k_col)
            if not _is_missing(kcp):
                kcp_f = float(kcp)
                _add_null_prediction(
                    nulls, "L0_persistence", pred=kcp_f, truth=truth_f,
                )

                mean_rw = mean_rw_by_cp.get(cp_str)
                if mean_rw is not None:
                    _add_null_prediction(
                        nulls, "calibrated_cp_mean_rw",
                        pred=kcp_f + mean_rw,
                        truth=truth_f,
                    )

                if empirical is not None and support_k:
                    dist, _source = empirical.predict_dist(
                        month=d.month,
                        cp=cp_str,
                        k_cp=int(kcp_f),
                        support_k=support_k,
                    )
                    _add_null_prediction(
                        nulls, "L4_empirical_conditional",
                        pred=float(_dist_p50(dist)),
                        truth=truth_f,
                    )

            tmax_dminus1 = tmax_by_date.get(d - dt.timedelta(days=1))
            if tmax_dminus1 is not None:
                _add_null_prediction(
                    nulls, "L1_dminus1",
                    pred=float(tmax_dminus1),
                    truth=truth_f,
                )

            if climo is not None:
                _add_null_prediction(
                    nulls, "L2_climatology_doy",
                    pred=float(climo.tmax_dec_for(d)),
                    truth=truth_f,
                )

            if nulls:
                nulls_by_cp_date[cp_str][d] = nulls

    return nulls_by_cp_date


def _select_best_null(
    day_data: list[dict],
) -> tuple[str, np.ndarray, np.ndarray, float]:
    """Pick the lowest-MAE null on the same days used by a hypothesis result."""
    candidates: list[tuple[float, int, str, np.ndarray, np.ndarray]] = []
    for priority, name in enumerate(_NULL_PRIORITY):
        errors: list[float] = []
        preds: list[float] = []
        complete = True
        for day in day_data:
            null_result = day.get("nulls", {}).get(name)
            if null_result is None:
                complete = False
                break
            errors.append(float(null_result["error"]))
            preds.append(float(null_result["pred"]))
        if not complete or not errors:
            continue
        err_arr = np.array(errors)
        pred_arr = np.array(preds)
        candidates.append((float(np.mean(err_arr)), priority, name, err_arr, pred_arr))

    if not candidates:
        errors = np.array([d["baseline_error"] for d in day_data])
        preds = np.array([d["baseline_pred"] for d in day_data])
        return "L0_persistence", errors, preds, float(np.mean(errors))

    best_mae, _priority, best_name, best_errors, best_preds = min(
        candidates,
        key=lambda item: (item[0], item[1]),
    )
    return best_name, best_errors, best_preds, best_mae


# ---------------------------------------------------------------------------
# Benjamini-Hochberg FDR
# ---------------------------------------------------------------------------


def _benjamini_hochberg(
    results: list[HypothesisResult],
    alpha: float = 0.05,
) -> list[HypothesisResult]:
    """Apply Benjamini-Hochberg FDR correction in-place.

    Only results with a non-``None`` p_value are considered.
    """
    # Collect (original_index, result) for those with a p_value
    indexed: list[tuple[int, HypothesisResult]] = [
        (i, r) for i, r in enumerate(results) if r.p_value is not None
    ]
    # FDR denominator m = number of tests WITH a p-value, not the total result
    # count (blocked/all-null results without a p-value must not inflate m) (#12).
    m = len(indexed)
    if m == 0:
        return results

    indexed.sort(key=lambda x: x[1].p_value)  # type: ignore[return-value]

    # largest k such that p_k <= (k/m) * alpha
    max_k = -1
    for k, (_, r) in enumerate(indexed, start=1):
        if r.p_value <= (k / m) * alpha:  # type: ignore[operator]
            max_k = k
        else:
            break

    # Mark surviving hypotheses
    for k, (_, r) in enumerate(indexed, start=1):
        r.fdr_adjusted = k <= max_k

    return results


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def _compute_single_result(
    hyp_id: str,
    feature_column: str,
    cp_str: str,
    regime: str,
    day_data: list[dict],
    *,
    seed: int = 42,
) -> HypothesisResult:
    """Compute bootstrap CI, p-value, and gates for a single (hyp, CP, regime)."""
    n_days = len(day_data)

    if n_days < 30:
        return HypothesisResult(
            id=hyp_id, feature_column=feature_column, cp=cp_str,
            regime=regime, status="rejected", n_days=n_days,
        )

    best_null_name, baseline_errors, baseline_preds, baseline_mae = _select_best_null(day_data)
    challenger_errors = np.array([d["challenger_error"] for d in day_data])
    challenger_preds = np.array([d["challenger_pred"] for d in day_data])
    tmax_arr = np.array([d["tmax"] for d in day_data])

    # Bootstrap CI on mean(baseline) - mean(challenger)
    effect_size, ci_lo, ci_hi = bootstrap_ci_diff(
        baseline_errors, challenger_errors, seed=seed,
    )

    # One-sided p-value
    p_value = _bootstrap_p_value(baseline_errors, challenger_errors, seed=seed)

    # Passes rule (frozen): ci95[0] > 0.0
    passes = ci_lo > _SKILL_EPSILON

    # MAEs
    challenger_mae = float(np.mean(challenger_errors))

    # G4: corr_diff = r(model, truth) - r(baseline, truth)
    r_model = _pearson_r(challenger_preds, tmax_arr)
    r_baseline = _pearson_r(baseline_preds, tmax_arr)
    corr_diff = r_model - r_baseline

    # G3: p50 mode share
    p50_mode = _mode_share(challenger_preds)

    # Gates — pass skill_ci_lo (MAE improvement CI lower bound) for G4
    # morning-CP stratification (Murphy 1987: correlation blind to bias)
    gates = apply_all_gates(
        model_mae=challenger_mae,
        best_null_mae=baseline_mae,
        cp=cp_str,
        fallback_rate=0.0,
        p50_mode_share=p50_mode,
        corr_diff=corr_diff,
        skill_ci_lo=ci_lo,
        per_cp_passed=challenger_mae < baseline_mae - _SKILL_EPSILON,
    )

    return HypothesisResult(
        id=hyp_id,
        feature_column=feature_column,
        cp=cp_str,
        regime=regime,
        effect_size=effect_size,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        p_value=p_value,
        fdr_adjusted=False,
        passes=passes,
        gate_results=gates,
        n_days=n_days,
        status="pending",
        best_null_name=best_null_name,
        best_null_mae=baseline_mae,
    )


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def validate_hypotheses(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    hypotheses: list,
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    test_starts: list[dt.date] | None = None,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[list[HypothesisResult], dict]:
    """Run walk-forward bootstrap validation for each hypothesis x CP pair.

    Parameters
    ----------
    features:
        Output of :func:`~solarstorm.features.builder.build_features`.
    labels:
        Output of :func:`~solarstorm.data._labels.build_tmax_labels`.
    hypotheses:
        List of :class:`~solarstorm.eda._hypotheses.Hypothesis` instances.
    cp_set:
        Checkpoint hours to test.
    test_starts:
        Walk-forward test-start dates.  Defaults to annual Jan-1 from the
        first year with >= 5 years of prior data through 2025.
    alpha:
        FDR significance level.
    seed:
        Reproducibility seed for bootstrap resampling.

    Returns
    -------
    all_results:
        Every :class:`HypothesisResult` (one per hyp x CP x regime).
    validated_contract:
        Summary dict for downstream consumers.
    """
    # ------------------------------------------------------------------
    # 1. Prepare labels
    # ------------------------------------------------------------------
    labels_ok = labels.filter(pl.col("day_complete")).sort("date_local")
    if labels_ok.height == 0:
        raise ValueError("No complete days in labels")

    if test_starts is None:
        test_starts = _default_test_starts(labels_ok)

    # ------------------------------------------------------------------
    # 2. Generate walk-forward splits
    # ------------------------------------------------------------------
    history_start = labels_ok["date_local"].min()
    splits = expanding_walk_forward_splits(
        history_start=history_start,
        test_starts=test_starts,
        test_length_days=365,
        min_train_days=365,
    )

    if not splits:
        raise ValueError(
            f"No walk-forward splits could be generated "
            f"(history_start={history_start}, test_starts={test_starts})"
        )

    # ------------------------------------------------------------------
    # 3. BLOCKED features lookup
    # ------------------------------------------------------------------
    blocked = dict(BLOCKED_FEATURES)

    # ------------------------------------------------------------------
    # 4. Walk-forward accumulation
    #    per_day: {(hyp_id, cp_str) -> [day_record]}
    # ------------------------------------------------------------------
    per_day: dict[tuple[str, str], list[dict]] = {}

    for split in splits:
        train_labels = labels_ok.filter(
            pl.col("date_local").is_between(split.train_start, split.train_end)
        )
        test_labels = labels_ok.filter(
            pl.col("date_local").is_between(split.test_start, split.test_end)
        )

        if test_labels.height < 30:
            continue

        # -- 4a. Per-CP null baselines, all fit on this split's train window --
        null_predictions = _build_split_null_predictions(
            labels_ok=labels_ok,
            train_labels=train_labels,
            test_labels=test_labels,
            cp_set=cp_set,
            split_train_start=split.train_start,
            split_train_end=split.train_end,
        )

        # -- 4b. For each active (hyp, CP), fit challenger --
        for hyp in hypotheses:
            fc = hyp.feature_column
            if fc in blocked or fc not in features.columns:
                continue

            for cp_str in cp_set:
                key = (hyp.id, cp_str)

                # Train features for this CP with non-null feature
                train_feats = features.filter(
                    pl.col("date_local").is_between(split.train_start, split.train_end)
                    & (pl.col("cp") == cp_str)
                )

                train_non_null = train_feats.filter(pl.col(fc).is_not_null())
                if train_non_null.height < 30:
                    continue

                ols = _fit_ols_challenger(
                    train_non_null, train_labels, fc, cp_str,
                )
                if ols is None:
                    continue

                # Test features with non-null feature
                test_feats = features.filter(
                    pl.col("date_local").is_between(split.test_start, split.test_end)
                    & (pl.col("cp") == cp_str)
                    & pl.col(fc).is_not_null()
                )

                if test_feats.height == 0:
                    continue

                test_joined = test_feats.join(
                    test_labels, on="date_local", how="inner",
                )
                k_col = _kcp_col(cp_str)

                for row in test_joined.iter_rows(named=True):
                    d = row["date_local"]
                    feat_val = row.get(fc)
                    tmax = row["tmax_int"]
                    kcp = row.get(k_col)
                    regime = row.get("regime_label", "unknown")

                    if feat_val is None or tmax is None or kcp is None:
                        continue

                    kcp_int = int(kcp)
                    tmax_int = int(tmax)
                    pred_rw = ols.predict_remaining_warming(feat_val)
                    if pred_rw is None:
                        continue
                    pred_tmax = float(kcp_int) + pred_rw
                    challenger_error = float(abs(pred_tmax - tmax_int))

                    nulls = null_predictions.get(cp_str, {}).get(d, {})
                    l0 = nulls.get("L0_persistence")
                    if l0 is None:
                        l0 = {
                            "pred": float(kcp_int),
                            "error": float(abs(kcp_int - tmax_int)),
                        }

                    per_day.setdefault(key, []).append({
                        "date": d,
                        "regime": regime,
                        "baseline_pred": l0["pred"],
                        "baseline_error": l0["error"],
                        "nulls": nulls,
                        "challenger_pred": pred_tmax,
                        "challenger_error": challenger_error,
                        "tmax": tmax_int,
                    })

    # ------------------------------------------------------------------
    # 5. Compute results for each (hyp, CP, "all") and per-regime
    # ------------------------------------------------------------------
    all_results: list[HypothesisResult] = []

    for hyp in hypotheses:
        fc = hyp.feature_column

        # --- BLOCKED ---
        if fc in blocked:
            for cp_str in cp_set:
                all_results.append(HypothesisResult(
                    id=hyp.id, feature_column=fc, cp=cp_str,
                    regime="all", status="BLOCKED",
                    blocked_reason=blocked[fc], n_days=0,
                ))
            continue

        # --- Feature not in columns ---
        if fc not in features.columns:
            for cp_str in cp_set:
                all_results.append(HypothesisResult(
                    id=hyp.id, feature_column=fc, cp=cp_str,
                    regime="all", status="rejected", n_days=0,
                ))
            continue

        # --- All-null ---
        all_null = features[fc].is_null().all()

        for cp_str in cp_set:
            key = (hyp.id, cp_str)
            day_data = per_day.get(key, [])

            if all_null:
                all_results.append(HypothesisResult(
                    id=hyp.id, feature_column=fc, cp=cp_str,
                    regime="all", status="rejected", n_days=0,
                ))
                continue

            # "all" regime result
            result = _compute_single_result(
                hyp.id, fc, cp_str, "all", day_data, seed=seed,
            )
            all_results.append(result)

    # ------------------------------------------------------------------
    # 6. Per-regime segmentation for validated hypotheses
    # ------------------------------------------------------------------
    validated_ids_cps = {
        (r.id, r.cp) for r in all_results if r.status == "validated"
    }

    for hyp in hypotheses:
        fc = hyp.feature_column
        if fc in blocked or fc not in features.columns:
            continue

        for cp_str in cp_set:
            if (hyp.id, cp_str) not in validated_ids_cps:
                continue

            key = (hyp.id, cp_str)
            day_data = per_day.get(key, [])

            # Collect distinct regimes (excluding "all")
            regimes = sorted({
                d["regime"] for d in day_data
                if d["regime"] not in ("all", "unknown", "")
            })

            for regime in regimes:
                regime_data = [d for d in day_data if d["regime"] == regime]
                if len(regime_data) < 30:
                    continue

                regime_result = _compute_single_result(
                    hyp.id, fc, cp_str, regime, regime_data, seed=seed,
                )
                all_results.append(regime_result)

    # ------------------------------------------------------------------
    # 7. FDR correction
    # ------------------------------------------------------------------
    _benjamini_hochberg(all_results, alpha=alpha)

    # ------------------------------------------------------------------
    # 8. Final status
    # ------------------------------------------------------------------
    for r in all_results:
        if r.status in ("BLOCKED",):
            continue
        if r.n_days < 30:
            r.status = "rejected"
            continue
        if (
            r.passes
            and r.fdr_adjusted
            and r.gate_results
            and all(g.passed for g in r.gate_results.values())
        ):
            r.status = "validated"
        else:
            r.status = "rejected"

    # ------------------------------------------------------------------
    # 9. Build validated contract dict
    # ------------------------------------------------------------------
    validated = [r for r in all_results if r.status == "validated"]
    blocked_list = [r for r in all_results if r.status == "BLOCKED"]
    rejected_list = [r for r in all_results if r.status == "rejected"]

    contract: dict = {
        "validated_features": [
            {
                "id": r.id,
                "feature_column": r.feature_column,
                "cp": r.cp,
                "regime": r.regime,
                "effect_size": r.effect_size,
                "ci_lo": r.ci_lo,
                "ci_hi": r.ci_hi,
                "p_value": r.p_value,
                "best_null_name": r.best_null_name,
                "best_null_mae": r.best_null_mae,
            }
            for r in validated
        ],
        "blocked": [
            {"id": r.id, "feature_column": r.feature_column, "reason": r.blocked_reason}
            for r in blocked_list
        ],
        "generated": dt.datetime.now(dt.UTC).isoformat(),
        "alpha": alpha,
        "n_hypotheses_tested": max(0, len(all_results) - len(blocked_list)),
        "n_validated": len(validated),
        "n_rejected": len(rejected_list),
    }

    return (all_results, contract)
