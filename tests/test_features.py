"""Tests for causal feature builder (B1+B2).

CP hours are in **UTC** (METAR convention).  For Wellington (UTC+12/13),
UTC CPs 20:00-23:00 on D-1 map to local morning (08-11 NZST / 09-12 NZDT)
on date D.  The pre-CP window for a morning CP is roughly midnight-to-8am
local, so typically only anchor hours 06 and 09 are in range.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from solarstorm.eda._catalog import SEED_HYPOTHESES
from solarstorm.features.builder import (
    BLOCKED_FEATURES,
    _obs_by_date,
    build_coverage_manifest,
    build_features,
)

TZ = ZoneInfo("Pacific/Auckland")
UTC = dt.UTC

# ---------------------------------------------------------------------------
# Test helpers — synthetic obs / labels
# ---------------------------------------------------------------------------

_CP_SET = ("20:00", "21:00", "22:00", "23:00")
_KCP_COLS: dict[str, str] = {
    cp: f"k_cp__cp_{cp.replace(':', '')}" for cp in _CP_SET
}


def _utc_dt(d: dt.date, utc_h: int) -> dt.datetime:
    """UTC datetime at *utc_h* on UTC date *d*."""
    return dt.datetime(d.year, d.month, d.day, utc_h, 0, tzinfo=UTC)


def _make_obs(
    dates: list[dt.date],
    hours: list[int],
    *,
    tmp_c: list[list[int | None]] | None = None,
    dwp_c: list[list[int | None]] | None = None,
    sknt: list[list[float | None]] | None = None,
    drct: list[list[float | None]] | None = None,
    alti: list[list[float | None]] | None = None,
    p01i: list[list[float | None]] | None = None,
    skyc1: list[list[str | None]] | None = None,
    skyl1: list[list[int | None]] | None = None,
    wxcodes: list[list[str | None]] | None = None,
    dq: str = "ok",
) -> pl.DataFrame:
    """Build an obs DataFrame with columns matching _obs.py schema.

    *hours* are in **UTC**.  Observations are created on UTC date *d*-1 so
    that they land on local date *d* (for NZ tz offsets this is the correct
    mapping for all hours 12-23 UTC).
    """
    def _default(val, d_idx, h_idx):
        if val is not None:
            return val[d_idx][h_idx]
        return None

    rows = []
    for di, d in enumerate(dates):
        for hi, h in enumerate(hours):
            # UTC D-1 at hour h → local date D for NZ (UTC+12/13)
            utc_ts = dt.datetime(d.year, d.month, d.day, h, 0, tzinfo=UTC)
            utc_ts = utc_ts - dt.timedelta(days=1)
            rows.append({
                "valid": utc_ts,
                "ts_local": utc_ts.astimezone(TZ),
                "tmp_c_int": _default(tmp_c, di, hi) or 12,
                "dwp_c_int": _default(dwp_c, di, hi) or 8,
                "dw_depression_c_int": None,
                "sknt": _default(sknt, di, hi) or 5.0,
                "drct": _default(drct, di, hi) or 180.0,
                "alti": _default(alti, di, hi) or 30.00,
                "p01i": _default(p01i, di, hi) or 0.0,
                "skyc1": _default(skyc1, di, hi) or "CLR",
                "skyl1": _default(skyl1, di, hi) or None,
                "skyc2": None, "skyl2": None,
                "skyc3": None, "skyl3": None,
                "skyc4": None, "skyl4": None,
                "wxcodes": _default(wxcodes, di, hi) or None,
                "dq_tmp_c_int": dq,
            })
    df = pl.DataFrame(rows)
    df = df.with_columns(
        (pl.col("tmp_c_int") - pl.col("dwp_c_int")).alias("dw_depression_c_int"),
    )
    return df


def _make_labels(
    dates: list[dt.date],
    *,
    tmax: list[int] | None = None,
    tmin: list[int] | None = None,
    tmax_hour: list[int] | None = None,
    kcp: dict[str, list[int]] | None = None,
) -> pl.DataFrame:
    if kcp is None:
        kcp = {}
    rows = []
    for i, d in enumerate(dates):
        row: dict = {
            "date_local": d,
            "tmax_int": tmax[i] if tmax else 20,
            "tmin_int": tmin[i] if tmin else 10,
            "tmax_hour": tmax_hour[i] if tmax_hour else 15,
        }
        for cp_str, col in _KCP_COLS.items():
            row[col] = kcp.get(cp_str, [12] * len(dates))[i]
        rows.append(row)
    return pl.DataFrame(rows)


# ===================================================================
# Tests
# ===================================================================

def test_build_features_returns_one_row_per_date_cp():
    """With obs for 3 days, 4 CPs -> 12 rows + all expected columns."""
    dates = [dt.date(2025, 6, 15), dt.date(2025, 6, 16), dt.date(2025, 6, 17)]
    # UTC hours 16, 18, 19 on D-1 → local 04, 06, 07 on D (all pre-CP)
    hours = [16, 18, 19]
    tmp_c = [
        [10, 11, 12],
        [10, 11, 12],
        [10, 11, 12],
    ]
    dwp_c = [
        [8, 8, 9],
        [8, 8, 9],
        [8, 8, 9],
    ]
    obs = _make_obs(dates, hours, tmp_c=tmp_c, dwp_c=dwp_c)
    labels = _make_labels(dates)

    result = build_features(obs, labels)

    assert result.height == 3 * 4
    assert "date_local" in result.columns
    assert "cp" in result.columns
    assert result["cp"].to_list() == ["20:00", "21:00", "22:00", "23:00"] * 3

    for hyp in SEED_HYPOTHESES:
        assert hyp.feature_column in result.columns, (
            f"Missing column: {hyp.feature_column} ({hyp.id})"
        )

    assert "regime_label" in result.columns


def test_obs_by_date_partitions_once_by_local_date():
    """Date partitions preserve local-day grouping without repeated global scans."""
    dates = [dt.date(2025, 6, 15), dt.date(2025, 6, 16)]
    obs = _make_obs(dates, [16, 18])

    groups = _obs_by_date(obs)

    assert list(groups) == dates
    assert groups[dates[0]].height == 2
    assert groups[dates[1]].height == 2
    assert set(groups[dates[0]]["date_local"].to_list()) == {dates[0]}


def test_post_cp_obs_do_not_leak():
    """Obs at or after CP UTC hour are excluded — causal firewall."""
    d = dt.date(2025, 6, 15)
    # UTC hours 18, 21, 22 on D-1 → local 06, 09, 10 on D
    # CP=22:00 UTC sees 18, 21 only (22 >= 22 excluded)
    # Hour 22 has contaminant tmp_c=999 — if it leaked, slope_3h would spike.
    # anchor 6 (from 18 UTC) = 10°C, anchor 9 (from 21 UTC) = 16°C → slope = 2.0
    hours = [18, 21, 22]
    tmp_c = [[10, 16, 999]]
    dwp_c = [[8, 10, 999]]
    obs = _make_obs([d], hours, tmp_c=tmp_c, dwp_c=dwp_c)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    # CP=22:00 can see both 18 and 21 UTC → 2 anchors → slope non-null
    cp22 = result.filter(pl.col("cp") == "22:00")
    slope = cp22["slope_3h"].to_list()[0]
    assert slope is not None
    assert abs(slope - 2.0) < 1e-6, f"expected slope ~2.0, got {slope}"

    # CP=20:00 only sees 18 UTC (21 is >=20, 22 is >=20) → 1 anchor → null slope
    cp20 = result.filter(pl.col("cp") == "20:00")
    assert cp20["slope_3h"].to_list()[0] is None


def test_blocked_features_are_null():
    """H19 sst_maritime_cap is always null."""
    dates = [dt.date(2025, 6, 15), dt.date(2025, 6, 16)]
    obs = _make_obs(dates, [16, 18, 19])
    labels = _make_labels(dates)
    result = build_features(obs, labels)

    assert result["sst_maritime_cap"].is_null().all()
    assert "sst_maritime_cap" in BLOCKED_FEATURES


def test_warming_rate_06_09():
    """H17: (T09 - T06) / 3. Only visible at CP>=22:00 UTC."""
    d = dt.date(2025, 6, 15)
    # UTC 18 D-1 = 06 local D, UTC 21 D-1 = 09 local D
    # CP=20:00 can't see 21 UTC; CP=21:00 can't either; CP=22:00 CAN
    hours = [18, 21]  # local 06:00 and 09:00 on D
    tmp_c = [[10, 16]]  # T06=10, T09=16 -> (16-10)/3 = 2.0
    obs = _make_obs([d], hours, tmp_c=tmp_c)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    # At CP=22:00 (10:00 local) and CP=23:00 (11:00 local), both anchors visible
    for cp_str in ("22:00", "23:00"):
        row = result.filter(pl.col("cp") == cp_str)
        assert row["warming_rate_06_09"].to_list()[0] == 2.0

    # At CP=20:00 and CP=21:00, anchor 09 is not yet visible → null
    for cp_str in ("20:00", "21:00"):
        row = result.filter(pl.col("cp") == cp_str)
        val = row["warming_rate_06_09"].to_list()[0]
        assert val is None, f"{cp_str}: expected null, got {val}"


def test_dewpoint_collapse_rate():
    """H20: (dwp_latest - dwp_earliest) / hours_between."""
    d = dt.date(2025, 6, 15)
    hours = [18, 21]  # 06 and 09 local
    tmp_c = [[10, 12]]
    dwp_c = [[8, 2]]  # dwp at 06=8, at 09=2 -> (2-8)/3 = -2.0
    obs = _make_obs([d], hours, tmp_c=tmp_c, dwp_c=dwp_c)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    for cp_str in ("22:00", "23:00"):
        row = result.filter(pl.col("cp") == cp_str)
        rate = row["dewpoint_collapse_rate_3h"].to_list()[0]
        assert rate is not None and abs(rate - (-2.0)) < 1e-6, (
            f"got {rate} for {cp_str}"
        )


def test_cloud_base_transparency():
    """H23: max(coverage_weight * min(1.0, base / 8000)) over layers."""
    d = dt.date(2025, 6, 15)
    hours = [18]  # 06 local = UTC 18 D-1 (pre all CPs)
    obs = _make_obs([d], hours, skyc1=[["OVC"]], skyl1=[[2500]])
    labels = _make_labels([d])

    result = build_features(obs, labels)
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        assert row["cloud_base_transparency"].to_list()[0] == pytest.approx(0.3125, abs=1e-4)

    # FEW at 8000ft -> 0.2 * 1.0 = 0.2
    obs2 = _make_obs([d], hours, skyc1=[["FEW"]], skyl1=[[8000]])
    result2 = build_features(obs2, labels)
    score2 = result2.filter(pl.col("cp") == "20:00")["cloud_base_transparency"].to_list()[0]
    assert score2 == pytest.approx(0.2, abs=1e-4)

    # CLR -> 0.0
    obs3 = _make_obs([d], hours, skyc1=[["CLR"]])
    result3 = build_features(obs3, labels)
    score3 = result3.filter(pl.col("cp") == "20:00")["cloud_base_transparency"].to_list()[0]
    assert score3 == 0.0


def test_cloud_cover_suppression():
    """H12: max over pre-CP obs. With morning CPs, only early-day clouds visible."""
    d = dt.date(2025, 6, 15)
    # All obs pre-CP, max cover = OVC (1.0)
    hours = [16, 18, 19]  # 04, 06, 07 local
    skyc1 = [["SCT", "BKN", "OVC"]]
    obs = _make_obs([d], hours, skyc1=skyc1)
    labels = _make_labels([d])

    result = build_features(obs, labels)
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        assert row["cloud_cover_suppression"].to_list()[0] == 1.0


def test_foehn_score_computation():
    """H14: nw_flow_strength * dwp_depression in pre-CP window."""
    d = dt.date(2025, 6, 15)
    hours = [16, 18, 19]  # 04, 06, 07 local — all pre-CP
    tmp_c = [[15, 17, 19]]
    dwp_c = [[8, 9, 10]]  # depression = 7, 8, 9 → mean = 8.0
    drct_data = [[320.0] * len(hours)]
    sknt_data = [[18.0] * len(hours)]
    obs = _make_obs([d], hours, tmp_c=tmp_c, dwp_c=dwp_c, drct=drct_data, sknt=sknt_data)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        score = row["foehn_score"].to_list()[0]
        # nw_flow_strength=18, mean_dwp_dep=8.0 → 144
        assert score is not None and score > 130, f"expected ~144, got {score}"


def test_late_full_day_tmax_does_not_override_causal_regime_label():
    """A late ex-post Tmax must not be injected into the CP regime feature."""
    d = dt.date(2025, 6, 15)
    rows = []
    for local_hour, tmp in [(5, 10), (6, 11), (7, 12), (21, 21)]:
        ts_local = dt.datetime(d.year, d.month, d.day, local_hour, tzinfo=TZ)
        rows.append({
            "valid": ts_local.astimezone(UTC),
            "ts_local": ts_local,
            "tmp_c_int": tmp,
            "dwp_c_int": 8,
            "dw_depression_c_int": tmp - 8,
            "sknt": 10.0,
            "drct": 330.0,
            "alti": 30.00,
            "p01i": 0.0,
            "skyc1": "CLR",
            "skyl1": None,
            "skyc2": None,
            "skyl2": None,
            "skyc3": None,
            "skyl3": None,
            "skyc4": None,
            "skyl4": None,
            "wxcodes": None,
            "dq_tmp_c_int": "ok",
        })
    obs = pl.DataFrame(rows)
    labels = _make_labels([d], tmax=[21], tmax_hour=[21])

    result = build_features(obs, labels)

    assert set(result["regime_label"].to_list()) == {"standard_nw"}
    assert "late_warming" not in set(result["regime_label"].to_list())


def test_prefrontal_warming_window():
    """H21: falling QNH + no precip + N/NW flow.

    Needs 2 alti anchors — CP=23:00 sees anchors 6 and 9 (from 18, 21 UTC).
    CP=20:00 only sees anchor 6 -> always 0 (not enough anchors).
    """
    d = dt.date(2025, 6, 15)
    # anchor 6 (18 UTC) alti=30.00, anchor 9 (21 UTC) alti=29.94
    hours = [18, 21]
    alti_data = [[30.00, 29.94]]
    drct_data = [[350.0, 350.0]]
    p01i_data = [[0.0, 0.0]]
    tmp_c = [[10, 12]]
    obs = _make_obs([d], hours, tmp_c=tmp_c, alti=alti_data,
                     drct=drct_data, p01i=p01i_data)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    # CP=23:00 can see both → 2 alti anchors → prefrontal fires
    row23 = result.filter(pl.col("cp") == "23:00")
    pf23 = row23["prefrontal_warming_window"].to_list()[0]
    assert pf23 == 1, f"expected 1 for 23:00, got {pf23}"

    # CP=22:00 also sees both → prefrontal fires
    row22 = result.filter(pl.col("cp") == "22:00")
    pf22 = row22["prefrontal_warming_window"].to_list()[0]
    assert pf22 == 1, f"expected 1 for 22:00, got {pf22}"

    # CP=20:00 and CP=21:00 cannot see 21 UTC → 1 anchor → prefrontal stays 0
    for cp_str in ("20:00", "21:00"):
        row = result.filter(pl.col("cp") == cp_str)
        pf = row["prefrontal_warming_window"].to_list()[0]
        assert pf == 0, f"expected 0 for {cp_str} (only 1 alti anchor), got {pf}"


def test_precip_disruption():
    """H10: 1 if p01i > 0.01 or RA in wxcodes."""
    d = dt.date(2025, 6, 15)
    hours = [16, 18, 19]  # pre-CP

    # RA in wxcodes
    obs = _make_obs([d], hours, wxcodes=[["RA", None, None]])
    labels = _make_labels([d])
    result = build_features(obs, labels)
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        assert row["precip_disruption"].to_list()[0] == 1

    # p01i > 0.01
    obs2 = _make_obs([d], hours, p01i=[[0.0, 0.05, 0.0]])
    result2 = build_features(obs2, labels)
    for cp_str in _CP_SET:
        row = result2.filter(pl.col("cp") == cp_str)
        assert row["precip_disruption"].to_list()[0] == 1

    # No precip
    obs3 = _make_obs([d], hours)
    result3 = build_features(obs3, labels)
    for cp_str in _CP_SET:
        row = result3.filter(pl.col("cp") == cp_str)
        assert row["precip_disruption"].to_list()[0] == 0


def test_day_sequence_pattern():
    """H9: warming/cooling/peaked/troughed/flat (uses D-1, D-2, D-3 only — causal, Fix 2)."""
    dates = [dt.date(2025, 6, 12), dt.date(2025, 6, 13), dt.date(2025, 6, 14), dt.date(2025, 6, 15)]
    hours = [16, 18, 19]
    obs = _make_obs(dates, hours)

    # D-3=12, D-2=14, D-1=16 → warming pattern on D=15
    labels_warming = _make_labels(dates, tmax=[10, 12, 14, 16])
    result = build_features(obs, labels_warming)
    row = result.filter(
        (pl.col("date_local") == dates[3]) & (pl.col("cp") == "20:00")
    )
    assert row["day_sequence_pattern"].to_list()[0] == "warming"

    # D-3=16, D-2=14, D-1=12 → cooling pattern on D=15
    labels_cooling = _make_labels(dates, tmax=[18, 16, 14, 12])
    result = build_features(obs, labels_cooling)
    row = result.filter(
        (pl.col("date_local") == dates[3]) & (pl.col("cp") == "20:00")
    )
    assert row["day_sequence_pattern"].to_list()[0] == "cooling"


def test_slope_3h_from_anchors():
    """H1: (T_latest - T_earliest) / hours_between. Uses CP=23:00 for max anchors."""
    d = dt.date(2025, 6, 15)
    # UTC 18 D-1 = 06 local, UTC 21 D-1 = 09 local
    # Both visible at CP=23:00. T_earliest=10, T_latest=18, delta=8, hours=3
    hours = [18, 21]
    tmp_c = [[10, 18]]
    obs = _make_obs([d], hours, tmp_c=tmp_c)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    # CP=23:00 sees both → slope = 8/3 ≈ 2.667
    row = result.filter(pl.col("cp") == "23:00")
    slope = row["slope_3h"].to_list()[0]
    assert slope is not None and abs(slope - 8.0 / 3.0) < 1e-6

    # CP=20:00 only sees anchor 06 → null (need at least 2 anchors)
    row20 = result.filter(pl.col("cp") == "20:00")
    assert row20["slope_3h"].to_list()[0] is None


def test_pressure_trend_3h():
    """H13: (alti_delta * hPa_per_inhg) / hours_between."""
    d = dt.date(2025, 6, 15)
    hours = [18, 21]  # 06, 09 local
    alti_data = [[30.00, 29.94]]
    obs = _make_obs([d], hours, alti=alti_data)
    labels = _make_labels([d])

    result = build_features(obs, labels)
    # CP=23:00 sees both anchors
    row = result.filter(pl.col("cp") == "23:00")
    pt = row["pressure_trend_3h"].to_list()[0]
    expected = (29.94 - 30.00) * 33.8639 / 3.0  # delta over 3h
    assert pt is not None and abs(pt - expected) < 1e-4


def test_nocturnal_plateau_flag():
    """H18: flat morning + N wind + cloudy.

    Requires 3 temp anchors (06, 09, 12). With NZ morning CPs (UTC 20-23 D-1),
    anchor 12 (noon local, 00 UTC D) is always post-CP → not available.
    The feature correctly returns 0 for all morning CPs. This is physically
    correct: you can't observe noon temperature at 08:00-11:00 local.
    """
    d = dt.date(2025, 6, 15)
    hours = [18, 21]  # local 06, 09
    tmp_c = [[10, 10]]  # flat: range 0
    drct_data = [[350.0, 350.0]]  # N wind
    skyc1 = [["OVC", "OVC"]]  # cloudy
    obs = _make_obs([d], hours, tmp_c=tmp_c, drct=drct_data, skyc1=skyc1)
    labels = _make_labels([d])

    result = build_features(obs, labels)
    # anchor 12 (noon local) unavailable at all morning CPs → flag stays 0
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        val = row["nocturnal_plateau_flag"].to_list()[0]
        assert val == 0, f"{cp_str}: expected 0 (anchor 12 unavailable at morning CPs)"


def test_dewpoint_depression():
    """H4: mean dw_depression_c_int in pre-CP window."""
    d = dt.date(2025, 6, 15)
    hours = [16, 18, 19]  # all pre-CP
    tmp_c = [[10, 10, 10]]
    dwp_c = [[5, 6, 7]]  # depression: 5, 4, 3 → mean = 4.0
    obs = _make_obs([d], hours, tmp_c=tmp_c, dwp_c=dwp_c)
    labels = _make_labels([d])

    result = build_features(obs, labels)
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        dd = row["dewpoint_depression"].to_list()[0]
        assert dd is not None and abs(dd - 4.0) < 1e-6, (
            f"{cp_str}: expected 4.0, got {dd}"
        )


def test_tmax_dminus1():
    """H5: tmax_int from previous day's labels."""
    dates = [dt.date(2025, 6, 14), dt.date(2025, 6, 15)]
    hours = [16, 18, 19]
    obs = _make_obs(dates, hours)
    labels = _make_labels(dates, tmax=[18, 22])

    result = build_features(obs, labels)
    row = result.filter(
        (pl.col("date_local") == dates[1]) & (pl.col("cp") == "20:00")
    )
    assert row["tmax_dminus1"].to_list()[0] == 18


