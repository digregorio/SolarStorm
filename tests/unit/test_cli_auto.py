"""CLI smoke: ``forecast --model auto --dry-run`` returns valid JSON (Phase 3, T-11-9).

Proves the conservative router is wired into the CLI end-to-end:
  * Phase 3 has no live NWP, so the router degrades to ridge (or the empirical
    floor when training rows are insufficient) without exploding.
  * stdout stays pure JSON; the --model auto diagnostic goes to stderr.
  * the emitted row carries a ``routing`` block with ``spread_used == False``.

Heavy loaders are monkeypatched in the ``core.cli.forecast`` namespace (mirrors
tests/unit/test_cli_decide.py) so the 20 MB NZWN.csv and model fitting are avoided.
"""

from __future__ import annotations

import json
import types
from datetime import date, datetime, timezone

import pytest

from core.features.training_panel import FEATURE_COLUMNS


class _FakeDateCol:
    """Stand-in for a polars date Series used only for window filtering."""

    def __init__(self, dates):
        self._dates = dates

    def unique(self):
        return self

    def to_list(self):
        return list(self._dates)

    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True


class _FakePanel:
    def __init__(self, dates):
        self._dates = dates

    def filter(self, *a, **kw):
        return self

    def __getitem__(self, key):
        return _FakeDateCol(self._dates)


class _FakeSeries:
    def __init__(self, height, dates):
        self._height = height
        self._dates = dates

    def to_numpy(self):
        import numpy as np

        return np.zeros(self._height)

    def to_list(self):
        return list(self._dates)[: self._height] or list(self._dates)


class _FakeTPanel:
    """Training panel whose only meaningful property is ``height``.

    When ``height >= 100`` the ridge branch fits (mocked); below that the auto
    path degrades to empirical and the column accessors are never touched.
    """

    def __init__(self, height, dates):
        self._height = height
        self._dates = [date(2025, 7, 1)] * height if height else list(dates)

    @property
    def height(self):
        return self._height

    def filter(self, *a, **kw):
        return self

    def __getitem__(self, key):
        return _FakeSeries(self._height, self._dates)


class _FakeClimo:
    def percentiles_for(self, d):
        return (10.0, 20.0)

    def tmax_dec_for(self, d):
        return 14.0


class _FakeEmpirical:
    def predict_dist(self, **kwargs):
        return {14: 1.0}, "empirical_fake"


class _FakeCfg:
    cp_set_utc = ["20:00", "21:00", "22:00", "23:00"]
    tz = "Pacific/Auckland"
    icao = "NZWN"

    class tmp_c_int_plausibility:
        min = -10
        max = 45


class _FakeStats:
    fallback_rate = 0.0


class _FakeFeats:
    cp_utc = datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc)
    cp_local = datetime(2025, 7, 15, 22, 0)
    feature_max_ts_utc = datetime(2025, 7, 15, 9, 30, tzinfo=timezone.utc)
    features = {**{c: 1.0 for c in FEATURE_COLUMNS}, "k_cp": 14}


def _fake_probe_unavailable(**kwargs):
    """Default probe stub: no causal NWP on disk (Phase-3 expectation)."""
    from core.ingest.nwp_live import NwpProbe

    return NwpProbe(
        ecmwf_available=False, gfs_available=False,
        ecmwf_run_time_utc=None, gfs_run_time_utc=None, nwp_run_time_utc=None,
        probe_root="fake", ecmwf_endpoint="single_runs", gfs_endpoint="s3_grib",
    )


def _invoke_auto(monkeypatch, tpanel_height, cp=22, probe=None):
    """Monkeypatch the forecast pipeline and invoke ``--model auto --dry-run``.

    The router itself (recommend_route/resolve_servable) is NOT mocked -- that is
    the unit under test. The NWP probe IS mocked (default: nothing available) so the
    test never reads the real on-disk snapshots; ``probe`` overrides it. With ecmwf/gfs
    unavailable the router routes to ridge (CP20-22 via NWP-absent fallback; CP23 by
    the conservative rule); the ridge fit is mocked, and ``tpanel_height`` decides
    ridge-served vs empirical.
    """
    dates = [date(2025, 7, 1), date(2025, 7, 2), date(2025, 7, 3)]

    monkeypatch.setattr(
        "core.cli.forecast.probe_causal_nwp", probe or _fake_probe_unavailable
    )
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
        lambda *a, **kw: _FakeTPanel(tpanel_height, dates),
    )
    monkeypatch.setattr(
        "core.cli.forecast.fit_ridge_band",
        lambda *a, **kw: types.SimpleNamespace(alpha=1.0),
    )
    monkeypatch.setattr("core.cli.forecast.ridge_predict_dist", lambda *a, **kw: [{14: 1.0}])

    from core.cli.forecast import run
    from typer.testing import CliRunner
    import typer

    app = typer.Typer()
    app.command()(run)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--date", "2025-07-15", "--cp", str(cp), "--model", "auto", "--dry-run"],
    )
    return result


