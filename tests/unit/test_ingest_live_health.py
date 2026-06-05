"""ingest-live health-check status logic (offline; fetch monkeypatched, no network)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest
import typer

import core.cli.ingest as ing
from core.ingest.iem_csv import ParseStats
from core.ingest.iem_csv import load_observations


def _live_frame(last_age_min: float, gap_min: float = 30.0, n: int = 6):
    now = datetime.now(timezone.utc)
    last = now - timedelta(minutes=last_age_min)
    ts = [last - timedelta(minutes=gap_min * i) for i in range(n)][::-1]
    return pl.DataFrame({
        "ts_utc": pl.Series(ts, dtype=pl.Datetime("us", time_zone="UTC")),
        "metar": ["METAR NZWN AUTO 15/08 Q1018"] * n,
        "tmp_c_int": pl.Series([15] * n, dtype=pl.Int32),
        "dq_tmp_c_int": ["ok"] * n,
    })


def _stats(n, fallback=0):
    return ParseStats(n_total=n, n_metar_present=n, n_metar_blank=0, n_parsed_ok=n - fallback,
                      n_parsed_imputed=fallback, n_parsed_missing=0, n_implausible=0)


def _run_capture(monkeypatch, live, stats, capsys):
    monkeypatch.setattr(ing, "fetch_observations", lambda *a, **k: (live, stats))
    import json
    from pathlib import Path
    try:
        ing.ingest_live(
            station_yaml=Path("nzwn/config/station.yaml"),
            csv=Path("does_not_exist.csv"), hours=96, out_csv=None,
        )
        code = 0
    except typer.Exit as e:
        code = e.exit_code
    return json.loads(capsys.readouterr().out), code


def test_status_ok_when_fresh_and_regular(monkeypatch, capsys):
    h, code = _run_capture(monkeypatch, _live_frame(20.0), _stats(6), capsys)
    assert h["status"] == "ok" and code == 0
    assert h["source"] == "aviationweather.gov" and h["max_gap_minutes_recent"] == 30.0


def test_status_stale_when_old_and_nonzero_exit(monkeypatch, capsys):
    h, code = _run_capture(monkeypatch, _live_frame(200.0), _stats(6), capsys)
    assert h["status"] == "stale" and code == 1


def test_status_degraded_on_big_gap(monkeypatch, capsys):
    h, code = _run_capture(monkeypatch, _live_frame(20.0, gap_min=120.0), _stats(6), capsys)
    assert h["status"] == "degraded" and code == 0


def test_out_csv_is_consumable_by_forecast_loader(monkeypatch, tmp_path, capsys):
    live = _live_frame(20.0)
    monkeypatch.setattr(ing, "fetch_observations", lambda *a, **k: (live, _stats(live.height)))
    out_csv = tmp_path / "live_merged.csv"

    ing.ingest_live(
        station_yaml=Path("nzwn/config/station.yaml"),
        csv=tmp_path / "missing_history.csv",
        hours=96,
        out_csv=out_csv,
    )

    obs, stats = load_observations(out_csv)
    assert "valid" in out_csv.read_text(encoding="utf-8").splitlines()[0]
    assert obs.height == live.height
    assert stats.fallback_rate == 0.0
    assert capsys.readouterr().out
