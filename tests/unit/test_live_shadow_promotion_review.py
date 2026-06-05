"""Unit tests for scripts/live_shadow_promotion_review.py (Wave 4)."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import live_shadow_promotion_review as promo


def _record(target_date: date, cp_hour: int, *, fallback_used: bool = False) -> dict:
    return {
        "run_id": f"run-{target_date.isoformat()}-{cp_hour}",
        "date_local": target_date.isoformat(),
        "cp_utc": f"{target_date.isoformat()}T{cp_hour:02d}:00:00+00:00",
        "prob_dist": {"18": 0.3, "19": 0.4, "20": 0.3},
        "model_version": "phase3-ridge-band-v1.0",
        "routing": {
            "model_route": "ecmwf",
            "served_model": "ecmwf_residual" if not fallback_used else "ridge",
            "fallback_used": fallback_used,
            "fallback_reason": "nwp_unavailable" if fallback_used else None,
            "ecmwf_fetch_status": "success",
            "gfs_fetch_status": "success",
            "run_age_h": 6.0,
            "valid_time_delta_h": 12.0,
        },
        "p50_int": 19,
    }


def _write_shadow_window(
    shadow_root: Path,
    start_date: date,
    n_days: int,
    *,
    cps: tuple[int, ...] = (20, 21, 22, 23),
) -> None:
    forecasts_dir = shadow_root / "forecasts"
    forecasts_dir.mkdir(parents=True, exist_ok=True)
    for offset in range(n_days):
        target = start_date + timedelta(days=offset)
        with open(forecasts_dir / f"{target.isoformat()}.jsonl", "w", encoding="ascii") as fh:
            for cp in cps:
                fh.write(json.dumps(_record(target, cp)) + "\n")


def _write_mos_report(path: Path, *, verdict: str = "PROMISING_FOR_FOLLOWUP_PREREG") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = {
        "gate_contract": {"min_coverage_required": 0.7},
        "honest_conclusion": {"verdict": verdict},
        "decision": {
            "20:00": {
                "candidates": {
                    "mos_ecmwf": {"coverage_ok": True, "eligible": True},
                }
            }
        },
    }
    path.write_text(json.dumps(raw), encoding="ascii")


def test_evaluate_promotion_blocks_short_window(tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    mos_report = tmp_path / "mos.json"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 7)
    _write_mos_report(mos_report)

    review = promo.evaluate_promotion(
        shadow_root,
        date(2025, 1, 1),
        date(2025, 1, 7),
        mos_report=mos_report,
    )

    assert review.verdict == promo.VERDICT_EXTEND_SHADOW
    check = next(c for c in review.promotion_checks if c.name == "minimum_shadow_days")
    assert not check.passed
    assert check.actual == 7


def test_evaluate_promotion_keep_shadow_when_readiness_fails(tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    mos_report = tmp_path / "mos.json"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 30)
    _write_mos_report(mos_report)
    # Remove one day from the frozen window.
    (shadow_root / "forecasts" / "2025-01-10.jsonl").unlink()

    review = promo.evaluate_promotion(
        shadow_root,
        date(2025, 1, 1),
        date(2025, 1, 30),
        mos_report=mos_report,
    )

    assert review.verdict == promo.VERDICT_KEEP_SHADOW
    completeness = next(c for c in review.readiness_gates if c.name == "completeness")
    assert not completeness.passed


def test_evaluate_promotion_extends_when_mos_evidence_missing(tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 30)

    review = promo.evaluate_promotion(
        shadow_root,
        date(2025, 1, 1),
        date(2025, 1, 30),
        mos_report=tmp_path / "missing.json",
    )

    assert review.verdict == promo.VERDICT_EXTEND_SHADOW
    quality = next(c for c in review.promotion_checks if c.name == "predictive_quality_evidence")
    assert not quality.passed
    assert quality.actual == "mos_emos_lite_report_missing"


def test_evaluate_promotion_promotes_only_when_all_checks_pass(tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    mos_report = tmp_path / "mos.json"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 30)
    _write_mos_report(mos_report)

    review = promo.evaluate_promotion(
        shadow_root,
        date(2025, 1, 1),
        date(2025, 1, 30),
        mos_report=mos_report,
    )

    assert review.verdict == promo.VERDICT_PROMOTE
    assert all(c.passed for c in review.readiness_gates)
    assert all(c.passed for c in review.promotion_checks)


def test_render_json_and_markdown_include_verdict(tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    mos_report = tmp_path / "mos.json"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 30)
    _write_mos_report(mos_report)
    review = promo.evaluate_promotion(
        shadow_root,
        date(2025, 1, 1),
        date(2025, 1, 30),
        mos_report=mos_report,
    )

    raw = promo.render_json(review, "sha-promo")
    md = promo.render_markdown(review, "sha-promo")

    assert raw["verdict"] == promo.VERDICT_PROMOTE
    assert raw["status"] == "read_only_no_trading_change"
    assert "PROMOTE_SERVING_DEFAULT" in md
    assert "automatic trading remains out of scope" in md


def test_main_writes_promotion_pack(monkeypatch, tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    out_root = tmp_path / "reports"
    mos_report = tmp_path / "mos.json"
    _write_shadow_window(shadow_root, date(2025, 1, 1), 30)
    _write_mos_report(mos_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "live_shadow_promotion_review.py",
            "--start",
            "2025-01-01",
            "--end",
            "2025-01-30",
            "--shadow-root",
            str(shadow_root),
            "--out-root",
            str(out_root),
            "--mos-report",
            str(mos_report),
            "--git-sha",
            "sha-main",
        ],
    )

    assert promo.main() == 0
    assert (out_root / "promotion_review_v1.json").exists()
    assert (out_root / "promotion_review_v1.md").exists()
    raw = json.loads((out_root / "promotion_review_v1.json").read_text(encoding="ascii"))
    assert raw["git_sha"] == "sha-main"
    assert raw["verdict"] == promo.VERDICT_PROMOTE
