import datetime as dt

import polars as pl

from solarstorm.baselines._empirical import fit_empirical_conditional
from solarstorm.baselines._persistence import predict_dminus1, predict_persistence


def test_predict_persistence_returns_k_cp():
    result = predict_persistence(k_cp=15)
    assert result["p50"] == 15
    assert result["source"] == "persistence"


def test_predict_dminus1_returns_yesterday_tmax():
    result = predict_dminus1(tmax_dminus1=22)
    assert result["p50"] == 22
    assert result["source"] == "dminus1"


def test_predict_persistence_dist_has_single_bucket():
    result = predict_persistence(k_cp=18)
    assert result["prob_dist"] == {18: 1.0}


def test_empirical_conditional_uses_conditional_bucket():
    labels = pl.DataFrame({
        "date_local": [dt.date(2025, 1, d) for d in range(1, 32)],
        "month": [1] * 31,
        "tmax_int": [20] * 15 + [25] * 16,
        "k_cp__cp_2300": [20] * 15 + [24] * 16,
        "day_complete": [True] * 31,
    })
    emp = fit_empirical_conditional(
        labels, train_window=(dt.date(2025, 1, 1), dt.date(2025, 1, 31)),
        n_min_bucket=5,
    )
    dist, source = emp.predict_dist(month=1, cp="2300", k_cp=24, support_k=list(range(10, 35)))
    assert source == "conditional"
    # With laplace smoothing, 25 should have highest prob
    assert dist[25] > dist[20]


def test_empirical_falls_back_to_marginal_when_bucket_too_small():
    labels = pl.DataFrame({
        "date_local": [dt.date(2025, 1, d) for d in range(1, 32)],
        "month": [1] * 31,
        "tmax_int": [20] * 31,
        "k_cp__cp_2300": [15] * 31,
        "day_complete": [True] * 31,
    })
    emp = fit_empirical_conditional(
        labels, train_window=(dt.date(2025, 1, 1), dt.date(2025, 1, 31)),
        n_min_bucket=50,  # higher than available data → forces fallback
    )
    _, source = emp.predict_dist(month=1, cp="2300", k_cp=15, support_k=list(range(10, 35)))
    assert source == "fallback_marginal"


def test_empirical_raises_without_train_window():
    labels = pl.DataFrame({
        "date_local": [dt.date(2025, 1, 1)],
        "month": [1], "tmax_int": [20], "k_cp__cp_2300": [15], "day_complete": [True],
    })
    try:
        fit_empirical_conditional(labels)
        assert False, "should have raised"
    except ValueError:
        pass
