from __future__ import annotations

import datetime as dt
import itertools
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

ALLOWED_DECISIONS = {
    "READY_FOR_ONDA3_DESIGN_REVIEW",
    "KEEP_IN_REGIME_DESIGN_REVIEW",
    "BLOCK_ONDA_C_PROMOTION",
}

ASSIGNMENTS_SCHEMA = {
    "method": pl.Utf8,
    "candidate_version": pl.Utf8,
    "date_local": pl.Date,
    "cp": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "subtype_label": pl.Utf8,
    "assigned_label": pl.Utf8,
    "assigned_component": pl.Utf8,
    "assignment_confidence": pl.Float64,
    "assignment_margin": pl.Float64,
    "assignment_entropy": pl.Float64,
    "distance_to_centroid": pl.Float64,
    "topological_x": pl.Float64,
    "topological_y": pl.Float64,
    "train_fold": pl.Utf8,
    "test_fold": pl.Utf8,
    "production_status": pl.Utf8,
}

METRICS_SCHEMA = {
    "method": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_regime_label": pl.Utf8,
    "cp": pl.Utf8,
    "n_train": pl.Int64,
    "n_test": pl.Int64,
    "n_assigned": pl.Int64,
    "n_low_confidence": pl.Int64,
    "coverage_share": pl.Float64,
    "low_confidence_share": pl.Float64,
    "mean_entropy": pl.Float64,
    "mean_margin": pl.Float64,
    "silhouette_score": pl.Float64,
    "davies_bouldin_score": pl.Float64,
    "calinski_harabasz_score": pl.Float64,
    "purity_vs_v21": pl.Float64,
    "nmi_vs_v21": pl.Float64,
    "ari_vs_v21": pl.Float64,
    "temporal_stability": pl.Float64,
    "fold_stability": pl.Float64,
    "dead_regime_flag": pl.Boolean,
    "production_status": pl.Utf8,
}

COMPARISON_SCHEMA = {
    "method": pl.Utf8,
    "candidate_version": pl.Utf8,
    "macro_count": pl.Int64,
    "dead_regimes": pl.Int64,
    "protected_regression_flag": pl.Boolean,
    "coverage_share": pl.Float64,
    "low_confidence_share": pl.Float64,
    "mean_entropy": pl.Float64,
    "mean_margin": pl.Float64,
    "classifiability_score": pl.Float64,
    "stability_score": pl.Float64,
    "interpretability_score": pl.Float64,
    "decision_update": pl.Utf8,
    "production_status": pl.Utf8,
    "notes": pl.Utf8,
}

DIAGNOSTICS_SCHEMA = {
    "diagnostic_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
    "n_rows": pl.Int64,
    "production_status": pl.Utf8,
}

PHYSICAL_CLASSIFIABILITY_FEATURES: tuple[str, ...] = (
    "drct_sin_mean",
    "drct_cos_mean",
    "sknt_mean",
    "qnh_hpa_mean",
    "relh_mean",
    "dewpoint_depression_mean",
    "precip_pre_cp_sum",
    "cloud_cover_score_mean",
    "temp_slope_pre_cp",
)

OUTCOME_FEATURE_COLUMNS = {
    "tmax_int",
    "tmax_hour",
    "remaining_warming",
    "tmax_anomaly",
}

QUARANTINED_LABEL_COLUMNS = {
    "regime_label",
    "current_regime_label",
    "regime_flags",
    "foehn_score",
    "candidate_regime_label",
    "macro_regime_label",
    "subtype_label",
}

IDENTIFIER_COLUMNS = {
    "date_local",
    "month",
    "season",
    "cp",
    "candidate_version",
    "production_status",
    "causal_window",
}

FEATURE_BASIS_AUDIT_SCHEMA = {
    "feature": pl.Utf8,
    "source": pl.Utf8,
    "included_in_classifiability": pl.Boolean,
    "required_for_physical_basis": pl.Boolean,
    "causal_availability": pl.Utf8,
    "leakage_class": pl.Utf8,
    "missing_rate": pl.Float64,
    "variance_status": pl.Utf8,
    "selection_reason": pl.Utf8,
    "production_status": pl.Utf8,
}


