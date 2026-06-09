"""Offline validation for Onda 2E regime-design candidates."""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.eda._hypotheses import Hypothesis
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA
from solarstorm.onda2e._full_eda import (
    CLUSTER_INPUT_COLUMNS,
    SEASONS,
    _build_cluster_matrix,
)
from solarstorm.robustness._regime_analysis import detect_dead_regimes, regime_sensitivity

ASSIGNMENT_SCHEMA: dict[str, pl.DataType] = {
    "date_local": pl.Date,
    "cp": pl.Utf8,
    "candidate_regime_label": pl.Utf8,
    "candidate_regime_family": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "distance_to_candidate": pl.Float64,
    "assignment_confidence": pl.Float64,
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_SCHEMA: dict[str, pl.DataType] = {
    "candidate_regime_label": pl.Utf8,
    "candidate_regime_family": pl.Utf8,
    "source_candidate_ids": pl.Utf8,
    "n_candidate_centroids": pl.Int64,
    "total_candidate_rows": pl.Int64,
    "mean_interpretability_score": pl.Float64,
    "production_status": pl.Utf8,
}

AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

DEAD_SCHEMA: dict[str, pl.DataType] = {
    "candidate_regime_family": pl.Utf8,
    "status": pl.Utf8,
}

VALIDATION_SCOPE_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

ASSIGNMENT_V2_SCHEMA: dict[str, pl.DataType] = {
    "date_local": pl.Date,
    "cp": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "candidate_regime_label": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "component_argmax": pl.Utf8,
    "component_probabilities": pl.Utf8,
    "family_probabilities": pl.Utf8,
    "component_entropy": pl.Float64,
    "component_margin": pl.Float64,
    "nearest_alternative_macro": pl.Utf8,
    "distance_to_candidate": pl.Float64,
    "distance_to_alternative": pl.Float64,
    "assignment_confidence": pl.Float64,
    "low_confidence_flag": pl.Boolean,
    "causal_window": pl.Utf8,
    "production_status": pl.Utf8,
}

ONTOLOGY_V2_SCHEMA: dict[str, pl.DataType] = {
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "latent_component_id": pl.Utf8,
    "source_candidate_id": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "n_source_rows": pl.Int64,
    "production_status": pl.Utf8,
}

AUDIT_V2_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

COMPARISON_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "protected_regression_flag": pl.Boolean,
    "low_confidence_share": pl.Float64,
    "mean_component_entropy": pl.Float64,
    "mean_component_margin": pl.Float64,
    "smallest_cp_support": pl.Int64,
    "v1_dead_regimes": pl.Int64,
    "v2_dead_regimes": pl.Int64,
    "protected_regressions": pl.Utf8,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
}

COMPARISON_V21_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "assignment_rows": pl.Int64,
    "absorbed_residual_rows": pl.Int64,
    "r2_rows": pl.Int64,
    "r2_pass_rows": pl.Int64,
    "r2_dead_status": pl.Utf8,
    "v2_dead_regimes": pl.Int64,
    "v21_dead_regimes": pl.Int64,
    "protected_regression_flag": pl.Boolean,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
}

V2_CENTROID_COLUMNS: tuple[str, ...] = (
    "wind_dir_deg_mean",
    "wind_speed_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum_mean",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp_mean",
)


def _empty_frame(schema: dict[str, pl.DataType]) -> pl.DataFrame:
    return pl.DataFrame(schema=schema)


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _family_label(family: str) -> str:
    normalized = family.removesuffix("_candidate")
    if normalized == "strong_nw_foehn":
        normalized = "nw_or_foehn"
    if normalized == "calm_radiative":
        normalized = "maritime_cloudy"
    if normalized == "cooling_disruption":
        normalized = "southerly_disrupted"
    return f"candidate_{normalized}"


def _candidate_vector(row: dict[str, object]) -> list[float | None]:
    wind_dir = _safe_float(row.get("wind_dir_deg_mean"))
    sin_mean = math.sin(math.radians(wind_dir)) if wind_dir is not None else None
    cos_mean = math.cos(math.radians(wind_dir)) if wind_dir is not None else None
    return [
        sin_mean,
        cos_mean,
        _safe_float(row.get("wind_speed_mean")),
        _safe_float(row.get("qnh_hpa_mean")),
        _safe_float(row.get("relh_mean")),
        _safe_float(row.get("dewpoint_depression_mean")),
        _safe_float(row.get("precip_pre_cp_sum_mean")),
        _safe_float(row.get("cloud_cover_score_mean")),
        _safe_float(row.get("temp_slope_pre_cp_mean")),
    ]


def _assignment_vector(row: dict[str, object]) -> list[float | None]:
    return [_safe_float(row.get(column)) for column in CLUSTER_INPUT_COLUMNS]


