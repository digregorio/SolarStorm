from solarstorm.baselines._ladder import LadderResult, best_null_for_cp, evaluate_step


def test_best_null_for_cp_picks_min_mae():
    results = {
        "20:00": [
            LadderResult(level="L0", name="persistence", cp="20:00", mae=2.1),
            LadderResult(level="L2", name="climatology", cp="20:00", mae=1.8),
        ],
    }
    best = best_null_for_cp(results, cp="20:00")
    assert best.name == "climatology"


def test_evaluate_step_computes_mae():
    pred = {"p50": 20}
    truth = 22
    result = evaluate_step(
        level="L0", name="persistence", cp="23:00", pred=pred, truth=truth,
        fallback_rate=0.0,
    )
    assert result.mae == 2.0
    assert result.bias == -2.0
