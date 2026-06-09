import datetime as dt

import polars as pl
import pytest

from solarstorm.data._iem import fetch_iem_asos


@pytest.mark.network
def test_fetch_iem_asos_returns_expected_columns():
    df = fetch_iem_asos(
        station="NZWN",
        start=dt.date(2025, 6, 1),
        end=dt.date(2025, 6, 3),
    )
    assert isinstance(df, pl.DataFrame)
    for col in ("valid", "metar", "tmpf", "dwpf", "sknt", "drct", "alti", "p01i"):
        assert col in df.columns


@pytest.mark.network
def test_fetch_iem_asos_dates_in_range():
    df = fetch_iem_asos(
        station="NZWN",
        start=dt.date(2025, 6, 1),
        end=dt.date(2025, 6, 3),
    )
    assert df.height > 0
    min_ts = df["valid"].min()
    max_ts = df["valid"].max()
    assert min_ts >= dt.datetime(2025, 6, 1, tzinfo=dt.UTC)
    assert max_ts < dt.datetime(2025, 6, 4, tzinfo=dt.UTC)


def test_fetch_iem_asos_cached(tmp_path, monkeypatch):
    """Second call reads from cache, not the network."""
    cache_dir = tmp_path / "iem_cache"
    calls = 0

    def _fake_fetch(*args, **kwargs):
        nonlocal calls
        calls += 1
        return pl.DataFrame({
            "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
            "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020"],
            "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
            "alti": [30.12], "p01i": [0.0],
        })

    from solarstorm.data import _iem
    monkeypatch.setattr(_iem, "_fetch_iem_raw", _fake_fetch)

    df1 = _iem.fetch_iem_asos("NZWN", dt.date(2025, 6, 1), dt.date(2025, 6, 1), cache_dir=cache_dir)
    df2 = _iem.fetch_iem_asos("NZWN", dt.date(2025, 6, 1), dt.date(2025, 6, 1), cache_dir=cache_dir)
    assert calls == 1  # second call cached
    assert df1.height == df2.height
