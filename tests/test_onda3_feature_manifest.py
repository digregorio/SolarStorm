from __future__ import annotations

import polars as pl

from solarstorm.onda3._feature_manifest import build_onda3_feature_manifest


def test_feature_manifest_allows_only_causal_pre_cp_features():
    features = pl.DataFrame(
        {
            "date_local": ["2025-01-01"],
            "cp": ["20:00"],
            "k_cp": [22],
            "cloud_cover_suppression": [1.5],
            "foehn_score": [72.0],
            "binary_macro_regime_label": ["macro_non_southerly"],
            "remaining_warming": [3.0],
            "tmax_hour": [15],
            "tmax_int": [25],
        }
    )

    manifest = build_onda3_feature_manifest(features)
    by_feature = {row["feature"]: row for row in manifest.iter_rows(named=True)}

    assert by_feature["k_cp"]["included_in_onda3"]
    assert by_feature["cloud_cover_suppression"]["included_in_onda3"]
    assert by_feature["foehn_score"]["included_in_onda3"]
    assert by_feature["binary_macro_regime_label"]["included_in_onda3"]
    assert not by_feature["remaining_warming"]["included_in_onda3"]
    assert by_feature["remaining_warming"]["leakage_class"] == "blocked_target_or_proxy"
    assert not by_feature["tmax_hour"]["included_in_onda3"]
    assert not by_feature["tmax_int"]["included_in_onda3"]
    assert set(manifest["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
