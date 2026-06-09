"""IEM ASOS client — backfill 10+ years of NZWN METAR from Iowa Environmental Mesonet."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import polars as pl

_IEM_URL = (
    "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
    "?station={station}&data=all&year1={y1}&month1={m1}&day1={d1}"
    "&year2={y2}&month2={m2}&day2={d2}&tz=Etc/UTC&format=comma"
    "&latlon=no&elev=no&missing=empty&trace=0.0001"
    "&direct=no&report_type=3&report_type=4"
)
_CACHE_VERSION = "1"


def _cache_key(station: str, start: dt.date, end: dt.date) -> str:
    raw = f"{station}_{start.isoformat()}_{end.isoformat()}_v{_CACHE_VERSION}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _fetch_iem_raw(station: str, start: dt.date, end: dt.date) -> pl.DataFrame:
    """Fetch raw CSV from IEM ASOS API."""
    url = _IEM_URL.format(
        station=station, y1=start.year, m1=start.month, d1=start.day,
        y2=end.year, m2=end.month, d2=end.day,
    )
    return pl.read_csv(
        url, null_values=["", "M", "MM"], comment_prefix="#",
        schema_overrides={
            "valid": pl.Utf8, "tmpf": pl.Float64, "dwpf": pl.Float64,
            "sknt": pl.Float64, "drct": pl.Float64, "alti": pl.Float64,
            "p01i": pl.Float64, "metar": pl.Utf8,
            "skyc1": pl.Utf8, "skyc2": pl.Utf8, "skyc3": pl.Utf8, "skyc4": pl.Utf8,
            "skyl1": pl.Utf8, "skyl2": pl.Utf8, "skyl3": pl.Utf8, "skyl4": pl.Utf8,
            "wxcodes": pl.Utf8,
        },
    )


def fetch_iem_asos(
    station: str,
    start: dt.date,
    end: dt.date,
    *,
    cache_dir: Path | None = None,
) -> pl.DataFrame:
    """Fetch IEM ASOS observations for `station` from `start` to `end` inclusive.

    Caches results to `cache_dir` when provided, keyed by station + date range.
    """
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = _cache_key(station, start, end)
        cache_path = cache_dir / f"{key}.parquet"
        meta_path = cache_dir / f"{key}.json"
        if cache_path.exists() and meta_path.exists():
            return pl.read_parquet(cache_path)

    df = _fetch_iem_raw(station, start, end)
    if df.schema["valid"] == pl.Utf8:
        df = df.with_columns(
            pl.col("valid").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M", strict=False)
            .dt.replace_time_zone("UTC")
        )

    if cache_dir is not None:
        df.write_parquet(cache_path)
        meta_path.write_text(json.dumps({
            "station": station, "start": start.isoformat(), "end": end.isoformat(),
        }))

    return df
