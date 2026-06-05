"""CLI: ingest-history + build-features."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import polars as pl
import typer

from core.contracts.station import load_station_config
from core.features.builder import build_cp_features
from core.ingest.iem_csv import load_observations
from core.ingest.metar_live import fetch_observations, merge_observations
from core.ingest.snapshot import snapshot_csv_by_local_day
from core.io.hashing import sha256_file
from core.io.logging import log_event, new_run_id


def ingest_history(
    csv: Path = typer.Option(..., "--csv", help="Path to NZWN.csv (IEM ASOS)."),
    station_yaml: Path = typer.Option(
        Path("nzwn/config/station.yaml"), "--station-config", help="Station YAML"
    ),
    out_root: Path = typer.Option(
        Path("artifacts/raw/metar"), "--out-root", help="Snapshot root."
    ),
) -> None:
    """Snapshot raw METAR by local day with SHA256 manifest (REQ-DAT-1)."""
    new_run_id()
    cfg = load_station_config(station_yaml)
    log_event("ingest", "ingest.start", extra={"csv": str(csv), "station": cfg.icao})
    obs, stats = load_observations(
        csv,
        tmp_min_c=cfg.tmp_c_int_plausibility.min,
        tmp_max_c=cfg.tmp_c_int_plausibility.max,
    )
    src_sha = sha256_file(csv)
    hashes = snapshot_csv_by_local_day(
        obs, station=cfg.icao, tz_name=cfg.tz, out_root=out_root, source_csv_sha256=src_sha
    )
    log_event(
        "ingest",
        "ingest.done",
        extra={
            "n_rows": obs.height,
            "n_dates": len(hashes),
            "parse_stats": stats.to_dict(),
            "source_sha256": src_sha,
        },
    )
    typer.echo(f"OK: {obs.height} rows, {len(hashes)} dates, fallback_rate={stats.fallback_rate:.5f}")


def build_features(
    station_yaml: Path = typer.Option(Path("nzwn/config/station.yaml"), "--station-config"),
    target_date: str = typer.Option(..., "--date", help="Local date YYYY-MM-DD"),
    cp: str = typer.Option(..., "--cp", help="CP HH (integer hour, REQ-CON-6)"),
    csv: Path = typer.Option(Path("NZWN.csv"), "--csv"),
) -> None:
    """Build the per-CP feature row for one date."""
    new_run_id()
    cfg = load_station_config(station_yaml)
    cp_hhmm = f"{int(cp):02d}:00"
    if cp_hhmm not in cfg.cp_set_utc:
        raise typer.BadParameter(f"CP {cp_hhmm} not in CP_SET {cfg.cp_set_utc} (REQ-CON-6).")
    d = date.fromisoformat(target_date)
    obs, _ = load_observations(
        csv,
        tmp_min_c=cfg.tmp_c_int_plausibility.min,
        tmp_max_c=cfg.tmp_c_int_plausibility.max,
    )
    # REQ-DAT-2 + design 4.5: D-1 features need the label panel.
    from core.labels.tmax import build_tmax_labels

    labels = build_tmax_labels(obs, tz_name=cfg.tz, cp_set_utc=cfg.cp_set_utc)
    feats = build_cp_features(
        obs, date_local=d, cp_hhmm=cp_hhmm, tz_name=cfg.tz, labels=labels
    )
    log_event(
        "features",
        "features.built",
        cp_utc=feats.cp_utc,
        cp_local=feats.cp_local,
        tz_name=cfg.tz,
        extra={
            "date_local": d.isoformat(),
            "feature_max_ts": feats.feature_max_ts_utc.isoformat(),
            "tmax_d_minus_1_int": feats.features.get("tmax_d_minus_1_int"),
        },
    )
    typer.echo(
        f"OK: cp_utc={feats.cp_utc.isoformat()} "
        f"feature_max_ts={feats.feature_max_ts_utc.isoformat()} "
        f"tmax_d_minus_1_int={feats.features.get('tmax_d_minus_1_int')}"
    )


def ingest_live(
    station_yaml: Path = typer.Option(Path("nzwn/config/station.yaml"), "--station-config"),
    csv: Path = typer.Option(Path("NZWN.csv"), "--csv", help="Historical IEM CSV to merge with."),
    hours: int = typer.Option(96, "--hours", help="Lookback window of live METAR."),
    out_csv: Path | None = typer.Option(None, "--out-csv", help="Optional merged CSV path."),
) -> None:
    """Fetch CURRENT METAR (aviationweather.gov) + merge with history; emit a health-check.

    Live obs share the historical schema (one source of truth for the integer temperature),
    so the label/feature/forecast path runs on fresh data unchanged. Prints a JSON health-check
    (station/source/coverage/last_obs/gap/status) so a cron/scheduler can call ``ingest-live``
    and just check ``status``. With ``--out-csv`` the merged frame is also written.
    """
    import json as _json
    from datetime import datetime, timezone

    new_run_id()
    cfg = load_station_config(station_yaml)
    tmin, tmax = cfg.tmp_c_int_plausibility.min, cfg.tmp_c_int_plausibility.max
    live, stats = fetch_observations(cfg.icao, hours=hours, tmp_min_c=tmin, tmp_max_c=tmax)
    n_hist = 0
    n_dups = 0
    if csv.exists():
        hist, _ = load_observations(csv, tmp_min_c=tmin, tmp_max_c=tmax)
        n_hist = hist.height
        hist_ts = set(hist["ts_utc"].to_list())
        n_dups = sum(1 for t in live["ts_utc"].to_list() if t in hist_ts)
        merged = merge_observations(hist, live)
    else:
        merged = live.sort("ts_utc")

    # Largest gap (minutes) between consecutive live obs in the fetched window.
    lts = live["ts_utc"].to_list()
    max_gap = max(((lts[i + 1] - lts[i]).total_seconds() / 60.0 for i in range(len(lts) - 1)),
                  default=0.0)
    last_obs = lts[-1] if lts else None
    now = datetime.now(timezone.utc)
    staleness_min = (now - last_obs).total_seconds() / 60.0 if last_obs else None
    # Two distinct fallback thresholds (update.txt 2026-05-30): an operational WARN bar (5%) for
    # the live health-check, and the much stricter historical CONTRACT KILL bar (0.5%, REQ-CON-8).
    # The contract-kill is surfaced as a flag but does NOT itself fail the live cron (it is a
    # data-quality contract signal, not a feed-freshness signal).
    fallback_warn_threshold = 0.05
    fallback_contract_kill_threshold = 0.005
    contract_kill = stats.fallback_rate > fallback_contract_kill_threshold
    # status: ok if fresh (<90 min) AND no big gap (<=60 min) AND fallback under the WARN bar.
    # degraded = ALERT (gap or warn-level fallback), NOT a hard failure -> exit 0 so the cron
    # keeps the feed but an operator/trading layer can choose to block on it. stale/no_data =
    # hard failure -> non-zero exit.
    if last_obs is None:
        status = "no_data"
    elif staleness_min is not None and staleness_min > 90.0:
        status = "stale"
    elif max_gap > 60.0 or stats.fallback_rate > fallback_warn_threshold:
        status = "degraded"
    else:
        status = "ok"

    health = {
        "station": cfg.icao,
        "source": "aviationweather.gov",
        "n_live_rows": int(live.height),
        "n_merged_rows": int(merged.height),
        "n_hist_rows": int(n_hist),
        "last_obs_ts_utc": last_obs.isoformat() if last_obs else None,
        "staleness_minutes": None if staleness_min is None else round(staleness_min, 1),
        "fallback_rate_live": round(stats.fallback_rate, 6),
        "fallback_rate_live_warn_threshold": fallback_warn_threshold,
        "fallback_rate_contract_kill_threshold": fallback_contract_kill_threshold,
        "fallback_contract_kill_exceeded": bool(contract_kill),
        "n_duplicates_replaced": int(n_dups),
        "max_gap_minutes_recent": round(max_gap, 1),
        "status": status,
        "status_semantics": "ok=healthy; degraded=ALERT not hard-fail (exit 0); stale/no_data=hard-fail (exit 1)",
    }
    log_event("ingest", "ingest.live", extra=health)
    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        out = merged
        if "valid" not in out.columns:
            out = out.with_columns(
                pl.col("ts_utc")
                .dt.strftime("%Y-%m-%d %H:%M")
                .alias("valid")
            )
        # Keep the runtime artifact in the same consumable schema as the IEM
        # history CSV. ``forecast --csv`` reads ``valid`` and reparses METAR as
        # the integer-temperature source of truth; writing only ``ts_utc,metar``
        # makes the live refresh unusable by the forecast command.
        iem_cols = (
            "station", "valid", "tmpf", "dwpf", "relh", "drct", "sknt", "p01i",
            "alti", "mslp", "vsby", "gust", "skyc1", "skyc2", "skyc3", "skyc4",
            "skyl1", "skyl2", "skyl3", "skyl4", "wxcodes", "ice_accretion_1hr",
            "ice_accretion_3hr", "ice_accretion_6hr", "peak_wind_gust",
            "peak_wind_drct", "peak_wind_time", "feel", "metar", "snowdepth",
        )
        write_cols = [c for c in iem_cols if c in out.columns]
        if "valid" not in write_cols or "metar" not in write_cols:
            raise typer.BadParameter("Merged live observations must contain valid and metar columns.")
        out.select(write_cols).write_csv(out_csv)
    typer.echo(_json.dumps(health, ensure_ascii=True, sort_keys=True, indent=2))
    if status in ("no_data", "stale"):
        raise typer.Exit(code=1)


__all__ = ["ingest_history", "build_features", "ingest_live"]
