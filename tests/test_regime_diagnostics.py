from __future__ import annotations

import datetime as dt

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.robustness._regime_diagnostics import (
    cooling_rule_experiment,
    regime_trigger_audit,
)

runner = CliRunner()


def _obs(rows: list[tuple[dt.date, int, int, float, float, float, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": d,
                "valid": dt.datetime(d.year, d.month, d.day, hour, tzinfo=dt.UTC),
                "ts_local": dt.datetime(d.year, d.month, d.day, hour),
                "hour_local": hour,
                "tmp_c_int": tmp,
                "dwp_c_int": dwp,
                "wind_dir_deg": drct,
                "drct": drct,
                "sknt": sknt,
                "p01i": p01i,
                "dq_tmp_c_int": "ok",
            }
            for d, hour, tmp, dwp, drct, sknt, p01i in rows
        ]
    )


def test_regime_trigger_audit_marks_cooling_as_primary_trigger():
    d = dt.date(2025, 6, 15)
    obs = _obs(
        [
            (d, 0, 14, 10, 90.0, 4.0, 0.0),
            (d, 3, 13, 10, 95.0, 4.0, 0.0),
            (d, 6, 6, 5, 100.0, 4.0, 0.0),
        ]
    )
    features = pl.DataFrame(
        [{"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"}]
    )

    audit = regime_trigger_audit(obs, features, cp_set=("20:00",), tz_name="UTC")

    row = audit.row(0, named=True)
    assert row["regime_label"] == "southerly_disrupted"
    assert row["primary_trigger"] == "cooling"
    assert row["cooling_trigger"] is True
    assert row["precip_trigger"] is False
    assert row["southerly_trigger"] is False


def test_regime_diagnostics_cli_writes_artifacts(tmp_path):
    d = dt.date(2025, 6, 15)
    obs = _obs(
        [
            (d, 0, 14, 10, 90.0, 4.0, 0.0),
            (d, 3, 13, 10, 95.0, 4.0, 0.0),
            (d, 6, 6, 5, 100.0, 4.0, 0.0),
        ]
    )
    features = pl.DataFrame(
        [{"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"}]
    )
    obs_path = tmp_path / "obs.parquet"
    features_path = tmp_path / "features.parquet"
    output_dir = tmp_path / "reports" / "regime"
    obs.write_parquet(obs_path)
    features.write_parquet(features_path)

    result = runner.invoke(
        app,
        [
            "regime-diagnostics",
            "--obs-path",
            str(obs_path),
            "--features-path",
            str(features_path),
            "--output-dir",
            str(output_dir),
            "--cp-set",
            "20:00",
            "--tz-name",
            "UTC",
        ],
    )

    assert result.exit_code == 0
    assert list(output_dir.glob("*-regime-trigger-audit.json"))
    assert list(output_dir.glob("*-regime-trigger-audit.md"))
    assert list(output_dir.glob("*-cooling-rule-experiment.json"))
    assert list(output_dir.glob("*-cooling-rule-experiment.md"))


def test_cooling_rule_experiment_keeps_radiative_cooling_out_of_southerly():
    d = dt.date(2025, 6, 15)
    obs = _obs(
        [
            (d, 0, 14, 10, 350.0, 3.0, 0.0),
            (d, 3, 13, 10, 350.0, 3.0, 0.0),
            (d, 6, 6, 5, 350.0, 3.0, 0.0),
        ]
    )
    features = pl.DataFrame(
        [{"date_local": d, "cp": "20:00", "regime_label": "southerly_disrupted"}]
    )
    audit = regime_trigger_audit(obs, features, cp_set=("20:00",), tz_name="UTC")

    experiment = cooling_rule_experiment(audit)

    rows = {row["variant"]: row for row in experiment.iter_rows(named=True)}
    assert rows["current"]["candidate_regime"] == "southerly_disrupted"
    assert rows["south_gated_cooling"]["candidate_regime"] == "standard_nw"
