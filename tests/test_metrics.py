import numpy as np

from solarstorm.eval._bootstrap import bootstrap_ci, bootstrap_ci_diff
from solarstorm.eval._metrics import bracket_match_at_p50, corr, mae, rmse, rps, skill_score


def test_mae():
    assert mae(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0])) == 0.0
    assert mae(np.array([10.0]), np.array([12.0])) == 2.0


def test_rmse():
    # RMSE = sqrt(mean([3**2, 4**2])) = sqrt(12.5); the spec's 2.5 was an
    # arithmetic slip (Euclidean norm / n, not root-mean-square).
    assert rmse(np.array([0.0, 0.0]), np.array([3.0, 4.0])) == np.sqrt(12.5)


def test_rps_perfect():
    prob = {18: 0.0, 19: 0.0, 20: 1.0, 21: 0.0}
    assert rps(prob, 20) == 0.0


def test_rps_off_by_one():
    prob = {18: 0.0, 19: 1.0, 20: 0.0, 21: 0.0}
    score = rps(prob, 20)
    assert score > 0.0


def test_bracket_match_at_p50_perfect():
    assert bracket_match_at_p50(20.1, 20) == 1.0


def test_bracket_match_at_p50_fail():
    assert bracket_match_at_p50(19.9, 21) == 0.0


def test_corr_perfect():
    a = np.array([1.0, 2.0, 3.0])
    assert corr(a, a * 2) == 1.0


def test_skill_score_positive():
    pred = np.array([1.0, 2.0, 3.0])
    truth = np.array([1.0, 2.0, 3.0])
    baseline = np.array([0.0, 0.0, 0.0])
    ss = skill_score(pred, baseline, truth)
    assert ss == 1.0  # perfect pred vs terrible baseline


def test_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(42)
    data = rng.normal(10, 2, 100)
    point, lo, hi = bootstrap_ci(data, np.mean, seed=42)
    assert lo <= point <= hi


def test_bootstrap_ci_diff_significant():
    rng = np.random.default_rng(42)
    a = rng.normal(12, 2, 100)
    b = rng.normal(10, 2, 100)
    _, lo, _ = bootstrap_ci_diff(a, b, seed=42)
    assert lo > 0  # a > b significantly
