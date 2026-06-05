#!/usr/bin/env python3
"""Live Shadow promotion review pack (Wave 4).

This script is read-only. It evaluates whether a completed shadow window has
enough operational evidence to recommend serving-default promotion. It never
enables automatic trading and never changes model routing.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

# Add project root and scripts to path for imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from live_shadow_readiness_report import (
    ReadinessMetrics,
    compute_metrics,
    evaluate_gates,
    render_json as render_readiness_json,
)


MIN_SHADOW_DAYS = 30
MIN_CP_DAYS_CP20_22 = 90
NWP_FETCH_SUCCESS_MIN = 0.95
RUN_AGE_H_P95_MAX = 18.0
FALLBACK_RATE_CP20_22_MAX = 0.10
DEFAULT_SHADOW_ROOT = Path("artifacts/shadow_ops")
DEFAULT_REPORT_ROOT = Path("reports/live_shadow")
DEFAULT_MOS_REPORT = Path("reports/serving/mos_emos_lite_v0.json")

VERDICT_KEEP_SHADOW = "KEEP_SHADOW"
VERDICT_EXTEND_SHADOW = "EXTEND_SHADOW"
VERDICT_PROMOTE = "PROMOTE_SERVING_DEFAULT"


@dataclass(frozen=True)
class PromotionCheck:
    """One promotion checklist item."""

    name: str
    passed: bool
    actual: Any
    threshold: Any
    description: str


@dataclass(frozen=True)
class PromotionReview:
    """Computed promotion review output."""

    start_date: date
    end_date: date
    metrics: ReadinessMetrics
    readiness_gates: list[PromotionCheck]
    promotion_checks: list[PromotionCheck]
    mos_emos_evidence: dict[str, Any]
    verdict: str


def _window_days(start_date: date, end_date: date) -> int:
    return end_date.toordinal() - start_date.toordinal() + 1


def _rate(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return num / den


def _nwp_fetch_success_rate(metrics: ReadinessMetrics) -> float | None:
    successes = metrics.ecmwf_fetch_success_count + metrics.gfs_fetch_success_count
    errors = metrics.ecmwf_fetch_error_count + metrics.gfs_fetch_error_count
    repairs = metrics.ecmwf_cache_repair_count + metrics.gfs_cache_repair_count
    return _rate(successes, successes + errors + repairs)


def _load_mos_emos_evidence(path: Path) -> dict[str, Any]:
    """Load MOS/EMOS-lite evidence if available.

    Missing evidence is not a crash; it blocks promotion and is recorded in the
    promotion pack.
    """
    if not path.exists():
        return {
            "available": False,
            "path": str(path),
            "passed": False,
            "reason": "mos_emos_lite_report_missing",
        }
    try:
        raw = json.loads(path.read_text(encoding="ascii"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {
            "available": False,
            "path": str(path),
            "passed": False,
            "reason": f"mos_emos_lite_report_unreadable:{type(exc).__name__}",
        }

    conclusion = raw.get("honest_conclusion", {})
    verdict = conclusion.get("verdict") or raw.get("verdict")
    decision = raw.get("decision", {})
    all_candidates_coverage_ok = True
    eligible_candidates = 0
    for cp_detail in decision.values():
        candidates = cp_detail.get("candidates", {}) if isinstance(cp_detail, dict) else {}
        for cand in candidates.values():
            if isinstance(cand, dict):
                all_candidates_coverage_ok = all_candidates_coverage_ok and bool(
                    cand.get("coverage_ok", False)
                )
                if cand.get("eligible"):
                    eligible_candidates += 1

    passed = verdict in {"PROMISING_FOR_FOLLOWUP_PREREG", "PROMOTE", "READY"} and all_candidates_coverage_ok
    return {
        "available": True,
        "path": str(path),
        "passed": passed,
        "verdict": verdict,
        "all_candidates_coverage_ok": all_candidates_coverage_ok,
        "eligible_candidates": eligible_candidates,
        "gate_contract": raw.get("gate_contract", {}),
        "reason": None if passed else "mos_emos_lite_not_promotion_ready",
    }


def _as_check(gate) -> PromotionCheck:
    return PromotionCheck(
        name=gate.name,
        passed=gate.passed,
        actual=gate.actual,
        threshold=gate.threshold,
        description=gate.description,
    )


def evaluate_promotion(
    shadow_root: Path,
    start_date: date,
    end_date: date,
    *,
    mos_report: Path = DEFAULT_MOS_REPORT,
) -> PromotionReview:
    """Evaluate a frozen shadow window against the promotion contract."""
    metrics = compute_metrics(
        shadow_root=shadow_root,
        start_date=start_date,
        end_date=end_date,
        expected_cps=(20, 21, 22, 23),
    )
    readiness_gates = [_as_check(g) for g in evaluate_gates(metrics)]

    window_days = _window_days(start_date, end_date)
    cp_days_cp20_22 = metrics.total_cp20_22_count
    nwp_success_rate = _nwp_fetch_success_rate(metrics)
    run_age_h_p95 = metrics.run_age_h_p95
    fallback_rate_cp20_22 = _rate(
        metrics.total_cp20_22_count - metrics.residual_served_cp20_22_count,
        metrics.total_cp20_22_count,
    )
    mos_evidence = _load_mos_emos_evidence(mos_report)

    promotion_checks = [
        PromotionCheck(
            name="minimum_shadow_days",
            passed=window_days >= MIN_SHADOW_DAYS,
            actual=window_days,
            threshold=MIN_SHADOW_DAYS,
            description="Minimum consecutive shadow observation days.",
        ),
        PromotionCheck(
            name="minimum_cp_days_cp20_22",
            passed=cp_days_cp20_22 >= MIN_CP_DAYS_CP20_22,
            actual=cp_days_cp20_22,
            threshold=MIN_CP_DAYS_CP20_22,
            description="Minimum CP20-22 observations for serving-default review.",
        ),
        PromotionCheck(
            name="nwp_fetch_success_rate",
            passed=nwp_success_rate is not None and nwp_success_rate >= NWP_FETCH_SUCCESS_MIN,
            actual=nwp_success_rate,
            threshold=NWP_FETCH_SUCCESS_MIN,
            description="NWP fetch success rate, excluding cache hits from the denominator.",
        ),
        PromotionCheck(
            name="run_age_h_p95",
            passed=run_age_h_p95 is not None and run_age_h_p95 < RUN_AGE_H_P95_MAX,
            actual=run_age_h_p95,
            threshold=f"< {RUN_AGE_H_P95_MAX}",
            description="NWP p95 run age must stay fresh enough for operations.",
        ),
        PromotionCheck(
            name="fallback_rate_cp20_22",
            passed=(
                fallback_rate_cp20_22 is not None
                and fallback_rate_cp20_22 < FALLBACK_RATE_CP20_22_MAX
            ),
            actual=fallback_rate_cp20_22,
            threshold=f"< {FALLBACK_RATE_CP20_22_MAX}",
            description="Fallback rate over CP20-22 must remain below the frozen threshold.",
        ),
        PromotionCheck(
            name="predictive_quality_evidence",
            passed=bool(mos_evidence.get("passed")),
            actual=mos_evidence.get("verdict") or mos_evidence.get("reason"),
            threshold="promotion-ready MOS/EMOS evidence",
            description="Predictive-quality evidence must be available and promotion-ready.",
        ),
        PromotionCheck(
            name="no_automatic_trading_activation",
            passed=True,
            actual="read_only_review",
            threshold="no live orders",
            description="Wave 4 only creates an evidence pack; it does not enable trading.",
        ),
    ]

    readiness_ok = all(c.passed for c in readiness_gates)
    promotion_ok = all(c.passed for c in promotion_checks)
    if readiness_ok and promotion_ok:
        verdict = VERDICT_PROMOTE
    elif not readiness_ok:
        verdict = VERDICT_KEEP_SHADOW
    else:
        verdict = VERDICT_EXTEND_SHADOW

    return PromotionReview(
        start_date=start_date,
        end_date=end_date,
        metrics=metrics,
        readiness_gates=readiness_gates,
        promotion_checks=promotion_checks,
        mos_emos_evidence=mos_evidence,
        verdict=verdict,
    )


def _check_to_json(check: PromotionCheck) -> dict[str, Any]:
    return {
        "passed": check.passed,
        "actual": check.actual,
        "threshold": check.threshold,
        "description": check.description,
    }


def render_json(review: PromotionReview, git_sha: str) -> dict[str, Any]:
    """Render promotion review to JSON."""
    return {
        "task": "phase5.1-wave4-promotion-review",
        "status": "read_only_no_trading_change",
        "git_sha": git_sha,
        "contract": "contracts/live_shadow_ops_v1_prereg.md",
        "window": {
            "start_date": review.start_date.isoformat(),
            "end_date": review.end_date.isoformat(),
            "days": _window_days(review.start_date, review.end_date),
        },
        "verdict": review.verdict,
        "allowed_verdicts": [
            VERDICT_KEEP_SHADOW,
            VERDICT_EXTEND_SHADOW,
            VERDICT_PROMOTE,
        ],
        "readiness_gates": {
            c.name: _check_to_json(c) for c in review.readiness_gates
        },
        "promotion_checks": {
            c.name: _check_to_json(c) for c in review.promotion_checks
        },
        "mos_emos_evidence": review.mos_emos_evidence,
        "readiness": render_readiness_json(
            review.metrics,
            evaluate_gates(review.metrics),
            git_sha,
        ),
    }


def _fmt_actual(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_markdown(review: PromotionReview, git_sha: str) -> str:
    """Render promotion review to Markdown."""
    lines = [
        "# Live Shadow Promotion Review v1",
        "",
        f"- git_sha: `{git_sha}`",
        f"- window: {review.start_date.isoformat()} to {review.end_date.isoformat()}",
        f"- verdict: **{review.verdict}**",
        f"- status: read_only_no_trading_change",
        "",
        "## Readiness Gates",
        "",
        "| gate | status | actual | threshold |",
        "|------|--------|--------|-----------|",
    ]
    for check in review.readiness_gates:
        status = "PASS" if check.passed else "FAIL"
        lines.append(
            f"| {check.name} | {status} | {_fmt_actual(check.actual)} | {check.threshold} |"
        )

    lines.extend([
        "",
        "## Promotion Checks",
        "",
        "| check | status | actual | threshold |",
        "|-------|--------|--------|-----------|",
    ])
    for check in review.promotion_checks:
        status = "PASS" if check.passed else "FAIL"
        lines.append(
            f"| {check.name} | {status} | {_fmt_actual(check.actual)} | {check.threshold} |"
        )

    lines.extend([
        "",
        "## Evidence Summary",
        "",
        f"- completeness: {review.metrics.completeness:.4f}",
        f"- leakage_violations: {review.metrics.leakage_violations}",
        f"- fallback_rate: {review.metrics.fallback_rate:.4f}",
        f"- residual_served_rate_cp20_22: {review.metrics.residual_served_rate_cp20_22:.4f}",
        f"- run_age_h_p95: {_fmt_actual(review.metrics.run_age_h_p95)}",
        f"- odds_available: {review.metrics.odds_available_count}",
        f"- odds_unavailable: {review.metrics.odds_unavailable_count}",
        "",
        "## MOS/EMOS Evidence",
        "",
        f"- available: {review.mos_emos_evidence.get('available')}",
        f"- verdict: {review.mos_emos_evidence.get('verdict')}",
        f"- reason: {review.mos_emos_evidence.get('reason')}",
        f"- path: {review.mos_emos_evidence.get('path')}",
        "",
        "## Decision",
        "",
    ])
    if review.verdict == VERDICT_PROMOTE:
        lines.append("- Recommendation: promote residual serving as serving default only; automatic trading remains out of scope.")
    elif review.verdict == VERDICT_KEEP_SHADOW:
        lines.append("- Recommendation: keep shadow mode and repair readiness failures before another review.")
    else:
        lines.append("- Recommendation: extend shadow mode until missing promotion evidence is available.")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only live shadow promotion review pack."
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
        "--mos-report",
        type=Path,
        default=DEFAULT_MOS_REPORT,
        help=f"MOS/EMOS evidence report (default: {DEFAULT_MOS_REPORT}).",
    )
    parser.add_argument(
        "--git-sha",
        type=str,
        default="unknown",
        help="Git SHA to embed in the promotion pack.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    if start_date > end_date:
        print("ERROR: --start must be <= --end", file=sys.stderr)
        return 2

    review = evaluate_promotion(
        args.shadow_root,
        start_date,
        end_date,
        mos_report=args.mos_report,
    )
    args.out_root.mkdir(parents=True, exist_ok=True)
    json_path = args.out_root / "promotion_review_v1.json"
    md_path = args.out_root / "promotion_review_v1.md"
    with open(json_path, "w", encoding="ascii") as fh:
        json.dump(render_json(review, args.git_sha), fh, ensure_ascii=True, indent=2, sort_keys=True)
    with open(md_path, "w", encoding="ascii") as fh:
        fh.write(render_markdown(review, args.git_sha))

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Verdict: {review.verdict}")
    return 0 if review.verdict == VERDICT_PROMOTE else 1


if __name__ == "__main__":
    sys.exit(main())
