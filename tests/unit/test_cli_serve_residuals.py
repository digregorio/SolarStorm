"""CLI end-to-end tests for ``forecast --model auto --serve-residuals`` (Onda 2 Track B).

Two layers:

* **Wiring (CLI level):** monkeypatch ``core.cli.forecast.serve_residual`` and the
  heavy loaders (mirroring ``tests/unit/test_cli_auto.py``) to pin the contract the
  reviewer asked for - served path populates the P3b telemetry
  (``valid_time_utc``/``valid_time_delta_h``/``lead_h``/``run_age_h``), every
  fallback reason is recorded as ``<reason>_fallback_ridge``, CP23 ignores the flag,
  and the flag-off path is a no-op (residual never serves).
* **Leakage pin (helper level):** call the REAL ``serve_residual`` with synthetic
  snapshots whose ONLY run is non-causal (``run_time_utc > cp_utc - safety``) and
  assert it returns ``(None, "no_causal_nwp_serve_row")`` without ever fitting -
  the frozen ``select_max_trajectory_anchor`` refuses the too-fresh run.
"""

from __future__ import annotations

import json
import types
from datetime import date, datetime, timedelta, timezone

import polars as pl
import pytest

from tests.unit.test_cli_auto import (
    _FakeCfg,
    _FakeClimo,
    _FakeEmpirical,
    _FakeFeats,
    _FakePanel,
    _FakeStats,
    _FakeTPanel,
)


def _probe_ecmwf(**kwargs):
    """Probe stub: a causal ECMWF (and GFS) run is available on disk."""
    from core.ingest.nwp_live import NwpProbe

    return NwpProbe(
        ecmwf_available=True, gfs_available=True,
        ecmwf_run_time_utc="2025-07-15T00:00:00+00:00",
        gfs_run_time_utc="2025-07-15T00:00:00+00:00",
        nwp_run_time_utc="2025-07-15T00:00:00+00:00",
        probe_root="fake", ecmwf_endpoint="single_runs", gfs_endpoint="s3_grib",
    )


def _make_residual_serve():
    """A canned ResidualServe as the served residual arm would return at CP22."""
    from core.cli.residual_serving import ResidualServe

    return ResidualServe(
        prob_dist={14: 1.0},
        source="residual_lgbm_ecmwf_ifs_hres",
        model_version="phase5-residual-lgbm-v0",
        served_model="ecmwf_residual",
        run_time_utc="2025-07-15T00:00:00+00:00",
        valid_time_utc="2025-07-15T10:00:00+00:00",
        valid_time_delta_h=0.0,
        lead_h=10,
        run_age_h=10.0,
    )


def _invoke_serve(monkeypatch, *, serve_return, cp=22, serve_flag=True):
    """Invoke ``--model auto [--serve-residuals]`` with ``serve_residual`` mocked.

    ``serve_return`` is either a ``(ResidualServe, None)`` (served) or
    ``(None, reason)`` (deterministic Ridge fallback). When ``serve_return`` is the
    sentinel ``"MUST_NOT_CALL"`` the mock raises if invoked (CP23 / flag-off paths).
    The ECMWF probe is available so CP20-22 routes ``ecmwf_residual``; the ridge
    fallback fit is mocked so fallbacks still emit valid JSON.
    """
    dates = [date(2025, 7, 1), date(2025, 7, 2), date(2025, 7, 3)]

    monkeypatch.setattr("core.cli.forecast.probe_causal_nwp", _probe_ecmwf)
    monkeypatch.setattr("core.cli.forecast.load_station_config", lambda _: _FakeCfg())
    monkeypatch.setattr("core.cli.forecast.load_observations", lambda *a, **kw: (None, _FakeStats()))
    monkeypatch.setattr("core.cli.forecast.build_tmax_labels", lambda *a, **kw: None)
    monkeypatch.setattr("core.cli.forecast.build_panel", lambda *a, **kw: _FakePanel(dates))
    monkeypatch.setattr("core.cli.forecast.fit_climatology", lambda *a, **kw: _FakeClimo())
    monkeypatch.setattr("core.cli.forecast.fit_empirical_conditional", lambda *a, **kw: _FakeEmpirical())
    monkeypatch.setattr("core.cli.forecast.build_cp_features", lambda *a, **kw: _FakeFeats())
    monkeypatch.setattr("core.cli.forecast.support_K", lambda *a, **kw: [13, 14, 15, 16])
    monkeypatch.setattr("core.cli.forecast.log_event", lambda *a, **kw: None)
    monkeypatch.setattr(
        "core.cli.forecast.build_training_panel",
        lambda *a, **kw: _FakeTPanel(120, dates),
    )
    monkeypatch.setattr(
        "core.cli.forecast.fit_ridge_band",
        lambda *a, **kw: types.SimpleNamespace(alpha=1.0),
    )
    monkeypatch.setattr("core.cli.forecast.ridge_predict_dist", lambda *a, **kw: [{14: 1.0}])

    if serve_return == "MUST_NOT_CALL":
        def _serve(*a, **kw):  # pragma: no cover - asserted not to run
            raise AssertionError("serve_residual must not be called on this path")
    else:
        def _serve(*a, **kw):
            return serve_return

    monkeypatch.setattr("core.cli.forecast.serve_residual", _serve)

    from core.cli.forecast import run
    from typer.testing import CliRunner
    import typer

    app = typer.Typer()
    app.command()(run)
    runner = CliRunner()
    args = ["--date", "2025-07-15", "--cp", str(cp), "--model", "auto", "--dry-run"]
    if serve_flag:
        args.append("--serve-residuals")
    return runner.invoke(app, args)


