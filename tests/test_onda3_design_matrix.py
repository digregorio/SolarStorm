from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._design_matrix import build_onda3_design_matrix


def test_design_matrix_joins_labels_and_binary_macro_without_mutating_inputs():
    features = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00"],
            "k_cp": [21, 22],
            "cloud_cover_suppression": [1.0, 2.0],
        }
    )
    labels = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "tmax_int": [24, 25],
        }
    )
    assignments = pl.DataFrame(
        {
            "date_local": [dt.date(2024, 1, 1), dt.date(2025, 1, 1)],
            "cp": ["20:00", "20:00"],
            "binary_macro_regime_label": ["macro_non_southerly", "macro_southerly_flow"],
            "production_status": ["EXPERIMENT_ONLY", "EXPERIMENT_ONLY"],
        }
    )

    matrix, audit = build_onda3_design_matrix(
        features=features,
        labels=labels,
        binary_assignments=assignments,
        train_end=dt.date(2024, 12, 31),
        test_start=dt.date(2025, 1, 1),
    )

    assert matrix.height == 2
    assert "binary_macro_regime_label" in matrix.columns
    assert matrix.filter(pl.col("fold") == "train").height == 1
    assert matrix.filter(pl.col("fold") == "test").height == 1
    assert set(audit["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert audit.row(0, named=True)["joined_rows"] == 2
