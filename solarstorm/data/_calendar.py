"""NZST/DST-aware calendar: local-day windows and checkpoint → UTC conversion."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo


def day_local_window(d: dt.date, tz_name: str) -> tuple[dt.datetime, dt.datetime]:
    """Return UTC [start, end) covering the full local day `d` in `tz_name`.

    On DST transition days the window may be 23h or 25h.
    """
    tz = ZoneInfo(tz_name)
    local_start = dt.datetime.combine(d, dt.time.min, tzinfo=tz)
    local_end = local_start + dt.timedelta(days=1)
    return local_start, local_end


def cp_to_utc(d: dt.date, cp_hhmm: str, tz_name: str) -> dt.datetime:
    """Convert a local-date + UTC checkpoint string to a UTC-aware datetime.

    The checkpoint hour is interpreted as **UTC** (METAR convention). For
    Wellington (UTC+12/13), UTC CPs 20:00-23:00 fall on UTC date D-1 and
    correspond to local morning (08-11 NZST / 09-12 NZDT) on date D.

    Args:
        d: Local date.
        cp_hhmm: Checkpoint hour in **UTC** (e.g. "20:00" = 20:00 UTC).
        tz_name: IANA timezone name.

    Returns:
        UTC-aware datetime for that checkpoint (tzinfo=UTC).

    Raises:
        ValueError: If no UTC date maps the CP to local date *d*.
    """
    tz = ZoneInfo(tz_name)
    hour = int(cp_hhmm.split(":")[0])

    # Try the CP at UTC hour on UTC date D, then D-1.  For NZ tz offsets
    # the CP almost always lands on D-1, but we try both to stay generic.
    utc_dt = dt.datetime(d.year, d.month, d.day, hour, 0, 0, tzinfo=dt.UTC)
    if utc_dt.astimezone(tz).date() == d:
        return utc_dt

    utc_dt = utc_dt - dt.timedelta(days=1)
    if utc_dt.astimezone(tz).date() == d:
        return utc_dt

    raise ValueError(
        f"CP {cp_hhmm} UTC cannot be mapped to local date {d} in {tz_name}"
    )