def test_serve_residuals_served_path_records_telemetry(monkeypatch):
    """ECMWF causal -> the residual arm SERVES and the P3b telemetry is recorded."""
    result = _invoke_serve(monkeypatch, serve_return=(_make_residual_serve(), None))
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["model_requested"] == "auto"
    assert row["served_model"] == "ecmwf_residual"
    assert row["model_version"] == "phase5-residual-lgbm-v0"
    assert row["prob_dist_source"] == "residual_lgbm_ecmwf_ifs_hres"

    routing = row["routing"]
    assert routing["cp"] == 22
    assert routing["model_route"] == "ecmwf_residual"
    assert routing["served_model"] == "ecmwf_residual"
    assert routing["degraded_reason"] is None
    # P3b telemetry: nothing is "at CP" without a recorded valid_time trace.
    assert routing["valid_time_utc"] == "2025-07-15T10:00:00+00:00"
    assert routing["valid_time_delta_h"] == 0.0
    assert routing["lead_h"] == 10
    assert routing["run_age_h"] == 10.0
    assert routing["nwp_run_time_utc"] == "2025-07-15T00:00:00+00:00"
    assert routing["ecmwf_endpoint"] == "single_runs"
    assert routing["gfs_endpoint"] == "s3_grib"
    assert routing["spread_used"] is False

    # The second banner line (served telemetry) is on stderr only.
    assert "served=ecmwf_residual" in result.stderr
    assert "valid_time=" in result.stderr
    assert "served=ecmwf_residual" not in result.stdout


def test_serve_residuals_no_causal_nwp_falls_back_to_ridge(monkeypatch):
    """No causal serve-row anchor -> DETERMINISTIC Ridge fallback, reason recorded."""
    result = _invoke_serve(
        monkeypatch, serve_return=(None, "no_causal_nwp_serve_row")
    )
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["served_model"] == "ridge"

    routing = row["routing"]
    assert routing["model_route"] == "ecmwf_residual"   # router unchanged
    assert routing["served_model"] == "ridge"           # but served Ridge
    assert "no_causal_nwp_serve_row_fallback_ridge" in routing["degraded_reason"]
    # Telemetry keys are present even on fallback (None when residual did not serve).
    assert routing["valid_time_utc"] is None
    assert routing["valid_time_delta_h"] is None
    assert routing["lead_h"] is None
    assert routing["run_age_h"] is None


def test_serve_residuals_insufficient_rows_falls_back_to_ridge(monkeypatch):
    """Too few residual train rows -> Ridge fallback with the row-count reason."""
    result = _invoke_serve(
        monkeypatch, serve_return=(None, "residual_insufficient_train_rows_42")
    )
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["served_model"] == "ridge"
    routing = row["routing"]
    assert "residual_insufficient_train_rows_42_fallback_ridge" in routing["degraded_reason"]


def test_serve_residuals_cp23_ignores_flag(monkeypatch):
    """CP23 routes to ridge, so --serve-residuals is a no-op (serve_residual unused)."""
    result = _invoke_serve(monkeypatch, serve_return="MUST_NOT_CALL", cp=23)
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["served_model"] == "ridge"
    routing = row["routing"]
    assert routing["cp"] == 23
    assert routing["model_route"] == "ridge"            # conservative rule, unchanged
    assert routing["decision_reason"] is not None
    assert "cp23" in routing["decision_reason"]
    # No residual telemetry on the CP23 path.
    assert routing["valid_time_utc"] is None


