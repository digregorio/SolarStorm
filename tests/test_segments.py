import datetime as dt

import polars as pl

from solarstorm.eval._segments import segment_results


def make_fake_results():
    return pl.DataFrame({
        "date_local": [dt.date(2025, 6, d) for d in range(1, 11)],
        "cp": ["23:00"] * 10,
        "regime": ["calm_radiative"] * 5 + ["standard_nw"] * 3 + ["southerly_disrupted"] * 2,
        "mae": [1.0, 1.2, 0.8, 1.1, 0.9, 2.5, 3.0, 2.8, 4.0, 3.5],
    })


def test_segment_results_by_regime():
    df = make_fake_results()
    segments = segment_results(df, by=["regime"])
    assert "calm_radiative" in segments
    assert "standard_nw" in segments
    calm_mae = segments["calm_radiative"]["mae"].mean()
    nw_mae = segments["standard_nw"]["mae"].mean()
    assert nw_mae > calm_mae


def test_segment_results_by_cp():
    df = make_fake_results()
    segments = segment_results(df, by=["cp"])
    assert "23:00" in segments
