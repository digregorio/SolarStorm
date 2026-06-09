"""Late-spike evidence pack for Onda 4."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl


def _empty_late_spikes() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.Utf8,
            "k_cp": pl.Int64,
            "tmax_int": pl.Int64,
            "delta_after_cp": pl.Int64,
            "tmax_hour": pl.Int64,
        }
    )


def find_late_spike_candidates(
    labels: pl.DataFrame,
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    min_delta: int = 1,
) -> pl.DataFrame:
    """Find days where final Tmax increased after a CP."""
    rows: list[dict] = []
    complete = labels.filter(pl.col("day_complete")) if "day_complete" in labels.columns else labels
    for row in complete.iter_rows(named=True):
        tmax = row.get("tmax_int")
        if tmax is None:
            continue
        for cp in cp_set:
            k_col = f"k_cp__cp_{cp.replace(':', '')}"
            k_cp = row.get(k_col)
            if k_cp is None:
                continue
            delta = int(tmax) - int(k_cp)
            if delta >= min_delta:
                rows.append(
                    {
                        "date_local": row["date_local"],
                        "cp": cp,
                        "k_cp": int(k_cp),
                        "tmax_int": int(tmax),
                        "delta_after_cp": delta,
                        "tmax_hour": row.get("tmax_hour"),
                    }
                )
    return pl.DataFrame(rows) if rows else _empty_late_spikes()


def write_late_spike_candidates(candidates: pl.DataFrame, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for row in candidates.iter_rows(named=True):
        record = dict(row)
        value = record.get("date_local")
        if hasattr(value, "isoformat"):
            record["date_local"] = value.isoformat()
        records.append(record)
    out.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
