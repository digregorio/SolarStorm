"""Unit tests for scripts/live_shadow_readiness_report.py (Phase 5.1).

Tests cover:
- Fixture JSONL generates deterministic report
- Gates frozen before reading (thresholds are constants)
- Markdown and JSON consistent
- Failures classified, not silent
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

# Import the report functions.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from live_shadow_readiness_report import (
    GATE_COMPLETENESS_REQUIRED,
    GATE_FALLBACK_CLASSIFIED_REQUIRED,
    GATE_LEAKAGE_VIOLATIONS_MAX,
    GateResult,
    ReadinessMetrics,
    _extract_cp_hour,
    _percentile,
    compute_metrics,
    evaluate_gates,
    main,
    render_json,
    render_markdown,
    render_weekly_markdown,
)


# --- Helper to create fixture JSONL ------------------------------------------


def _write_fixture_jsonl(
    forecasts_dir: Path,
    target_date: date,
    records: list[dict] | None = None,
) -> Path:
    """Write a fixture JSONL file for testing."""
    forecasts_dir.mkdir(parents=True, exist_ok=True)
    out_path = forecasts_dir / f"{target_date.isoformat()}.jsonl"

    if records is None:
        records = [
            _make_record(cp_hour=20, fallback_used=False),
            _make_record(cp_hour=21, fallback_used=False),
            _make_record(cp_hour=22, fallback_used=False),
            _make_record(cp_hour=23, fallback_used=False),
        ]

    with open(out_path, "w", encoding="ascii") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return out_path


def _make_record(
    cp_hour: int = 20,
    fallback_used: bool = False,
    fallback_reason: str | None = None,
    served_model: str = "ecmwf_residual",
    run_age_h: float = 6.0,
    valid_time_delta_h: float = 12.0,
) -> dict:
    """Create a minimal valid forecast record."""
    return {
        "run_id": f"test-run-cp{cp_hour}",
        "date_local": "2025-01-15",
        "cp_utc": f"2025-01-15T{cp_hour:02d}:00:00+00:00",
        "prob_dist": {"18": 0.3, "19": 0.5, "20": 0.2},
        "model_version": "phase3-ridge-band-v1.0",
        "routing": {
            "model_route": "ecmwf" if "ecmwf" in served_model else "ridge",
            "served_model": served_model,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "ecmwf_cache_hit": True,
            "ecmwf_fetch_status": "success" if not fallback_used else "failed",
            "run_age_h": run_age_h,
            "valid_time_delta_h": valid_time_delta_h,
        },
        "p50_int": 19,
    }


# --- Percentile tests ---------------------------------------------------------


def test_percentile_empty():
    assert _percentile([], 50) is None


def test_percentile_single():
    assert _percentile([10.0], 50) == 10.0


def test_percentile_even():
    vals = [1.0, 2.0, 3.0, 4.0]
    assert _percentile(vals, 50) == pytest.approx(2.5)


def test_percentile_p95():
    vals = list(range(1, 21))  # 1..20
    assert _percentile(vals, 95) == pytest.approx(19.05)


# --- Extract CP hour tests ----------------------------------------------------


def test_extract_cp_hour_valid():
    assert _extract_cp_hour("2025-01-15T20:00:00+00:00") == 20
    assert _extract_cp_hour("2025-01-15T23:30:00Z") == 23


def test_extract_cp_hour_invalid():
    assert _extract_cp_hour("invalid") is None
    assert _extract_cp_hour("2025-01-15") is None


# --- Compute metrics tests ----------------------------------------------------


def test_compute_metrics_empty_dir(tmp_path: Path):
    metrics = compute_metrics(tmp_path)
    assert metrics.expected_records == 0
    assert metrics.found_records == 0
    assert metrics.completeness == 0.0


def test_compute_metrics_complete(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15))

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.expected_records == 4
    assert metrics.found_records == 4
    assert metrics.completeness == 1.0
    assert metrics.missing_records == 0


def test_compute_metrics_partial(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    # Only 2 records instead of 4.
    _write_fixture_jsonl(
        forecasts_dir,
        date(2025, 1, 15),
        records=[_make_record(cp_hour=20), _make_record(cp_hour=21)],
    )

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.expected_records == 4
    assert metrics.found_records == 2
    assert metrics.completeness == 0.5
    assert metrics.missing_records == 2


def test_compute_metrics_with_fallbacks(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, fallback_used=True, fallback_reason="nwp_unavailable"),
        _make_record(cp_hour=21, fallback_used=True, fallback_reason="nwp_unavailable"),
        _make_record(cp_hour=22, fallback_used=True, fallback_reason=None),  # unclassified
        _make_record(cp_hour=23, fallback_used=False),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.fallback_used_count == 3
    assert metrics.fallback_reasons_classified == 2
    assert metrics.fallback_reasons_unclassified == 1
    assert metrics.fallback_reason_counts["nwp_unavailable"] == 2


def test_compute_metrics_date_filter(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 10))
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15))
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 20))

    # Filter to only 2025-01-15.
    metrics = compute_metrics(
        tmp_path,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 1, 15),
    )
    assert metrics.expected_records == 4
    assert metrics.found_records == 4


def test_compute_metrics_nwp_telemetry(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15))

    metrics = compute_metrics(tmp_path)
    assert metrics.ecmwf_cache_hit_count == 4  # All 4 records have cache_hit=True
    assert metrics.ecmwf_fetch_success_count == 4


def test_compute_metrics_timing(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, run_age_h=4.0, valid_time_delta_h=10.0),
        _make_record(cp_hour=21, run_age_h=6.0, valid_time_delta_h=12.0),
        _make_record(cp_hour=22, run_age_h=8.0, valid_time_delta_h=14.0),
        _make_record(cp_hour=23, run_age_h=10.0, valid_time_delta_h=16.0),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.run_age_h_p50 == pytest.approx(7.0)
    assert metrics.run_age_h_p95 == pytest.approx(9.7)
    assert metrics.valid_time_delta_h_mean == pytest.approx(13.0)


# --- Evaluate gates tests -----------------------------------------------------


def test_evaluate_gates_all_pass():
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        leakage_violations=0,
        fallback_reasons_classified=2,
        fallback_reasons_unclassified=0,
        total_with_routing=4,
    )
    gates = evaluate_gates(metrics)
    assert all(g.passed for g in gates)


def test_evaluate_gates_completeness_fail():
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=2,  # Only 50%
        leakage_violations=0,
    )
    gates = evaluate_gates(metrics)
    completeness_gate = next(g for g in gates if g.name == "completeness")
    assert not completeness_gate.passed


def test_evaluate_gates_fallback_unclassified_fail():
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        leakage_violations=0,
        fallback_reasons_classified=1,
        fallback_reasons_unclassified=1,  # 1 unclassified
    )
    gates = evaluate_gates(metrics)
    fallback_gate = next(g for g in gates if g.name == "fallback_classified")
    assert not fallback_gate.passed


# --- Gates are frozen constants -----------------------------------------------


def test_gates_are_constants():
    """Verify gate thresholds are module-level constants (frozen before reading)."""
    assert GATE_COMPLETENESS_REQUIRED == 1.0
    assert GATE_LEAKAGE_VIOLATIONS_MAX == 0
    assert GATE_FALLBACK_CLASSIFIED_REQUIRED == 1.0


# --- Render tests -------------------------------------------------------------


def test_render_json_structure():
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        leakage_violations=0,
    )
    gates = evaluate_gates(metrics)
    output = render_json(metrics, gates, "abc123")

    assert output["task"] == "phase5.1-live-shadow-readiness"
    assert output["git_sha"] == "abc123"
    assert output["verdict"] == "READY"
    assert "completeness" in output["gates"]
    assert "metrics" in output


def test_render_markdown_structure():
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        leakage_violations=0,
    )
    gates = evaluate_gates(metrics)
    output = render_markdown(metrics, gates, "abc123")

    assert "# Live Shadow Readiness Report" in output
    assert "abc123" in output
    assert "READY" in output
    assert "| completeness |" in output


def test_render_consistency():
    """JSON and Markdown should report the same verdict."""
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=2,  # Incomplete
    )
    gates = evaluate_gates(metrics)
    json_output = render_json(metrics, gates, "sha1")
    md_output = render_markdown(metrics, gates, "sha1")

    assert json_output["verdict"] == "NOT_READY"
    assert "NOT_READY" in md_output


# --- Determinism test ---------------------------------------------------------


def test_deterministic_report(tmp_path: Path):
    """Same input produces same output."""
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15))

    m1 = compute_metrics(tmp_path)
    m2 = compute_metrics(tmp_path)

    assert m1.completeness == m2.completeness
    assert m1.fallback_rate == m2.fallback_rate
    assert m1.run_age_h_p50 == m2.run_age_h_p50


# --- Invalid JSONL handling ---------------------------------------------------


def test_invalid_jsonl_skipped(tmp_path: Path):
    """Invalid lines are skipped, not causing crashes."""
    forecasts_dir = tmp_path / "forecasts"
    forecasts_dir.mkdir(parents=True)
    out_path = forecasts_dir / "2025-01-15.jsonl"

    with open(out_path, "w") as fh:
        fh.write(json.dumps(_make_record(cp_hour=20)) + "\n")
        fh.write("this is not json\n")
        fh.write(json.dumps(_make_record(cp_hour=21)) + "\n")

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.found_records == 2  # Only valid records counted


def test_missing_fields_skipped(tmp_path: Path):
    """Records with missing required fields are skipped."""
    forecasts_dir = tmp_path / "forecasts"
    forecasts_dir.mkdir(parents=True)
    out_path = forecasts_dir / "2025-01-15.jsonl"

    incomplete = {"run_id": "x", "date_local": "2025-01-15"}  # Missing many fields
    with open(out_path, "w") as fh:
        fh.write(json.dumps(incomplete) + "\n")
        fh.write(json.dumps(_make_record(cp_hour=20)) + "\n")

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.found_records == 1


# --- Negative test scenarios (patch-forward) ----------------------------------


def test_leakage_detected_future_nwp(tmp_path: Path):
    """A forecast with nwp_run_time_utc AFTER cp_utc is a leakage violation."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
    ]
    # Inject leakage: cp_utc is 20:00, but nwp_run_time is 21:00 (future).
    records[0]["routing"]["nwp_run_time_utc"] = "2025-01-15T21:00:00+00:00"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.leakage_violations == 1