def test_wind_dir_change_s_to_n():
    """H8: early S wind + late N wind -> non-zero change.

    Requires late_obs (local >= 15), which is always post-CP for morning CPs
    (UTC 20-23 D-1).  The feature correctly returns 0.0 for all morning CPs —
    you cannot observe afternoon wind at 08:00-11:00 local.
    """
    d = dt.date(2025, 6, 15)
    hours = [18, 21]  # local 06, 09
    # early (06 local) = S wind, late (09 local) = N wind but late_obs needs >=15
    drct_data = [[180.0, 350.0]]
    obs = _make_obs([d], hours, drct=drct_data)
    labels = _make_labels([d])

    result = build_features(obs, labels)

    # No obs with local hour >= 15 pre-CP → wind_change stays 0.0
    for cp_str in _CP_SET:
        row = result.filter(pl.col("cp") == cp_str)
        change = row["wind_dir_change_s_to_n"].to_list()[0]
        assert change == 0.0, f"{cp_str}: expected 0.0 (no late obs pre-CP), got {change}"


def test_build_coverage_manifest():
    """build_coverage_manifest returns correct structure."""
    dates = [dt.date(2025, 6, 15), dt.date(2025, 6, 16)]
    obs = _make_obs(dates, [16, 18, 19])
    labels = _make_labels(dates)
    features = build_features(obs, labels)
    manifest = build_coverage_manifest(features)

    assert len(manifest) == len(SEED_HYPOTHESES)

    assert manifest["sst_maritime_cap"]["status"] == "BLOCKED"
    assert "reason" in manifest["sst_maritime_cap"]

    for hyp in SEED_HYPOTHESES:
        fc = hyp.feature_column
        if fc in BLOCKED_FEATURES:
            assert manifest[fc]["status"] == "BLOCKED"
        else:
            assert manifest[fc]["status"] == "computable", f"{fc} not computable"

    assert manifest["slope_3h"]["n_total"] == features.height