def test_auto_dry_run_emits_valid_json_ridge_served(monkeypatch):
    """Enough training rows -> ridge is served; stdout is valid JSON with a routing block."""
    result = _invoke_auto(monkeypatch, tpanel_height=120)
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["model_requested"] == "auto"
    assert row["served_model"] == "ridge"
    assert row["feature_max_ts_utc"] == "2025-07-15T09:30:00+00:00"
    assert row["feature_staleness_min"] == 30
    assert row["k_cp_available"] is True

    routing = row["routing"]
    assert routing["cp"] == 22
    assert routing["model_route"] == "ridge"          # no NWP in Phase 3 -> ridge
    assert routing["served_model"] == "ridge"
    assert routing["fallback_used"] is True           # routed to ridge by NWP-absent fallback
    assert routing["fallback_reason"] == "no_causal_nwp_fallback_ridge"
    assert routing["decision_reason"] is None          # a fallback, not a CP23-style conservative decision
    assert routing["degraded_reason"] is None         # ridge is servable, no further degrade
    assert routing["ecmwf_available"] is False
    assert routing["gfs_available"] is False
    assert routing["ecmwf_endpoint"] == "single_runs"  # P3: endpoints recorded for traceability
    assert routing["gfs_endpoint"] == "s3_grib"
    assert routing["spread_used"] is False            # invariant: spread never routes

    # Banner is on stderr, never on stdout (keeps the JSON clean).
    assert "[forecast --model auto]" in result.stderr
    assert "spread_used=False" in result.stderr
    assert "[forecast --model auto]" not in result.stdout


def test_auto_ridge_builds_training_panel_for_requested_cp_only(monkeypatch):
    """A single-CP forecast must not rebuild the rich Ridge panel for all CPs."""
    captured: list[tuple[str, ...]] = []

    def _build_training_panel(*a, **kw):
        captured.append(tuple(kw["cp_set"]))
        return _FakeTPanel(120, [date(2025, 7, 1)])

    monkeypatch.setattr("core.cli.forecast.probe_causal_nwp", _fake_probe_unavailable)
    monkeypatch.setattr("core.cli.forecast.load_station_config", lambda _: _FakeCfg())
    monkeypatch.setattr("core.cli.forecast.load_observations", lambda *a, **kw: (None, _FakeStats()))
    monkeypatch.setattr("core.cli.forecast.build_tmax_labels", lambda *a, **kw: None)
    monkeypatch.setattr("core.cli.forecast.build_panel", lambda *a, **kw: _FakePanel([date(2025, 7, 1)]))
    monkeypatch.setattr("core.cli.forecast.fit_climatology", lambda *a, **kw: _FakeClimo())
    monkeypatch.setattr("core.cli.forecast.fit_empirical_conditional", lambda *a, **kw: _FakeEmpirical())
    monkeypatch.setattr("core.cli.forecast.build_cp_features", lambda *a, **kw: _FakeFeats())
    monkeypatch.setattr("core.cli.forecast.support_K", lambda *a, **kw: [13, 14, 15, 16])
    monkeypatch.setattr("core.cli.forecast.log_event", lambda *a, **kw: None)
    monkeypatch.setattr("core.cli.forecast.build_training_panel", _build_training_panel)
    monkeypatch.setattr("core.cli.forecast.fit_ridge_band", lambda *a, **kw: types.SimpleNamespace(alpha=1.0))
    monkeypatch.setattr("core.cli.forecast.ridge_predict_dist", lambda *a, **kw: [{14: 1.0}])

    from core.cli.forecast import run
    from typer.testing import CliRunner
    import typer

    app = typer.Typer()
    app.command()(run)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--date", "2025-07-15", "--cp", "22", "--model", "auto", "--dry-run"],
    )

    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))
    assert captured == [("22:00",)]


def test_auto_dry_run_cp23_records_decision_reason(monkeypatch):
    """CP23 keeping Ridge is a conservative DECISION end-to-end, not a fallback.

    CP23 is the most common Phase-3 path (no NWP needed to decide it), so pin the
    CLI-emitted routing block: decision_reason is populated and mentions cp23,
    while fallback_reason stays None and fallback_used is False (intern A8).
    """
    result = _invoke_auto(monkeypatch, tpanel_height=120, cp=23)
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["served_model"] == "ridge"

    routing = row["routing"]
    assert routing["cp"] == 23
    assert routing["model_route"] == "ridge"           # conservative rule, not a fallback
    assert routing["fallback_used"] is False
    assert routing["fallback_reason"] is None
    assert routing["decision_reason"] is not None
    assert "cp23" in routing["decision_reason"]
    assert routing["spread_used"] is False             # invariant: spread never routes