def test_leakage_none_when_nwp_before_cp(tmp_path: Path):
    """Normal case: nwp_run_time BEFORE cp_utc - 60min -> no leakage."""
    forecasts_dir = tmp_path / "forecasts"
    records = [_make_record(cp_hour=20)]
    # cp_utc is 20:00, causal cutoff is 19:00, NWP run is 12:00 (well before cutoff).
    records[0]["routing"]["nwp_run_time_utc"] = "2025-01-15T12:00:00+00:00"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.leakage_violations == 0


def test_leakage_detected_inside_safety_margin(tmp_path: Path):
    """NWP run time inside the 60-min safety margin is leakage.

    The causal selector requires run_time <= cp_utc - 60min.
    A run 30 min before CP (at 19:30 for CP20) is non-causal.
    """
    forecasts_dir = tmp_path / "forecasts"
    records = [_make_record(cp_hour=20)]
    # cp_utc is 20:00, causal cutoff is 19:00, NWP run at 19:30 is AFTER cutoff.
    records[0]["routing"]["nwp_run_time_utc"] = "2025-01-15T19:30:00+00:00"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.leakage_violations == 1


def test_leakage_checks_all_run_time_fields(tmp_path: Path):
    """Leakage check should detect leakage in any NWP run time field."""
    forecasts_dir = tmp_path / "forecasts"
    records = [_make_record(cp_hour=20)]
    # Only gfs_selected_run_time is set (inside safety margin).
    records[0]["routing"]["gfs_selected_run_time"] = "2025-01-15T19:45:00+00:00"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.leakage_violations == 1