def test_serve_residuals_flag_off_is_no_op(monkeypatch):
    """Without --serve-residuals the residual arm never runs (Phase-3 behavior)."""
    result = _invoke_serve(
        monkeypatch, serve_return="MUST_NOT_CALL", cp=22, serve_flag=False
    )
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    # ecmwf_residual route, but not servable this phase and flag off -> ridge.
    assert row["served_model"] == "ridge"
    routing = row["routing"]
    assert routing["model_route"] == "ecmwf_residual"
    assert "ecmwf_residual_not_servable" in routing["degraded_reason"]
    assert routing["valid_time_utc"] is None


# --------------------------------------------------------------------------- #
# Helper-level tests: call the REAL serve_residual (no CLI).
# --------------------------------------------------------------------------- #


def test_serve_residual_route_not_residual_returns_early():
    """A non-residual route is rejected before any I/O or fitting."""
    from core.cli.residual_serving import serve_residual

    result, reason = serve_residual(
        route_model="ridge",
        station="NZWN", obs=None, labels=None, climo=None, feats=None,
        support_k=[13, 14, 15], cp_hhmm="22:00", d=date(2025, 7, 15),
        tz_name="Pacific/Auckland", cp_set=["22:00"],
        train_start_d=date(2020, 1, 1), train_end_d=date(2025, 7, 14),
        nwp_root="fake",
    )
    assert result is None
    assert reason == "route_not_residual"


def _synthetic_noncausal_snaps(cp_utc: datetime) -> pl.DataFrame:
    """One ECMWF run issued AFTER the causal cutoff (run_time > cp - 60min).

    ``select_max_trajectory_anchor`` (via ``select_nwp_v1``) must filter it out
    entirely, so the anchor is None and no residual is ever fit from it.
    """
    run_time = cp_utc - timedelta(minutes=30)  # 30min < 60min safety -> NON-causal
    rows = []
    for lead in range(0, 6):
        rows.append({
            "station": "NZWN",
            "model": "ecmwf_ifs_hres",
            "endpoint": "single_runs",
            "run_time_utc": run_time,
            "valid_time_utc": cp_utc - timedelta(hours=5 - lead),
            "lead_h": lead,
            "t2m_c": 12.0 + lead,
            "wind_speed_10m": 5.0,
            "wind_direction_10m": 180.0,
            "pressure_msl": 1012.0,
            "cloud_cover": 50.0,
            "precipitation": 0.0,
        })
    return pl.DataFrame(rows).with_columns(
        pl.col("run_time_utc").dt.replace_time_zone("UTC"),
        pl.col("valid_time_utc").dt.replace_time_zone("UTC"),
        pl.col("lead_h").cast(pl.Int32),
    )


class _FakeThc:
    """Minimal tmax-hour climatology exposing the causal window only."""

    def __init__(self, cp_utc: datetime):
        self._cp_utc = cp_utc

    def window_utc(self, d, cp_utc):
        return (self._cp_utc - timedelta(hours=5), self._cp_utc)


class _FakeResidualPanel:
    """>=100-row panel so the row gate passes; columns never read (anchor fails first)."""

    height = 120

    def filter(self, *a, **kw):
        return self

    def __getitem__(self, key):  # pragma: no cover - not reached (anchor None first)
        raise AssertionError("panel columns must not be read when anchor is non-causal")


def test_serve_residual_leakage_pin_refuses_noncausal_run(monkeypatch):
    """A too-fresh run is NEVER served: anchor None -> (None, no_causal_nwp_serve_row).

    Mirrors tests/unit/test_nwp_leakage_gate.py at the serving boundary: the only
    snapshot run violates ``run_time <= cp - safety``, so the frozen anchor selector
    refuses it and the residual model is never fit (we assert the fit is unreachable).
    """
    cp_utc = datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc)
    feats = types.SimpleNamespace(
        cp_utc=cp_utc, cp_local=datetime(2025, 7, 15, 22, 0),
        features={"last_obs_tmp_c_int": 13},
    )

    monkeypatch.setattr(
        "core.cli.residual_serving.read_snapshots",
        lambda *a, **kw: _synthetic_noncausal_snaps(cp_utc),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.fit_tmax_hour_climatology",
        lambda *a, **kw: _FakeThc(cp_utc),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.build_training_panel",
        lambda *a, **kw: _FakeResidualPanel(),
    )

    def _must_not_fit(*a, **kw):  # pragma: no cover - asserted unreachable
        raise AssertionError("residual must NOT be fit from a non-causal run (leakage)")

    monkeypatch.setattr("core.cli.residual_serving.fit_residual_lgbm", _must_not_fit)

    from core.cli.residual_serving import serve_residual

    result, reason = serve_residual(
        route_model="ecmwf_residual",
        station="NZWN", obs=None,
        labels=pl.DataFrame({"date_local": [date(2025, 7, 1)]}),
        climo=_FakeClimo(), feats=feats,
        support_k=[13, 14, 15], cp_hhmm="22:00", d=date(2025, 7, 15),
        tz_name="Pacific/Auckland", cp_set=["22:00"],
        train_start_d=date(2020, 1, 1), train_end_d=date(2025, 7, 14),
        nwp_root="fake",
    )
    assert result is None
    assert reason == "no_causal_nwp_serve_row"


