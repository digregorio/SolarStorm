"""Walk-forward CV: expanding-window splits + recent-holdout windows."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass
class Split:
    name: str
    train_start: dt.date
    train_end: dt.date
    test_start: dt.date
    test_end: dt.date


def expanding_walk_forward_splits(
    *,
    history_start: dt.date,
    test_starts: list[dt.date],
    test_length_days: int = 365,
    min_train_days: int = 365,
    holdout_windows_days: list[int] | None = None,
) -> list[Split]:
    splits: list[Split] = []
    for ts in test_starts:
        train_start = history_start
        train_end = ts - dt.timedelta(days=1)
        # Annual test windows: if test_length is ~1 year and ts is Jan 1, use the
        # full calendar year (Dec 31) — leap-year-safe instead of +364 days (#22).
        if test_length_days >= 365 and ts.month == 1 and ts.day == 1:
            test_end = dt.date(ts.year + 1, 1, 1) - dt.timedelta(days=1)
        else:
            test_end = ts + dt.timedelta(days=test_length_days - 1)
        if (train_end - train_start).days + 1 < min_train_days:
            continue
        splits.append(Split(
            name=f"test_{ts.isoformat()}",
            train_start=train_start, train_end=train_end,
            test_start=ts, test_end=test_end,
        ))

    # Append holdout windows as additional splits anchored at a recent reference date
    if holdout_windows_days:
        today = dt.date.today()
        for window_days in holdout_windows_days:
            holdout_start = today - dt.timedelta(days=window_days)
            holdout_train_end = holdout_start - dt.timedelta(days=1)
            # Apply the same min_train_days guard as regular splits (#22).
            if (holdout_train_end - history_start).days + 1 < min_train_days:
                continue
            splits.append(Split(
                name=f"holdout_{window_days}d",
                train_start=history_start,
                train_end=holdout_train_end,
                test_start=holdout_start,
                test_end=today - dt.timedelta(days=1),
            ))

    return splits