def _candidate_centroids(candidate: pl.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in candidate.iter_rows(named=True):
        if str(row.get("stratum_type")) not in {"month", "season"}:
            continue
        vector = _candidate_vector(row)
        if any(value is None for value in vector):
            continue
        family = str(row["candidate_regime_family"])
        rows.append(
            {
                "candidate_id": str(row["candidate_id"]),
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "candidate_regime_family": _family_label(family),
                "candidate_regime_label": _family_label(family),
                "n_rows": int(row.get("n_rows") or 0),
                "interpretability_score": _safe_float(row.get("interpretability_score")),
                "production_status": "NOT_PRODUCTION",
                "vector": [float(value) for value in vector if value is not None],
            }
        )
    return rows


def _standardization(
    matrix: pl.DataFrame,
    centroids: list[dict[str, object]],
) -> tuple[np.ndarray, np.ndarray]:
    row_vectors = [_assignment_vector(row) for row in matrix.iter_rows(named=True)]
    centroid_vectors = [centroid["vector"] for centroid in centroids]
    values = np.array(
        [
            [float(value) if value is not None else math.nan for value in vector]
            for vector in [*row_vectors, *centroid_vectors]
        ],
        dtype=float,
    )
    means = np.nanmean(values, axis=0)
    stds = np.nanstd(values, axis=0)
    means = np.where(np.isfinite(means), means, 0.0)
    stds = np.where((stds > 0) & np.isfinite(stds), stds, 1.0)
    return means, stds


def _standardize_vector(
    vector: list[float | None],
    means: np.ndarray,
    stds: np.ndarray,
) -> tuple[np.ndarray, int]:
    arr = np.array([math.nan if value is None else float(value) for value in vector])
    missing = ~np.isfinite(arr)
    missing_count = int(missing.sum())
    if missing_count:
        arr = np.where(missing, means, arr)
    return (arr - means) / stds, missing_count


def _pick_candidates(
    centroids: list[dict[str, object]],
    *,
    month: int,
) -> tuple[list[dict[str, object]], bool]:
    month_centroids = [
        row for row in centroids if row["stratum_type"] == "month" and row["stratum_value"] == str(month)
    ]
    if month_centroids:
        return month_centroids, False
    season = SEASONS.get(month, "unknown")
    season_centroids = [
        row for row in centroids if row["stratum_type"] == "season" and row["stratum_value"] == season
    ]
    return season_centroids, True


def _ontology(centroids: list[dict[str, object]]) -> pl.DataFrame:
    if not centroids:
        return _empty_frame(ONTOLOGY_SCHEMA)
    rows: list[dict[str, object]] = []
    families = sorted({str(row["candidate_regime_family"]) for row in centroids})
    for family in families:
        subset = [row for row in centroids if str(row["candidate_regime_family"]) == family]
        scores = [
            float(row["interpretability_score"])
            for row in subset
            if row.get("interpretability_score") is not None
        ]
        rows.append(
            {
                "candidate_regime_label": family,
                "candidate_regime_family": family,
                "source_candidate_ids": ";".join(str(row["candidate_id"]) for row in subset),
                "n_candidate_centroids": len(subset),
                "total_candidate_rows": sum(int(row.get("n_rows") or 0) for row in subset),
                "mean_interpretability_score": float(np.mean(scores)) if scores else None,
                "production_status": "NOT_PRODUCTION",
            }
        )
    return pl.DataFrame(rows, schema=ONTOLOGY_SCHEMA, strict=False)


def _audit(
    assignments: pl.DataFrame,
    matrix: pl.DataFrame,
    used_fallback: int,
    imputed_values: int,
) -> pl.DataFrame:
    nulls = assignments.filter(pl.col("candidate_regime_label").is_null()).height if assignments.height else 0
    rows = [
        {
            "audit_item": "assignment_coverage",
            "status": "PASS" if assignments.height == matrix.height else "FAIL",
            "detail": f"{assignments.height}/{matrix.height} feature rows received candidate labels.",
        },
        {
            "audit_item": "null_assignments",
            "status": "PASS" if nulls == 0 else "FAIL",
            "detail": f"{nulls} assignment rows have null candidate labels.",
        },
        {
            "audit_item": "season_fallback",
            "status": "PASS" if used_fallback == 0 else "WARN",
            "detail": f"{used_fallback} rows used season-level fallback centroids.",
        },
        {
            "audit_item": "missing_input_imputation",
            "status": "PASS" if imputed_values == 0 else "WARN",
            "detail": f"{imputed_values} missing assignment inputs were imputed from training means.",
        },
        {
            "audit_item": "causal_inputs",
            "status": "PASS",
            "detail": "Assignment inputs are pre-CP aggregates from the Onda 2E cluster matrix.",
        },
    ]
    return pl.DataFrame(rows, schema=AUDIT_SCHEMA)


def build_regime_candidate_artifacts(
    candidate: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Assign offline candidate regime labels from Onda 2E design centroids."""
    centroids = _candidate_centroids(candidate)
    ontology = _ontology(centroids)
    matrix = _build_cluster_matrix(features, labels, obs, tz_name=tz_name)
    if matrix.height == 0 or not centroids:
        assignments = _empty_frame(ASSIGNMENT_SCHEMA)
        return {
            "regime_candidate_assignments": assignments,
            "regime_candidate_ontology": ontology,
            "regime_candidate_assignment_audit": _audit(assignments, matrix, 0, 0),
        }

    means, stds = _standardization(matrix, centroids)
    centroid_vectors = {
        str(row["candidate_id"]): _standardize_vector(row["vector"], means, stds)[0]  # type: ignore[arg-type]
        for row in centroids
    }
    rows: list[dict[str, object]] = []
    used_fallback = 0
    imputed_values = 0
    for row in matrix.iter_rows(named=True):
        month = int(row["month"])
        choices, fallback = _pick_candidates(centroids, month=month)
        if fallback:
            used_fallback += 1
        row_vector, row_imputed = _standardize_vector(_assignment_vector(row), means, stds)
        imputed_values += row_imputed
        best: dict[str, object] | None = None
        best_distance: float | None = None
        for choice in choices:
            centroid_vector = centroid_vectors.get(str(choice["candidate_id"]))
            if centroid_vector is None:
                continue
            distance = float(np.linalg.norm(row_vector - centroid_vector))
            if best_distance is None or distance < best_distance:
                best = choice
                best_distance = distance
        confidence = None if best_distance is None else 1.0 / (1.0 + best_distance)
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": str(row["cp"]),
                "candidate_regime_label": (
                    str(best["candidate_regime_label"]) if best is not None else None
                ),
                "candidate_regime_family": (
                    str(best["candidate_regime_family"]) if best is not None else None
                ),
                "source_candidate_id": str(best["candidate_id"]) if best is not None else "",
                "stratum_type": str(best["stratum_type"]) if best is not None else "",
                "stratum_value": str(best["stratum_value"]) if best is not None else "",
                "distance_to_candidate": best_distance,
                "assignment_confidence": confidence,
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )
    assignments = pl.DataFrame(rows, schema=ASSIGNMENT_SCHEMA, strict=False)
    return {
        "regime_candidate_assignments": assignments,
        "regime_candidate_ontology": ontology,
        "regime_candidate_assignment_audit": _audit(
            assignments,
            matrix,
            used_fallback,
            imputed_values,
        ),
    }


def _candidate_v2_vector(row: dict[str, object]) -> list[float | None]:
    wind_dir = _safe_float(row.get("wind_dir_deg_mean"))
    sin_mean = math.sin(math.radians(wind_dir)) if wind_dir is not None else None
    cos_mean = math.cos(math.radians(wind_dir)) if wind_dir is not None else None
    return [
        sin_mean,
        cos_mean,
        _safe_float(row.get("wind_speed_mean")),
        _safe_float(row.get("qnh_hpa_mean")),
        _safe_float(row.get("relh_mean")),
        _safe_float(row.get("dewpoint_depression_mean")),
        _safe_float(row.get("precip_pre_cp_sum_mean")),
        _safe_float(row.get("cloud_cover_score_mean")),
        _safe_float(row.get("temp_slope_pre_cp_mean")),
    ]


def _candidate_v2_centroids(candidate_v2: pl.DataFrame) -> list[dict[str, object]]:
    centroids: list[dict[str, object]] = []
    for row in candidate_v2.iter_rows(named=True):
        vector = _candidate_v2_vector(row)
        if any(value is None for value in vector):
            continue
        centroids.append(
            {
                "candidate_id": str(row["candidate_id"]),
                "macro_regime_label": str(row["macro_regime_label"]),
                "subtype_label": str(row["subtype_label"]),
                "latent_component_id": str(
                    row.get("latent_component_id") or row["candidate_id"]
                ),
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "n_source_rows": int(row.get("n_source_rows") or 0),
                "production_status": "NOT_PRODUCTION",
                "vector": [float(value) for value in vector if value is not None],
            }
        )
    return centroids


def _softmax_from_distances(distances: list[float]) -> list[float]:
    if not distances:
        return []
    scores = np.array([-float(distance) for distance in distances], dtype=float)
    scores = scores - np.max(scores)
    exp_scores = np.exp(scores)
    total = float(exp_scores.sum())
    return [float(value / total) for value in exp_scores]


def _entropy(probabilities: list[float]) -> float:
    return float(-sum(prob * math.log(prob) for prob in probabilities if prob > 0.0))


def _probability_json(pairs: list[tuple[str, float]]) -> str:
    return json.dumps(
        {key: round(float(value), 12) for key, value in pairs},
        sort_keys=True,
    )


def _ontology_v2(centroids: list[dict[str, object]]) -> pl.DataFrame:
    rows = [
        {
            "macro_regime_label": row["macro_regime_label"],
            "subtype_label": row["subtype_label"],
            "latent_component_id": row["latent_component_id"],
            "source_candidate_id": row["candidate_id"],
            "stratum_type": row["stratum_type"],
            "stratum_value": row["stratum_value"],
            "n_source_rows": row["n_source_rows"],
            "production_status": "NOT_PRODUCTION",
        }
        for row in centroids
    ]
    return pl.DataFrame(rows, schema=ONTOLOGY_V2_SCHEMA, strict=False)


def _audit_v2(
    assignments: pl.DataFrame,
    matrix: pl.DataFrame,
    *,
    used_fallback: int,
    imputed_values: int,
) -> pl.DataFrame:
    probability_status = "PASS"
    if assignments.height:
        for row in assignments.iter_rows(named=True):
            total = sum(json.loads(str(row["component_probabilities"])).values())
            if abs(float(total) - 1.0) > 1e-6:
                probability_status = "FAIL"
                break
    production_status = "PASS"
    if assignments.height:
        production_status = (
            "PASS"
            if assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height == 0
            else "FAIL"
        )
    rows = [
        {
            "audit_item": "assignment_coverage",
            "status": "PASS" if assignments.height == matrix.height else "FAIL",
            "detail": f"{assignments.height}/{matrix.height} feature rows received v2 labels.",
        },
        {
            "audit_item": "soft_assignment_probabilities",
            "status": probability_status,
            "detail": "Component probabilities are distance-softmax normalized.",
        },
        {
            "audit_item": "season_fallback",
            "status": "PASS" if used_fallback == 0 else "WARN",
            "detail": f"{used_fallback} rows used season-level fallback centroids.",
        },
        {
            "audit_item": "missing_input_imputation",
            "status": "PASS" if imputed_values == 0 else "WARN",
            "detail": f"{imputed_values} missing assignment inputs were imputed from training means.",
        },
        {
            "audit_item": "production_status",
            "status": production_status,
            "detail": "v2 assignment artifacts remain NOT_PRODUCTION.",
        },
    ]
    return pl.DataFrame(rows, schema=AUDIT_V2_SCHEMA, strict=False)


def build_regime_candidate_v2_assignment_artifacts(
    candidate_v2: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
) -> dict[str, pl.DataFrame]:
    """Assign non-production v2 macro regimes with component probabilities."""
    required = {
        "candidate_id",
        "macro_regime_label",
        "subtype_label",
        "stratum_type",
        "stratum_value",
        "production_status",
        *V2_CENTROID_COLUMNS,
    }
    missing = required - set(candidate_v2.columns)
    if missing:
        raise ValueError(
            "candidate_v2 missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    if candidate_v2.filter(pl.col("production_status") != "NOT_PRODUCTION").height:
        raise ValueError("candidate_v2 must remain NOT_PRODUCTION")

    centroids = _candidate_v2_centroids(candidate_v2)
    ontology = _ontology_v2(centroids)
    matrix = _build_cluster_matrix(features, labels, obs, tz_name=tz_name)
    if matrix.height == 0 or not centroids:
        assignments = _empty_frame(ASSIGNMENT_V2_SCHEMA)
        return {
            "regime_candidate_assignments_v2": assignments,
            "regime_candidate_ontology_v2": ontology,
            "regime_candidate_assignment_audit_v2": _audit_v2(
                assignments,
                matrix,
                used_fallback=0,
                imputed_values=0,
            ),
        }

    means, stds = _standardization(matrix, centroids)
    centroid_vectors = {
        str(row["candidate_id"]): _standardize_vector(row["vector"], means, stds)[0]  # type: ignore[arg-type]
        for row in centroids
    }
    rows: list[dict[str, object]] = []
    used_fallback = 0
    imputed_values = 0
    for row in matrix.iter_rows(named=True):
        choices, fallback = _pick_candidates(centroids, month=int(row["month"]))
        if not choices:
            choices = centroids
        if fallback:
            used_fallback += 1
        row_vector, row_imputed = _standardize_vector(_assignment_vector(row), means, stds)
        imputed_values += row_imputed
        distances: list[float] = [
            float(np.linalg.norm(row_vector - centroid_vectors[str(choice["candidate_id"])]))
            for choice in choices
        ]
        probabilities = _softmax_from_distances(distances)
        ranked = sorted(
            zip(choices, distances, probabilities, strict=False),
            key=lambda item: item[2],
            reverse=True,
        )
        best, best_distance, best_probability = ranked[0]
        alternative = ranked[1] if len(ranked) > 1 else None
        margin = (
            float(best_probability - alternative[2])
            if alternative is not None
            else 1.0
        )
        family_totals: dict[str, float] = {}
        for choice, _distance, probability in ranked:
            macro = str(choice["macro_regime_label"])
            family_totals[macro] = family_totals.get(macro, 0.0) + float(probability)
        nearest_alternative_macro = (
            str(alternative[0]["macro_regime_label"]) if alternative is not None else ""
        )
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": str(row["cp"]),
                "macro_regime_label": str(best["macro_regime_label"]),
                "subtype_label": str(best["subtype_label"]),
                "candidate_regime_label": str(best["macro_regime_label"]),
                "source_candidate_id": str(best["candidate_id"]),
                "component_argmax": str(best["latent_component_id"]),
                "component_probabilities": _probability_json(
                    [
                        (str(choice["latent_component_id"]), probability)
                        for choice, _distance, probability in ranked
                    ]
                ),
                "family_probabilities": _probability_json(sorted(family_totals.items())),
                "component_entropy": _entropy(probabilities),
                "component_margin": margin,
                "nearest_alternative_macro": nearest_alternative_macro,
                "distance_to_candidate": float(best_distance),
                "distance_to_alternative": (
                    float(alternative[1]) if alternative is not None else None
                ),
                "assignment_confidence": float(best_probability),
                "low_confidence_flag": bool(margin < 0.15 or _entropy(probabilities) > 1.0),
                "causal_window": "valid < CP",
                "production_status": "NOT_PRODUCTION",
            }
        )
    assignments = pl.DataFrame(rows, schema=ASSIGNMENT_V2_SCHEMA, strict=False)
    return {
        "regime_candidate_assignments_v2": assignments,
        "regime_candidate_ontology_v2": ontology,
        "regime_candidate_assignment_audit_v2": _audit_v2(
            assignments,
            matrix,
            used_fallback=used_fallback,
            imputed_values=imputed_values,
        ),
    }


def _features_with_candidate_regime(
    features: pl.DataFrame,
    assignments: pl.DataFrame,
) -> pl.DataFrame:
    replacement = assignments.select(
        [
            "date_local",
            "cp",
            pl.col("candidate_regime_label").alias("candidate_regime_label_joined"),
        ]
    )
    return (
        features.join(replacement, on=["date_local", "cp"], how="left")
        .with_columns(pl.col("candidate_regime_label_joined").alias("regime_label"))
        .drop("candidate_regime_label_joined")
    )


def candidate_screening_test_starts(labels: pl.DataFrame) -> list[dt.date]:
    """Return the latest annual screening start supported by label data."""
    if labels.height == 0 or "date_local" not in labels.columns:
        return []
    labels_ok = labels
    if "day_complete" in labels_ok.columns:
        labels_ok = labels_ok.filter(pl.col("day_complete"))
    latest = labels_ok["date_local"].max()
    if latest is None:
        return []
    latest_year = min(int(latest.year), 2025)
    return [dt.date(latest_year, 1, 1)]


def _validation_scope(
    *,
    cp_set: tuple[str, ...],
    test_starts: list[dt.date] | None,
) -> pl.DataFrame:
    starts = test_starts or []
    mode = "screening_single_year" if len(starts) == 1 else "explicit_multi_window"
    return pl.DataFrame(
        [
            {
                "audit_item": "r2_validation_mode",
                "status": "WARN" if mode == "screening_single_year" else "PASS",
                "detail": (
                    "Candidate R2 screening uses one annual walk-forward window; "
                    "run full Onda 4 before production promotion."
                    if mode == "screening_single_year"
                    else "Candidate R2 validation uses explicit test-start windows."
                ),
            },
            {
                "audit_item": "r2_cp_set",
                "status": "PASS",
                "detail": ",".join(cp_set),
            },
            {
                "audit_item": "r2_test_starts",
                "status": "PASS" if starts else "WARN",
                "detail": ";".join(start.isoformat() for start in starts) if starts else "",
            },
        ],
        schema=VALIDATION_SCOPE_SCHEMA,
    )


def validate_regime_candidate_r2(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame,
    hypotheses: list[Hypothesis],
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
    test_starts: list[dt.date] | None = None,
    seed: int = 42,
) -> dict[str, pl.DataFrame]:
    """Run Onda 4 R2 regime sensitivity against candidate labels."""
    resolved_test_starts = (
        candidate_screening_test_starts(labels) if test_starts is None else test_starts
    )
    candidate_features = _features_with_candidate_regime(features, assignments)
    families = sorted(
        str(value)
        for value in assignments["candidate_regime_label"].drop_nulls().unique().to_list()
    )
    cross_tab = regime_sensitivity(
        candidate_features,
        labels,
        hypotheses,
        cp_set=cp_set,
        test_starts=resolved_test_starts,
        seed=seed,
    )
    dead = detect_dead_regimes(cross_tab, regimes=families)
    dead_rows = [
        {
            "candidate_regime_family": family,
            "status": "DEAD" if family in dead else "PASS",
        }
        for family in families
    ]
    return {
        "regime_candidate_r2_validation": cross_tab,
        "dead_candidate_regimes": (
            pl.DataFrame(dead_rows, schema=DEAD_SCHEMA)
            if dead_rows
            else _empty_frame(DEAD_SCHEMA)
        ),
        "regime_candidate_validation_scope": _validation_scope(
            cp_set=cp_set,
            test_starts=resolved_test_starts,
        ),
    }


def _as_bool_passes(frame: pl.DataFrame) -> pl.DataFrame:
    if "passes" not in frame.columns or frame.schema.get("passes") == pl.Boolean:
        return frame
    return frame.with_columns(
        pl.col("passes")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .is_in(["true", "1", "yes"])
        .alias("passes")
    )


def _r2_summary_for_regime(r2: pl.DataFrame, regime: str) -> tuple[int, int]:
    if r2.height == 0 or "regime" not in r2.columns:
        return 0, 0
    subset = r2.filter(pl.col("regime") == regime)
    if subset.height == 0 or "passes" not in subset.columns:
        return subset.height, 0
    return subset.height, subset.filter(pl.col("passes").fill_null(False)).height


def _assignment_summary_for_macro(
    assignments: pl.DataFrame,
    macro: str,
) -> tuple[int, float | None, float | None, float | None, int]:
    label_col = (
        "macro_regime_label"
        if "macro_regime_label" in assignments.columns
        else "candidate_regime_label"
    )
    if assignments.height == 0 or label_col not in assignments.columns:
        return 0, None, None, None, 0
    subset = assignments.filter(pl.col(label_col) == macro)
    if subset.height == 0:
        return 0, None, None, None, 0
    low_confidence = (
        float(subset.filter(pl.col("low_confidence_flag").fill_null(False)).height / subset.height)
        if "low_confidence_flag" in subset.columns
        else None
    )
    mean_entropy = (
        float(subset["component_entropy"].mean())
        if "component_entropy" in subset.columns
        else None
    )
    mean_margin = (
        float(subset["component_margin"].mean())
        if "component_margin" in subset.columns
        else None
    )
    smallest_cp_support = (
        int(subset.group_by("cp").len(name="n")["n"].min())
        if "cp" in subset.columns
        else subset.height
    )
    return subset.height, low_confidence, mean_entropy, mean_margin, smallest_cp_support


def compare_regime_candidate_r2(
    *,
    v1_r2: pl.DataFrame,
    v2_r2: pl.DataFrame,
    v2_assignments: pl.DataFrame,
    v1_regimes: tuple[str, ...],
    v2_regimes: tuple[str, ...],
    protected_v2_regimes: tuple[str, ...],
    min_assignment_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Compare flat v1 R2 status with hierarchical v2 macro-regime R2 status."""
    v1_norm = _as_bool_passes(v1_r2)
    v2_norm = _as_bool_passes(v2_r2)
    v1_dead = detect_dead_regimes(v1_norm, regimes=v1_regimes)
    v2_dead = detect_dead_regimes(v2_norm, regimes=v2_regimes)
    regressions = sorted(set(v2_dead) & set(protected_v2_regimes))
    support_by_macro: dict[str, int] = {}
    rows: list[dict[str, object]] = []
    for macro in v2_regimes:
        assignment_rows, low_share, mean_entropy, mean_margin, smallest_cp = (
            _assignment_summary_for_macro(v2_assignments, macro)
        )
        support_by_macro[macro] = assignment_rows
        r2_rows, r2_pass_rows = _r2_summary_for_regime(v2_norm, macro)
        rows.append(
            {
                "candidate_version": "v2",
                "macro_regime_label": macro,
                "assignment_rows": assignment_rows,
                "r2_rows": r2_rows,
                "r2_pass_rows": r2_pass_rows,
                "r2_dead_status": "DEAD" if macro in v2_dead else "PASS",
                "protected_regression_flag": macro in regressions,
                "low_confidence_share": low_share,
                "mean_component_entropy": mean_entropy,
                "mean_component_margin": mean_margin,
                "smallest_cp_support": smallest_cp,
                "v1_dead_regimes": len(v1_dead),
                "v2_dead_regimes": len(v2_dead),
                "protected_regressions": ";".join(regressions),
                "decision_update": "",
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    underpowered = [
        macro for macro, support in support_by_macro.items() if support < min_assignment_rows
    ]
    decision = (
        "READY_FOR_FULL_ONDA4_RERUN"
        if not v2_dead and not regressions and not underpowered
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    rows = [{**row, "decision_update": decision} for row in rows]
    return {
        "regime_candidate_v1_v2_comparison": pl.DataFrame(
            rows,
            schema=COMPARISON_SCHEMA,
            strict=False,
        )
    }


def _invalid_residual_targets(residual_diagnostics: pl.DataFrame) -> int:
    if residual_diagnostics.height == 0:
        return 0
    required = {"diagnostic_item", "status"}
    missing = required - set(residual_diagnostics.columns)
    if missing:
        raise ValueError(
            "residual_diagnostics missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    invalid = residual_diagnostics.filter(
        (pl.col("diagnostic_item") == "invalid_absorption_targets")
        & (pl.col("status") == "FAIL")
    )
    return invalid.height


def _absorbed_rows_for_macro(assignments: pl.DataFrame, macro: str) -> int:
    required = {"macro_regime_label", "absorbed_from_residual"}
    if assignments.height == 0:
        return 0
    missing = required - set(assignments.columns)
    if missing:
        raise ValueError(
            "v21_assignments missing required columns: "
            f"{', '.join(sorted(missing))}"
        )
    return assignments.filter(
        (pl.col("macro_regime_label") == macro)
        & pl.col("absorbed_from_residual").fill_null(False)
    ).height


def compare_regime_candidate_v2_v21(
    *,
    v2_r2: pl.DataFrame,
    v21_r2: pl.DataFrame,
    v21_assignments: pl.DataFrame,
    residual_diagnostics: pl.DataFrame,
    v2_regimes: tuple[str, ...],
    v21_regimes: tuple[str, ...],
    protected_v21_regimes: tuple[str, ...],
) -> dict[str, pl.DataFrame]:
    """Compare v2 and v2.1 macro R2 status after residual absorption."""
    if (
        v21_assignments.height
        and "production_status" in v21_assignments.columns
        and v21_assignments.filter(pl.col("production_status") != "NOT_PRODUCTION").height
    ):
        raise ValueError("v21_assignments production_status must be NOT_PRODUCTION")
    v2_norm = _as_bool_passes(v2_r2)
    v21_norm = _as_bool_passes(v21_r2)
    v2_dead = detect_dead_regimes(v2_norm, regimes=v2_regimes)
    v21_dead = detect_dead_regimes(v21_norm, regimes=v21_regimes)
    invalid_targets = _invalid_residual_targets(residual_diagnostics)
    regressions = sorted(set(v21_dead) & set(protected_v21_regimes))
    decision = (
        "READY_FOR_FULL_ONDA4_RERUN"
        if not v21_dead and not regressions and invalid_targets == 0
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    rows: list[dict[str, object]] = []
    for macro in v21_regimes:
        assignment_rows, *_rest = _assignment_summary_for_macro(v21_assignments, macro)
        r2_rows, r2_pass_rows = _r2_summary_for_regime(v21_norm, macro)
        rows.append(
            {
                "candidate_version": "v2.1",
                "macro_regime_label": macro,
                "assignment_rows": assignment_rows,
                "absorbed_residual_rows": _absorbed_rows_for_macro(
                    v21_assignments,
                    macro,
                ),
                "r2_rows": r2_rows,
                "r2_pass_rows": r2_pass_rows,
                "r2_dead_status": "DEAD" if macro in v21_dead else "PASS",
                "v2_dead_regimes": len(v2_dead),
                "v21_dead_regimes": len(v21_dead),
                "protected_regression_flag": macro in regressions,
                "decision_update": decision,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return {
        "regime_candidate_v2_v21_comparison": pl.DataFrame(
            rows,
            schema=COMPARISON_V21_SCHEMA,
            strict=False,
        )
    }


def _decision_update(dead: pl.DataFrame) -> pl.DataFrame:
    dead_count = dead.filter(pl.col("status") == "DEAD").height if dead.height else 0
    r2_status = "PASS" if dead_count == 0 else "BLOCK"
    return pl.DataFrame(
        [
            {
                "decision_id": "DEC-WCT-REGIME-016-CANDIDATE-R2",
                "item_id": "WCT-REGIME-016",
                "item_type": "thesis",
                "domain": "REGIME",
                "decision_status": "PROMOTED_TO_REGIME_DESIGN",
                "evidence_level": "E3_candidate_r2_validation",
                "source_artifact": "reports/regime-design/regime_candidate_validation_report.md",
                "strata": "candidate regime family x CP",
                "sample_size_warning": f"Candidate R2 validation status: {r2_status}; dead families: {dead_count}.",
                "causal_availability": "Candidate labels are assigned from pre-CP Onda 2E cluster inputs.",
                "leakage_risk": "Offline validation only; no production classifier or feature artifact is overwritten.",
                "decision_rationale": (
                    "Candidate regime design is ready for full Onda 4 rerun."
                    if dead_count == 0
                    else "Candidate regime design still has dead R2 families and remains in design review."
                ),
                "next_allowed_action": (
                    "Run full Onda 4 robustness against the candidate feature copy."
                    if dead_count == 0
                    else "Revise candidate ontology or assignment before full Onda 4 rerun."
                ),
            }
        ],
        schema=DECISION_SCHEMA,
    )


def _report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    assignments = artifacts["regime_candidate_assignments"]
    ontology = artifacts["regime_candidate_ontology"]
    dead = artifacts["dead_candidate_regimes"]
    scope = artifacts.get("regime_candidate_validation_scope", _empty_frame(VALIDATION_SCOPE_SCHEMA))
    dead_count = dead.filter(pl.col("status") == "DEAD").height if dead.height else 0
    family_counts = (
        assignments.group_by("candidate_regime_label").len(name="n").sort("candidate_regime_label")
        if assignments.height
        else pl.DataFrame({"candidate_regime_label": [], "n": []})
    )
    lines = [
        f"# Regime Candidate Validation - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        "Candidate labels are assigned offline for Onda 4 R2 validation only.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Candidate ontology families: {ontology.height}",
        f"- Dead candidate families: {dead_count}",
        "",
        "## Validation Scope",
        "",
        "| Audit item | Status | Detail |",
        "|---|---|---|",
    ]
    for row in scope.iter_rows(named=True):
        lines.append(f"| {row['audit_item']} | {row['status']} | {row['detail']} |")
    lines += [
        "",
        "## Candidate Family Counts",
        "",
        "| Candidate family | Rows |",
        "|---|---:|",
    ]
    for row in family_counts.iter_rows(named=True):
        lines.append(f"| {row['candidate_regime_label']} | {row['n']} |")
    lines += [
        "",
        "## R2 Candidate Result",
        "",
        "| Candidate family | Status |",
        "|---|---|",
    ]
    for row in dead.iter_rows(named=True):
        lines.append(f"| {row['candidate_regime_family']} | {row['status']} |")
    lines += [
        "",
        "## Next Action",
        "",
        (
            "Run a full Onda 4 robustness rerun with a candidate feature copy."
            if dead_count == 0
            else "Keep the candidate in regime-design review and revise dead families before a full Onda 4 rerun."
        ),
    ]
    return lines


def write_regime_candidate_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write offline regime-candidate validation artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments": "regime_candidate_assignments_v1.csv",
        "regime_candidate_ontology": "regime_candidate_ontology_v1.csv",
        "regime_candidate_assignment_audit": "regime_candidate_assignment_audit.csv",
        "regime_candidate_validation_scope": "regime_candidate_validation_scope.csv",
        "regime_candidate_r2_validation": "regime_candidate_r2_validation.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    decision = _decision_update(artifacts["dead_candidate_regimes"])
    decision_path = out_dir / "regime_candidate_decision_update.csv"
    decision.write_csv(decision_path)
    paths["regime_candidate_decision_update_csv"] = decision_path
    report_path = out_dir / "regime_candidate_validation_report.md"
    report_path.write_text("\n".join(_report_lines(artifacts, report_date)), encoding="utf-8")
    paths["validation_report_md"] = report_path
    return paths


def _v2_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    assignments = artifacts["regime_candidate_assignments_v2"]
    comparison = artifacts["regime_candidate_v1_v2_comparison"]
    decision = (
        str(comparison["decision_update"][0])
        if comparison.height and "decision_update" in comparison.columns
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    lines = [
        f"# Regime Candidate v2 Validation - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        "Regime Ontology v2 is an offline candidate for Onda 4 R2 validation only.",
        "",
        f"- Assignment rows: {assignments.height}",
        f"- Macro regimes: {assignments['macro_regime_label'].n_unique() if assignments.height else 0}",
        f"- Decision update: {decision}",
        "",
        "## v1-v2 Comparison",
        "",
        "| Macro regime | Assignments | R2 pass rows | Dead status | Low confidence | Decision |",
        "|---|---:|---:|---|---:|---|",
    ]
    for row in comparison.sort("macro_regime_label").iter_rows(named=True):
        lines.append(
            "| "
            f"{row['macro_regime_label']} | "
            f"{row['assignment_rows']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_dead_status']} | "
            f"{row['low_confidence_share']} | "
            f"{row['decision_update']} |"
        )
    lines += [
        "",
        "## Next Action",
        "",
        (
            "Run a full Onda 4 robustness rerun with a candidate feature copy."
            if decision == "READY_FOR_FULL_ONDA4_RERUN"
            else "Keep Onda 3 blocked and revise v2 regime design before a full Onda 4 rerun."
        ),
    ]
    return lines


def write_regime_candidate_v2_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write non-production v2 validation artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_assignments_v2": "regime_candidate_assignments_v2.csv",
        "regime_candidate_ontology_v2": "regime_candidate_ontology_v2.csv",
        "regime_candidate_assignment_audit_v2": "regime_candidate_assignment_audit_v2.csv",
        "regime_candidate_r2_validation": "regime_candidate_r2_validation_v2.csv",
        "regime_candidate_v1_v2_comparison": "regime_candidate_v1_v2_comparison.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    report_path = out_dir / "regime_candidate_v2_validation_report.md"
    report_path.write_text(
        "\n".join(_v2_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_candidate_v2_validation_report_md"] = report_path
    return paths


def _v21_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    r2 = artifacts["regime_candidate_r2_validation"]
    comparison = artifacts["regime_candidate_v2_v21_comparison"]
    decision = (
        str(comparison["decision_update"][0])
        if comparison.height and "decision_update" in comparison.columns
        else "KEEP_IN_REGIME_DESIGN_REVIEW"
    )
    dead_count = (
        int(comparison["v21_dead_regimes"][0])
        if comparison.height and "v21_dead_regimes" in comparison.columns
        else 0
    )
    absorbed = (
        int(comparison["absorbed_residual_rows"].sum())
        if comparison.height and "absorbed_residual_rows" in comparison.columns
        else 0
    )
    lines = [
        f"# Regime Candidate v2.1 Validation - {report_date.isoformat()}",
        "",
        "This is not a production classifier.",
        "Regime Ontology v2.1 is an offline residual-absorption screening experiment.",
        "",
        f"- R2 rows: {r2.height}",
        f"- Absorbed residual rows: {absorbed}",
        f"- v2.1 dead macros: {dead_count}",
        f"- Decision update: {decision}",
        "",
        "## v2-v2.1 Comparison",
        "",
        "| Macro regime | Assignments | Absorbed residual | R2 pass rows | Dead status | Decision |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in comparison.sort("macro_regime_label").iter_rows(named=True):
        lines.append(
            "| "
            f"{row['macro_regime_label']} | "
            f"{row['assignment_rows']} | "
            f"{row['absorbed_residual_rows']} | "
            f"{row['r2_pass_rows']} | "
            f"{row['r2_dead_status']} | "
            f"{row['decision_update']} |"
        )
    lines += [
        "",
        "## Next Action",
        "",
        (
            "Run a full Onda 4 robustness rerun before any Onda 3 promotion."
            if decision == "READY_FOR_FULL_ONDA4_RERUN"
            else "Keep Onda 3 blocked and revise v2.1 before a full Onda 4 rerun."
        ),
        "",
        "Onda C remains planned as the follow-up topology/classifiability wave.",
    ]
    return lines


def write_regime_candidate_v21_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write non-production v2.1 validation artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "regime_candidate_r2_validation": "regime_candidate_r2_validation_v2_1.csv",
        "regime_candidate_v2_v21_comparison": "regime_candidate_v2_v21_comparison.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path
    report_path = out_dir / "regime_candidate_v21_validation_report.md"
    report_path.write_text(
        "\n".join(_v21_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_candidate_v21_validation_report_md"] = report_path
    return paths


def validate_regime_design_queue(queue: pl.DataFrame) -> bool:
    """Return True when queue authorizes WCT-REGIME-016 design validation."""
    if queue.height == 0:
        return False
    required = {"source_item_id", "source_decision_status"}
    if not required.issubset(queue.columns):
        return False
    return (
        queue.filter(
            (pl.col("source_item_id") == "WCT-REGIME-016")
            & (pl.col("source_decision_status") == "PROMOTED_TO_REGIME_DESIGN")
        ).height
        > 0
    )
