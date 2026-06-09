"""Synthetic tests for the hypothesis validation harness.

FROZEN SEEDS AND THRESHOLDS — do not change after first real run.

Test catalog
------------
test_known_signal_passes
    Feature = remaining_warming + N(0, 0.1).  MUST be ``validated``.

test_noise_fails
    Feature = N(0, 1) — pure noise.  MUST be ``rejected``.

test_fdr_correction
    20 noise features + 1 signal.  After BH correction the signal must
    survive and all noise must be rejected.

test_blocked_handled
    ``sst_maritime_cap`` is in ``BLOCKED_FEATURES`` — must get status
    ``BLOCKED`` without attempting to fit.

test_empty_feature_handled
    An all-null feature column must be gracefully rejected (no crash).

Anti-gaming commitment: seeds/thresholds frozen before any real data seen.
    seed = 42
    pass rule: ci95[0] > 0.0  (see run_hypothesis_test)
    BH alpha = 0.05
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.eda._validate import validate_hypotheses

# ---------------------------------------------------------------------------
# Synthetic data factory
# ---------------------------------------------------------------------------

def _make_dataset(
    *,
    n_years: int = 7,
    rw_std: float = 3.0,
    start_year: int = 2018,
    seed: int = 42,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    extra_features: dict[str, list | None] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Generate synthetic daily labels + per-(date, cp) features.

    ``remaining_warming`` (tmax - k_cp) has **exact zero mean** per CP
    so that a model using only an intercept cannot beat L0 persistence.
    """
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    # tmax with seasonal cycle
    doy_arr = np.arange(n_days)
    tmax_cont = 20.0 + 8.0 * np.sin(2.0 * np.pi * doy_arr / 365.0)
    tmax_int = np.round(tmax_cont + rng.normal(0, 0.3, n_days)).astype(int)

    # remaining warming — exact zero mean (per-CP if needed)
    rw_cont = rng.normal(0, rw_std, n_days)
    rw_cont -= rw_cont.mean()          # force zero mean
    rw_int = np.round(rw_cont).astype(int)

    # ---- Labels ----
    labels_rows: list[dict] = []
    for i, d in enumerate(dates):
        row: dict = {
            "date_local": d,
            "tmax_int": int(tmax_int[i]),
            "day_complete": True,
        }
        for cp_str in cp_set:
            kcol = f"k_cp__cp_{cp_str.replace(':', '')}"
            row[kcol] = int(tmax_int[i] - rw_int[i])
        labels_rows.append(row)
    labels = pl.DataFrame(labels_rows)

    # ---- Features ----
    signal_vals = rw_int.astype(float) + rng.normal(0, 0.1, n_days)
    noise_vals = rng.normal(0, 1.0, n_days)
    fdr_noise = [rng.normal(0, 1.0, n_days) for _ in range(20)]

    features_rows: list[dict] = []
    for i, d in enumerate(dates):
        for cp_str in cp_set:
            row: dict = {
                "date_local": d,
                "cp": cp_str,
                "regime_label": "all",
                "regime_flags": "{}",
                "signal_feature": float(signal_vals[i]),
                "noise_feature": float(noise_vals[i]),
            }
            for j in range(20):
                row[f"noise_{j}"] = float(fdr_noise[j][i])
            row["empty_feature"] = None
            if extra_features:
                for k, v in extra_features.items():
                    row[k] = v[i] if isinstance(v, np.ndarray) else v
            features_rows.append(row)

    features = pl.DataFrame(features_rows)
    return features, labels