def test_duplicate_cps_not_counted_as_coverage(tmp_path: Path):
    """Duplicate CP records should not count as coverage (P1 fix).

    A file with 4 lines of CP20 should have found_records=1 (unique), not 4.
    """
    forecasts_dir = tmp_path / "forecasts"
    # 4 records all with CP20 (duplicates).
    records = [
        _make_record(cp_hour=20),
        _make_record(cp_hour=20),  # duplicate
        _make_record(cp_hour=20),  # duplicate
        _make_record(cp_hour=20),  # duplicate
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    # Only 1 unique CP found, not 4.
    assert metrics.found_records == 1
    # 3 duplicates detected.
    assert metrics.duplicate_cp_records == 3
    # Completeness should be 1/4 = 0.25.
    assert metrics.completeness == pytest.approx(0.25)


def test_completeness_missing_whole_date_in_window(tmp_path: Path):
    """A missing date in the window reduces completeness below 1.0."""
    forecasts_dir = tmp_path / "forecasts"
    # Only write data for 2 of 5 days in window.
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 1))
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 3))
    # Days 2, 4, 5 are missing.

    metrics = compute_metrics(
        tmp_path,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 5),
        expected_cps=(20, 21, 22, 23),
    )
    # Expected: 5 days * 4 CPs = 20 records.
    assert metrics.expected_records == 20
    # Found: only 2 days * 4 CPs = 8 records.
    assert metrics.found_records == 8
    assert metrics.completeness == pytest.approx(0.4)
    assert metrics.dates_expected == 5
    assert metrics.dates_found == 2


