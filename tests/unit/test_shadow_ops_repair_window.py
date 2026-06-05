"""Unit tests for scripts/shadow_ops_repair_window.py (Wave 3)."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import shadow_ops_repair_window as repair
from core.ops.shadow_runner import ShadowRunResult, ShadowRunnerConfig


def _make_record(cp_hour: int) -> dict:
    return {
        "run_id": f"test-run-cp{cp_hour}",
        "date_local": "2025-01-15",
        "cp_utc": f"2025-01-15T{cp_hour:02d}:00:00+00:00",
        "prob_dist": {"18": 0.3, "19": 0.5, "20": 0.2},
        "model_version": "phase3-ridge-band-v1.0",
        "routing": {"served_model": "ecmwf_residual", "fallback_used": False},
        "p50_int": 19,
    }


def _write_fixture_jsonl(
    forecasts_dir: Path,
    target_date: date,
    records: list[dict] | None = None,
) -> Path:
    forecasts_dir.mkdir(parents=True, exist_ok=True)
    out_path = forecasts_dir / f"{target_date.isoformat()}.jsonl"
    if records is None:
        records = [_make_record(cp) for cp in (20, 21, 22, 23)]
    with open(out_path, "w", encoding="ascii") as fh:
        for record in records:
            record = dict(record)
            record["date_local"] = target_date.isoformat()
            cp_hour = int(str(record["cp_utc"]).split("T")[1].split(":")[0])
            record["cp_utc"] = f"{target_date.isoformat()}T{cp_hour:02d}:00:00+00:00"
            fh.write(json.dumps(record) + "\n")
    return out_path


def test_build_repair_plan_includes_whole_missing_dates(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 1))
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 3))

    plan = repair.build_repair_plan(
        tmp_path,
        date(2025, 1, 1),
        date(2025, 1, 3),
    )

    assert plan.dates == (date(2025, 1, 2),)
    assert plan.missing_inventory == (("2025-01-02", (20, 21, 22, 23)),)


def test_build_repair_plan_includes_partial_missing_cps(tmp_path: Path):
    forecasts_dir = tmp_path / "forecasts"
    records = [
        _make_record(20),
    ]
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 15), records)

    plan = repair.build_repair_plan(
        tmp_path,
        date(2025, 1, 15),
        date(2025, 1, 15),
    )

    assert plan.dates == (date(2025, 1, 15),)
    assert plan.missing_inventory == (("2025-01-15", (21, 22, 23)),)


def test_run_repair_plan_dry_run_does_not_invoke_runner(tmp_path: Path):
    plan = repair.RepairPlan(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 1),
        dates=(date(2025, 1, 1),),
        missing_inventory=(("2025-01-01", (20, 21, 22, 23)),),
    )

    summary = repair.run_repair_plan(
        plan,
        ShadowRunnerConfig(shadow_root=tmp_path),
        dry_run=True,
    )

    assert summary.dry_run is True
    assert summary.results == ()
    assert summary.repaired_dates == 0


def test_run_repair_plan_invokes_runner_for_planned_dates(monkeypatch, tmp_path: Path):
    calls: list[date] = []

    class FakeRunner:
        def __init__(self, config: ShadowRunnerConfig) -> None:
            self.config = config

        def run_date(self, target_date: date) -> ShadowRunResult:
            calls.append(target_date)
            return ShadowRunResult(
                date_local=target_date,
                output_path=tmp_path / "forecasts" / f"{target_date.isoformat()}.jsonl",
            )

    monkeypatch.setattr(repair, "ShadowRunner", FakeRunner)
    plan = repair.RepairPlan(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        dates=(date(2025, 1, 1), date(2025, 1, 2)),
        missing_inventory=(
            ("2025-01-01", (20,)),
            ("2025-01-02", (21,)),
        ),
    )

    summary = repair.run_repair_plan(
        plan,
        ShadowRunnerConfig(shadow_root=tmp_path, with_decisions=True),
        dry_run=False,
    )

    assert calls == [date(2025, 1, 1), date(2025, 1, 2)]
    assert summary.with_decisions is True
    assert summary.repaired_dates == 2


def test_render_summary_json_and_markdown_expose_inventory(tmp_path: Path):
    plan = repair.RepairPlan(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 1),
        dates=(date(2025, 1, 1),),
        missing_inventory=(("2025-01-01", (20, 21)),),
    )
    summary = repair.RepairSummary(plan=plan, dry_run=True, with_decisions=False)

    raw = repair.render_summary_json(summary)
    md = repair.render_summary_markdown(summary)

    assert raw["planned_dates"] == ["2025-01-01"]
    assert raw["planned_missing_inventory"][0]["missing_cps"] == [20, 21]
    assert "2025-01-01: missing CPs [20, 21]" in md


def test_main_writes_repair_reports_in_dry_run(monkeypatch, tmp_path: Path):
    shadow_root = tmp_path / "shadow"
    out_root = tmp_path / "reports"
    forecasts_dir = shadow_root / "forecasts"
    _write_fixture_jsonl(forecasts_dir, date(2025, 1, 1))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "shadow_ops_repair_window.py",
            "--start",
            "2025-01-01",
            "--end",
            "2025-01-02",
            "--shadow-root",
            str(shadow_root),
            "--out-root",
            str(out_root),
            "--dry-run",
        ],
    )

    assert repair.main() == 0
    json_path = out_root / "shadow_repair_2025-01-01_2025-01-02.json"
    md_path = out_root / "shadow_repair_2025-01-01_2025-01-02.md"
    assert json_path.exists()
    assert md_path.exists()
    raw = json.loads(json_path.read_text(encoding="ascii"))
    assert raw["dry_run"] is True
    assert raw["planned_dates"] == ["2025-01-02"]