def _synthetic_anchor_snaps(cp_utc: datetime) -> pl.DataFrame:
    """Causal run where at-CP is not the max-trajectory anchor.

    The old telemetry path called ``select_nwp_ensemble(... target_valid=cp)`` and
    would report valid_time=CP. The served residual uses the max-trajectory anchor,
    whose peak here is CP+2h; telemetry must report that anchor row instead.
    """
    run_time = cp_utc - timedelta(hours=6)
    rows = [
        {
            "station": "NZWN",
            "model": "ecmwf_ifs_hres",
            "endpoint": "single_runs",
            "run_time_utc": run_time,
            "valid_time_utc": cp_utc,
            "lead_h": 6,
            "t2m_c": 12.0,
            "wind_speed_10m": 5.0,
            "wind_direction_10m": 180.0,
            "pressure_msl": 1012.0,
            "cloud_cover": 50.0,
            "precipitation": 0.0,
        },
        {
            "station": "NZWN",
            "model": "ecmwf_ifs_hres",
            "endpoint": "single_runs",
            "run_time_utc": run_time,
            "valid_time_utc": cp_utc + timedelta(hours=2),
            "lead_h": 8,
            "t2m_c": 20.0,
            "wind_speed_10m": 5.0,
            "wind_direction_10m": 180.0,
            "pressure_msl": 1012.0,
            "cloud_cover": 50.0,
            "precipitation": 0.0,
        },
    ]
    return pl.DataFrame(rows).with_columns(
        pl.col("run_time_utc").dt.replace_time_zone("UTC"),
        pl.col("valid_time_utc").dt.replace_time_zone("UTC"),
        pl.col("lead_h").cast(pl.Int32),
    )


def _residual_train_panel(cp: str = "22:00") -> pl.DataFrame:
    from core.cli.residual_serving import PHASE4_FEATURES

    rows = []
    for i in range(120):
        row = {c: 1.0 for c in PHASE4_FEATURES}
        row.update({
            "cp": cp,
            "target_tmax_int": 14 + (i % 2),
            "nwp_t2m_maxtraj_c": 13.0 + (i % 3),
        })
        rows.append(row)
    return pl.DataFrame(rows)


def test_serve_residual_reports_maxtraj_anchor_telemetry(monkeypatch):
    """Served telemetry follows the anchor row, not the separate at-CP selector."""
    cp_utc = datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc)
    feats = types.SimpleNamespace(
        cp_utc=cp_utc,
        cp_local=datetime(2025, 7, 15, 22, 0),
        features={
            "k_cp": 14,
            "last_obs_tmp_c_int": 13,
            "wind_dir_deg": 180.0,
        },
    )

    monkeypatch.setattr(
        "core.cli.residual_serving.read_snapshots",
        lambda *a, **kw: _synthetic_anchor_snaps(cp_utc),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.fit_tmax_hour_climatology",
        lambda *a, **kw: _FakeThc(cp_utc + timedelta(hours=2)),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.build_training_panel",
        lambda *a, **kw: _residual_train_panel(),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.fit_residual_lgbm",
        lambda *a, **kw: object(),
    )
    monkeypatch.setattr(
        "core.cli.residual_serving.residual_predict_dist",
        lambda *a, **kw: [{14: 1.0}],
    )

    from core.cli.residual_serving import serve_residual

    result, reason = serve_residual(
        route_model="ecmwf_residual",
        station="NZWN", obs=None,
        labels=pl.DataFrame({"date_local": [date(2025, 7, 1)]}),
        climo=_FakeClimo(), feats=feats,
        support_k=[13, 14, 15], cp_hhmm="22:00", d=date(2025, 7, 15),
        tz_name="Pacific/Auckland", cp_set=["22:00"],
        train_start_d=date(2020, 1, 1), train_end_d=date(2025, 7, 14),
        nwp_root="fake",
    )

    assert reason is None
    assert result is not None
    assert result.valid_time_utc == (cp_utc + timedelta(hours=2)).isoformat()
    assert result.valid_time_delta_h == 2.0
    assert result.lead_h == 8
    assert result.run_age_h == 6.0
