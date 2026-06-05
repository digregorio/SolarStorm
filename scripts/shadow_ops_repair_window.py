#!/usr/bin/env python3
"""Repair missing Shadow Ops dates/CPs for a readiness window.

The repair loop is deliberately narrow:
- compute readiness with the same code as the dashboard
- read missing_inventory
- rerun the ShadowRunner for affected dates only
- optionally regenerate the readiness report after repair

No live trading is enabled. If --with-decisions is used, ShadowRunner invokes
the decide CLI with --dry-run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Add project root to path for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ops.shadow_runner import (
    DEFAULT_CPS,
    DEFAULT_SHADOW_ROOT,
    ShadowRunResult,
    ShadowRunner,
    ShadowRunnerConfig,
)
from live_shadow_readiness_report import compute_metrics


DEFAULT_REPORT_ROOT = Path("reports/live_shadow")


@dataclass(frozen=True)
class RepairPlan:
    """Dates selected for repair from readiness missing_inventory."""

    start_date: date
    end_date: date
    dates: tuple[date, ...]
    missing_inventory: tuple[tuple[str, tuple[int, ...]], ...]

    @property
    def n_dates(self) -> int:
        return len(self.dates)


@dataclass(frozen=True)
class RepairSummary:
    """Summary of a repair-window execution."""

    plan: RepairPlan
    dry_run: bool
    with_decisions: bool
    results: tuple[ShadowRunResult, ...] = field(default_factory=tuple)

    @property
    def forecast_failures(self) -> int:
        return sum(r.n_failed for r in self.results)

    @property
    def decision_failures(self) -> int:
        return sum(r.n_decision_failed for r in self.results)

    @property
    def repaired_dates(self) -> int:
        return sum(1 for r in self.results if not r.skipped and r.output_path is not None)


def build_repair_plan(
    shadow_root: Path,
    start_date: date,
    end_date: date,
    expected_cps: tuple[int, ...] = DEFAULT_CPS,
) -> RepairPlan:
    """Build a repair plan from readiness missing_inventory."""
    metrics = compute_metrics(
        shadow_root=shadow_root,
        start_date=start_date,
        end_date=end_date,
        expected_cps=expected_cps,
    )
    missing_inventory = tuple(
        (date_iso, tuple(missing_cps))
        for date_iso, missing_cps in metrics.missing_inventory
    )
    dates = tuple(
        sorted({date.fromisoformat(date_iso) for date_iso, _ in missing_inventory})
    )
    return RepairPlan(
        start_date=start_date,
        end_date=end_date,
        dates=dates,
        missing_inventory=missing_inventory,
    )


def run_repair_plan(
    plan: RepairPlan,
    config: ShadowRunnerConfig,
    dry_run: bool,
) -> RepairSummary:
    """Execute a repair plan, or return the plan unchanged in dry-run mode."""
    if dry_run or not plan.dates:
        return RepairSummary(
            plan=plan,
            dry_run=dry_run,
            with_decisions=config.with_decisions,
        )

    runner = ShadowRunner(config)
    results = tuple(runner.run_date(target_date) for target_date in plan.dates)
    return RepairSummary(
        plan=plan,
        dry_run=False,
        with_decisions=config.with_decisions,
        results=results,
    )


def render_summary_json(summary: RepairSummary) -> dict:
    """Render a repair summary to JSON."""
    return {
        "task": "phase5.1-wave3-shadow-ops-repair-window",
        "start_date": summary.plan.start_date.isoformat(),
        "end_date": summary.plan.end_date.isoformat(),
        "dry_run": summary.dry_run,
        "with_decisions": summary.with_decisions,
        "planned_dates": [d.isoformat() for d in summary.plan.dates],
        "planned_missing_inventory": [
            {"date_local": date_iso, "missing_cps": list(missing_cps)}
            for date_iso, missing_cps in summary.plan.missing_inventory
        ],
        "repaired_dates": summary.repaired_dates,
        "forecast_failures": summary.forecast_failures,
        "decision_failures": summary.decision_failures,
        "results": [
            {
                "date_local": r.date_local.isoformat(),
                "skipped": r.skipped,
                "output_path": str(r.output_path) if r.output_path else None,
                "forecast_success": r.n_success,
                "forecast_failures": r.n_failed,
                "decision_failures": r.n_decision_failed,
            }
            for r in summary.results
        ],
    }


def render_summary_markdown(summary: RepairSummary) -> str:
    """Render a repair summary to Markdown."""
    lines = [
        "# Shadow Ops Repair Window v1",
        "",
        f"- window: {summary.plan.start_date.isoformat()} to {summary.plan.end_date.isoformat()}",
        f"- dry_run: {summary.dry_run}",
        f"- with_decisions: {summary.with_decisions}",
        f"- planned_dates: {summary.plan.n_dates}",
        f"- repaired_dates: {summary.repaired_dates}",
        f"- forecast_failures: {summary.forecast_failures}",
        f"- decision_failures: {summary.decision_failures}",
        "",
        "## Missing Inventory",
        "",
    ]
    if summary.plan.missing_inventory:
        for date_iso, missing_cps in summary.plan.missing_inventory:
            lines.append(f"- {date_iso}: missing CPs {list(missing_cps)}")
    else:
        lines.append("- none")

    lines.extend(["", "## Repair Results", ""])
    if summary.results:
        for result in summary.results:
            lines.append(
                f"- {result.date_local.isoformat()}: forecasts_ok={result.n_success}, "
                f"forecast_failures={result.n_failed}, decision_failures={result.n_decision_failed}"
            )
    else:
        lines.append("- no repair executed")
    return "\n".join(lines) + "\n"


def _parse_cps(raw: str) -> tuple[int, ...]:
    cps = tuple(int(c.strip()) for c in raw.split(",") if c.strip())
    if not cps:
        raise argparse.ArgumentTypeError("At least one CP is required.")
    return cps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair missing Shadow Ops dates/CPs over a readiness window."
    )
    parser.add_argument("--start", required=True, type=str, help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end", required=True, type=str, help="End date (YYYY-MM-DD).")
    parser.add_argument(
        "--shadow-root",
        type=Path,
        default=DEFAULT_SHADOW_ROOT,
        help=f"Shadow ops root (default: {DEFAULT_SHADOW_ROOT}).",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=DEFAULT_REPORT_ROOT,
        help=f"Report output root (default: {DEFAULT_REPORT_ROOT}).",
    )
    parser.add_argument(
        "--cps",
        type=_parse_cps,
        default=DEFAULT_CPS,
        help=f"Comma-separated checkpoint hours (default: {DEFAULT_CPS}).",
    )
    parser.add_argument("--force", action="store_true", help="Force rerun selected dates.")
    parser.add_argument(
        "--with-decisions",
        action="store_true",
        help="Also regenerate dry-run decision artifacts for selected dates.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the repair plan without executing forecasts.",
    )
    parser.add_argument(
        "--regenerate-readiness",
        action="store_true",
        help="Run live_shadow_readiness_report.py after repair.",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Subprocess timeout seconds.")
    parser.add_argument(
        "--station-config",
        type=Path,
        default=Path("nzwn/config/station.yaml"),
        help="Station config for decide.",
    )
    parser.add_argument("--csv", type=Path, default=Path("NZWN.csv"), help="Observations CSV.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    if start_date > end_date:
        print("ERROR: --start must be <= --end", file=sys.stderr)
        return 2

    plan = build_repair_plan(args.shadow_root, start_date, end_date, args.cps)
    config = ShadowRunnerConfig(
        shadow_root=args.shadow_root,
        cps=args.cps,
        force=args.force,
        timeout_s=args.timeout,
        with_decisions=args.with_decisions,
        station_yaml=args.station_config,
        csv_path=args.csv,
    )
    summary = run_repair_plan(plan, config, args.dry_run)

    args.out_root.mkdir(parents=True, exist_ok=True)
    suffix = f"{start_date.isoformat()}_{end_date.isoformat()}"
    json_path = args.out_root / f"shadow_repair_{suffix}.json"
    md_path = args.out_root / f"shadow_repair_{suffix}.md"
    with open(json_path, "w", encoding="ascii") as fh:
        json.dump(render_summary_json(summary), fh, ensure_ascii=True, indent=2, sort_keys=True)
    with open(md_path, "w", encoding="ascii") as fh:
        fh.write(render_summary_markdown(summary))

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")

    if args.regenerate_readiness:
        cmd = [
            sys.executable,
            str(Path(__file__).resolve().parent / "live_shadow_readiness_report.py"),
            "--shadow-root",
            str(args.shadow_root),
            "--out-root",
            str(args.out_root),
            "--start",
            start_date.isoformat(),
            "--end",
            end_date.isoformat(),
        ]
        subprocess.run(cmd, check=False)

    if summary.forecast_failures or summary.decision_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
