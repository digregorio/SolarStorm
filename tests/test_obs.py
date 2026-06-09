"""Tests for per-observation persistence (obs.parquet)."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm.data._obs import persist_obs


def test_persist_obs_schema(tmp_path):
    """persist_obs writes obs.parquet with expected columns."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020"],
        "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "skyc1": ["FEW"], "skyc2": [None], "skyc3": [None], "skyc4": [None],
        "skyl1": ["2000"], "skyl2": [None], "skyl3": [None], "skyl4": [None],
        "wxcodes": [None],
        "tmp_c_int": [15], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert (tmp_path / "obs.parquet").exists()
    for col in ("valid", "ts_local", "metar", "tmp_c_int", "dw_depression_c_int",
                "dwp_c_int", "dq_tmp_c_int", "skyc1", "skyl1", "wxcodes"):
        assert col in result.columns


def test_persist_obs_parses_dwp_from_metar(tmp_path):
    """METAR TT/DD group determines dwp, not rounded tmpf."""
    # 15/10 in METAR -> dwp=10, depression=5 (tmp_c_int is already 15 from ingest)
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020"],
        "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "tmp_c_int": [15], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert result["dwp_c_int"][0] == 10
    assert result["dw_depression_c_int"][0] == 5


def test_persist_obs_negative_temperature(tmp_path):
    """M05/M10 in METAR -> dwp=-10, depression=5 (tmp_c_int=-5)."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 M05/M10 Q1020"],
        "tmpf": [23.0], "dwpf": [14.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "tmp_c_int": [-5], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert result["dwp_c_int"][0] == -10
    assert result["dw_depression_c_int"][0] == 5


def test_persist_obs_ts_local_is_pacific_auckland(tmp_path):
    """ts_local preserves Pacific/Auckland timezone with correct offset for NZST."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020"],
        "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "tmp_c_int": [15], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert result.schema["ts_local"] == pl.Datetime(time_zone="Pacific/Auckland")
    ts = result["ts_local"][0]
    # June is NZST (UTC+12): UTC midnight = 12:00 local
    assert ts.hour == 12
    assert ts.day == 1
    assert ts.month == 6


def test_persist_obs_skyl_casts_to_int64(tmp_path):
    """skyl* columns are cast to Int64 in the output."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 18/12 Q1020"],
        "tmpf": [64.0], "dwpf": [54.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "skyc1": ["FEW"], "skyc2": ["BKN"], "skyc3": [None], "skyc4": [None],
        "skyl1": ["0500"], "skyl2": ["2500"], "skyl3": [None], "skyl4": [None],
        "wxcodes": [None],
        "tmp_c_int": [18], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert result.schema["skyl1"] == pl.Int64
    assert result["skyl1"][0] == 500
    assert result["skyl2"][0] == 2500
    # null skyl* columns remain null
    assert result["skyl3"][0] is None
    assert result["skyl4"][0] is None


def test_persist_obs_preserves_wxcodes(tmp_path):
    """wxcodes column passes through."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 18/12 Q1020"],
        "tmpf": [64.0], "dwpf": [54.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "wxcodes": ["RA"],
        "tmp_c_int": [18], "dq_tmp_c_int": ["ok"],
    })
    result = persist_obs(df, tmp_path)
    assert "wxcodes" in result.columns
    assert result["wxcodes"][0] == "RA"


def test_persist_obs_missing_metar_yields_null_dwp(tmp_path):
    """When METAR is missing, dwp and depression should be null."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": [None],
        "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "tmp_c_int": [15], "dq_tmp_c_int": ["imputed"],
    })
    result = persist_obs(df, tmp_path)
    assert result["dwp_c_int"][0] is None
    assert result["dw_depression_c_int"][0] is None


def test_persist_obs_multiple_rows(tmp_path):
    """Multiple rows are handled correctly."""
    ts1 = dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)
    ts2 = dt.datetime(2025, 6, 1, 1, 0, tzinfo=dt.UTC)
    df = pl.DataFrame({
        "valid": [ts1, ts2],
        "metar": [
            "NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020",
            "NZWN 010100Z AUTO 00000KT 9999 FEW030 16/11 Q1022",
        ],
        "tmpf": [59.0, 60.8], "dwpf": [50.0, 51.8],
        "sknt": [0.0, 5.0], "drct": [0.0, 180.0],
        "alti": [30.12, 30.15], "p01i": [0.0, 0.0],
        "tmp_c_int": [15, 16], "dq_tmp_c_int": ["ok", "ok"],
    })
    result = persist_obs(df, tmp_path)
    assert result.height == 2
    assert result["dwp_c_int"].to_list() == [10, 11]
    assert result["dw_depression_c_int"].to_list() == [5, 5]
    nzt = ZoneInfo("Pacific/Auckland")
    assert result["ts_local"][0] == ts1.astimezone(nzt)
    assert result["ts_local"][1] == ts2.astimezone(nzt)


def test_persist_obs_roundtrip(tmp_path):
    """Written obs.parquet can be read back with the same schema."""
    df = pl.DataFrame({
        "valid": [dt.datetime(2025, 6, 1, 0, 0, tzinfo=dt.UTC)],
        "metar": ["NZWN 010000Z AUTO 00000KT 9999 FEW020 15/10 Q1020"],
        "tmpf": [59.0], "dwpf": [50.0], "sknt": [0.0], "drct": [0.0],
        "alti": [30.12], "p01i": [0.0],
        "skyl1": ["2000"],
        "tmp_c_int": [15], "dq_tmp_c_int": ["ok"],
    })
    persist_obs(df, tmp_path)
    loaded = pl.read_parquet(tmp_path / "obs.parquet")
    assert loaded.schema["dwp_c_int"] == pl.Int64
    assert loaded.schema["dw_depression_c_int"] == pl.Int64
    assert loaded.schema["ts_local"] == pl.Datetime(time_zone="Pacific/Auckland")
    assert loaded.schema["skyl1"] == pl.Int64
    assert loaded["dwp_c_int"][0] == 10
    assert loaded["tmp_c_int"][0] == 15