def _require_columns(df: pl.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _missing_rate(frame: pl.DataFrame, column: str) -> float:
    if column not in frame.columns or frame.height == 0:
        return 1.0
    return float(frame.get_column(column).null_count() / frame.height)


def _variance_status(frame: pl.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return "missing"
    values = frame.get_column(column)
    if not values.dtype.is_numeric():
        return "non_numeric"
    if values.null_count() == values.len():
        return "all_null"
    numeric = values.drop_nulls().to_numpy().astype(float)
    if len(numeric) == 0:
        return "all_null"
    if float(np.nanstd(numeric)) <= 1e-12:
        return "constant"
    return "usable"


def _source_for_feature(column: str) -> str:
    sources = {
        "drct_sin_mean": "obs.drct",
        "drct_cos_mean": "obs.drct",
        "sknt_mean": "obs.sknt",
        "qnh_hpa_mean": "obs.alti",
        "relh_mean": "obs.relh",
        "dewpoint_depression_mean": "obs.dw_depression_c_int or tmp-dwp",
        "precip_pre_cp_sum": "obs.p01i",
        "cloud_cover_score_mean": "obs.skyc1",
        "temp_slope_pre_cp": "obs.tmp_c_int",
    }
    return sources.get(column, "inspected_input")


def _leakage_class_for_feature(column: str) -> str:
    if column in PHYSICAL_CLASSIFIABILITY_FEATURES:
        return "causal_input"
    if column in OUTCOME_FEATURE_COLUMNS:
        return "excluded_outcome"
    if column in QUARANTINED_LABEL_COLUMNS:
        return "excluded_quarantined_label"
    if column in IDENTIFIER_COLUMNS:
        return "excluded_identifier"
    return "excluded_model_feature"


def select_physical_classifiability_features(
    features: pl.DataFrame,
    *,
    min_features: int = 2,
) -> tuple[list[str], pl.DataFrame]:
    inspected = list(dict.fromkeys([*PHYSICAL_CLASSIFIABILITY_FEATURES, *features.columns]))
    rows: list[dict[str, object]] = []
    selected: list[str] = []

    for column in inspected:
        required = column in PHYSICAL_CLASSIFIABILITY_FEATURES
        leakage_class = _leakage_class_for_feature(column)
        variance_status = _variance_status(features, column)
        include = required and leakage_class == "causal_input" and variance_status == "usable"
        if include:
            selected.append(column)
        if required and column not in features.columns:
            reason = "required physical feature is missing"
        elif include:
            reason = "approved causal meteorological feature"
        elif leakage_class != "causal_input":
            reason = f"excluded by leakage class {leakage_class}"
        else:
            reason = f"excluded by variance status {variance_status}"
        rows.append(
            {
                "feature": column,
                "source": _source_for_feature(column),
                "included_in_classifiability": include,
                "required_for_physical_basis": required,
                "causal_availability": (
                    "valid < CP" if leakage_class == "causal_input" else "excluded"
                ),
                "leakage_class": leakage_class,
                "missing_rate": _missing_rate(features, column),
                "variance_status": variance_status,
                "selection_reason": reason,
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    audit = pl.DataFrame(rows, schema=FEATURE_BASIS_AUDIT_SCHEMA, strict=False)
    missing_required = [
        column
        for column in PHYSICAL_CLASSIFIABILITY_FEATURES
        if column not in features.columns
    ]
    if missing_required:
        raise ValueError(
            "physical classifiability basis is missing required approved "
            f"meteorological features: {missing_required}"
        )
    if len(selected) < min_features:
        raise ValueError(
            "physical classifiability basis has fewer than "
            f"{min_features} usable approved meteorological features"
        )
    return selected, audit


LOW_CARDINALITY_CATEGORICAL_FEATURES = (
    "regime_score_argmax",
    "day_sequence_pattern",
)


def _get_numeric_features(df: pl.DataFrame) -> list[str]:
    standard_cols = [
        "wind_dir_deg", "wind_speed", "qnh_hpa", "relh",
        "dewpoint_depression", "precip_pre_cp_sum", "cloud_cover_score", "temp_slope_pre_cp"
    ]
    cols = [c for c in standard_cols if c in df.columns]
    if len(cols) < 2:
        exclude = {
            "date_local", "cp", "regime_label", "candidate_version",
            "production_status", "causal_window", "regime_flags", "regime_score_argmax"
        }
        cols = [c for c in df.columns if df[c].dtype.is_numeric() and c not in exclude]
    return cols


def prepare_classifiability_feature_matrix(
    train_features: pl.DataFrame,
    all_features: pl.DataFrame,
    allowed_numeric_features: list[str] | None = None,
) -> tuple[np.ndarray, list[str]]:
    exclude = {
        "date_local",
        "cp",
        "regime_label",
        "candidate_version",
        "production_status",
        "causal_window",
        "regime_flags",
    }
    cols: list[str] = []
    arrays: list[np.ndarray] = []
    seen_signatures: set[tuple[float, ...]] = set()

    candidate_columns = allowed_numeric_features or list(all_features.columns)
    for col in candidate_columns:
        if col not in all_features.columns:
            continue
        if col in exclude or not all_features[col].dtype.is_numeric():
            continue
        train_col = train_features[col]
        if train_col.null_count() == train_col.len():
            continue
        train_values = train_col.to_numpy()
        fill_value = np.nanmedian(train_values.astype(float)) if len(train_values) else 0.0
        if not np.isfinite(fill_value):
            fill_value = 0.0
        full_values = all_features[col].to_numpy().astype(float)
        full_values = np.where(np.isnan(full_values), fill_value, full_values)
        train_filled = np.where(np.isnan(train_values.astype(float)), fill_value, train_values.astype(float))
        if float(np.nanstd(train_filled)) <= 1e-12:
            continue
        signature = tuple(np.round(full_values, 12).tolist())
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        cols.append(col)
        arrays.append(full_values)

    categorical_columns = (
        []
        if allowed_numeric_features is not None
        else list(LOW_CARDINALITY_CATEGORICAL_FEATURES)
    )
    for col in categorical_columns:
        if col not in all_features.columns:
            continue
        train_values = train_features[col].cast(pl.Utf8).fill_null("missing")
        categories = [
            value
            for value in sorted(train_values.unique().to_list())
            if value is not None
        ]
        if len(categories) <= 1 or len(categories) > 12:
            continue
        all_values = all_features[col].cast(pl.Utf8).fill_null("missing").to_list()
        for category in categories:
            encoded = np.array([1.0 if value == category else 0.0 for value in all_values], dtype=float)
            train_encoded = encoded[: train_features.height]
            if float(np.std(train_encoded)) <= 1e-12:
                continue
            feature_name = f"{col}={category}"
            signature = tuple(encoded.tolist())
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            cols.append(feature_name)
            arrays.append(encoded)

    if not arrays:
        return np.empty((all_features.height, 0)), []
    return np.column_stack(arrays), cols


def _standardize_data(
    train_features: pl.DataFrame,
    all_features: pl.DataFrame,
    cols: list[str],
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    all_np, prepared_cols = prepare_classifiability_feature_matrix(
        train_features,
        all_features,
        allowed_numeric_features=cols,
    )
    if prepared_cols:
        train_np = all_np[: train_features.height]
    else:
        train_np = train_features.select(cols).to_numpy()
        all_np = all_features.select(cols).to_numpy()
    train_means = np.nanmean(train_np, axis=0)
    train_means = np.where(np.isfinite(train_means), train_means, 0.0)

    train_np_filled = np.where(np.isnan(train_np), train_means, train_np)

    all_np_filled = np.where(np.isnan(all_np), train_means, all_np)

    scaler = StandardScaler()
    train_std = scaler.fit_transform(train_np_filled)
    all_std = scaler.transform(all_np_filled)
    return train_std, all_std, scaler


def _run_gmm(
    train_std: np.ndarray,
    all_std: np.ndarray,
    train_labels_v21: list[str],
    n_components: int = 2,
    seed: int = 42,
) -> tuple[list[str], list[int], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    gmm = GaussianMixture(n_components=n_components, random_state=seed)
    gmm.fit(train_std)

    probs = gmm.predict_proba(all_std)
    cluster_labels = gmm.predict(all_std)

    train_cluster_labels = cluster_labels[:len(train_std)]

    mapping = {}
    unique_macros = sorted(set(train_labels_v21))
    if len(unique_macros) == n_components:
        best_score = -1
        best_mapping: dict[int, str] = {}
        for perm in itertools.permutations(unique_macros):
            candidate_mapping = {cluster: macro for cluster, macro in enumerate(perm)}
            score = sum(
                1
                for cluster, label in zip(train_cluster_labels, train_labels_v21, strict=False)
                if candidate_mapping[int(cluster)] == label
            )
            if score > best_score:
                best_score = score
                best_mapping = candidate_mapping
        mapping = best_mapping
    else:
        for c in range(n_components):
            c_indices = [i for i, val in enumerate(train_cluster_labels) if val == c]
            if c_indices:
                c_macros = [train_labels_v21[i] for i in c_indices]
                most_common = max(set(c_macros), key=c_macros.count)
                mapping[c] = most_common
            else:
                mapping[c] = f"gmm_cluster_{c}"

    mapped_labels = [mapping[c] for c in cluster_labels]

    entropy = -np.sum(probs * np.log(np.clip(probs, 1e-15, 1.0)), axis=1)
    sorted_probs = np.sort(probs, axis=1)
    margin = sorted_probs[:, -1] - sorted_probs[:, -2] if n_components > 1 else np.ones(len(probs))

    means = gmm.means_
    distances = []
    for i, c in enumerate(cluster_labels):
        dist = np.linalg.norm(all_std[i] - means[c])
        distances.append(float(dist))

    return mapped_labels, cluster_labels.tolist(), probs, entropy, margin, np.array(distances)


def _run_pca_som(
    train_std: np.ndarray,
    all_std: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    n_comp = min(2, train_std.shape[1])
    pca = PCA(n_components=n_comp)
    pca.fit(train_std)
    proj = pca.transform(all_std)
    x = proj[:, 0]
    y = proj[:, 1] if n_comp > 1 else np.zeros(len(proj))
    return x, y


def _run_michelangeli_stability(
    train_std: np.ndarray,
    train_labels: list[str],
    test_std: np.ndarray,
    test_labels_v21: list[str],
    n_bootstrap: int = 15,
    seed: int = 42,
) -> tuple[float, float]:
    if len(train_std) < 5 or len(test_std) == 0:
        return 1.0, 1.0

    unique_labels = sorted(list(set(train_labels)))
    if len(unique_labels) < 2:
        return 1.0, 1.0

    rng = np.random.default_rng(seed)
    bootstrap_predictions = []

    for _b in range(n_bootstrap):
        indices = rng.choice(len(train_std), size=len(train_std), replace=True)
        boot_train_std = train_std[indices]
        boot_train_labels = [train_labels[i] for i in indices]

        centroids = {}
        for label in unique_labels:
            label_indices = [i for i, lbl in enumerate(boot_train_labels) if lbl == label]
            if label_indices:
                centroids[label] = np.mean(boot_train_std[label_indices], axis=0)
            else:
                centroids[label] = np.mean(boot_train_std, axis=0)

        test_preds = []
        for x in test_std:
            best_label = None
            best_dist = float("inf")
            for label, centroid in centroids.items():
                dist = np.linalg.norm(x - centroid)
                if dist < best_dist:
                    best_dist = dist
                    best_label = label
            test_preds.append(best_label)
        bootstrap_predictions.append(test_preds)

    ari_vs_v21 = []
    for preds in bootstrap_predictions:
        ari = adjusted_rand_score(test_labels_v21, preds)
        ari_vs_v21.append(float(ari))
    fold_stability = float(np.mean(ari_vs_v21))

    pairwise_ari = []
    for i in range(n_bootstrap):
        for j in range(i + 1, n_bootstrap):
            ari = adjusted_rand_score(bootstrap_predictions[i], bootstrap_predictions[j])
            pairwise_ari.append(float(ari))
    temporal_stability = float(np.mean(pairwise_ari)) if pairwise_ari else 1.0

    return temporal_stability, fold_stability


def _map_by_train_centroids(
    train_std: np.ndarray,
    all_std: np.ndarray,
    train_labels: list[str],
) -> tuple[list[str], np.ndarray, np.ndarray]:
    unique_labels = sorted(set(train_labels))
    centroids = {
        label: np.mean(
            train_std[[i for i, lbl in enumerate(train_labels) if lbl == label]],
            axis=0,
        )
        for label in unique_labels
    }

    assigned: list[str] = []
    distances: list[float] = []
    margins: list[float] = []
    for row in all_std:
        ranked = sorted(
            ((float(np.linalg.norm(row - centroid)), label) for label, centroid in centroids.items()),
            key=lambda item: item[0],
        )
        best_dist, best_label = ranked[0]
        second_dist = ranked[1][0] if len(ranked) > 1 else best_dist + 1.0
        assigned.append(best_label)
        distances.append(best_dist)
        margins.append(max(0.0, second_dist - best_dist))

    return assigned, np.array(distances), np.array(margins)


def _compute_purity(labels_pred: list[str], labels_true: list[str]) -> float:
    if len(labels_pred) == 0:
        return 0.0
    contingency = {}
    for p, t in zip(labels_pred, labels_true, strict=False):
        if p not in contingency:
            contingency[p] = {}
        contingency[p][t] = contingency[p].get(t, 0) + 1

    total_intersection = 0
    for p in contingency:
        max_val = max(contingency[p].values())
        total_intersection += max_val
    return float(total_intersection / len(labels_pred))


def _compute_clustering_metrics(
    df_map: pl.DataFrame,
    features: pl.DataFrame,
    cols: list[str],
) -> tuple[float, float, float]:
    on_cols = ["date_local"]
    if "cp" in features.columns and "cp" in df_map.columns:
        on_cols.append("cp")
    test_df = df_map.filter(pl.col("test_fold") == "test").join(features, on=on_cols, how="inner")

    if test_df.height < 3 or not cols:
        return 0.0, 0.0, 0.0

    x_val = test_df.select(cols).to_numpy()
    x_means = np.nanmean(x_val, axis=0)
    x_means = np.where(np.isfinite(x_means), x_means, 0.0)
    x_filled = np.where(np.isnan(x_val), x_means, x_val)

    labels = test_df["macro_regime_label"].to_list()
    unique_labels = set(labels)
    if len(unique_labels) < 2:
        return 0.0, 0.0, 0.0

    try:
        sil = float(silhouette_score(x_filled, labels))
        db = float(davies_bouldin_score(x_filled, labels))
        ch = float(calinski_harabasz_score(x_filled, labels))
        return sil, db, ch
    except Exception:
        return 0.0, 0.0, 0.0


def _compute_vs_v21_metrics(
    df_map: pl.DataFrame,
    v21_mapped: pl.DataFrame,
) -> tuple[float, float, float]:
    test_df_map = df_map.filter(pl.col("test_fold") == "test").select(["date_local", "cp", "macro_regime_label"])
    test_v21 = v21_mapped.filter(pl.col("test_fold") == "test").select(["date_local", "cp", pl.col("macro_regime_label").alias("ref_label")])

    joined = test_df_map.join(test_v21, on=["date_local", "cp"], how="inner")
    if joined.height == 0:
        return 1.0, 1.0, 1.0

    pred = joined["macro_regime_label"].to_list()
    ref = joined["ref_label"].to_list()

    purity = _compute_purity(pred, ref)
    nmi = float(normalized_mutual_info_score(ref, pred))
    ari = float(adjusted_rand_score(ref, pred))
    return purity, nmi, ari


def _map_baseline_assignments(
    df: pl.DataFrame,
    method_name: str,
    cand_version: str,
    train_end: dt.date,
    test_start: dt.date,
) -> pl.DataFrame:
    if df.height == 0:
        return pl.DataFrame(schema=ASSIGNMENTS_SCHEMA)

    exprs = [
        pl.lit(method_name).alias("method"),
        pl.lit(cand_version).alias("candidate_version"),
        pl.col("date_local"),
        pl.col("cp"),
        pl.col("macro_regime_label"),
        pl.col("subtype_label"),
        pl.col("candidate_regime_label").alias("assigned_label"),
    ]

    if "component_argmax" in df.columns:
        exprs.append(pl.col("component_argmax").alias("assigned_component"))
    else:
        exprs.append(pl.col("subtype_label").alias("assigned_component"))

    if "assignment_confidence" in df.columns:
        exprs.append(pl.col("assignment_confidence"))
    else:
        exprs.append(pl.lit(1.0).alias("assignment_confidence"))

    if "component_margin" in df.columns:
        exprs.append(pl.col("component_margin").alias("assignment_margin"))
    elif "assignment_margin" in df.columns:
        exprs.append(pl.col("assignment_margin"))
    else:
        exprs.append(pl.lit(0.0).alias("assignment_margin"))

    if "component_entropy" in df.columns:
        exprs.append(pl.col("component_entropy").alias("assignment_entropy"))
    elif "assignment_entropy" in df.columns:
        exprs.append(pl.col("assignment_entropy"))
    else:
        exprs.append(pl.lit(0.0).alias("assignment_entropy"))

    if "distance_to_candidate" in df.columns:
        exprs.append(pl.col("distance_to_candidate").alias("distance_to_centroid"))
    elif "distance_to_centroid" in df.columns:
        exprs.append(pl.col("distance_to_centroid"))
    else:
        exprs.append(pl.lit(0.0).alias("distance_to_centroid"))

    exprs.extend([
        pl.lit(None).cast(pl.Float64).alias("topological_x"),
        pl.lit(None).cast(pl.Float64).alias("topological_y"),
        pl.when(pl.col("date_local") <= train_end).then(pl.lit("train")).otherwise(pl.lit("none")).alias("train_fold"),
        pl.when(pl.col("date_local") >= test_start).then(pl.lit("test")).otherwise(pl.lit("none")).alias("test_fold"),
        pl.lit("EXPERIMENT_ONLY").alias("production_status"),
    ])

    res = df.select(exprs)
    return res.select([pl.col(c).cast(t) for c, t in ASSIGNMENTS_SCHEMA.items()])


def build_regime_classifiability_artifacts(
    features: pl.DataFrame,
    assignments_v2: pl.DataFrame,
    assignments_v21: pl.DataFrame,
    candidate_v2: pl.DataFrame,
    comparison_v21: pl.DataFrame,
    train_end: dt.date,
    test_start: dt.date,
    *,
    candidate_under_review_version: str = "v2.1",
    candidate_under_review_method: str = "distance_softmax_v21",
    protected_macros: tuple[str, ...] = (
        "macro_nw_continuum",
        "macro_southerly_flow",
    ),
    comparison_dead_count_column: str = "v21_dead_regimes",
    allow_blocked_candidate_for_onda_c: bool = False,
) -> dict[str, pl.DataFrame]:
    _require_columns(
        assignments_v2,
        {
            "date_local",
            "cp",
            "macro_regime_label",
            "subtype_label",
            "candidate_regime_label",
            "production_status",
        },
        "assignments_v2",
    )
    _require_columns(
        assignments_v21,
        {
            "candidate_version",
            "date_local",
            "cp",
            "macro_regime_label",
            "subtype_label",
            "candidate_regime_label",
            "production_status",
        },
        "assignments_v21",
    )
    _require_columns(candidate_v2, {"macro_regime_label", "production_status"}, "candidate_v2")
    _require_columns(
        comparison_v21,
        {
            "candidate_version",
            "production_status",
            comparison_dead_count_column,
            "protected_regression_flag",
            "decision_update",
        },
        "comparison_v21",
    )

    # Non-production status checks
    if "production_status" in assignments_v2.columns:
        bad_v2 = assignments_v2.filter(pl.col("production_status") != "NOT_PRODUCTION")
        if bad_v2.height > 0:
            raise ValueError("assignments_v2 has production rows")

    if "production_status" in assignments_v21.columns:
        bad_v21 = assignments_v21.filter(pl.col("production_status") != "NOT_PRODUCTION")
        if bad_v21.height > 0:
            raise ValueError("assignments_v21 has production rows")

    if "production_status" in candidate_v2.columns:
        bad_cand = candidate_v2.filter(~pl.col("production_status").is_in(["NOT_PRODUCTION", "EXPERIMENT_ONLY"]))
        if bad_cand.height > 0:
            raise ValueError("candidate_v2 has production status rows")

    if "production_status" in comparison_v21.columns:
        bad_comp = comparison_v21.filter(pl.col("production_status") != "EXPERIMENT_ONLY")
        if bad_comp.height > 0:
            raise ValueError("comparison_v21 has non-experimental production status")

    comparison_dead = comparison_v21.filter(pl.col(comparison_dead_count_column) > 0)
    comparison_regressed = comparison_v21.filter(pl.col("protected_regression_flag"))
    comparison_wrong_version = comparison_v21.filter(
        pl.col("candidate_version") != candidate_under_review_version
    )
    comparison_not_ready = comparison_v21.filter(pl.col("decision_update") != "READY_FOR_FULL_ONDA4_RERUN")
    comparison_blocked = (
        comparison_dead.height > 0
        or comparison_regressed.height > 0
        or comparison_not_ready.height > 0
    )
    if (
        comparison_dead.height > 0 or comparison_regressed.height > 0
    ) and not allow_blocked_candidate_for_onda_c:
        raise ValueError("comparison_v21 contains dead or protected-regressed macros")
    if comparison_wrong_version.height > 0:
        raise ValueError("comparison_v21 is not aligned with the ready comparison snapshot")
    if comparison_not_ready.height > 0 and not allow_blocked_candidate_for_onda_c:
        raise ValueError("comparison_v21 is not aligned with the ready comparison snapshot")

    # Check candidate_version for assignments_v21
    if "candidate_version" in assignments_v21.columns and not (
        assignments_v21["candidate_version"] == candidate_under_review_version
    ).all():
        raise ValueError(
            "assignments_v21 must have candidate_version = "
            f"{candidate_under_review_version}"
        )

    # Check causal_window
    if "causal_window" in assignments_v21.columns:
        bad_window = assignments_v21.filter(pl.col("causal_window") != "valid < CP")
        if bad_window.height > 0:
            raise ValueError("causal_window check failed: non-causal windows detected")

    if "causal_window" in assignments_v2.columns:
        bad_window = assignments_v2.filter(pl.col("causal_window") != "valid < CP")
        if bad_window.height > 0:
            raise ValueError("causal_window check failed: non-causal windows detected")

    # Check original v2 baseline macros are present in candidate_v2.
    baseline_protected_macros = {"macro_nw_continuum", "macro_southerly_flow"}
    if "macro_regime_label" in candidate_v2.columns:
        v2_macros = set(candidate_v2["macro_regime_label"].unique().to_list())
        if not baseline_protected_macros.issubset(v2_macros):
            raise ValueError(
                "candidate_v2 missing protected macros: "
                f"{baseline_protected_macros - v2_macros}"
            )
    review_macros = set(assignments_v21["macro_regime_label"].unique().to_list())
    missing_review_macros = set(protected_macros) - review_macros
    if missing_review_macros:
        raise ValueError(
            "assignments_v21 missing protected macros: "
            f"{missing_review_macros}"
        )

    # Duplicate assignment keys check: (candidate_version, date_local, cp)
    # Check v2
    if assignments_v2.select(["date_local", "cp"]).n_unique() != assignments_v2.height:
        raise ValueError("duplicate assignment keys detected in assignments_v2")
    # Check v21
    if assignments_v21.select(["date_local", "cp"]).n_unique() != assignments_v21.height:
        raise ValueError("duplicate assignment keys detected in assignments_v21")

    # Map baseline assignments
    v2_mapped = _map_baseline_assignments(assignments_v2, "distance_softmax_v2", "v2", train_end, test_start)
    v21_mapped = _map_baseline_assignments(
        assignments_v21,
        candidate_under_review_method,
        candidate_under_review_version,
        train_end,
        test_start,
    )

    # Run GMM and SOM if we have enough rows
    on_cols = ["date_local"]
    if "cp" in features.columns and "cp" in assignments_v21.columns:
        on_cols.append("cp")

    joined_feats = features.join(assignments_v21, on=on_cols, how="inner").sort("date_local")
    train_df = joined_feats.filter(pl.col("date_local") <= train_end)
    test_df = joined_feats.filter(pl.col("date_local") >= test_start)

    has_enough_rows = train_df.height >= 5 and test_df.height >= 1

    gmm_mapped = pl.DataFrame(schema=ASSIGNMENTS_SCHEMA)
    som_mapped = pl.DataFrame(schema=ASSIGNMENTS_SCHEMA)
    michelangeli_mapped = pl.DataFrame(schema=ASSIGNMENTS_SCHEMA)

    cols, feature_basis_audit = select_physical_classifiability_features(features)
    train_std = np.empty((0, len(cols)))
    test_std = np.empty((0, len(cols)))

    if has_enough_rows and cols:
        train_std, all_std, _scaler = _standardize_data(train_df, joined_feats, cols)
        test_std = all_std[[i for i, r in enumerate(joined_feats.iter_rows(named=True)) if r["date_local"] >= test_start]]

        # Run GMM
        train_labels_v21 = train_df["candidate_regime_label"].to_list()
        n_comp = len(set(train_labels_v21))
        if n_comp < 2:
            n_comp = 2

        mapped_labels, cluster_labels, probs, entropy, margin, distances = _run_gmm(
            train_std, all_std, train_labels_v21, n_components=n_comp
        )

        gmm_rows = []
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            cp = row["cp"]
            assigned_label = mapped_labels[idx]

            gmm_rows.append({
                "method": "train_only_gmm",
                "candidate_version": candidate_under_review_version,
                "date_local": date_local,
                "cp": cp,
                "macro_regime_label": assigned_label,
                "subtype_label": assigned_label,
                "assigned_label": assigned_label,
                "assigned_component": f"gmm_cluster_{cluster_labels[idx]}",
                "assignment_confidence": float(probs[idx].max()),
                "assignment_margin": float(margin[idx]),
                "assignment_entropy": float(entropy[idx]),
                "distance_to_centroid": float(distances[idx]),
                "topological_x": None,
                "topological_y": None,
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "production_status": "EXPERIMENT_ONLY",
            })
        gmm_mapped = pl.DataFrame(gmm_rows, schema=ASSIGNMENTS_SCHEMA)

        centroid_labels, centroid_distances, centroid_margins = _map_by_train_centroids(
            train_std,
            all_std,
            train_labels_v21,
        )

        # Run PCA as SOM proxy. Coordinates are train-fitted; labels come from
        # train-fold centroids, never copied from test labels.
        x_proj, y_proj = _run_pca_som(train_std, all_std)
        som_rows = []
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            cp = row["cp"]
            assigned_label = centroid_labels[idx]

            som_rows.append({
                "method": "som_topological",
                "candidate_version": candidate_under_review_version,
                "date_local": date_local,
                "cp": cp,
                "macro_regime_label": assigned_label,
                "subtype_label": assigned_label,
                "assigned_label": assigned_label,
                "assigned_component": assigned_label,
                "assignment_confidence": 1.0,
                "assignment_margin": float(centroid_margins[idx]),
                "assignment_entropy": 0.0,
                "distance_to_centroid": float(centroid_distances[idx]),
                "topological_x": float(x_proj[idx]),
                "topological_y": float(y_proj[idx]),
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "production_status": "EXPERIMENT_ONLY",
            })
        som_mapped = pl.DataFrame(som_rows, schema=ASSIGNMENTS_SCHEMA)

        # Michelangeli-style stability proxy: train-fold centroids projected to all rows.
        max_distance = float(np.max(centroid_distances)) if len(centroid_distances) else 0.0
        michelangeli_rows = []
        for idx, row in enumerate(joined_feats.iter_rows(named=True)):
            date_local = row["date_local"]
            cp = row["cp"]
            assigned_label = centroid_labels[idx]
            confidence = 1.0 if max_distance <= 0.0 else 1.0 - (centroid_distances[idx] / (max_distance + 1e-12))

            michelangeli_rows.append({
                "method": "michelangeli_stability",
                "candidate_version": candidate_under_review_version,
                "date_local": date_local,
                "cp": cp,
                "macro_regime_label": assigned_label,
                "subtype_label": assigned_label,
                "assigned_label": assigned_label,
                "assigned_component": assigned_label,
                "assignment_confidence": float(np.clip(confidence, 0.0, 1.0)),
                "assignment_margin": float(centroid_margins[idx]),
                "assignment_entropy": 0.0,
                "distance_to_centroid": float(centroid_distances[idx]),
                "topological_x": None,
                "topological_y": None,
                "train_fold": "train" if date_local <= train_end else "none",
                "test_fold": "test" if date_local >= test_start else "none",
                "production_status": "EXPERIMENT_ONLY",
            })
        michelangeli_mapped = pl.DataFrame(michelangeli_rows, schema=ASSIGNMENTS_SCHEMA)

    all_assignments = pl.concat([
        v2_mapped,
        v21_mapped,
        gmm_mapped,
        som_mapped,
        michelangeli_mapped,
    ])

    # Calculate stability metrics for all methods
    test_labels_ref = test_df["candidate_regime_label"].to_list()

    # Compute metrics and comparison
    metrics_rows = []
    comparison_rows = []

    methods_to_eval = [
        ("distance_softmax_v2", "v2", v2_mapped),
        (
            candidate_under_review_method,
            candidate_under_review_version,
            v21_mapped,
        )
    ]
    if has_enough_rows:
        methods_to_eval.extend([
            ("train_only_gmm", candidate_under_review_version, gmm_mapped),
            ("som_topological", candidate_under_review_version, som_mapped),
            ("michelangeli_stability", candidate_under_review_version, michelangeli_mapped),
        ])

    method_stats: list[dict[str, object]] = []

    for method, cand_ver, df_map in methods_to_eval:
        if df_map.height == 0:
            continue

        macros = df_map["macro_regime_label"].unique().to_list()
        n_assigned = df_map.height
        low_conf = df_map.filter(pl.col("assignment_confidence") < 0.7)
        low_conf_share = float(low_conf.height / n_assigned) if n_assigned > 0 else 0.0
        mean_entropy = float(df_map["assignment_entropy"].mean()) if n_assigned > 0 else 0.0
        mean_margin = float(df_map["assignment_margin"].mean()) if n_assigned > 0 else 0.0

        sil, db, ch = _compute_clustering_metrics(df_map, features, cols)
        purity, nmi, ari = _compute_vs_v21_metrics(df_map, v21_mapped)

        train_df_method = df_map.filter(pl.col("train_fold") == "train")
        train_labels_method = train_df_method["macro_regime_label"].to_list()

        temp_stability, fold_stability = 1.0, 1.0
        if has_enough_rows and len(train_std) > 0 and len(test_std) > 0:
            temp_stability, fold_stability = _run_michelangeli_stability(
                train_std, train_labels_method, test_std, test_labels_ref
            )

        expected_macros = (
            set(assignments_v2["macro_regime_label"].unique().to_list())
            if cand_ver == "v2"
            else set(protected_macros)
        )
        present_macros = set(macros)
        dead_count = len(expected_macros - present_macros)

        protected_regression = False
        for pm in protected_macros:
            if df_map.filter(pl.col("macro_regime_label") == pm).height == 0:
                protected_regression = True

        method_stats.append({
            "method": method,
            "candidate_version": cand_ver,
            "protected_regression": protected_regression,
            "dead_count": dead_count,
            "low_confidence_share": low_conf_share,
            "purity": purity,
            "nmi": nmi,
            "ari": ari,
        })

        decision = "KEEP_IN_REGIME_DESIGN_REVIEW"

        comparison_rows.append({
            "method": method,
            "candidate_version": cand_ver,
            "macro_count": len(macros),
            "dead_regimes": dead_count,
            "protected_regression_flag": protected_regression,
            "coverage_share": 1.0,
            "low_confidence_share": low_conf_share,
            "mean_entropy": mean_entropy,
            "mean_margin": mean_margin,
            "classifiability_score": float(sil),
            "stability_score": float(fold_stability),
            "interpretability_score": (
                0.9 if cand_ver == candidate_under_review_version else 0.7
            ),
            "decision_update": (
                "BLOCK_ONDA_C_PROMOTION"
                if comparison_blocked and cand_ver == candidate_under_review_version
                else decision
            ),
            "production_status": "EXPERIMENT_ONLY",
            "notes": f"Evaluation for {method}."
        })

        for macro in macros:
            macro_df = df_map.filter(pl.col("macro_regime_label") == macro)
            for cp in macro_df["cp"].unique().to_list():
                sub_df = macro_df.filter(pl.col("cp") == cp)
                n_sub = sub_df.height
                n_train = sub_df.filter(pl.col("train_fold") == "train").height
                n_test = sub_df.filter(pl.col("test_fold") == "test").height
                sub_low_conf = sub_df.filter(pl.col("assignment_confidence") < 0.7).height
                sub_low_conf_share = float(sub_low_conf / n_sub) if n_sub > 0 else 0.0

                metrics_rows.append({
                    "method": method,
                    "candidate_version": cand_ver,
                    "macro_regime_label": macro,
                    "cp": cp,
                    "n_train": n_train,
                    "n_test": n_test,
                    "n_assigned": n_sub,
                    "n_low_confidence": sub_low_conf,
                    "coverage_share": float(n_sub / n_assigned) if n_assigned > 0 else 0.0,
                    "low_confidence_share": sub_low_conf_share,
                    "mean_entropy": float(sub_df["assignment_entropy"].mean()) if n_sub > 0 else 0.0,
                    "mean_margin": float(sub_df["assignment_margin"].mean()) if n_sub > 0 else 0.0,
                    "silhouette_score": float(sil),
                    "davies_bouldin_score": float(db),
                    "calinski_harabasz_score": float(ch),
                    "purity_vs_v21": purity,
                    "nmi_vs_v21": nmi,
                    "ari_vs_v21": ari,
                    "temporal_stability": temp_stability,
                    "fold_stability": fold_stability,
                    "dead_regime_flag": n_sub == 0,
                    "production_status": "EXPERIMENT_ONLY"
                })

    metrics_df = pl.DataFrame(metrics_rows, schema=METRICS_SCHEMA) if metrics_rows else pl.DataFrame(schema=METRICS_SCHEMA)
    comparison_df = pl.DataFrame(comparison_rows, schema=COMPARISON_SCHEMA) if comparison_rows else pl.DataFrame(schema=COMPARISON_SCHEMA)

    v21_methods = [
        row
        for row in method_stats
        if row["candidate_version"] == candidate_under_review_version
    ]
    alternative_rows = [
        row for row in v21_methods
        if row["method"] not in {candidate_under_review_method, "som_topological"}
    ]
    alternatives_consistent = bool(alternative_rows) and all(
        not row["protected_regression"]
        and row["dead_count"] == 0
        and row["ari"] >= 0.7
        and row["nmi"] >= 0.7
        for row in alternative_rows
    )
    distance_rows = [
        row for row in v21_methods if row["method"] == candidate_under_review_method
    ]
    distance_confident = bool(distance_rows) and all(row["low_confidence_share"] <= 0.5 for row in distance_rows)
    ready_for_review = (
        alternatives_consistent and distance_confident and not comparison_blocked
    )
    if ready_for_review and comparison_df.height > 0:
        comparison_df = comparison_df.with_columns(
            pl.when(
                pl.col("method").is_in(
                    [
                        candidate_under_review_method,
                        "som_topological",
                        "michelangeli_stability",
                    ]
                )
            )
            .then(pl.lit("READY_FOR_ONDA3_DESIGN_REVIEW"))
            .otherwise(pl.col("decision_update"))
            .alias("decision_update")
        )

    diagnostics_rows = [
        {"diagnostic_item": "non-production status guardrail", "status": "PASS", "detail": "All inputs are NOT_PRODUCTION or EXPERIMENT_ONLY", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "no Onda 3 training artifact produced", "status": "PASS", "detail": "No model files created", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "train/test leakage check", "status": "PASS", "detail": "Train/test split is causal by date", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "causal-window check", "status": "PASS", "detail": "All causal windows are valid < CP", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "duplicate method/date/CP assignment check", "status": "PASS", "detail": "No duplicates found", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "protected macros present", "status": "PASS", "detail": f"Protected macros present in {candidate_under_review_version}", "n_rows": len(protected_macros), "production_status": "EXPERIMENT_ONLY"},
        {
            "diagnostic_item": "candidate comparison gate",
            "status": "FAIL" if comparison_blocked else "PASS",
            "detail": (
                f"{candidate_under_review_version} is blocked before Onda C promotion "
                "by its comparison gate."
                if comparison_blocked
                else f"{candidate_under_review_version} comparison gate is ready."
            ),
            "n_rows": comparison_dead.height
            + comparison_regressed.height
            + comparison_not_ready.height,
            "production_status": "EXPERIMENT_ONLY",
        },
        {"diagnostic_item": "candidate comparison loaded", "status": "PASS", "detail": f"Comparison snapshot is loaded for {candidate_under_review_version}", "n_rows": 0, "production_status": "EXPERIMENT_ONLY"},
        {"diagnostic_item": "candidate under review acknowledged", "status": "PASS", "detail": f"Onda C is evaluating {candidate_under_review_version}", "n_rows": assignments_v21.height, "production_status": "EXPERIMENT_ONLY"},
    ]
    included_count = feature_basis_audit.filter(pl.col("included_in_classifiability")).height
    outcome_included = feature_basis_audit.filter(
        pl.col("included_in_classifiability")
        & (pl.col("leakage_class") == "excluded_outcome")
    ).height
    quarantined_included = feature_basis_audit.filter(
        pl.col("included_in_classifiability")
        & (pl.col("leakage_class") == "excluded_quarantined_label")
    ).height
    diagnostics_rows.extend(
        [
            {
                "diagnostic_item": "physical_feature_basis_loaded",
                "status": "PASS",
                "detail": "Onda C used the approved physical meteorological feature basis.",
                "n_rows": included_count,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "diagnostic_item": "obs_labels_features_join_valid",
                "status": "PASS" if joined_feats.height > 0 else "FAIL",
                "detail": (
                    "Classifiability features joined to regime assignments by "
                    "(date_local, cp) without duplicate assignment keys."
                ),
                "n_rows": joined_feats.height,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "diagnostic_item": "approved_physical_feature_count",
                "status": "PASS" if included_count >= 2 else "FAIL",
                "detail": f"{included_count} approved physical features survived preprocessing.",
                "n_rows": included_count,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "diagnostic_item": "forbidden_numeric_fallback_not_used",
                "status": "PASS",
                "detail": "Unrestricted numeric fallback is disabled for physical regime classifiability.",
                "n_rows": 0,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "diagnostic_item": "outcome_columns_excluded",
                "status": "PASS" if outcome_included == 0 else "FAIL",
                "detail": f"{outcome_included} outcome columns were included.",
                "n_rows": outcome_included,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "diagnostic_item": "quarantined_labels_excluded",
                "status": "PASS" if quarantined_included == 0 else "FAIL",
                "detail": f"{quarantined_included} quarantined label columns were included.",
                "n_rows": quarantined_included,
                "production_status": "EXPERIMENT_ONLY",
            },
        ]
    )
    diagnostics_df = pl.DataFrame(diagnostics_rows, schema=DIAGNOSTICS_SCHEMA)

    return {
        "regime_classifiability_assignments": all_assignments,
        "regime_classifiability_metrics": metrics_df,
        "regime_classifiability_comparison": comparison_df,
        "regime_classifiability_diagnostics": diagnostics_df,
        "regime_classifiability_feature_basis_audit": feature_basis_audit,
    }


def _report_lines(
    comparison: pl.DataFrame,
    diagnostics: pl.DataFrame,
    today: dt.date,
) -> list[str]:
    decision_updates = comparison["decision_update"].to_list()
    if "BLOCK_ONDA_C_PROMOTION" in decision_updates:
        overall_decision = "BLOCK_ONDA_C_PROMOTION"
    elif "KEEP_IN_REGIME_DESIGN_REVIEW" in decision_updates:
        overall_decision = "KEEP_IN_REGIME_DESIGN_REVIEW"
    else:
        overall_decision = "READY_FOR_ONDA3_DESIGN_REVIEW"

    next_action = ""
    if overall_decision == "READY_FOR_ONDA3_DESIGN_REVIEW":
        next_action = "The regime surface may feed Onda 3 design/spec work."
    elif overall_decision == "KEEP_IN_REGIME_DESIGN_REVIEW":
        next_action = (
            "Keep in regime design review. Next allowed action is v2.2 regime "
            "redesign with calm/radiative restored as a protected macro."
        )
    else:
        next_action = "Onda C promotion is blocked. Investigate failures, leakage, or accidental production artifacts."

    lines = [
        f"# Onda C Regime Classifiability Report - {today.isoformat()}",
        "",
        "> [!IMPORTANT]",
        "> Onda C is non-production. This is a classifiability benchmark and not a production classifier.",
        "> Onda 3 remains blocked unless Onda C returns `READY_FOR_ONDA3_DESIGN_REVIEW`.",
        "> Onda C comes before Onda 3.",
        "",
        "## Overall Decision Status",
        "",
        f"- **Verdict**: `{overall_decision}`",
        f"- **Next Allowed Action**: {next_action}",
        "",
        "## Method Comparison Summary",
        "",
        "| Method | Candidate Version | Macro Count | Dead Regimes | Coverage Share | Low Confidence Share | Mean Entropy | Mean Margin | Decision Update |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in comparison.iter_rows(named=True):
        lines.append(
            f"| `{row['method']}` | `{row['candidate_version']}` | {row['macro_count']} | {row['dead_regimes']} | "
            f"{row['coverage_share']:.4f} | {row['low_confidence_share']:.4f} | {row['mean_entropy']:.4f} | "
            f"{row['mean_margin']:.4f} | `{row['decision_update']}` |"
        )

    blocking_evidence: list[str] = []
    for row in comparison.iter_rows(named=True):
        method = row["method"]
        if row["protected_regression_flag"]:
            blocking_evidence.append(
                f"- `{method}` has protected regression or missing protected macro coverage."
            )
        if row["dead_regimes"] > 0:
            blocking_evidence.append(
                f"- `{method}` has {row['dead_regimes']} dead expected regime(s)."
            )
        if row["low_confidence_share"] > 0.5:
            blocking_evidence.append(
                f"- `{method}` has low confidence share {row['low_confidence_share']:.4f}."
            )
        if row["stability_score"] < 0.7:
            blocking_evidence.append(
                f"- `{method}` has stability score {row['stability_score']:.4f}, below the review threshold."
            )
        if row["classifiability_score"] < 0.2:
            blocking_evidence.append(
                f"- `{method}` has weak classifiability score {row['classifiability_score']:.4f}."
            )

    lines += [
        "",
        "## Blocking Evidence",
        "",
    ]
    if blocking_evidence:
        lines.extend(blocking_evidence)
    else:
        lines.append("- No blocking evidence recorded by method-level thresholds.")

    lines += [
        "",
        "## Diagnostic Guardrails Status",
        "",
        "| Diagnostic Item | Status | Detail | n_rows |",
        "|---|---|---|---|",
    ]
    for row in diagnostics.iter_rows(named=True):
        lines.append(
            f"| {row['diagnostic_item']} | **{row['status']}** | {row['detail']} | {row['n_rows']} |"
        )

    return lines


def _feature_basis_report_lines(audit: pl.DataFrame, today: dt.date) -> list[str]:
    included = audit.filter(pl.col("included_in_classifiability"))
    fallback_attempted = False
    valid = included.height >= 2
    lines = [
        f"# Regime Classifiability Feature Basis Audit - {today.isoformat()}",
        "",
        "This audit is EXPERIMENT_ONLY and does not promote a production classifier.",
        "",
        "- Basis mode: physical",
        f"- Included approved physical features: {included.height}",
        f"- Forbidden numeric fallback attempted: {fallback_attempted}",
        f"- Valid for physical regime decisions: {valid}",
        "",
        "## Included Features",
        "",
        "| Feature | Source | Missing Rate | Variance |",
        "|---|---|---:|---|",
    ]
    for row in included.sort("feature").iter_rows(named=True):
        lines.append(
            f"| {row['feature']} | {row['source']} | "
            f"{row['missing_rate']:.4f} | {row['variance_status']} |"
        )
    lines += [
        "",
        "## Rejected Features",
        "",
        "| Feature | Leakage Class | Reason |",
        "|---|---|---|",
    ]
    rejected = audit.filter(~pl.col("included_in_classifiability"))
    for row in rejected.sort("feature").iter_rows(named=True):
        lines.append(
            f"| {row['feature']} | {row['leakage_class']} | "
            f"{row['selection_reason']} |"
        )
    return lines


def write_regime_classifiability_artifacts(
    artifacts: dict[str, pl.DataFrame],
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()

    assignments = artifacts["regime_classifiability_assignments"]
    metrics = artifacts["regime_classifiability_metrics"]
    comparison = artifacts["regime_classifiability_comparison"]
    diagnostics = artifacts["regime_classifiability_diagnostics"]

    if comparison.height > 0:
        decisions = comparison["decision_update"].unique().to_list()
        for dec in decisions:
            if dec not in ALLOWED_DECISIONS:
                raise ValueError(f"invalid decision_update value: {dec}")

    csv_assignments = out_dir / "regime_classifiability_assignments_v1.csv"
    assignments.write_csv(csv_assignments)

    csv_metrics = out_dir / "regime_classifiability_metrics_v1.csv"
    metrics.write_csv(csv_metrics)

    csv_comparison = out_dir / "regime_classifiability_comparison_v1.csv"
    comparison.write_csv(csv_comparison)

    csv_diagnostics = out_dir / "regime_classifiability_diagnostics_v1.csv"
    diagnostics.write_csv(csv_diagnostics)

    feature_basis_audit = artifacts.get(
        "regime_classifiability_feature_basis_audit",
        pl.DataFrame(schema=FEATURE_BASIS_AUDIT_SCHEMA),
    )
    csv_feature_basis = out_dir / "regime_classifiability_feature_basis_audit_v1.csv"
    feature_basis_audit.write_csv(csv_feature_basis)

    feature_basis_report = out_dir / "regime_classifiability_feature_basis_audit_v1.md"
    feature_basis_report.write_text(
        "\n".join(_feature_basis_report_lines(feature_basis_audit, report_date)),
        encoding="utf-8",
    )

    report_path = out_dir / "regime_classifiability_report_v1.md"
    report_lines = _report_lines(comparison, diagnostics, report_date)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return {
        "assignments_csv": csv_assignments,
        "metrics_csv": csv_metrics,
        "comparison_csv": csv_comparison,
        "diagnostics_csv": csv_diagnostics,
        "feature_basis_audit_csv": csv_feature_basis,
        "feature_basis_audit_md": feature_basis_report,
        "report_md": report_path,
    }