def test_auto_dry_run_degrades_to_empirical_without_exploding(monkeypatch):
    """Too few training rows -> auto degrades to the empirical floor (does NOT raise)."""
    result = _invoke_auto(monkeypatch, tpanel_height=5)
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["model_requested"] == "auto"
    assert row["served_model"] == "empirical"

    routing = row["routing"]
    assert routing["model_route"] == "ridge"
    assert routing["served_model"] == "empirical"
    assert routing["spread_used"] is False
    # The degradation reason records the row shortfall and the empirical fallback.
    assert "ridge_insufficient_rows_5" in routing["degraded_reason"]
    assert "fallback_empirical" in routing["degraded_reason"]


def test_auto_with_ecmwf_probe_routes_residual_serves_ridge(monkeypatch):
    """When the probe finds a causal ECMWF run, CP20-22 routes ecmwf_residual but
    still SERVES ridge this phase (no residual serving yet) -- model_route vs
    served_model are recorded distinctly, with a degraded_reason."""

    def _probe_ecmwf(**kwargs):
        from core.ingest.nwp_live import NwpProbe

        return NwpProbe(
            ecmwf_available=True, gfs_available=True,
            ecmwf_run_time_utc="2025-07-15T00:00:00+00:00",
            gfs_run_time_utc="2025-07-15T00:00:00+00:00",
            nwp_run_time_utc="2025-07-15T00:00:00+00:00",
            probe_root="fake", ecmwf_endpoint="single_runs", gfs_endpoint="s3_grib",
        )

    result = _invoke_auto(monkeypatch, tpanel_height=120, cp=22, probe=_probe_ecmwf)
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    row = json.loads(result.stdout)
    assert row["served_model"] == "ridge"

    routing = row["routing"]
    assert routing["cp"] == 22
    assert routing["model_route"] == "ecmwf_residual"   # real probe drives the route
    assert routing["served_model"] == "ridge"           # not servable this phase -> ridge
    assert routing["ecmwf_available"] is True
    assert routing["gfs_available"] is True
    assert routing["ecmwf_endpoint"] == "single_runs"  # P3: from probe.ecmwf_endpoint
    assert routing["gfs_endpoint"] == "s3_grib"
    assert routing["nwp_run_time_utc"] == "2025-07-15T00:00:00+00:00"
    assert "ecmwf_residual_not_servable" in routing["degraded_reason"]
    assert routing["spread_used"] is False              # invariant: spread never routes


def test_auto_no_nwp_probe_flag_forces_ridge(monkeypatch):
    """``--no-nwp-probe`` skips the probe entirely and treats NWP as unavailable."""
    # Even if the (unused) probe stub would say available, the flag must win.
    def _probe_would_be_available(**kwargs):  # pragma: no cover - must NOT be called
        raise AssertionError("probe must not run under --no-nwp-probe")

    monkeypatch.setattr("core.cli.forecast.probe_causal_nwp", _probe_would_be_available)
    monkeypatch.setattr("core.cli.forecast.load_station_config", lambda _: _FakeCfg())
    monkeypatch.setattr("core.cli.forecast.load_observations", lambda *a, **kw: (None, _FakeStats()))
    monkeypatch.setattr("core.cli.forecast.build_tmax_labels", lambda *a, **kw: None)
    monkeypatch.setattr("core.cli.forecast.build_panel", lambda *a, **kw: _FakePanel(
        [date(2025, 7, 1), date(2025, 7, 2), date(2025, 7, 3)]))
    monkeypatch.setattr("core.cli.forecast.fit_climatology", lambda *a, **kw: _FakeClimo())
    monkeypatch.setattr("core.cli.forecast.fit_empirical_conditional", lambda *a, **kw: _FakeEmpirical())
    monkeypatch.setattr("core.cli.forecast.build_cp_features", lambda *a, **kw: _FakeFeats())
    monkeypatch.setattr("core.cli.forecast.support_K", lambda *a, **kw: [13, 14, 15, 16])
    monkeypatch.setattr("core.cli.forecast.log_event", lambda *a, **kw: None)
    monkeypatch.setattr(
        "core.cli.forecast.build_training_panel",
        lambda *a, **kw: _FakeTPanel(120, [date(2025, 7, 1)]),
    )
    monkeypatch.setattr(
        "core.cli.forecast.fit_ridge_band",
        lambda *a, **kw: types.SimpleNamespace(alpha=1.0),
    )
    monkeypatch.setattr("core.cli.forecast.ridge_predict_dist", lambda *a, **kw: [{14: 1.0}])

    from core.cli.forecast import run
    from typer.testing import CliRunner
    import typer

    app = typer.Typer()
    app.command()(run)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["--date", "2025-07-15", "--cp", "22", "--model", "auto", "--no-nwp-probe", "--dry-run"],
    )
    assert result.exit_code == 0, (result.stdout, result.stderr, repr(result.exception))

    routing = json.loads(result.stdout)["routing"]
    assert routing["ecmwf_available"] is False
    assert routing["gfs_available"] is False
    assert routing["model_route"] == "ridge"
    # P3: even with the probe skipped, the canonical endpoints are recorded.
    assert routing["ecmwf_endpoint"] == "single_runs"
    assert routing["gfs_endpoint"] == "s3_grib"