def test_missing_inventory_includes_whole_missing_dates(tmp_path: Path):
    """A window date with no JSONL file is listed with all expected CPs missing."""
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 1))
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 3))

    metrics = compute_metrics(
        tmp_path,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        expected_cps=(20, 21, 22, 23),
    )

    assert metrics.missing_inventory == [("2025-01-02", [20, 21, 22, 23])]


def test_residual_served_not_counted_for_ridge_fallback(tmp_path: Path):
    """All-Ridge fallback at CP20-22 should NOT count as residual served."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, served_model="ridge"),
        _make_record(cp_hour=21, served_model="ridge"),
        _make_record(cp_hour=22, served_model="ridge"),
        _make_record(cp_hour=23, served_model="ridge"),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    # CP20-22 all served by ridge -> residual_served_count = 0.
    assert metrics.total_cp20_22_count == 3
    assert metrics.residual_served_cp20_22_count == 0
    assert metrics.residual_served_rate_cp20_22 == 0.0


def test_residual_served_counted_for_ecmwf_residual(tmp_path: Path):
    """ecmwf_residual served at CP20-22 should count as residual served."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, served_model="ecmwf_residual"),
        _make_record(cp_hour=21, served_model="ecmwf_residual"),
        _make_record(cp_hour=22, served_model="gfs_residual"),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.total_cp20_22_count == 3
    assert metrics.residual_served_cp20_22_count == 3


def test_gfs_telemetry_counted(tmp_path: Path):
    """GFS cache/fetch telemetry should be counted separately from ECMWF."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
    ]
    # Add GFS telemetry.
    for r in records:
        r["routing"]["gfs_cache_hit"] = True
        r["routing"]["gfs_fetch_status"] = "success"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.gfs_cache_hit_count == 2
    assert metrics.gfs_fetch_success_count == 2
    # ECMWF also counted (from default fixture).
    assert metrics.ecmwf_cache_hit_count == 2


def test_unexpected_cp_not_counted_as_coverage(tmp_path: Path):
    """CPs outside the contracted set must NOT count as found_records.

    A file with CP19/20/21/22 should report found_records=3 (only 20-22),
    unexpected_cp_records=1, and completeness=0.75 (3 of 4 expected).
    """
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=19),  # unexpected
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
        _make_record(cp_hour=22),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.found_records == 3
    assert metrics.unexpected_cp_records == 1
    assert metrics.completeness == pytest.approx(0.75)
    # CP23 is missing, so dates_complete should be 0.
    assert metrics.dates_complete == 0


def test_dates_complete_requires_exact_expected_set(tmp_path: Path):
    """Unexpected CPs do NOT compensate for missing expected CPs.

    A file with CP19 (unexpected) + CP20/21/22 (expected) is missing CP23.
    dates_complete should be 0 because the exact set {20,21,22,23} is not met.
    """
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=19),  # unexpected, but valid ISO hour
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
        _make_record(cp_hour=22),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.found_records == 3
    assert metrics.unexpected_cp_records == 1
    assert metrics.dates_complete == 0  # CP23 missing
    assert metrics.completeness == pytest.approx(0.75)


# --- Wave 2: missing inventory, fallback distribution, NWP endpoint, weekly ---


def test_compute_metrics_missing_inventory(tmp_path: Path):
    """Missing CPs are recorded in missing_inventory."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert len(metrics.missing_inventory) == 1
    date_iso, missing = metrics.missing_inventory[0]
    assert date_iso == "2025-01-15"
    assert missing == [22, 23]


def test_compute_metrics_no_missing_inventory_when_complete(tmp_path: Path):
    """When all CPs are present, missing_inventory is empty."""
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15))

    metrics = compute_metrics(tmp_path, expected_cps=(20, 21, 22, 23))
    assert metrics.missing_inventory == []


def test_compute_metrics_fallback_by_cp(tmp_path: Path):
    """Fallbacks are counted per CP."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, fallback_used=True, fallback_reason="nwp_unavailable"),
        _make_record(cp_hour=21, fallback_used=True, fallback_reason="cache_miss"),
        _make_record(cp_hour=22, fallback_used=False),
        _make_record(cp_hour=23, fallback_used=True, fallback_reason="nwp_unavailable"),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.fallback_by_cp[20] == 1
    assert metrics.fallback_by_cp[21] == 1
    assert metrics.fallback_by_cp[23] == 1
    assert 22 not in metrics.fallback_by_cp


def test_compute_metrics_fallback_by_model(tmp_path: Path):
    """Fallbacks are counted per served_model."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20, fallback_used=True, served_model="ridge"),
        _make_record(cp_hour=21, fallback_used=True, served_model="ridge"),
        _make_record(cp_hour=22, fallback_used=True, served_model="ecmwf_residual"),
        _make_record(cp_hour=23, fallback_used=False, served_model="gfs_residual"),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert metrics.fallback_by_model["ridge"] == 2
    assert metrics.fallback_by_model["ecmwf_residual"] == 1
    assert "gfs_residual" not in metrics.fallback_by_model


