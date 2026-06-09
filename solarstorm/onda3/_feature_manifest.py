from __future__ import annotations

import polars as pl

BLOCKED_TARGET_OR_PROXY = {
    "tmax_int",
    "tmax_hour",
    "remaining_warming",
    "tmax_anomaly",
}

IDENTIFIER_COLUMNS = {"date_local", "cp", "month", "season"}

MANIFEST_SCHEMA = {
    "feature": pl.Utf8,
    "included_in_onda3": pl.Boolean,
    "leakage_class": pl.Utf8,
    "feature_role": pl.Utf8,
    "production_status": pl.Utf8,
}


def build_onda3_feature_manifest(features: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for feature in features.columns:
        if feature in IDENTIFIER_COLUMNS:
            included = False
            leakage_class = "identifier"
            role = "join_key"
        elif feature in BLOCKED_TARGET_OR_PROXY:
            included = False
            leakage_class = "blocked_target_or_proxy"
            role = "blocked"
        else:
            included = True
            leakage_class = "causal_pre_cp_or_experiment_only"
            role = "candidate_input"
        rows.append(
            {
                "feature": feature,
                "included_in_onda3": included,
                "leakage_class": leakage_class,
                "feature_role": role,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, schema=MANIFEST_SCHEMA)
