import datetime as dt

import polars as pl

from solarstorm.eda._regimes import classify_regime


def make_obs(rows: list[tuple[int, float, float, float, float]]):
    """(hour_local, tmp_c, wind_dir, wind_speed_kt, dwp_c, p01i)"""
    return pl.DataFrame([
        {
            "ts_local": dt.datetime(2025, 6, 15, h, 0, 0),
            "tmp_c_int": int(t), "wind_dir_deg": wd, "sknt": ws,
            "dwp_c_int": int(dwp), "p01i": p,
        }
        for h, t, wd, ws, dwp, p in rows
    ])


def test_classify_calm_day():
    obs = make_obs([
        (6, 8, 90, 3, 6, 0.0),
        (9, 10, 100, 4, 7, 0.0),
        (12, 13, 110, 4, 8, 0.0),
        (15, 14, 100, 4, 7, 0.0),
        (18, 12, 90, 3, 6, 0.0),
    ])
    regime, flags = classify_regime(obs)
    assert regime == "calm_radiative"
    assert not flags.get("intraday_regime_change", False)


def test_late_tmax_does_not_create_causal_regime():
    obs = make_obs([
        (6, 10, 320, 8, 8, 0.0),
        (9, 12, 330, 10, 9, 0.0),
        (12, 14, 340, 12, 10, 0.0),
        (15, 15, 340, 10, 10, 0.0),
        (18, 16, 330, 12, 11, 0.0),
        (21, 19, 320, 15, 10, 0.0),   # jump after 21Z NZST (9Z UTC)
    ])
    regime, _ = classify_regime(obs)
    assert regime == "standard_nw"


def test_classify_foehn_nw():
    obs = make_obs([
        (6, 12, 320, 18, 6, 0.0),   # NW wind, dewpoint depression = 6°C
        (9, 14, 330, 20, 8, 0.0),
        (12, 17, 340, 22, 9, 0.0),  # depression > 4°C
        (15, 17, 330, 20, 10, 0.0),
    ])
    regime, _ = classify_regime(obs)
    assert regime == "strong_nw_foehn"


def test_classify_southerly_disrupted_from_precip_or_cooling():
    obs = make_obs([
        (6, 14, 180, 18, 12, 0.0),
        (9, 13, 170, 20, 11, 0.0),
        (12, 10, 160, 22, 9, 0.05),
        (15, 9, 170, 22, 8, 0.0),
    ])

    regime, _ = classify_regime(obs)

    assert regime == "southerly_disrupted"