def test_compute_metrics_nwp_endpoint_summary(tmp_path: Path):
    """NWP endpoint summary aggregates ECMWF and GFS telemetry."""
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(cp_hour=20),
        _make_record(cp_hour=21),
    ]
    for r in records:
        r["routing"]["gfs_cache_hit"] = True
        r["routing"]["gfs_fetch_status"] = "success"
        r["routing"]["gfs_fetch_error_type"] = None
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    metrics = compute_metrics(tmp_path)
    assert "ecmwf" in metrics.nwp_endpoint_summary
    assert "gfs" in metrics.nwp_endpoint_summary
    assert metrics.nwp_endpoint_summary["ecmwf"]["cache_hit"] == 2
    assert metrics.nwp_endpoint_summary["gfs"]["cache_hit"] == 2


def test_render_weekly_markdown_structure():
    """Weekly report contains all Wave 2 sections."""
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        leakage_violations=0,
        fallback_by_cp={20: 1},
        fallback_by_model={"ridge": 1},
        missing_inventory=[("2025-01-15", [23])],
        nwp_endpoint_summary={
            "ecmwf": {"cache_hit": 2, "fetch_success": 2, "cache_repair": 0, "fetch_error": 0},
            "gfs": {"cache_hit": 1, "fetch_success": 1, "cache_repair": 0, "fetch_error": 0},
        },
    )
    gates = evaluate_gates(metrics)
    output = render_weekly_markdown(metrics, gates, "sha1")

    assert "# Shadow Ops Weekly Report v1" in output
    assert "sha1" in output
    assert "READY" in output
    assert "### By CP" in output
    assert "### By Model" in output
    assert "### By Reason" in output
    assert "## Missing Date/CP Inventory" in output
    assert "2025-01-15: missing CPs [23]" in output
    assert "## NWP Endpoint Summary" in output
    assert "ecmwf:" in output
    assert "gfs:" in output


def test_render_markdown_includes_wave2_sections():
    """Readiness markdown (not weekly) includes Wave 2 sections."""
    metrics = ReadinessMetrics(
        expected_records=4,
        found_records=4,
        missing_inventory=[("2025-01-15", [23])],
        fallback_by_cp={20: 1},
        fallback_by_model={"ridge": 1},
        nwp_endpoint_summary={
            "ecmwf": {"cache_hit": 2, "fetch_success": 2, "cache_repair": 0, "fetch_error": 0},
        },
    )
    gates = evaluate_gates(metrics)
    output = render_markdown(metrics, gates, "sha1")

    assert "## Missing Date/CP Inventory" in output
    assert "2025-01-15: missing CPs [23]" in output
    assert "### Fallback Distribution by CP" in output
    assert "### Fallback Distribution by Model" in output
    assert "### NWP Endpoint Summary" in output
    assert "ecmwf:" in output


def test_main_writes_shadow_window_aliases(monkeypatch, tmp_path: Path):
    """An explicit readiness window writes stable shadow_window artifacts."""
    shadow_root = tmp_path / "shadow"
    out_root = tmp_path / "reports"
    _write_fixture_jsonl(shadow_root / "forecasts", date(2025, 1, 15))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "live_shadow_readiness_report.py",
            "--shadow-root",
            str(shadow_root),
            "--out-root",
            str(out_root),
            "--start",
            "2025-01-15",
            "--end",
            "2025-01-15",
            "--git-sha",
            "sha-window",
        ],
    )

    assert main() == 0
    assert (out_root / "readiness_v1.json").exists()
    assert (out_root / "readiness_v1.md").exists()
    assert (out_root / "shadow_ops_weekly_v1.md").exists()
    assert (out_root / "shadow_window_2025-01-15_2025-01-15.json").exists()
    assert (out_root / "shadow_window_2025-01-15_2025-01-15.md").exists()


def test_render_weekly_markdown_no_fallbacks():
    """Weekly report handles zero-fallback gracefully."""
    metrics = ReadinessMetrics(expected_records=4, found_records=4)
    gates = evaluate_gates(metrics)
    output = render_weekly_markdown(metrics, gates, "sha1")

    assert "(no fallbacks)" in output
    assert "(no missing CPs)" in output
