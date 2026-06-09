from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.onda2e._regime_candidate_revision import (
    build_regime_design_candidate_v2,
    write_regime_design_candidate_v2_artifacts,
)

runner = CliRunner()


def _candidate_v1_rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_id": "RDC-V1-MONTH-1-C00",
                "candidate_regime_family": "mixed_or_transition",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 40,
                "interpretability_score": 0.25,
                "physical_signature": "weak_gradient;cloudy",
                "wind_dir_deg_mean": 202.5,
                "wind_speed_mean": 7.25,
                "qnh_hpa_mean": 1017.75,
                "relh_mean": 88.5,
                "dewpoint_depression_mean": 1.5,
                "precip_pre_cp_sum_mean": 0.2,
                "cloud_cover_score_mean": 2.75,
                "temp_slope_pre_cp_mean": -0.12,
                "dominant_current_regime": "calm_radiative",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_id": "RDC-V1-MONTH-1-C01",
                "candidate_regime_family": "maritime_cloudy_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 50,
                "interpretability_score": 0.6,
                "physical_signature": "moist_cloudy_or_rain",
                "wind_dir_deg_mean": 190.0,
                "wind_speed_mean": 9.0,
                "qnh_hpa_mean": 1013.0,
                "relh_mean": 92.0,
                "dewpoint_depression_mean": 0.9,
                "precip_pre_cp_sum_mean": 0.6,
                "cloud_cover_score_mean": 3.0,
                "temp_slope_pre_cp_mean": -0.2,
                "dominant_current_regime": "calm_radiative",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_id": "RDC-V1-MONTH-1-C02",
                "candidate_regime_family": "nw_or_foehn_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 60,
                "interpretability_score": 0.7,
                "physical_signature": "northerly_nw_flow;windy",
                "wind_dir_deg_mean": 352.0,
                "wind_speed_mean": 17.0,
                "qnh_hpa_mean": 1008.0,
                "relh_mean": 65.0,
                "dewpoint_depression_mean": 7.5,
                "precip_pre_cp_sum_mean": 0.0,
                "cloud_cover_score_mean": 1.0,
                "temp_slope_pre_cp_mean": 0.4,
                "dominant_current_regime": "strong_nw_foehn",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_id": "RDC-V1-MONTH-1-C03",
                "candidate_regime_family": "southerly_disrupted_candidate",
                "stratum_type": "month",
                "stratum_value": "1",
                "n_rows": 70,
                "interpretability_score": 0.8,
                "physical_signature": "southerly_flow;cooling",
                "wind_dir_deg_mean": 180.0,
                "wind_speed_mean": 15.0,
                "qnh_hpa_mean": 1009.0,
                "relh_mean": 85.0,
                "dewpoint_depression_mean": 2.0,
                "precip_pre_cp_sum_mean": 0.1,
                "cloud_cover_score_mean": 2.0,
                "temp_slope_pre_cp_mean": -0.7,
                "dominant_current_regime": "southerly_disrupted",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_build_regime_design_candidate_v2_maps_macro_and_subtype_labels():
    artifacts = build_regime_design_candidate_v2(_candidate_v1_rows())

    candidate_v2 = artifacts["regime_design_candidate_v2"]

    assert candidate_v2.height == 4
    assert candidate_v2["candidate_version"].unique().to_list() == ["v2"]
    assert set(candidate_v2["production_status"]) == {"NOT_PRODUCTION"}
    by_id = {
        row["candidate_id"]: row
        for row in candidate_v2.iter_rows(named=True)
    }
    assert by_id["RDC-V1-MONTH-1-C00"]["macro_regime_label"] == "macro_light_marine_or_residual"
    assert by_id["RDC-V1-MONTH-1-C00"]["subtype_label"] == "subtype_transition_low_confidence"
    assert by_id["RDC-V1-MONTH-1-C01"]["macro_regime_label"] == "macro_light_marine_or_residual"
    assert by_id["RDC-V1-MONTH-1-C01"]["subtype_label"] == "subtype_maritime_cloudy"
    assert by_id["RDC-V1-MONTH-1-C02"]["macro_regime_label"] == "macro_nw_continuum"
    assert by_id["RDC-V1-MONTH-1-C03"]["macro_regime_label"] == "macro_southerly_flow"


def test_build_regime_design_candidate_v2_preserves_physical_centroid_columns_as_floats():
    candidate_v2 = build_regime_design_candidate_v2(_candidate_v1_rows())[
        "regime_design_candidate_v2"
    ]

    first = candidate_v2.row(0, named=True)

    assert first["wind_dir_deg_mean"] == 202.5
    assert first["wind_speed_mean"] == 7.25
    for column in [
        "wind_dir_deg_mean",
        "wind_speed_mean",
        "qnh_hpa_mean",
        "relh_mean",
        "dewpoint_depression_mean",
        "precip_pre_cp_sum_mean",
        "cloud_cover_score_mean",
        "temp_slope_pre_cp_mean",
    ]:
        assert candidate_v2.schema[column] == pl.Float64


def test_build_regime_design_candidate_v2_rejects_missing_required_columns():
    candidate_v1 = _candidate_v1_rows().drop(["physical_signature", "relh_mean"])

    with pytest.raises(ValueError, match=r"physical_signature.*relh_mean"):
        build_regime_design_candidate_v2(candidate_v1)


def test_build_regime_design_candidate_v2_rejects_production_rows():
    candidate_v1 = _candidate_v1_rows().with_columns(
        pl.when(pl.col("candidate_id") == "RDC-V1-MONTH-1-C02")
        .then(pl.lit("PRODUCTION"))
        .otherwise(pl.col("production_status"))
        .alias("production_status")
    )

    with pytest.raises(ValueError, match=r"production_status.*NOT_PRODUCTION"):
        build_regime_design_candidate_v2(candidate_v1)


def test_write_regime_design_candidate_v2_artifacts(tmp_path: Path):
    artifacts = build_regime_design_candidate_v2(_candidate_v1_rows())

    paths = write_regime_design_candidate_v2_artifacts(
        artifacts,
        tmp_path,
        today=dt.date(2026, 6, 7),
    )

    csv_path = tmp_path / "regime_design_candidate_v2.csv"
    report_path = tmp_path / "regime_design_candidate_v2.md"
    assert paths["regime_design_candidate_v2_csv"] == csv_path
    assert paths["regime_design_candidate_v2_md"] == report_path
    assert csv_path.exists()
    assert report_path.exists()
    persisted = pl.read_csv(csv_path)
    assert persisted.height == 4
    report = report_path.read_text(encoding="utf-8")
    assert "# Regime Design Candidate v2 - 2026-06-07" in report
    assert "NOT_PRODUCTION" in report


def test_regime_candidate_v2_cli_writes_artifacts(tmp_path: Path):
    candidate_v1_path = tmp_path / "regime_design_candidate_v1.csv"
    output_dir = tmp_path / "onda2e"
    _candidate_v1_rows().write_csv(candidate_v1_path)

    result = runner.invoke(
        app,
        [
            "regime-candidate-v2",
            "--candidate-v1-path",
            str(candidate_v1_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output_dir / "regime_design_candidate_v2.csv").exists()
    assert (output_dir / "regime_design_candidate_v2.md").exists()
