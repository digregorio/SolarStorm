#!/usr/bin/env python3
"""Live Shadow Readiness Report (Phase 5.1).

Reads JSONL forecasts from shadow ops and computes readiness metrics.

Usage:
    python scripts/live_shadow_readiness_report.py --shadow-root artifacts/shadow_ops
    python scripts/live_shadow_readiness_report.py --start 2025-01-01 --end 2025-01-31
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# Add project root to path for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ops.schemas import REQUIRED_FORECAST_FIELDS, ShadowSchemaError, validate_record


# Causal safety margin: matches select_nwp_v1 cutoff (run_time <= cp_utc - 60min).
# A forecast is considered "leaked" if nwp_run_time > cp_utc - SAFETY_MARGIN.
CAUSAL_SAFETY_MARGIN = timedelta(minutes=60)


# --- Frozen gates (defined BEFORE reading results) ---------------------------

GATE_COMPLETENESS_REQUIRED = 1.0  # 100% of expected records present
GATE_LEAKAGE_VIOLATIONS_MAX = 0  # Zero tolerance for leakage
GATE_FALLBACK_CLASSIFIED_REQUIRED = 1.0  # 100% of fallbacks classified


@dataclass
class ReadinessMetrics:
    """Computed readiness metrics from shadow ops data."""

    # Completeness
    expected_records: int = 0
    found_records: int = 0
    missing_records: int = 0

    @property
    def completeness(self) -> float:
        return self.found_records / self.expected_records if self.expected_records > 0 else 0.0

    # Leakage
    leakage_violations: int = 0

    # Fallback stats
    total_with_routing: int = 0
    fallback_used_count: int = 0
    fallback_reasons_classified: int = 0
    fallback_reasons_unclassified: int = 0

    @property
    def fallback_rate(self) -> float:
        return self.fallback_used_count / self.total_with_routing if self.total_with_routing > 0 else 0.0

    @property
    def fallback_classified_rate(self) -> float:
        total_fb = self.fallback_reasons_classified + self.fallback_reasons_unclassified
        return self.fallback_reasons_classified / total_fb if total_fb > 0 else 1.0

    # NWP telemetry (ECMWF)
    ecmwf_cache_hit_count: int = 0
    ecmwf_fetch_success_count: int = 0
    ecmwf_cache_repair_count: int = 0
    ecmwf_fetch_error_count: int = 0

    # NWP telemetry (GFS)
    gfs_cache_hit_count: int = 0
    gfs_fetch_success_count: int = 0
    gfs_cache_repair_count: int = 0
    gfs_fetch_error_count: int = 0

    # run_age_h stats
    run_age_h_values: list[float] = field(default_factory=list)

    @property
    def run_age_h_p50(self) -> float | None:
        return _percentile(self.run_age_h_values, 50)

    @property
    def run_age_h_p95(self) -> float | None:
        return _percentile(self.run_age_h_values, 95)

    # valid_time_delta_h stats
    valid_time_delta_h_values: list[float] = field(default_factory=list)

    @property
    def valid_time_delta_h_mean(self) -> float | None:
        if not self.valid_time_delta_h_values:
            return None
        return sum(self.valid_time_delta_h_values) / len(self.valid_time_delta_h_values)

    # Residual served stats (CP20-22)
    residual_served_cp20_22_count: int = 0
    total_cp20_22_count: int = 0

    # Date-level completeness
    dates_expected: int = 0
    dates_found: int = 0
    dates_complete: int = 0  # dates with all expected CPs present and valid

    @property
    def residual_served_rate_cp20_22(self) -> float:
        return (
            self.residual_served_cp20_22_count / self.total_cp20_22_count
            if self.total_cp20_22_count > 0
            else 0.0
        )

    # Fallback reason distribution
    fallback_reason_counts: dict[str, int] = field(default_factory=dict)

    # Odds stats (if decisions were run)
    odds_available_count: int = 0
    odds_unavailable_count: int = 0

    # Duplicate/anomaly tracking (P1 fix: duplicates don't count as coverage)
    duplicate_cp_records: int = 0

    # CPs outside the contract set (e.g. CP19 when only 20-23 are expected)
    unexpected_cp_records: int = 0

    # CP coverage per date (for per-date completeness audit)
    cp_coverage_per_date: dict[str, int] = field(default_factory=dict)

    # Wave 2: missing date/CP inventory.
    missing_inventory: list[tuple[str, list[int]]] = field(default_factory=list)

    # Wave 2: fallback distribution by CP and by model.
    fallback_by_cp: dict[int, int] = field(default_factory=dict)
    fallback_by_model: dict[str, int] = field(default_factory=dict)

    # Wave 2: NWP fetch/cache summary by endpoint (ECMWF / GFS).
    nwp_endpoint_summary: dict[str, dict[str, int]] = field(default_factory=dict)


def _check_leakage(cp_utc_str: str, routing: dict) -> bool:
    """Return True if the record has leakage (NWP run_time > cp_utc - safety margin).

    Leakage = using NWP data from a run that started AFTER the causal cutoff.
    The real causal selector (select_nwp_v1) requires:
        run_time_utc <= cp_utc - SAFETY_MARGIN_DEFAULT (60 min)

    So a run that started 30 minutes before CP is non-causal by the operational
    contract, even though it's before CP itself.

    Checks all NWP run time fields:
    - nwp_run_time_utc (generic)
    - ecmwf_selected_run_time
    - gfs_selected_run_time
    """
    cp_utc = None
    try:
        cp_utc = datetime.fromisoformat(cp_utc_str)
    except (ValueError, TypeError):
        return False

    # Causal cutoff: cp_utc - 60 min safety margin.
    causal_cutoff = cp_utc - CAUSAL_SAFETY_MARGIN

    # Check all possible NWP run time fields.
    run_time_fields = (
        "nwp_run_time_utc",
        "ecmwf_selected_run_time",
        "gfs_selected_run_time",
    )

    for field_name in run_time_fields:
        nwp_run_time_str = routing.get(field_name)
        if not nwp_run_time_str:
            continue
        try:
            nwp_run_time = datetime.fromisoformat(str(nwp_run_time_str))
            # Normalize tzinfo for comparison.
            if cp_utc.tzinfo is not None and nwp_run_time.tzinfo is None:
                nwp_run_time = nwp_run_time.replace(tzinfo=cp_utc.tzinfo)
            elif cp_utc.tzinfo is None and nwp_run_time.tzinfo is not None:
                cutoff_tz = nwp_run_time.tzinfo
                causal_cutoff = cp_utc.replace(tzinfo=cutoff_tz) - CAUSAL_SAFETY_MARGIN
            if nwp_run_time > causal_cutoff:
                return True  # Leakage detected from this field.
        except (ValueError, TypeError):
            continue  # Unparseable -> skip this field.

    return False  # No leakage found.


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_vals) else f
    d = k - f
    return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])


def _extract_cp_hour(cp_utc: str) -> int | None:
    """Extract hour from cp_utc ISO string."""
    try:
        if "T" in cp_utc:
            time_part = cp_utc.split("T")[1]
            return int(time_part.split(":")[0])
    except (IndexError, ValueError):
        pass
    return None


def compute_metrics(
    shadow_root: Path,
    start_date: date | None = None,
    end_date: date | None = None,
    expected_cps: tuple[int, ...] = (20, 21, 22, 23),
) -> ReadinessMetrics:
    """Compute readiness metrics from shadow ops JSONL files.

    Args:
        shadow_root: Root directory containing forecasts/ subdirectory.
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        expected_cps: Expected checkpoints per date.

    Returns:
        ReadinessMetrics with computed stats.
    """
    metrics = ReadinessMetrics()
    forecasts_dir = shadow_root / "forecasts"
    decisions_dir = shadow_root / "decisions"

    # --- Compute expected records from date range (not just existing files) ----
    expected_dates: set[date] = set()
    if start_date is not None and end_date is not None:
        # Window-based: every date in [start, end] is expected.
        current = start_date
        while current <= end_date:
            expected_dates.add(current)
            metrics.dates_expected += 1
            metrics.expected_records += len(expected_cps)
            current = date.fromordinal(current.toordinal() + 1)
    elif not forecasts_dir.exists():
        return metrics

    # --- Scan existing JSONL files ---------------------------------------------
    jsonl_files = sorted(forecasts_dir.glob("*.jsonl")) if forecasts_dir.exists() else []
    seen_dates: set[date] = set()

    for jsonl_path in jsonl_files:
        # Parse date from filename.
        try:
            file_date = date.fromisoformat(jsonl_path.stem)
        except ValueError:
            continue

        # Apply date filters.
        if start_date and file_date < start_date:
            continue
        if end_date and file_date > end_date:
            continue
        seen_dates.add(file_date)

        # If no window was given, count expected from existing files.
        if start_date is None or end_date is None:
            metrics.dates_expected += 1
            metrics.expected_records += len(expected_cps)

        # Track valid CPs found for this date (for per-date completeness).
        # Use set to count unique CPs only; duplicates are anomalies, not coverage.
        date_valid_cps: set[int] = set()
        # Read and validate records.
        with open(jsonl_path, "r", encoding="ascii") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    record = validate_record(raw)

                    # Extract routing telemetry.
                    routing = record.routing or {}

                    # --- CP uniqueness check (P1 fix) ---
                    # Only count as found if this is a NEW unique CP for this date
                    # AND the CP is in the expected set.
                    cp_hour = _extract_cp_hour(record.cp_utc)
                    if cp_hour is not None:
                        if cp_hour not in expected_cps:
                            metrics.unexpected_cp_records += 1
                        elif cp_hour in date_valid_cps:
                            # Duplicate CP = anomaly, don't count as coverage.
                            metrics.duplicate_cp_records += 1
                        else:
                            date_valid_cps.add(cp_hour)
                            metrics.found_records += 1  # Only unique (date, cp) pairs.
                    # If we can't extract cp_hour, still validate but don't count.

                    # Check fallback.
                    if routing.get("fallback_used"):
                        metrics.fallback_used_count += 1
                        # Wave 2: fallback by CP.
                        if cp_hour is not None:
                            metrics.fallback_by_cp[cp_hour] = (
                                metrics.fallback_by_cp.get(cp_hour, 0) + 1
                            )
                        # Wave 2: fallback by model.
                        served = routing.get("served_model", "unknown")
                        metrics.fallback_by_model[served] = (
                            metrics.fallback_by_model.get(served, 0) + 1
                        )
                        reason = routing.get("fallback_reason")
                        if reason:
                            metrics.fallback_reasons_classified += 1
                            metrics.fallback_reason_counts[reason] = (
                                metrics.fallback_reason_counts.get(reason, 0) + 1
                            )
                        else:
                            metrics.fallback_reasons_unclassified += 1

                    if routing:
                        metrics.total_with_routing += 1

                    # --- Leakage check (REAL, from actual data) ---
                    if _check_leakage(record.cp_utc, routing):
                        metrics.leakage_violations += 1

                    # --- NWP telemetry: ECMWF ---
                    if routing.get("ecmwf_cache_hit"):
                        metrics.ecmwf_cache_hit_count += 1
                    if routing.get("ecmwf_fetch_status") == "success":
                        metrics.ecmwf_fetch_success_count += 1
                    if routing.get("ecmwf_fetch_status") == "cache_repair":
                        metrics.ecmwf_cache_repair_count += 1
                    if routing.get("ecmwf_fetch_error_type"):
                        metrics.ecmwf_fetch_error_count += 1

                    # --- NWP telemetry: GFS ---
                    if routing.get("gfs_cache_hit"):
                        metrics.gfs_cache_hit_count += 1
                    if routing.get("gfs_fetch_status") == "success":
                        metrics.gfs_fetch_success_count += 1
                    if routing.get("gfs_fetch_status") == "cache_repair":
                        metrics.gfs_cache_repair_count += 1
                    if routing.get("gfs_fetch_error_type"):
                        metrics.gfs_fetch_error_count += 1

                    # run_age_h.
                    run_age = routing.get("run_age_h")
                    if run_age is not None and isinstance(run_age, (int, float)) and math.isfinite(run_age):
                        metrics.run_age_h_values.append(float(run_age))

                    # valid_time_delta_h.
                    delta_h = routing.get("valid_time_delta_h")
                    if delta_h is not None and isinstance(delta_h, (int, float)) and math.isfinite(delta_h):
                        metrics.valid_time_delta_h_values.append(float(delta_h))

                    # --- CP20-22 residual served (CORRECTED) ---
                    # Note: cp_hour was already extracted above for uniqueness check.
                    if cp_hour is not None and 20 <= cp_hour <= 22:
                        metrics.total_cp20_22_count += 1
                        # Residual is served when the actual model is ecmwf/gfs_residual,
                        # NOT when it falls back to ridge/empirical.
                        if routing.get("served_model") in ("ecmwf_residual", "gfs_residual"):
                            metrics.residual_served_cp20_22_count += 1

                except (json.JSONDecodeError, ShadowSchemaError):
                    # Count as missing.
                    pass

        # Per-date CP coverage.
        metrics.dates_found += 1
        metrics.cp_coverage_per_date[file_date.isoformat()] = len(date_valid_cps)
        # Check that ALL expected CPs are present and NO extras (exact set match).
        if date_valid_cps == set(expected_cps):
            metrics.dates_complete += 1
        else:
            # Wave 2: record missing CPs for this date.
            missing_cps = sorted(set(expected_cps) - date_valid_cps)
            if missing_cps:
                metrics.missing_inventory.append(
                    (file_date.isoformat(), missing_cps)
                )

    # Window-based inventories must include dates with no JSONL file at all.
    if expected_dates:
        for missing_date in sorted(expected_dates - seen_dates):
            metrics.missing_inventory.append(
                (missing_date.isoformat(), sorted(expected_cps))
            )

    # Wave 2: build NWP endpoint summary from telemetry counts.
    metrics.nwp_endpoint_summary = {
        "ecmwf": {
            "cache_hit": metrics.ecmwf_cache_hit_count,
            "fetch_success": metrics.ecmwf_fetch_success_count,
            "cache_repair": metrics.ecmwf_cache_repair_count,
            "fetch_error": metrics.ecmwf_fetch_error_count,
        },
        "gfs": {
            "cache_hit": metrics.gfs_cache_hit_count,
            "fetch_success": metrics.gfs_fetch_success_count,
            "cache_repair": metrics.gfs_cache_repair_count,
            "fetch_error": metrics.gfs_fetch_error_count,
        },
    }

    # --- Read decision artifacts for odds stats (P3) ---
    if decisions_dir.exists():
        for dec_path in sorted(decisions_dir.glob("*.jsonl")):
            try:
                dec_date = date.fromisoformat(dec_path.stem)
            except ValueError:
                continue
            if start_date and dec_date < start_date:
                continue
            if end_date and dec_date > end_date:
                continue
            with open(dec_path, "r", encoding="ascii") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        dec = json.loads(line)
                        status = dec.get("odds_status", "unknown")
                        if status == "ok":
                            metrics.odds_available_count += 1
                        else:
                            metrics.odds_unavailable_count += 1
                    except json.JSONDecodeError:
                        pass

    metrics.missing_records = metrics.expected_records - metrics.found_records
    return metrics


@dataclass
class GateResult:
    """Result of a single gate check."""

    name: str
    passed: bool
    actual: Any
    threshold: Any
    description: str


def evaluate_gates(metrics: ReadinessMetrics) -> list[GateResult]:
    """Evaluate readiness gates against frozen thresholds.

    Args:
        metrics: Computed readiness metrics.

    Returns:
        List of GateResult, one per gate.
    """
    gates = [
        GateResult(
            name="completeness",
            passed=metrics.completeness >= GATE_COMPLETENESS_REQUIRED,
            actual=metrics.completeness,
            threshold=GATE_COMPLETENESS_REQUIRED,
            description=f"Found {metrics.found_records}/{metrics.expected_records} expected records",
        ),
        GateResult(
            name="leakage_violations",
            passed=metrics.leakage_violations <= GATE_LEAKAGE_VIOLATIONS_MAX,
            actual=metrics.leakage_violations,
            threshold=GATE_LEAKAGE_VIOLATIONS_MAX,
            description=f"Leakage violations: {metrics.leakage_violations}",
        ),
        GateResult(
            name="fallback_classified",
            passed=metrics.fallback_classified_rate >= GATE_FALLBACK_CLASSIFIED_REQUIRED,
            actual=metrics.fallback_classified_rate,
            threshold=GATE_FALLBACK_CLASSIFIED_REQUIRED,
            description=f"Classified {metrics.fallback_reasons_classified} fallbacks, "
            f"{metrics.fallback_reasons_unclassified} unclassified",
        ),
    ]
    return gates


def render_json(metrics: ReadinessMetrics, gates: list[GateResult], git_sha: str) -> dict:
    """Render metrics and gates to a JSON-serializable dict."""
    all_passed = all(g.passed for g in gates)

    return {
        "task": "phase5.1-live-shadow-readiness",
        "status": "read_only_no_serving_change",
        "git_sha": git_sha,
        "gates": {
            g.name: {
                "passed": g.passed,
                "actual": g.actual,
                "threshold": g.threshold,
                "description": g.description,
            }
            for g in gates
        },
        "verdict": "READY" if all_passed else "NOT_READY",
        "metrics": {
            "completeness": metrics.completeness,
            "expected_records": metrics.expected_records,
            "found_records": metrics.found_records,
            "missing_records": metrics.missing_records,
            "leakage_violations": metrics.leakage_violations,
            "fallback_rate": metrics.fallback_rate,
            "fallback_classified_rate": metrics.fallback_classified_rate,
            "fallback_reason_counts": metrics.fallback_reason_counts,
            "ecmwf_cache_hit": metrics.ecmwf_cache_hit_count,
            "ecmwf_fetch_success": metrics.ecmwf_fetch_success_count,
            "ecmwf_cache_repair": metrics.ecmwf_cache_repair_count,
            "ecmwf_fetch_error": metrics.ecmwf_fetch_error_count,
            "gfs_cache_hit": metrics.gfs_cache_hit_count,
            "gfs_fetch_success": metrics.gfs_fetch_success_count,
            "gfs_cache_repair": metrics.gfs_cache_repair_count,
            "gfs_fetch_error": metrics.gfs_fetch_error_count,
            "run_age_h_p50": metrics.run_age_h_p50,
            "run_age_h_p95": metrics.run_age_h_p95,
            "valid_time_delta_h_mean": metrics.valid_time_delta_h_mean,
            "residual_served_rate_cp20_22": metrics.residual_served_rate_cp20_22,
            "dates_expected": metrics.dates_expected,
            "dates_found": metrics.dates_found,
            "dates_complete": metrics.dates_complete,
            "odds_available": metrics.odds_available_count,
            "odds_unavailable": metrics.odds_unavailable_count,
            "unexpected_cp_records": metrics.unexpected_cp_records,
            "duplicate_cp_records": metrics.duplicate_cp_records,
            "missing_inventory": metrics.missing_inventory,
            "fallback_by_cp": metrics.fallback_by_cp,
            "fallback_by_model": metrics.fallback_by_model,
            "nwp_endpoint_summary": metrics.nwp_endpoint_summary,
        },
    }


def render_weekly_markdown(
    metrics: ReadinessMetrics,
    gates: list[GateResult],
    git_sha: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> str:
    """Render a weekly shadow ops summary report.

    Covers the same metrics as the readiness report but formatted as a
    consolidated weekly view with trend-oriented headings.
    """
    all_passed = all(g.passed for g in gates)
    verdict = "READY" if all_passed else "NOT_READY"
    period = ""
    if start_date and end_date:
        period = f"{start_date.isoformat()} to {end_date.isoformat()}"
    elif start_date:
        period = f"from {start_date.isoformat()}"
    elif end_date:
        period = f"up to {end_date.isoformat()}"
    else:
        period = "all available data"

    lines = [
        "# Shadow Ops Weekly Report v1",
        "",
        f"- period: {period}",
        f"- git_sha: `{git_sha}`",
        f"- verdict: **{verdict}**",
        "",
        "## Completeness",
        "",
        f"- expected_records: {metrics.expected_records}",
        f"- found_records: {metrics.found_records}",
        f"- missing_records: {metrics.missing_records}",
        f"- completeness: {metrics.completeness:.4f}",
        f"- dates_expected: {metrics.dates_expected}",
        f"- dates_found: {metrics.dates_found}",
        f"- dates_complete: {metrics.dates_complete}",
        "",
        "## Quality Gates",
        "",
    ]

    for g in gates:
        status = "PASS" if g.passed else "FAIL"
        actual_str = f"{g.actual:.4f}" if isinstance(g.actual, float) else str(g.actual)
        lines.append(f"- {g.name}: {status} (actual={actual_str}, threshold={g.threshold})")

    lines.extend([
        "",
        "## Fallback Distribution",
        "",
        "### By CP",
        "",
    ])
    if metrics.fallback_by_cp:
        for cp in sorted(metrics.fallback_by_cp):
            lines.append(f"- CP{cp:02d}: {metrics.fallback_by_cp[cp]}")
    else:
        lines.append("- (no fallbacks)")

    lines.extend([
        "",
        "### By Model",
        "",
    ])
    if metrics.fallback_by_model:
        for model in sorted(metrics.fallback_by_model):
            lines.append(f"- {model}: {metrics.fallback_by_model[model]}")
    else:
        lines.append("- (no fallbacks)")

    lines.extend([
        "",
        "### By Reason",
        "",
    ])
    if metrics.fallback_reason_counts:
        for reason, count in sorted(metrics.fallback_reason_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- (no fallbacks)")

    lines.extend([
        "",
        "## NWP Endpoint Summary",
        "",
    ])
    for endpoint, summary in metrics.nwp_endpoint_summary.items():
        lines.append(f"- {endpoint}:")
        for key, value in summary.items():
            lines.append(f"  - {key}: {value}")

    lines.extend([
        "",
        "## Residual Served (CP20-22)",
        "",
        f"- rate: {metrics.residual_served_rate_cp20_22:.4f}",
        f"- count: {metrics.residual_served_cp20_22_count}/{metrics.total_cp20_22_count}",
        "",
        "## Missing Date/CP Inventory",
        "",
    ])
    if metrics.missing_inventory:
        for date_iso, missing_cps in metrics.missing_inventory:
            lines.append(f"- {date_iso}: missing CPs {missing_cps}")
    else:
        lines.append("- (no missing CPs)")

    lines.extend([
        "",
        "## Anomalies",
        "",
        f"- unexpected_cp_records: {metrics.unexpected_cp_records}",
        f"- duplicate_cp_records: {metrics.duplicate_cp_records}",
        "",
        "## Odds Availability",
        "",
        f"- available: {metrics.odds_available_count}",
        f"- unavailable: {metrics.odds_unavailable_count}",
        "",
        "## Timing",
        "",
        f"- run_age_h p50: {metrics.run_age_h_p50:.2f}" if metrics.run_age_h_p50 else "- run_age_h p50: N/A",
        f"- run_age_h p95: {metrics.run_age_h_p95:.2f}" if metrics.run_age_h_p95 else "- run_age_h p95: N/A",
        f"- valid_time_delta_h mean: {metrics.valid_time_delta_h_mean:.2f}"
        if metrics.valid_time_delta_h_mean
        else "- valid_time_delta_h mean: N/A",
        "",
    ])

    return "\n".join(lines)


def render_markdown(metrics: ReadinessMetrics, gates: list[GateResult], git_sha: str) -> str:
    """Render metrics and gates to a Markdown report."""
    all_passed = all(g.passed for g in gates)
    verdict = "READY" if all_passed else "NOT_READY"

    lines = [
        "# Live Shadow Readiness Report (Phase 5.1)",
        "",
        f"- git_sha: `{git_sha}`",
        f"- verdict: **{verdict}**",
        "",
        "## Gate Summary",
        "",
        "| Gate | Passed | Actual | Threshold | Description |",
        "|------|--------|--------|-----------|-------------|",
    ]
    for g in gates:
        status = "PASS" if g.passed else "FAIL"
        actual_str = f"{g.actual:.4f}" if isinstance(g.actual, float) else str(g.actual)
        lines.append(f"| {g.name} | {status} | {actual_str} | {g.threshold} | {g.description} |")

    lines.extend([
        "",
        "## Metrics",
        "",
        f"- completeness: {metrics.completeness:.4f} ({metrics.found_records}/{metrics.expected_records})",
        f"- leakage_violations: {metrics.leakage_violations}",
        f"- fallback_rate: {metrics.fallback_rate:.4f}",
        f"- fallback_classified_rate: {metrics.fallback_classified_rate:.4f}",
        "",
        "### NWP Telemetry (ECMWF + GFS)",
        "",
        f"- ecmwf_cache_hit: {metrics.ecmwf_cache_hit_count}",
        f"- ecmwf_fetch_success: {metrics.ecmwf_fetch_success_count}",
        f"- ecmwf_cache_repair: {metrics.ecmwf_cache_repair_count}",
        f"- ecmwf_fetch_error: {metrics.ecmwf_fetch_error_count}",
        f"- gfs_cache_hit: {metrics.gfs_cache_hit_count}",
        f"- gfs_fetch_success: {metrics.gfs_fetch_success_count}",
        f"- gfs_cache_repair: {metrics.gfs_cache_repair_count}",
        f"- gfs_fetch_error: {metrics.gfs_fetch_error_count}",
        "",
        "### Timing",
        "",
        f"- run_age_h p50: {metrics.run_age_h_p50:.2f}" if metrics.run_age_h_p50 else "- run_age_h p50: N/A",
        f"- run_age_h p95: {metrics.run_age_h_p95:.2f}" if metrics.run_age_h_p95 else "- run_age_h p95: N/A",
        f"- valid_time_delta_h mean: {metrics.valid_time_delta_h_mean:.2f}"
        if metrics.valid_time_delta_h_mean
        else "- valid_time_delta_h mean: N/A",
        "",
        "### Fallback Reason Distribution",
        "",
    ])

    if metrics.fallback_reason_counts:
        for reason, count in sorted(metrics.fallback_reason_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- (no fallbacks recorded)")

    lines.extend([
        "",
        "### Residual Served (CP20-22)",
        "",
        f"- rate: {metrics.residual_served_rate_cp20_22:.4f}",
        f"- count: {metrics.residual_served_cp20_22_count}/{metrics.total_cp20_22_count}",
        "",
        "### Date Completeness",
        "",
        f"- dates_expected: {metrics.dates_expected}",
        f"- dates_found: {metrics.dates_found}",
        f"- dates_complete: {metrics.dates_complete}",
        "",
        "### Anomalies",
        "",
        f"- unexpected_cp_records: {metrics.unexpected_cp_records}",
        f"- duplicate_cp_records: {metrics.duplicate_cp_records}",
        "",
        "### Odds Availability",
        "",
        f"- available: {metrics.odds_available_count}",
        f"- unavailable: {metrics.odds_unavailable_count}",
        "",
        "### Missing Date/CP Inventory",
        "",
    ])

    if metrics.missing_inventory:
        for date_iso, missing_cps in metrics.missing_inventory:
            lines.append(f"- {date_iso}: missing CPs {missing_cps}")
    else:
        lines.append("- (no missing CPs)")

    lines.extend([
        "",
        "### Fallback Distribution by CP",
        "",
    ])

    if metrics.fallback_by_cp:
        for cp in sorted(metrics.fallback_by_cp):
            lines.append(f"- CP{cp:02d}: {metrics.fallback_by_cp[cp]}")
    else:
        lines.append("- (no fallbacks)")

    lines.extend([
        "",
        "### Fallback Distribution by Model",
        "",
    ])

    if metrics.fallback_by_model:
        for model in sorted(metrics.fallback_by_model):
            lines.append(f"- {model}: {metrics.fallback_by_model[model]}")
    else:
        lines.append("- (no fallbacks)")

    lines.extend([
        "",
        "### NWP Endpoint Summary",
        "",
    ])

    for endpoint, summary in metrics.nwp_endpoint_summary.items():
        lines.append(f"- {endpoint}:")
        for key, value in summary.items():
            lines.append(f"  - {key}: {value}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Live Shadow Readiness Report."
    )
    parser.add_argument(
        "--shadow-root",
        type=Path,
        default=Path("artifacts/shadow_ops"),
        help="Root directory for shadow ops (default: artifacts/shadow_ops).",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date filter (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date filter (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("reports/live_shadow"),
        help="Output directory for reports (default: reports/live_shadow).",
    )
    parser.add_argument(
        "--git-sha",
        type=str,
        default="unknown",
        help="Git SHA to embed in report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    start_date = date.fromisoformat(args.start) if args.start else None
    end_date = date.fromisoformat(args.end) if args.end else None

    metrics = compute_metrics(
        shadow_root=args.shadow_root,
        start_date=start_date,
        end_date=end_date,
    )
    gates = evaluate_gates(metrics)

    # Render outputs.
    json_output = render_json(metrics, gates, args.git_sha)
    md_output = render_markdown(metrics, gates, args.git_sha)

    # Write outputs.
    args.out_root.mkdir(parents=True, exist_ok=True)
    json_path = args.out_root / "readiness_v1.json"
    md_path = args.out_root / "readiness_v1.md"
    weekly_path = args.out_root / "shadow_ops_weekly_v1.md"

    with open(json_path, "w", encoding="ascii") as fh:
        json.dump(json_output, fh, ensure_ascii=True, indent=2, sort_keys=True)
    print(f"Wrote: {json_path}")

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md_output)
    print(f"Wrote: {md_path}")

    weekly_md = render_weekly_markdown(metrics, gates, args.git_sha, start_date, end_date)
    with open(weekly_path, "w", encoding="utf-8") as fh:
        fh.write(weekly_md)
    print(f"Wrote: {weekly_path}")

    if start_date and end_date:
        suffix = f"{start_date.isoformat()}_{end_date.isoformat()}"
        window_json_path = args.out_root / f"shadow_window_{suffix}.json"
        window_md_path = args.out_root / f"shadow_window_{suffix}.md"
        with open(window_json_path, "w", encoding="ascii") as fh:
            json.dump(json_output, fh, ensure_ascii=True, indent=2, sort_keys=True)
        with open(window_md_path, "w", encoding="utf-8") as fh:
            fh.write(weekly_md)
        print(f"Wrote: {window_json_path}")
        print(f"Wrote: {window_md_path}")

    # Print summary.
    verdict = json_output["verdict"]
    print(f"\nVerdict: {verdict}")
    for g in gates:
        status = "PASS" if g.passed else "FAIL"
        print(f"  [{status}] {g.name}: {g.actual} (threshold: {g.threshold})")

    return 0 if verdict == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
