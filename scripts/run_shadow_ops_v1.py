#!/usr/bin/env python3
"""Shadow Ops Runner CLI (Phase 5.1).

Runs forecasts for CP20-23 over a date range and writes structured JSONL output.

Usage:
    python scripts/run_shadow_ops_v1.py --start 2025-01-01 --end 2025-01-07
    python scripts/run_shadow_ops_v1.py --date 2025-01-15 --force
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

# Add project root to path for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ops.shadow_runner import (
    DEFAULT_CPS,
    DEFAULT_SHADOW_ROOT,
    ShadowRunner,
    ShadowRunnerConfig,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Shadow Ops Runner: execute forecasts for CP20-23 over date ranges."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--date",
        type=str,
        help="Single date to run (YYYY-MM-DD).",
    )
    group.add_argument(
        "--start",
        type=str,
        help="Start date for range (YYYY-MM-DD). Requires --end.",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date for range (YYYY-MM-DD, inclusive).",
    )
    parser.add_argument(
        "--shadow-root",
        type=Path,
        default=DEFAULT_SHADOW_ROOT,
        help=f"Root directory for shadow ops output (default: {DEFAULT_SHADOW_ROOT}).",
    )
    parser.add_argument(
        "--cps",
        type=str,
        default=",".join(str(c) for c in DEFAULT_CPS),
        help=f"Comma-separated checkpoint hours (default: {DEFAULT_CPS}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Subprocess timeout in seconds (default: 120).",
    )
    parser.add_argument(
        "--with-decisions",
        action="store_true",
        help="Generate decision artifacts after forecasts (Wave 1). Always uses --dry-run, never places live orders.",
    )
    parser.add_argument(
        "--station-config",
        type=Path,
        default=Path("nzwn/config/station.yaml"),
        help="Station config for decide (default: nzwn/config/station.yaml).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("NZWN.csv"),
        help="Observations CSV for forecast and decide (default: NZWN.csv).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Parse dates.
    if args.date:
        start = end = date.fromisoformat(args.date)
    else:
        if not args.end:
            print("ERROR: --start requires --end", file=sys.stderr)
            return 2
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)

    # Parse CPs.
    cps = tuple(int(c.strip()) for c in args.cps.split(","))

    config = ShadowRunnerConfig(
        shadow_root=args.shadow_root,
        cps=cps,
        force=args.force,
        timeout_s=args.timeout,
        with_decisions=args.with_decisions,
        station_yaml=args.station_config,
        csv_path=args.csv,
    )

    runner = ShadowRunner(config)
    results = runner.run_range(start, end)

    # Print summary.
    total_success = sum(r.n_success for r in results)
    total_failed = sum(r.n_failed for r in results)
    total_skipped = sum(1 for r in results if r.skipped)
    total_decision_failed = sum(r.n_decision_failed for r in results)

    print(f"Shadow Ops Run Complete")
    print(f"  Dates: {start} .. {end} ({len(results)} days)")
    print(f"  Success: {total_success} forecasts")
    print(f"  Failed: {total_failed} forecast checkpoints")
    print(f"  Skipped: {total_skipped} dates (already exist)")
    if args.with_decisions:
        print(f"  Decision failures: {total_decision_failed}")

    # Print forecast errors if any.
    for r in results:
        if r.errors:
            print(f"\n  {r.date_local} forecast errors:")
            for cp, err in r.errors:
                print(f"    CP{cp}: {err}")

    # Print decision errors if any.
    if args.with_decisions:
        for r in results:
            if r.decision_errors:
                print(f"\n  {r.date_local} decision errors:")
                for cp, err in r.decision_errors:
                    print(f"    CP{cp}: {err}")

    return 0 if total_failed == 0 and total_decision_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
