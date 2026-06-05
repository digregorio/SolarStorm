"""Tests for scripts/run_live_forecast_once.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import run_live_forecast_once as live_once


def test_run_live_forecast_once_ingests_before_forecast(monkeypatch, tmp_path: Path, capsys):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        if "ingest-live" in cmd:
            return subprocess.CompletedProcess(cmd, 0, '{"status":"ok"}\n', "")
        return subprocess.CompletedProcess(
            cmd,
            0,
            '{"feature_gap_to_cp_min":30,"k_cp_available":true}\n',
            "",
        )

    monkeypatch.setattr(live_once, "_run", fake_run)
    runtime_csv = tmp_path / "live.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(runtime_csv),
        ],
    )

    assert live_once.main() == 0
    assert "ingest-live" in calls[0]
    assert "forecast" in calls[1]
    assert str(runtime_csv) in calls[0]
    assert str(runtime_csv) in calls[1]
    assert capsys.readouterr().out == '{"feature_gap_to_cp_min":30,"k_cp_available":true}\n'


def test_run_live_forecast_once_fails_closed_when_stale(monkeypatch, tmp_path: Path, capsys):
    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        if "ingest-live" in cmd:
            return subprocess.CompletedProcess(cmd, 0, '{"status":"ok"}\n', "")
        return subprocess.CompletedProcess(
            cmd,
            0,
            '{"feature_gap_to_cp_min":9870,"k_cp_available":false}\n',
            "",
        )

    monkeypatch.setattr(live_once, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(tmp_path / "live.csv"),
        ],
    )

    assert live_once.main() == 2
    assert "feature_gap_to_cp_min=9870" in capsys.readouterr().err


def test_run_live_forecast_once_can_allow_stale_for_diagnostics(monkeypatch, tmp_path: Path, capsys):
    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        if "ingest-live" in cmd:
            return subprocess.CompletedProcess(cmd, 0, '{"status":"ok"}\n', "")
        return subprocess.CompletedProcess(
            cmd,
            0,
            '{"feature_gap_to_cp_min":9870,"k_cp_available":false}\n',
            "",
        )

    monkeypatch.setattr(live_once, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(tmp_path / "live.csv"),
            "--allow-stale",
        ],
    )

    assert live_once.main() == 0
    err = capsys.readouterr().err
    assert "feature_gap_to_cp_min=9870" in err
    assert "k_cp_available=false" in err


def test_run_live_forecast_once_fails_when_kcp_missing(monkeypatch, tmp_path: Path, capsys):
    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        if "ingest-live" in cmd:
            return subprocess.CompletedProcess(cmd, 0, '{"status":"ok"}\n', "")
        return subprocess.CompletedProcess(
            cmd,
            0,
            '{"feature_gap_to_cp_min":30,"k_cp_available":false}\n',
            "",
        )

    monkeypatch.setattr(live_once, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(tmp_path / "live.csv"),
        ],
    )

    assert live_once.main() == 2
    assert "k_cp_available=false" in capsys.readouterr().err


def test_run_live_forecast_once_stops_on_ingest_failure(monkeypatch, tmp_path: Path):
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, '{"status":"stale"}\n', "bad\n")

    monkeypatch.setattr(live_once, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(tmp_path / "live.csv"),
        ],
    )

    assert live_once.main() == 1
    assert len(calls) == 1


def test_run_live_forecast_once_timeout_returns_124(monkeypatch, tmp_path: Path, capsys):
    def fake_run(cmd: list[str], *, timeout_s: int) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd, timeout_s)

    monkeypatch.setattr(live_once, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_live_forecast_once.py",
            "--date",
            "2026-06-04",
            "--cp",
            "20",
            "--runtime-csv",
            str(tmp_path / "live.csv"),
            "--timeout-s",
            "1",
        ],
    )

    assert live_once.main() == 124
    assert "timed out after 1s" in capsys.readouterr().err
