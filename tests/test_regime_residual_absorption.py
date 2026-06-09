from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl

from solarstorm.onda2e._regime_residual_absorption import (
    build_regime_residual_absorption_artifacts,
    write_regime_residual_absorption_artifacts,
)


def _v2_assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2025, 2, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_light_marine_or_residual",
                "subtype_label": "subtype_maritime_cloudy",
                "candidate_regime_label": "macro_light_marine_or_residual",
                "source_candidate_id": "RDC-V1-MONTH-2-C02",
                "component_argmax": "RDC-V1-MONTH-2-C02",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-2-C02": 0.6}),
                "family_probabilities": json.dumps(
                    {
                        "macro_light_marine_or_residual": 0.6,
                        "macro_nw_continuum": 0.3,
                        "macro_southerly_flow": 0.1,
                    }
                ),
                "component_entropy": 1.4,
                "component_margin": 0.1,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 1.2,
                "distance_to_alternative": 1.3,
                "assignment_confidence": 0.4,
                "low_confidence_flag": True,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
            {
                "date_local": dt.date(2025, 2, 2),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_southerly_disrupted",
                "candidate_regime_label": "macro_southerly_flow",
                "source_candidate_id": "RDC-V1-MONTH-2-C05",
                "component_argmax": "RDC-V1-MONTH-2-C05",
                "component_probabilities": json.dumps({"RDC-V1-MONTH-2-C05": 0.9}),
                "family_probabilities": json.dumps({"macro_southerly_flow": 0.9}),
                "component_entropy": 0.2,
                "component_margin": 0.8,
                "nearest_alternative_macro": "macro_nw_continuum",
                "distance_to_candidate": 0.2,
                "distance_to_alternative": 1.0,
                "assignment_confidence": 0.9,
                "low_confidence_flag": False,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def test_residual_absorption_reassigns_to_nearest_physical_macro():
    artifacts = build_regime_residual_absorption_artifacts(_v2_assignments())

    assignments = artifacts["regime_candidate_assignments_v2_1"]
    diagnostics = artifacts["regime_residual_absorption_diagnostics"]
    absorbed = assignments.filter(pl.col("absorbed_from_residual")).row(0, named=True)
    kept = assignments.filter(~pl.col("absorbed_from_residual")).row(0, named=True)

    assert assignments.height == 2
    assert absorbed["candidate_version"] == "v2.1"
    assert absorbed["macro_regime_label"] == "macro_nw_continuum"
    assert absorbed["candidate_regime_label"] == "macro_nw_continuum"
    assert absorbed["original_macro_regime_label"] == "macro_light_marine_or_residual"
    assert absorbed["original_subtype_label"] == "subtype_maritime_cloudy"
    assert "nearest physical macro" in absorbed["residual_absorption_reason"]
    assert kept["macro_regime_label"] == "macro_southerly_flow"
    assert kept["original_macro_regime_label"] == "macro_southerly_flow"
    assert set(assignments["production_status"]) == {"NOT_PRODUCTION"}
    assert diagnostics.filter(pl.col("diagnostic_item") == "invalid_absorption_targets").row(
        0,
        named=True,
    )["status"] == "PASS"


def test_write_regime_residual_absorption_artifacts(tmp_path: Path):
    artifacts = build_regime_residual_absorption_artifacts(_v2_assignments())

    paths = write_regime_residual_absorption_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 8),
    )

    assert (tmp_path / "regime_candidate_assignments_v2_1.csv").exists()
    assert (tmp_path / "regime_candidate_ontology_v2_1.csv").exists()
    assert (tmp_path / "regime_residual_absorption_diagnostics_v1.csv").exists()
    assert (tmp_path / "regime_residual_absorption_diagnostics_v1.md").exists()
    report = paths["regime_residual_absorption_diagnostics_md"].read_text(
        encoding="utf-8"
    )
    assert "Regime Residual Absorption Diagnostics - 2026-06-08" in report
    assert "not a production classifier" in report
