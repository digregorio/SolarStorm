#!/usr/bin/env python3
"""Run one live forecast after refreshing METAR observations.

Wave 4.1 operational wrapper:
1. fetch recent METARs and merge with the historical CSV into a runtime CSV
2. run the forecast CLI against that refreshed CSV

This keeps the 30-minute METAR cadence explicit. A forecast run that skips this
step may be valid JSON but not CP-ready, as shown by
``feature_gap_to_cp_min``/``k_cp_available``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

DEFAULT_RUNTIME_CSV = Path("artifacts/state/NZWN_live_merged.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh live METAR, then run one forecast.")
    parser.add_argument("--date", required=True, type=str, help="Local target date YYYY-MM-DD.")
    parser.add_argument("--cp", required=True, type=str, help="Checkpoint hour, e.g. 20.")
    parser.add_argument("--model", default="empirical", choices=["empirical", "ridge", "auto"])
    parser.add_argument("--station-config", type=Path, default=Path("nzwn/config/station.yaml"))
    parser.add_argument("--csv", type=Path, default=Path("NZWN.csv"), help="Historical CSV.")
    parser.add_argument("--runtime-csv", type=Path, default=DEFAULT_RUNTIME_CSV)
    parser.add_argument("--hours", type=int, default=168, help="Live METAR lookback window.")
    parser.add_argument("--max-feature-gap-to-cp-min", type=int, default=90)
    parser.add_argument("--allow-stale", action="store_true", help="Return success even when freshness telemetry fails.")
    parser.add_argument("--timeout-s", type=int, default=120, help="Timeout for each subprocess call.")
    parser.add_argument("--nwp-root", type=Path, default=Path("artifacts/raw/nwp"))
    parser.add_argument("--serve-residuals", action="store_true")
    parser.add_argument("--nwp-fetch-live", action="store_true")
    return parser.parse_args()


def _run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout_s)


def main() -> int:
    args = parse_args()
    # Validate date early for clearer CLI failures.
    date.fromisoformat(args.date)
    args.runtime_csv.parent.mkdir(parents=True, exist_ok=True)

    ingest_cmd = [
        sys.executable,
        "-m",
        "tmax",
        "ingest-live",
        "--station-config",
        str(args.station_config),
        "--csv",
        str(args.csv),
        "--hours",
        str(args.hours),
        "--out-csv",
        str(args.runtime_csv),
    ]
    try:
        ingest = _run(ingest_cmd, timeout_s=args.timeout_s)
    except subprocess.TimeoutExpired as exc:
        sys.stderr.write(f"ingest-live timed out after {args.timeout_s}s: {exc}\n")
        return 124
    if ingest.returncode != 0:
        sys.stderr.write(ingest.stderr)
        sys.stdout.write(ingest.stdout)
        return ingest.returncode

    forecast_cmd = [
        sys.executable,
        "-m",
        "tmax",
        "forecast",
        "--station-config",
        str(args.station_config),
        "--csv",
        str(args.runtime_csv),
        "--date",
        args.date,
        "--cp",
        args.cp,
        "--model",
        args.model,
        "--nwp-root",
        str(args.nwp_root),
        "--dry-run",
    ]
    if args.serve_residuals:
        forecast_cmd.append("--serve-residuals")
    if args.nwp_fetch_live:
        forecast_cmd.append("--nwp-fetch-live")

    try:
        forecast = _run(forecast_cmd, timeout_s=args.timeout_s)
    except subprocess.TimeoutExpired as exc:
        sys.stderr.write(f"forecast timed out after {args.timeout_s}s: {exc}\n")
        return 124
    sys.stderr.write(forecast.stderr)
    sys.stdout.write(forecast.stdout)
    if forecast.returncode != 0:
        return forecast.returncode

    try:
        row = json.loads(forecast.stdout)
    except json.JSONDecodeError:
        return 1
    feature_gap = row.get("feature_gap_to_cp_min", row.get("feature_staleness_min"))
    stale = isinstance(feature_gap, int) and feature_gap > args.max_feature_gap_to_cp_min
    missing_kcp = row.get("k_cp_available") is not True
    if stale:
        sys.stderr.write(
            f"WARNING: forecast feature_gap_to_cp_min={feature_gap}; "
            f"max_feature_gap_to_cp_min={args.max_feature_gap_to_cp_min}.\n"
        )
    if missing_kcp:
        sys.stderr.write("WARNING: forecast k_cp_available=false; CP features are incomplete.\n")
    if (stale or missing_kcp) and not args.allow_stale:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