def _make_biased_remaining_warming_dataset(
    *,
    n_years: int = 7,
    start_year: int = 2018,
    seed: int = 42,
    cp_set: tuple[str, ...] = ("20:00",),
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Dataset where an intercept-only challenger beats L0 but not calibrated null."""
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    tmax_int = np.round(18.0 + rng.normal(0.0, 5.0, n_days)).astype(int)
    rw = 3 + rng.choice([-1, 0, 1], size=n_days)

    labels_rows: list[dict] = []
    features_rows: list[dict] = []
    for i, d in enumerate(dates):
        label_row: dict = {
            "date_local": d,
            "tmax_int": int(tmax_int[i]),
            "day_complete": True,
        }
        for cp_str in cp_set:
            label_row[f"k_cp__cp_{cp_str.replace(':', '')}"] = int(tmax_int[i] - rw[i])
            features_rows.append({
                "date_local": d,
                "cp": cp_str,
                "regime_label": "all",
                "regime_flags": "{}",
                "constant_feature": 0.0,
            })
        labels_rows.append(label_row)

    return pl.DataFrame(features_rows), pl.DataFrame(labels_rows)


def _make_climatology_dominates_dataset(
    *,
    n_years: int = 7,
    start_year: int = 2018,
    seed: int = 42,
    cp_set: tuple[str, ...] = ("20:00",),
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Dataset where a weak feature beats L0 but loses to train-only L2 climatology."""
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    doy_arr = np.arange(n_days)
    tmax_cont = 20.0 + 8.0 * np.sin(2.0 * np.pi * doy_arr / 365.0)
    tmax_int = np.round(tmax_cont).astype(int)
    rw = rng.normal(0.0, 3.0, n_days)
    rw -= rw.mean()
    rw_int = np.round(rw).astype(int)
    weak_signal = rw_int.astype(float) + rng.normal(0.0, 6.0, n_days)

    labels_rows: list[dict] = []
    features_rows: list[dict] = []
    for i, d in enumerate(dates):
        label_row: dict = {
            "date_local": d,
            "tmax_int": int(tmax_int[i]),
            "day_complete": True,
        }
        for cp_str in cp_set:
            label_row[f"k_cp__cp_{cp_str.replace(':', '')}"] = int(tmax_int[i] - rw_int[i])
            features_rows.append({
                "date_local": d,
                "cp": cp_str,
                "regime_label": "all",
                "regime_flags": "{}",
                "weak_signal": float(weak_signal[i]),
            })
        labels_rows.append(label_row)

    return pl.DataFrame(features_rows), pl.DataFrame(labels_rows)


def _make_categorical_signal_dataset(
    *,
    n_years: int = 7,
    start_year: int = 2018,
    seed: int = 42,
    cp_set: tuple[str, ...] = ("20:00",),
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Dataset where a string category cleanly predicts remaining_warming."""
    rng = np.random.default_rng(seed)
    n_days = n_years * 365
    start = dt.date(start_year, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(n_days)]

    tmax_int = np.round(18.0 + rng.normal(0.0, 4.0, n_days)).astype(int)
    categories = np.where(np.arange(n_days) % 2 == 0, "cooling", "warming")
    rw = np.where(categories == "warming", 4, -4)

    labels_rows: list[dict] = []
    features_rows: list[dict] = []
    for i, d in enumerate(dates):
        label_row: dict = {
            "date_local": d,
            "tmax_int": int(tmax_int[i]),
            "day_complete": True,
        }
        for cp_str in cp_set:
            label_row[f"k_cp__cp_{cp_str.replace(':', '')}"] = int(tmax_int[i] - rw[i])
            features_rows.append({
                "date_local": d,
                "cp": cp_str,
                "regime_label": "all",
                "regime_flags": "{}",
                "category_signal": str(categories[i]),
            })
        labels_rows.append(label_row)

    return pl.DataFrame(features_rows), pl.DataFrame(labels_rows)


# ===================================================================
# Tests
# ===================================================================

class TestKnownSignalPasses:
    """A feature that IS remaining_warming + small noise must validate."""

    def test_single_cp(self):
        features, labels = _make_dataset()
        hyp = Hypothesis(
            id="H_SIGNAL",
            feature_column="signal_feature",
            description="Known signal — =remaining_warming + N(0,0.1)",
        )
        results, contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )
        sig = [r for r in results if r.id == "H_SIGNAL"]
        for r in sig:
            msg = (
                f"CP={r.cp} regime={r.regime}: status={r.status}, "
                f"effect={r.effect_size:.4f}, ci=[{r.ci_lo:.4f}, {r.ci_hi:.4f}], "
                f"p={r.p_value:.6f}, n={r.n_days}"
            )
            assert r.status == "validated", msg
        assert contract["n_validated"] >= 1


class TestNoiseFails:
    """A pure-noise feature must be rejected."""

    def test_single_cp(self):
        features, labels = _make_dataset()
        hyp = Hypothesis(
            id="H_NOISE",
            feature_column="noise_feature",
            description="Pure noise — must fail",
        )
        results, contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )
        noisy = [r for r in results if r.id == "H_NOISE"]
        for r in noisy:
            msg = (
                f"CP={r.cp} regime={r.regime}: status={r.status}, "
                f"effect={r.effect_size:.4f}, ci=[{r.ci_lo:.4f}, {r.ci_hi:.4f}], "
                f"p={r.p_value:.6f}, n={r.n_days}"
            )
            assert r.status == "rejected", msg
        assert contract["n_validated"] == 0


class TestHonestNulls:
    """Regression tests for real best-null-per-CP and calibrated null gates."""

    def test_intercept_only_loses_to_calibrated_null(self):
        features, labels = _make_biased_remaining_warming_dataset()
        hyp = Hypothesis(
            id="H_CONSTANT",
            feature_column="constant_feature",
            description="Constant feature must not get credit for intercept-only calibration",
        )

        results, contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        result = next(r for r in results if r.id == "H_CONSTANT")
        assert result.status == "rejected"
        assert result.best_null_name == "calibrated_cp_mean_rw"
        assert result.best_null_mae is not None
        assert contract["n_validated"] == 0

    def test_feature_must_beat_best_null_not_just_l0(self):
        features, labels = _make_climatology_dominates_dataset()
        hyp = Hypothesis(
            id="H_WEAK",
            feature_column="weak_signal",
            description="Weak feature beats L0 but must lose to the best train-only null",
        )

        results, contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        result = next(r for r in results if r.id == "H_WEAK")
        assert result.status == "rejected"
        assert result.best_null_name != "L0_persistence"
        assert result.best_null_mae is not None
        assert result.gate_results["G1"].passed is False
        assert result.gate_results["G5"].passed is False
        assert contract["n_validated"] == 0

    def test_categorical_feature_can_validate_via_one_hot(self):
        features, labels = _make_categorical_signal_dataset()
        hyp = Hypothesis(
            id="H_CATEGORY",
            feature_column="category_signal",
            description="String categories should be one-hot encoded by the harness",
        )

        results, contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        result = next(r for r in results if r.id == "H_CATEGORY")
        assert result.status == "validated"
        assert result.best_null_name is not None
        assert result.gate_results["G1"].passed is True
        assert result.gate_results["G5"].passed is True
        assert contract["n_validated"] == 1


class TestFdrCorrection:
    """BH across 20 noise + 1 signal — only the signal survives."""

    def test_fdr_separates_signal(self):
        features, labels = _make_dataset()

        # 20 noise hypotheses
        hyps = [
            Hypothesis(
                id=f"H_NOISE_{j}",
                feature_column=f"noise_{j}",
                description=f"Pure noise #{j}",
            )
            for j in range(20)
        ]
        # 1 known signal
        hyps.append(
            Hypothesis(
                id="H_SIGNAL",
                feature_column="signal_feature",
                description="Known signal",
            )
        )

        results, contract = validate_hypotheses(
            features, labels, hyps,
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        signal_results = [r for r in results if r.id == "H_SIGNAL"]
        noise_results = [r for r in results if r.id.startswith("H_NOISE_")]

        # Signal must validate
        for r in signal_results:
            msg = (
                f"Signal CP={r.cp} regime={r.regime}: status={r.status}, "
                f"fdr_adjusted={r.fdr_adjusted}, effect={r.effect_size:.4f}, "
                f"p={r.p_value:.6f}, n={r.n_days}"
            )
            assert r.status == "validated", msg

        # All noise must be rejected
        for r in noise_results:
            msg = (
                f"Noise {r.id} CP={r.cp} regime={r.regime}: status={r.status}, "
                f"fdr_adjusted={r.fdr_adjusted}, p={r.p_value:.6f}"
            )
            assert r.status == "rejected", msg

        # Contract counts
        assert contract["n_validated"] == 1, f"Expected 1 validated, got {contract['n_validated']}"
        assert contract["n_rejected"] == 20, f"Expected 20 rejected, got {contract['n_rejected']}"


class TestBlockedFeatures:
    """Features in BLOCKED_FEATURES get BLOCKED status, never fitted."""

    def test_blocked_handled(self):
        """sst_maritime_cap is in BLOCKED_FEATURES."""
        features, labels = _make_dataset()

        hyp = Hypothesis(
            id="H_BLOCKED",
            feature_column="sst_maritime_cap",
            description="Requires SST — should be BLOCKED",
        )

        results, _contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        blocked = [r for r in results if r.id == "H_BLOCKED"]
        assert len(blocked) > 0
        for r in blocked:
            assert r.status == "BLOCKED", f"Expected BLOCKED, got {r.status}: {r.blocked_reason}"
            assert r.blocked_reason is not None and len(r.blocked_reason) > 0


class TestEmptyFeature:
    """An all-null feature = rejected, never crashes."""

    def test_all_null_rejected(self):
        features, labels = _make_dataset()

        hyp = Hypothesis(
            id="H_EMPTY",
            feature_column="empty_feature",
            description="All nulls — must not crash",
        )

        # Should not raise
        results, _contract = validate_hypotheses(
            features, labels, [hyp],
            cp_set=("20:00",),
            test_starts=[dt.date(2024, 1, 1)],
            seed=42,
        )

        empty = [r for r in results if r.id == "H_EMPTY"]
        assert len(empty) > 0
        for r in empty:
            assert r.status == "rejected", f"Expected rejected for all-null, got {r.status}"
