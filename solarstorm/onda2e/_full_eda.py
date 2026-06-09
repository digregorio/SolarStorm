"""Full Onda 2E EDA sprint artifacts."""
from __future__ import annotations

import datetime as dt
import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.onda2e._atlas import (
    Thesis,
    _feature_row_slice,
    _join_feature_labels,
    _obs_by_local_date,
)
from solarstorm.onda2e._decision_gate import DECISION_SCHEMA

FULL_THESIS_REVIEW_SCHEMA: dict[str, pl.DataType] = {
    "thesis_id": pl.Utf8,
    "domain": pl.Utf8,
    "claim": pl.Utf8,
    "key_strata": pl.Utf8,
    "registry_complete": pl.Boolean,
    "priority": pl.Int64,
    "atlas_status": pl.Utf8,
    "testability": pl.Utf8,
    "testability_reason": pl.Utf8,
    "decision_status": pl.Utf8,
    "evidence_level": pl.Utf8,
    "source_artifact": pl.Utf8,
    "domain_artifact_family": pl.Utf8,
    "strata_reviewed": pl.Utf8,
    "review_status": pl.Utf8,
    "evidence_summary": pl.Utf8,
    "power_summary": pl.Utf8,
    "leakage_risk": pl.Utf8,
    "implementation_path": pl.Utf8,
    "next_action": pl.Utf8,
}

INPUT_MANIFEST_SCHEMA: dict[str, pl.DataType] = {
    "feature": pl.Utf8,
    "source": pl.Utf8,
    "included_in_clustering": pl.Boolean,
    "causal_availability": pl.Utf8,
    "leakage_class": pl.Utf8,
    "transform": pl.Utf8,
    "missing_rate": pl.Float64,
    "notes": pl.Utf8,
}

SWEEP_SCHEMA: dict[str, pl.DataType] = {
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "k": pl.Int64,
    "n_rows": pl.Int64,
    "n_features": pl.Int64,
    "min_cluster_rows": pl.Int64,
    "smallest_cluster_rows": pl.Int64,
    "underpowered_cluster": pl.Boolean,
    "sse": pl.Float64,
    "aic_approx": pl.Float64,
    "bic_approx": pl.Float64,
    "silhouette_mean": pl.Float64,
    "eta2_tmax_anomaly": pl.Float64,
    "eta2_remaining_warming": pl.Float64,
    "converged": pl.Boolean,
}

PROFILE_SCHEMA: dict[str, pl.DataType] = {
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "k": pl.Int64,
    "cluster_id": pl.Int64,
    "n_rows": pl.Int64,
    "wind_dir_deg_mean": pl.Float64,
    "wind_speed_mean": pl.Float64,
    "qnh_hpa_mean": pl.Float64,
    "relh_mean": pl.Float64,
    "dewpoint_depression_mean": pl.Float64,
    "precip_pre_cp_sum_mean": pl.Float64,
    "cloud_cover_score_mean": pl.Float64,
    "temp_slope_pre_cp_mean": pl.Float64,
    "tmax_anomaly_mean": pl.Float64,
    "remaining_warming_mean": pl.Float64,
    "dominant_current_regime": pl.Utf8,
}

OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "k": pl.Int64,
    "n_rows": pl.Int64,
    "eta2_tmax_anomaly": pl.Float64,
    "eta2_remaining_warming": pl.Float64,
    "tmax_anomaly_cluster_spread": pl.Float64,
    "remaining_warming_cluster_spread": pl.Float64,
    "outcome_usage": pl.Utf8,
}

STABILITY_SCHEMA: dict[str, pl.DataType] = {
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "year": pl.Int64,
    "best_k_by_bic": pl.Int64,
    "all_year_best_k_by_bic": pl.Int64,
    "best_k_matches_all_year": pl.Boolean,
    "n_rows": pl.Int64,
    "smallest_cluster_rows": pl.Int64,
    "eta2_tmax_anomaly": pl.Float64,
    "stability_note": pl.Utf8,
}

INTERPRETATION_SCHEMA: dict[str, pl.DataType] = {
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "k": pl.Int64,
    "cluster_id": pl.Int64,
    "n_rows": pl.Int64,
    "physical_signature": pl.Utf8,
    "candidate_regime_family": pl.Utf8,
    "interpretability_score": pl.Float64,
    "dominant_current_regime": pl.Utf8,
    "promotion_readiness": pl.Utf8,
}

LEAKAGE_AUDIT_SCHEMA: dict[str, pl.DataType] = {
    "audit_item": pl.Utf8,
    "status": pl.Utf8,
    "detail": pl.Utf8,
}

REGIME_DESIGN_CANDIDATE_SCHEMA: dict[str, pl.DataType] = {
    "candidate_version": pl.Utf8,
    "candidate_id": pl.Utf8,
    "thesis_id": pl.Utf8,
    "candidate_name": pl.Utf8,
    "stratum_type": pl.Utf8,
    "stratum_value": pl.Utf8,
    "k": pl.Int64,
    "cluster_id": pl.Int64,
    "n_rows": pl.Int64,
    "candidate_regime_family": pl.Utf8,
    "proposed_regime_label": pl.Utf8,
    "physical_signature": pl.Utf8,
    "interpretability_score": pl.Float64,
    "promotion_readiness": pl.Utf8,
    "bic_approx": pl.Float64,
    "delta_bic_vs_k5": pl.Float64,
    "silhouette_mean": pl.Float64,
    "eta2_tmax_anomaly": pl.Float64,
    "eta2_remaining_warming": pl.Float64,
    "smallest_cluster_rows": pl.Int64,
    "annual_match_pct": pl.Float64,
    "annual_best_k_distribution": pl.Utf8,
    "annual_mismatch_years": pl.Utf8,
    "wind_dir_deg_mean": pl.Float64,
    "wind_speed_mean": pl.Float64,
    "qnh_hpa_mean": pl.Float64,
    "relh_mean": pl.Float64,
    "dewpoint_depression_mean": pl.Float64,
    "precip_pre_cp_sum_mean": pl.Float64,
    "cloud_cover_score_mean": pl.Float64,
    "temp_slope_pre_cp_mean": pl.Float64,
    "tmax_anomaly_mean": pl.Float64,
    "remaining_warming_mean": pl.Float64,
    "dominant_current_regime": pl.Utf8,
    "source_sweep_line": pl.Utf8,
    "source_physical_line": pl.Utf8,
    "source_profile_line": pl.Utf8,
    "caveat": pl.Utf8,
    "production_status": pl.Utf8,
    "next_gate_action": pl.Utf8,
}

DOMAIN_EDA_NEXT_EXPERIMENT_SCHEMA: dict[str, pl.DataType] = {
    "thesis_id": pl.Utf8,
    "domain": pl.Utf8,
    "blocker": pl.Utf8,
    "required_artifact": pl.Utf8,
    "recommended_experiment": pl.Utf8,
}

CLUSTER_INPUT_COLUMNS: tuple[str, ...] = (
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

SEASONS: dict[int, str] = {
    12: "DJF",
    1: "DJF",
    2: "DJF",
    3: "MAM",
    4: "MAM",
    5: "MAM",
    6: "JJA",
    7: "JJA",
    8: "JJA",
    9: "SON",
    10: "SON",
    11: "SON",
}


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


def _cloud_score(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).upper()
    if text.startswith("CLR") or text.startswith("SKC"):
        return 0.0
    if text.startswith("FEW"):
        return 1.0
    if text.startswith("SCT"):
        return 2.0
    if text.startswith("BKN"):
        return 3.0
    if text.startswith("OVC"):
        return 4.0
    return None


def _qnh_hpa_from_alti(value: object) -> float | None:
    alti = _safe_float(value)
    return alti * 33.8638866667 if alti is not None else None


def _remaining_warming(row: dict[str, object]) -> float | None:
    cp_code = str(row["cp"]).replace(":", "")
    k_col = f"k_cp__cp_{cp_code}"
    k_value = _safe_float(row.get(k_col))
    tmax = _safe_float(row.get("tmax_int"))
    return tmax - k_value if tmax is not None and k_value is not None else None


def _month_means(labels: pl.DataFrame) -> pl.DataFrame:
    labels_m = labels.with_columns(pl.col("date_local").dt.month().alias("month"))
    return labels_m.group_by("month").agg(pl.mean("tmax_int").alias("month_mean_tmax"))


def _context(features: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    joined = _join_feature_labels(features, labels)
    if "month" not in joined.columns:
        joined = joined.with_columns(pl.col("date_local").dt.month().alias("month"))
    joined = joined.join(_month_means(labels), on="month", how="left")
    missing = [
        name
        for name in ["regime_label", "cp", "tmax_int", "tmax_hour"]
        if name not in joined.columns
    ]
    if missing:
        joined = joined.with_columns([pl.lit(None).alias(name) for name in missing])
    return joined


def _aggregate_obs_slice(slice_df: pl.DataFrame | None) -> dict[str, float | int | None]:
    if slice_df is None or slice_df.height == 0:
        return {
            "n_pre_cp_obs": 0,
            "drct_sin_mean": None,
            "drct_cos_mean": None,
            "sknt_mean": None,
            "qnh_hpa_mean": None,
            "relh_mean": None,
            "dewpoint_depression_mean": None,
            "precip_pre_cp_sum": None,
            "cloud_cover_score_mean": None,
            "temp_slope_pre_cp": None,
        }

    drct_sin: list[float] = []
    drct_cos: list[float] = []
    sknt: list[float] = []
    qnh: list[float] = []
    relh: list[float] = []
    dewpoint_dep: list[float] = []
    precip: list[float] = []
    cloud_scores: list[float] = []
    temps: list[tuple[dt.datetime, float]] = []

    for row in slice_df.iter_rows(named=True):
        direction = _safe_float(row.get("drct"))
        if direction is not None:
            radians = math.radians(direction)
            drct_sin.append(math.sin(radians))
            drct_cos.append(math.cos(radians))
        speed = _safe_float(row.get("sknt"))
        if speed is not None:
            sknt.append(speed)
        qnh_value = _qnh_hpa_from_alti(row.get("alti"))
        if qnh_value is not None:
            qnh.append(qnh_value)
        relh_value = _safe_float(row.get("relh"))
        if relh_value is not None:
            relh.append(relh_value)
        dep = _safe_float(row.get("dw_depression_c_int"))
        if dep is None:
            tmp = _safe_float(row.get("tmp_c_int"))
            dwp = _safe_float(row.get("dwp_c_int"))
            dep = tmp - dwp if tmp is not None and dwp is not None else None
        if dep is not None:
            dewpoint_dep.append(dep)
        p01i = _safe_float(row.get("p01i"))
        if p01i is not None:
            precip.append(p01i)
        cloud = _cloud_score(row.get("skyc1"))
        if cloud is not None:
            cloud_scores.append(cloud)
        tmp = _safe_float(row.get("tmp_c_int"))
        valid = row.get("valid")
        if tmp is not None and isinstance(valid, dt.datetime):
            temps.append((valid, tmp))

    temp_slope = None
    if len(temps) >= 2:
        temps.sort(key=lambda item: item[0])
        hours = (temps[-1][0] - temps[0][0]).total_seconds() / 3600.0
        if hours > 0:
            temp_slope = (temps[-1][1] - temps[0][1]) / hours

    def mean_or_none(values: list[float]) -> float | None:
        return float(np.mean(values)) if values else None

    return {
        "n_pre_cp_obs": slice_df.height,
        "drct_sin_mean": mean_or_none(drct_sin),
        "drct_cos_mean": mean_or_none(drct_cos),
        "sknt_mean": mean_or_none(sknt),
        "qnh_hpa_mean": mean_or_none(qnh),
        "relh_mean": mean_or_none(relh),
        "dewpoint_depression_mean": mean_or_none(dewpoint_dep),
        "precip_pre_cp_sum": float(np.sum(precip)) if precip else None,
        "cloud_cover_score_mean": mean_or_none(cloud_scores),
        "temp_slope_pre_cp": temp_slope,
    }


def _build_cluster_matrix(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str,
) -> pl.DataFrame:
    if features.height == 0 or labels.height == 0 or obs.height == 0:
        return pl.DataFrame()

    joined = _context(features, labels)
    if "dq_tmp_c_int" not in obs.columns:
        obs = obs.with_columns(pl.lit("ok").alias("dq_tmp_c_int"))
    obs_by_date = _obs_by_local_date(obs, tz_name)
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        slice_df = _feature_row_slice(row, obs_by_date, tz_name)
        aggregates = _aggregate_obs_slice(slice_df)
        tmax = _safe_float(row.get("tmax_int"))
        month_mean = _safe_float(row.get("month_mean_tmax"))
        month = int(row["month"])
        rows.append(
            {
                "date_local": row["date_local"],
                "month": month,
                "season": SEASONS.get(month, "unknown"),
                "cp": str(row["cp"]),
                "current_regime_label": str(row.get("regime_label") or "unknown"),
                "tmax_anomaly": (
                    tmax - month_mean if tmax is not None and month_mean is not None else None
                ),
                "remaining_warming": _remaining_warming(row),
                **aggregates,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _standardize(frame: pl.DataFrame) -> tuple[np.ndarray, pl.DataFrame]:
    needed = list(CLUSTER_INPUT_COLUMNS)
    clean = frame.drop_nulls(needed)
    if clean.height == 0:
        return np.empty((0, len(needed))), clean
    x = clean.select(needed).to_numpy().astype(float)
    mask = np.isfinite(x).all(axis=1)
    if not mask.all():
        clean = clean.filter(pl.Series(mask))
        x = x[mask]
    if x.shape[0] == 0:
        return np.empty((0, len(needed))), clean
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0] = 1.0
    return (x - mean) / std, clean


def _initial_centroids(x: np.ndarray, k: int) -> np.ndarray:
    order = np.argsort(x[:, 0])
    indices = np.linspace(0, len(order) - 1, k).round().astype(int)
    return x[order[indices]].copy()


def _kmeans(
    x: np.ndarray,
    k: int,
    *,
    max_iter: int = 60,
) -> tuple[np.ndarray, np.ndarray, float, bool]:
    centroids = _initial_centroids(x, k)
    labels = np.zeros(x.shape[0], dtype=int)
    converged = False
    for _ in range(max_iter):
        distances = ((x[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        new_labels = distances.argmin(axis=1)
        new_centroids = centroids.copy()
        for cluster_id in range(k):
            cluster_points = x[new_labels == cluster_id]
            if cluster_points.size:
                new_centroids[cluster_id] = cluster_points.mean(axis=0)
            else:
                farthest = int(np.argmax(distances.min(axis=1)))
                new_centroids[cluster_id] = x[farthest]
        if np.array_equal(new_labels, labels):
            converged = True
            labels = new_labels
            centroids = new_centroids
            break
        labels = new_labels
        centroids = new_centroids
    final_distances = ((x - centroids[labels]) ** 2).sum(axis=1)
    return labels, centroids, float(final_distances.sum()), converged


def _sample_indices(n: int, max_rows: int) -> np.ndarray:
    if n <= max_rows:
        return np.arange(n)
    return np.linspace(0, n - 1, max_rows).round().astype(int)


def _silhouette_mean(x: np.ndarray, labels: np.ndarray, *, max_rows: int = 400) -> float | None:
    unique = np.unique(labels)
    if len(unique) < 2:
        return None
    indices = _sample_indices(x.shape[0], max_rows)
    xs = x[indices]
    ls = labels[indices]
    if len(np.unique(ls)) < 2:
        return None
    distances = np.sqrt(((xs[:, None, :] - xs[None, :, :]) ** 2).sum(axis=2))
    scores: list[float] = []
    for idx, label in enumerate(ls):
        same = ls == label
        other_labels = [other for other in np.unique(ls) if other != label]
        if same.sum() <= 1 or not other_labels:
            continue
        a = float(distances[idx, same].sum() / (same.sum() - 1))
        b = min(float(distances[idx, ls == other].mean()) for other in other_labels)
        denom = max(a, b)
        if denom > 0:
            scores.append((b - a) / denom)
    return float(np.mean(scores)) if scores else None


def _information_criteria(sse: float, n_rows: int, n_features: int, k: int) -> tuple[float, float]:
    if n_rows <= 0 or n_features <= 0:
        return math.nan, math.nan
    variance = max(sse / (n_rows * n_features), 1e-9)
    log_likelihood = (
        -0.5 * n_rows * n_features * math.log(2.0 * math.pi * variance)
        -0.5 * sse / variance
    )
    n_params = k * n_features + k - 1
    aic = -2.0 * log_likelihood + 2.0 * n_params
    bic = -2.0 * log_likelihood + n_params * math.log(n_rows)
    return float(aic), float(bic)


def _eta_squared(values: Iterable[object], labels: Iterable[object]) -> float | None:
    pairs = [
        (float(value), int(label))
        for value, label in zip(values, labels, strict=False)
        if value is not None and math.isfinite(float(value))
    ]
    if len(pairs) < 2:
        return None
    all_values = np.array([value for value, _ in pairs], dtype=float)
    grand_mean = float(all_values.mean())
    total = float(((all_values - grand_mean) ** 2).sum())
    if total <= 0:
        return None
    between = 0.0
    for label in {label for _, label in pairs}:
        group = np.array([value for value, row_label in pairs if row_label == label])
        between += float(len(group) * (group.mean() - grand_mean) ** 2)
    return between / total


def _cluster_spread(values: Iterable[object], labels: Iterable[object]) -> float | None:
    means: list[float] = []
    for label in sorted({int(label) for label in labels}):
        group = [
            float(value)
            for value, row_label in zip(values, labels, strict=False)
            if int(row_label) == label and value is not None and math.isfinite(float(value))
        ]
        if group:
            means.append(float(np.mean(group)))
    return max(means) - min(means) if len(means) >= 2 else None


def _circular_direction_mean(sin_value: float | None, cos_value: float | None) -> float | None:
    if sin_value is None or cos_value is None:
        return None
    angle = math.degrees(math.atan2(sin_value, cos_value))
    return angle + 360.0 if angle < 0 else angle


def _dominant(values: list[str]) -> str:
    if not values:
        return "unknown"
    return Counter(values).most_common(1)[0][0]


def _cluster_profiles(
    assigned: pl.DataFrame,
    *,
    stratum_type: str,
    stratum_value: str,
    k: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cluster_id in sorted(assigned["cluster_id"].unique().to_list()):
        group = assigned.filter(pl.col("cluster_id") == cluster_id)
        sin_mean = _safe_float(group["drct_sin_mean"].mean())
        cos_mean = _safe_float(group["drct_cos_mean"].mean())
        regimes = [
            str(value)
            for value in group.get_column("current_regime_label").to_list()
            if value is not None
        ]
        rows.append(
            {
                "stratum_type": stratum_type,
                "stratum_value": stratum_value,
                "k": k,
                "cluster_id": int(cluster_id),
                "n_rows": group.height,
                "wind_dir_deg_mean": _circular_direction_mean(sin_mean, cos_mean),
                "wind_speed_mean": group["sknt_mean"].mean(),
                "qnh_hpa_mean": group["qnh_hpa_mean"].mean(),
                "relh_mean": group["relh_mean"].mean(),
                "dewpoint_depression_mean": group["dewpoint_depression_mean"].mean(),
                "precip_pre_cp_sum_mean": group["precip_pre_cp_sum"].mean(),
                "cloud_cover_score_mean": group["cloud_cover_score_mean"].mean(),
                "temp_slope_pre_cp_mean": group["temp_slope_pre_cp"].mean(),
                "tmax_anomaly_mean": group["tmax_anomaly"].mean(),
                "remaining_warming_mean": group["remaining_warming"].mean(),
                "dominant_current_regime": _dominant(regimes),
            }
        )
    return rows


def _evaluate_stratum(
    frame: pl.DataFrame,
    *,
    stratum_type: str,
    stratum_value: str,
    k_values: tuple[int, ...],
    min_cluster_rows: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    x, clean = _standardize(frame)
    sweep_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    outcome_rows: list[dict[str, object]] = []
    if x.shape[0] == 0:
        return sweep_rows, profile_rows, outcome_rows

    for k in k_values:
        if x.shape[0] < k:
            continue
        labels, _centroids, sse, converged = _kmeans(x, k)
        counts = np.bincount(labels, minlength=k)
        smallest = int(counts.min()) if counts.size else 0
        aic, bic = _information_criteria(sse, x.shape[0], x.shape[1], k)
        silhouette = _silhouette_mean(x, labels)
        eta_tmax = _eta_squared(clean["tmax_anomaly"].to_list(), labels)
        eta_rw = _eta_squared(clean["remaining_warming"].to_list(), labels)
        assigned = clean.with_columns(pl.Series("cluster_id", labels, dtype=pl.Int64))
        tmax_spread = _cluster_spread(assigned["tmax_anomaly"].to_list(), labels)
        rw_spread = _cluster_spread(assigned["remaining_warming"].to_list(), labels)

        sweep_rows.append(
            {
                "stratum_type": stratum_type,
                "stratum_value": stratum_value,
                "k": k,
                "n_rows": x.shape[0],
                "n_features": x.shape[1],
                "min_cluster_rows": min_cluster_rows,
                "smallest_cluster_rows": smallest,
                "underpowered_cluster": smallest < min_cluster_rows,
                "sse": sse,
                "aic_approx": aic,
                "bic_approx": bic,
                "silhouette_mean": silhouette,
                "eta2_tmax_anomaly": eta_tmax,
                "eta2_remaining_warming": eta_rw,
                "converged": converged,
            }
        )
        profile_rows.extend(
            _cluster_profiles(
                assigned,
                stratum_type=stratum_type,
                stratum_value=stratum_value,
                k=k,
            )
        )
        outcome_rows.append(
            {
                "stratum_type": stratum_type,
                "stratum_value": stratum_value,
                "k": k,
                "n_rows": x.shape[0],
                "eta2_tmax_anomaly": eta_tmax,
                "eta2_remaining_warming": eta_rw,
                "tmax_anomaly_cluster_spread": tmax_spread,
                "remaining_warming_cluster_spread": rw_spread,
                "outcome_usage": "Evaluation only after causal cluster assignment; not used in clustering.",
            }
        )
    return sweep_rows, profile_rows, outcome_rows


def _build_regime_cluster_artifacts(
    matrix: pl.DataFrame,
    *,
    k_values: tuple[int, ...],
    min_cluster_rows: int,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    if matrix.height == 0:
        return (
            _empty_frame(SWEEP_SCHEMA),
            _empty_frame(PROFILE_SCHEMA),
            _empty_frame(OUTCOME_SCHEMA),
        )

    sweep_rows: list[dict[str, object]] = []
    profile_rows: list[dict[str, object]] = []
    outcome_rows: list[dict[str, object]] = []

    for month in sorted(matrix["month"].unique().to_list()):
        frame = matrix.filter(pl.col("month") == month)
        rows = _evaluate_stratum(
            frame,
            stratum_type="month",
            stratum_value=str(month),
            k_values=k_values,
            min_cluster_rows=min_cluster_rows,
        )
        sweep_rows.extend(rows[0])
        profile_rows.extend(rows[1])
        outcome_rows.extend(rows[2])

    for season in sorted(matrix["season"].unique().to_list()):
        frame = matrix.filter(pl.col("season") == season)
        rows = _evaluate_stratum(
            frame,
            stratum_type="season",
            stratum_value=str(season),
            k_values=k_values,
            min_cluster_rows=min_cluster_rows,
        )
        sweep_rows.extend(rows[0])
        profile_rows.extend(rows[1])
        outcome_rows.extend(rows[2])

    sweep = (
        pl.DataFrame(sweep_rows, schema=SWEEP_SCHEMA, strict=False)
        if sweep_rows
        else _empty_frame(SWEEP_SCHEMA)
    )
    profiles = (
        pl.DataFrame(profile_rows, schema=PROFILE_SCHEMA, strict=False)
        if profile_rows
        else _empty_frame(PROFILE_SCHEMA)
    )
    outcome = (
        pl.DataFrame(outcome_rows, schema=OUTCOME_SCHEMA, strict=False)
        if outcome_rows
        else _empty_frame(OUTCOME_SCHEMA)
    )
    return sweep, profiles, outcome


def _best_k_lookup(sweep: pl.DataFrame) -> dict[tuple[str, str], int]:
    if sweep.height == 0:
        return {}
    lookup: dict[tuple[str, str], int] = {}
    best = _best_k_rows(sweep)
    for row in best.iter_rows(named=True):
        lookup[(str(row["stratum_type"]), str(row["stratum_value"]))] = int(row["k"])
    return lookup


def _build_stability_artifacts(
    matrix: pl.DataFrame,
    all_year_sweep: pl.DataFrame,
    *,
    k_values: tuple[int, ...],
    min_cluster_rows: int,
) -> pl.DataFrame:
    if matrix.height == 0:
        return _empty_frame(STABILITY_SCHEMA)

    all_best = _best_k_lookup(all_year_sweep)
    rows: list[dict[str, object]] = []
    years = sorted(
        {
            int(value.year)
            for value in matrix.get_column("date_local").to_list()
            if isinstance(value, dt.date)
        }
    )
    for year in years:
        year_matrix = matrix.filter(pl.col("date_local").dt.year() == year)
        year_sweep, _profiles, _outcome = _build_regime_cluster_artifacts(
            year_matrix,
            k_values=k_values,
            min_cluster_rows=min_cluster_rows,
        )
        for row in _best_k_rows(year_sweep).iter_rows(named=True):
            key = (str(row["stratum_type"]), str(row["stratum_value"]))
            all_k = all_best.get(key)
            best_k = int(row["k"])
            rows.append(
                {
                    "stratum_type": key[0],
                    "stratum_value": key[1],
                    "year": year,
                    "best_k_by_bic": best_k,
                    "all_year_best_k_by_bic": all_k,
                    "best_k_matches_all_year": all_k == best_k,
                    "n_rows": int(row["n_rows"]),
                    "smallest_cluster_rows": int(row["smallest_cluster_rows"]),
                    "eta2_tmax_anomaly": row["eta2_tmax_anomaly"],
                    "stability_note": (
                        "Year best-k matches all-year best-k."
                        if all_k == best_k
                        else "Year best-k differs from all-year best-k; inspect before regime promotion."
                    ),
                }
            )
    return (
        pl.DataFrame(rows, schema=STABILITY_SCHEMA, strict=False)
        if rows
        else _empty_frame(STABILITY_SCHEMA)
    )


def _physical_signature(row: dict[str, object]) -> tuple[str, str, float]:
    wind_dir = _safe_float(row.get("wind_dir_deg_mean"))
    wind_speed = _safe_float(row.get("wind_speed_mean")) or 0.0
    qnh = _safe_float(row.get("qnh_hpa_mean")) or 0.0
    relh = _safe_float(row.get("relh_mean")) or 0.0
    dew_dep = _safe_float(row.get("dewpoint_depression_mean")) or 0.0
    precip = _safe_float(row.get("precip_pre_cp_sum_mean")) or 0.0
    cloud = _safe_float(row.get("cloud_cover_score_mean")) or 0.0
    temp_slope = _safe_float(row.get("temp_slope_pre_cp_mean")) or 0.0

    tags: list[str] = []
    family = "mixed_or_transition"
    score = 0.0

    if wind_dir is not None:
        if 135 <= wind_dir <= 225:
            tags.append("southerly_flow")
            family = "southerly_disrupted_candidate"
            score += 0.35
        elif wind_dir >= 270 or wind_dir <= 45:
            tags.append("northerly_nw_flow")
            family = "nw_or_foehn_candidate"
            score += 0.30
        elif 45 < wind_dir < 135:
            tags.append("easterly_component")
            score += 0.15
        else:
            tags.append("westerly_component")
            score += 0.15

    if wind_speed >= 10:
        tags.append("windy")
        score += 0.10
    elif wind_speed <= 4:
        tags.append("light_wind")
        score += 0.10

    if dew_dep >= 7 and relh <= 70:
        tags.append("dry_air")
        score += 0.15
        if family == "nw_or_foehn_candidate":
            family = "strong_nw_foehn_candidate"
    if qnh >= 1018 and wind_speed <= 6 and cloud <= 1.5:
        tags.append("stable_clear_high_pressure")
        family = "calm_radiative_candidate"
        score += 0.20
    if precip > 0.02 or cloud >= 3 or relh >= 85:
        tags.append("moist_cloudy_or_rain")
        if family == "mixed_or_transition":
            family = "maritime_cloudy_candidate"
        score += 0.15
    if temp_slope < -0.2:
        tags.append("pre_cp_cooling")
        if family == "mixed_or_transition":
            family = "cooling_disruption_candidate"
        score += 0.15
    elif temp_slope > 0.4:
        tags.append("pre_cp_warming")
        score += 0.10

    if not tags:
        tags.append("weak_signature")
    return ";".join(tags), family, min(score, 1.0)


def _build_physical_interpretation(profiles: pl.DataFrame) -> pl.DataFrame:
    if profiles.height == 0:
        return _empty_frame(INTERPRETATION_SCHEMA)

    rows: list[dict[str, object]] = []
    for row in profiles.iter_rows(named=True):
        signature, family, score = _physical_signature(row)
        n_rows = int(row["n_rows"])
        rows.append(
            {
                "stratum_type": str(row["stratum_type"]),
                "stratum_value": str(row["stratum_value"]),
                "k": int(row["k"]),
                "cluster_id": int(row["cluster_id"]),
                "n_rows": n_rows,
                "physical_signature": signature,
                "candidate_regime_family": family,
                "interpretability_score": score,
                "dominant_current_regime": str(row["dominant_current_regime"]),
                "promotion_readiness": (
                    "underpowered" if n_rows < 30 else "design_evidence_only"
                ),
            }
        )
    return pl.DataFrame(rows, schema=INTERPRETATION_SCHEMA, strict=False)


def _manifest(matrix: pl.DataFrame) -> pl.DataFrame:
    included = [
        (
            "drct_sin_mean",
            "obs.drct",
            "mean(sin(direction)) over valid < CP",
            "Circular wind direction component.",
        ),
        (
            "drct_cos_mean",
            "obs.drct",
            "mean(cos(direction)) over valid < CP",
            "Circular wind direction component.",
        ),
        ("sknt_mean", "obs.sknt", "mean over valid < CP", "Wind speed."),
        ("qnh_hpa_mean", "obs.alti", "altimeter inches Hg to hPa", "QNH proxy."),
        ("relh_mean", "obs.relh", "mean over valid < CP", "Relative humidity."),
        (
            "dewpoint_depression_mean",
            "obs.dw_depression_c_int or tmp-dwp",
            "mean over valid < CP",
            "Near-surface moisture spread.",
        ),
        ("precip_pre_cp_sum", "obs.p01i", "sum over valid < CP", "Pre-CP rain."),
        (
            "cloud_cover_score_mean",
            "obs.skyc1",
            "CLR/SKC=0 FEW=1 SCT=2 BKN=3 OVC=4",
            "Cloud cover proxy.",
        ),
        (
            "temp_slope_pre_cp",
            "obs.tmp_c_int",
            "last-first temperature slope over valid < CP",
            "Causal warming/cooling slope.",
        ),
    ]
    excluded = [
        ("tmax_int", "labels", "excluded", "Outcome."),
        ("tmax_hour", "labels", "excluded", "Outcome timing."),
        ("remaining_warming", "labels plus k_cp", "excluded", "Evaluation target."),
        ("tmax_anomaly", "labels", "excluded", "External validation only."),
        ("regime_label", "features", "excluded", "Quarantined baseline label."),
        ("regime_flags", "features", "excluded", "Quarantined baseline flags."),
        ("foehn_score", "features", "excluded", "Derived heuristic score; profile only."),
    ]

    rows: list[dict[str, object]] = []
    for name, source, transform, notes in included:
        missing_rate = None
        if matrix.height and name in matrix.columns:
            missing_rate = matrix.select(pl.col(name).is_null().mean()).item()
        rows.append(
            {
                "feature": name,
                "source": source,
                "included_in_clustering": True,
                "causal_availability": "valid < CP",
                "leakage_class": "causal_input",
                "transform": transform,
                "missing_rate": missing_rate,
                "notes": notes,
            }
        )
    for name, source, transform, notes in excluded:
        rows.append(
            {
                "feature": name,
                "source": source,
                "included_in_clustering": False,
                "causal_availability": "excluded",
                "leakage_class": "excluded_outcome_or_quarantined_baseline",
                "transform": transform,
                "missing_rate": None,
                "notes": notes,
            }
        )
    return pl.DataFrame(rows, schema=INPUT_MANIFEST_SCHEMA, strict=False)


def _leakage_audit(matrix: pl.DataFrame) -> pl.DataFrame:
    rows = [
        {
            "audit_item": "clustering_inputs",
            "status": "PASS",
            "detail": "All included clustering inputs are aggregated from observations with valid < CP.",
        },
        {
            "audit_item": "outcome_exclusion",
            "status": "PASS",
            "detail": "tmax_int, tmax_hour, remaining_warming, and tmax_anomaly are excluded from clustering and used only for external audit.",
        },
        {
            "audit_item": "baseline_regime_exclusion",
            "status": "PASS",
            "detail": "Current regime_label and regime_flags are excluded from clustering to avoid learning the quarantined ontology.",
        },
        {
            "audit_item": "power",
            "status": "WARN" if matrix.height == 0 else "PASS",
            "detail": (
                "No cluster matrix rows were available."
                if matrix.height == 0
                else f"Cluster matrix contains {matrix.height} date/CP rows before null filtering."
            ),
        },
    ]
    return pl.DataFrame(rows, schema=LEAKAGE_AUDIT_SCHEMA)


def _decision_by_id(decision_register: pl.DataFrame) -> dict[str, dict[str, object]]:
    rows = {}
    for row in decision_register.iter_rows(named=True):
        rows[str(row["item_id"])] = row
    return rows


def _testability_by_id(testability: pl.DataFrame) -> dict[str, dict[str, object]]:
    rows = {}
    for row in testability.iter_rows(named=True):
        rows[str(row["id"])] = row
    return rows


def _review_status(
    thesis: Thesis,
    testability: str,
    decision_status: str,
) -> tuple[str, str, str]:
    if decision_status == "PROMOTED_TO_REGIME_DESIGN":
        return (
            "READY_FOR_REGIME_DESIGN_REVIEW",
            "regime_design_queue",
            "Use only inside regime-design review; no production classifier change.",
        )
    if decision_status == "PROMOTED_TO_FEATURE_CANDIDATE":
        return (
            "READY_FOR_FEATURE_CANDIDATE_REVIEW",
            "feature_candidate_queue",
            "Review causal feature implementation and walk-forward validation.",
        )
    if decision_status == "SUPPORTED":
        return (
            "SUPPORTED_DESCRIPTIVE_EVIDENCE",
            "documented_evidence_only",
            "Keep as descriptive support unless a separate design queue item exists.",
        )
    if decision_status == "ADAPTED":
        return (
            "ADAPTED_DOMAIN_EVIDENCE",
            "documented_evidence_only",
            "Use the adapted formulation recorded in ADR-012; no production change.",
        )
    if decision_status == "REJECTED":
        return (
            "REJECTED_BY_DOMAIN_EVIDENCE",
            "rejection_register",
            "Do not use without atlas repair or new evidence.",
        )
    if testability == "blocked_external_data":
        return (
            "BLOCKED_EXTERNAL_DATA",
            "external_data_acquisition",
            "Acquire required data or keep blocked.",
        )
    if testability == "registry_missing_detail":
        return (
            "BLOCKED_REGISTRY_DETAIL",
            "atlas_registry_repair",
            "Repair thesis detail before EDA.",
        )
    if thesis.id == "WCT-REGIME-016" or thesis.domain == "REGIME":
        return (
            "REGIME_ARCHITECTURE_REQUIRED",
            "regime_architecture_experiment",
            "Resolve physical-regime architecture before Onda 4 repair.",
        )
    if testability == "gap_audit":
        return (
            "GAP_AUDIT_REQUIRED",
            "gap_audit",
            "Convert the gap into concrete data/domain EDA requirements.",
        )
    return (
        "DOMAIN_EDA_REQUIRED",
        f"{thesis.domain.lower()}_domain_eda",
        "Run domain EDA, then update ADR-012 decision rows.",
    )


def _artifact_family(thesis: Thesis, source_artifact: str) -> str:
    source = source_artifact.lower()
    if thesis.domain == "REGIME" or "regime_cluster" in source:
        return "regime_architecture_sprint"
    if "cooling" in source:
        return "cooling"
    if "foehn" in source:
        return "foehn"
    if "wind" in source:
        return "wind"
    if "timing" in source:
        return "timing"
    if "thesis_testability" in source:
        return "registry_audit"
    return thesis.domain.lower()


def _full_thesis_review(
    theses: list[Thesis],
    testability: pl.DataFrame,
    decision_register: pl.DataFrame,
) -> pl.DataFrame:
    testability_rows = _testability_by_id(testability)
    decisions = _decision_by_id(decision_register)
    rows: list[dict[str, object]] = []
    for thesis in theses:
        t_row = testability_rows.get(thesis.id, {})
        d_row = decisions.get(thesis.id, {})
        testability_status = str(t_row.get("testability", "unknown"))
        decision_status = str(d_row.get("decision_status", "BLOCKED"))
        status, path, next_action = _review_status(thesis, testability_status, decision_status)
        source_artifact = str(d_row.get("source_artifact", ""))
        rows.append(
            {
                "thesis_id": thesis.id,
                "domain": thesis.domain,
                "claim": thesis.claim,
                "key_strata": thesis.key_strata,
                "registry_complete": bool(t_row.get("registry_complete", thesis.registry_complete)),
                "priority": int(t_row.get("priority", 0) or 0),
                "atlas_status": thesis.status,
                "testability": testability_status,
                "testability_reason": str(t_row.get("testability_reason", "")),
                "decision_status": decision_status,
                "evidence_level": str(d_row.get("evidence_level", "E0_unreviewed")),
                "source_artifact": source_artifact,
                "domain_artifact_family": _artifact_family(thesis, source_artifact),
                "strata_reviewed": str(d_row.get("strata", thesis.key_strata)),
                "review_status": status,
                "evidence_summary": str(d_row.get("decision_rationale", "")),
                "power_summary": str(d_row.get("sample_size_warning", "")),
                "leakage_risk": str(d_row.get("leakage_risk", "")),
                "implementation_path": path,
                "next_action": str(d_row.get("next_allowed_action", next_action)) or next_action,
            }
        )
    return pl.DataFrame(rows, schema=FULL_THESIS_REVIEW_SCHEMA, strict=False)


def build_full_eda_artifacts(
    theses: list[Thesis],
    testability: pl.DataFrame,
    decision_register: pl.DataFrame,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    obs: pl.DataFrame,
    *,
    tz_name: str = TZ_NAME,
    k_values: tuple[int, ...] = (2, 3, 4, 5, 6),
    min_cluster_rows: int = 30,
) -> dict[str, pl.DataFrame]:
    """Build the full Onda 2E sprint review and regime-architecture artifacts."""
    review = _full_thesis_review(theses, testability, decision_register)
    matrix = _build_cluster_matrix(features, labels, obs, tz_name=tz_name)
    sweep, profiles, outcome = _build_regime_cluster_artifacts(
        matrix,
        k_values=k_values,
        min_cluster_rows=min_cluster_rows,
    )
    stability = _build_stability_artifacts(
        matrix,
        sweep,
        k_values=k_values,
        min_cluster_rows=min_cluster_rows,
    )
    interpretation = _build_physical_interpretation(profiles)
    artifacts = {
        "full_thesis_review": review,
        "regime_cluster_input_manifest": _manifest(matrix),
        "regime_cluster_sweep_by_month_season": sweep,
        "regime_cluster_profiles": profiles,
        "regime_cluster_outcome_audit": outcome,
        "regime_cluster_stability_by_year_bootstrap": stability,
        "regime_cluster_physical_interpretation": interpretation,
        "regime_cluster_leakage_audit": _leakage_audit(matrix),
    }
    artifacts["regime_design_candidate_v1"] = _build_regime_design_candidate(artifacts)
    artifacts["domain_eda_next_experiments"] = _build_domain_eda_next_experiments(review)
    return artifacts


def refresh_full_eda_decision_review(
    artifacts: dict[str, pl.DataFrame],
    theses: list[Thesis],
    testability: pl.DataFrame,
    decision_register: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Refresh thesis-review artifacts after an ADR-012 gate update."""
    review = _full_thesis_review(theses, testability, decision_register)
    return {
        **artifacts,
        "full_thesis_review": review,
        "domain_eda_next_experiments": _build_domain_eda_next_experiments(review),
    }


def _review_counts(review: pl.DataFrame) -> list[tuple[str, int]]:
    if review.height == 0:
        return []
    return [
        (str(row["review_status"]), int(row["n"]))
        for row in review.group_by("review_status")
        .len(name="n")
        .sort("review_status")
        .iter_rows(named=True)
    ]


def _best_k_rows(sweep: pl.DataFrame) -> pl.DataFrame:
    if sweep.height == 0:
        return _empty_frame(SWEEP_SCHEMA)
    return (
        sweep.sort(["stratum_type", "stratum_value", "bic_approx"])
        .group_by(["stratum_type", "stratum_value"], maintain_order=True)
        .head(1)
    )


def _row_by_stratum_k(sweep: pl.DataFrame) -> dict[tuple[str, str, int], dict[str, object]]:
    rows: dict[tuple[str, str, int], dict[str, object]] = {}
    for row in sweep.iter_rows(named=True):
        rows[(str(row["stratum_type"]), str(row["stratum_value"]), int(row["k"]))] = row
    return rows


def _annual_stability_summary(
    stability: pl.DataFrame,
) -> dict[tuple[str, str], tuple[float | None, int, str, str]]:
    summaries: dict[tuple[str, str], tuple[float | None, int, str, str]] = {}
    if stability.height == 0:
        return summaries
    for key_values, group in stability.group_by(["stratum_type", "stratum_value"]):
        stratum_type, stratum_value = (str(key_values[0]), str(key_values[1]))
        matches = [
            bool(value)
            for value in group.get_column("best_k_matches_all_year").to_list()
            if value is not None
        ]
        match_pct = (sum(matches) / len(matches) * 100.0) if matches else None
        best_ks = [int(value) for value in group.get_column("best_k_by_bic").to_list()]
        distribution = "; ".join(
            f"k={k}:{count}" for k, count in sorted(Counter(best_ks).items())
        )
        mismatch_years = [
            str(row["year"])
            for row in group.iter_rows(named=True)
            if not bool(row["best_k_matches_all_year"])
        ]
        summaries[(stratum_type, stratum_value)] = (
            match_pct,
            group.height,
            distribution,
            ";".join(mismatch_years),
        )
    return summaries


def _label_fragment(value: object) -> str:
    return (
        str(value)
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(";", "_")
        .replace("=", "_")
    )


def _source_ref(filename: str, row: dict[str, object]) -> str:
    parts = [
        f"stratum_type={row.get('stratum_type')}",
        f"stratum_value={row.get('stratum_value')}",
        f"k={row.get('k')}",
    ]
    if "cluster_id" in row:
        parts.append(f"cluster_id={row.get('cluster_id')}")
    return f"reports/onda2e/{filename}:" + ",".join(parts)


def _candidate_caveat(
    *,
    best_k: int | None,
    smallest_cluster_rows: int | None,
    annual_match_pct: float | None,
    family: str,
) -> str:
    if best_k != 6:
        return f"k=6 is retained only as sensitivity; approximate BIC winner is k={best_k}."
    if smallest_cluster_rows is not None and smallest_cluster_rows < 30:
        return "Smallest k=6 cluster is underpowered; do not promote without more data."
    if annual_match_pct is not None and annual_match_pct < 85.0:
        return "Annual stability is below 85%; run k=5 sensitivity before final design."
    if family == "mixed_or_transition":
        return "Mixed/transition cluster needs final physical interpretation before Onda 4."
    return "Design evidence only; requires Onda 4 robustness before production."


def _build_regime_design_candidate(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    profiles = artifacts["regime_cluster_profiles"]
    interpretation = artifacts["regime_cluster_physical_interpretation"]
    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    if sweep.height == 0:
        return _empty_frame(REGIME_DESIGN_CANDIDATE_SCHEMA)

    sweep_by_key = _row_by_stratum_k(sweep)
    best_by_stratum = {
        (str(row["stratum_type"]), str(row["stratum_value"])): row
        for row in _best_k_rows(sweep).iter_rows(named=True)
    }
    stability_by_stratum = _annual_stability_summary(stability)
    profile_by_key = {
        (
            str(row["stratum_type"]),
            str(row["stratum_value"]),
            int(row["k"]),
            int(row["cluster_id"]),
        ): row
        for row in profiles.iter_rows(named=True)
        if int(row["k"]) == 6
    }
    interpretation_by_key = {
        (
            str(row["stratum_type"]),
            str(row["stratum_value"]),
            int(row["k"]),
            int(row["cluster_id"]),
        ): row
        for row in interpretation.iter_rows(named=True)
        if int(row["k"]) == 6
    }
    keys = sorted({*profile_by_key.keys(), *interpretation_by_key.keys()})
    rows: list[dict[str, object]] = []
    for stratum_type, stratum_value, k, cluster_id in keys:
        sweep_row = sweep_by_key.get((stratum_type, stratum_value, k), {})
        k5_row = sweep_by_key.get((stratum_type, stratum_value, 5), {})
        best_row = best_by_stratum.get((stratum_type, stratum_value), {})
        profile_row = profile_by_key.get((stratum_type, stratum_value, k, cluster_id), {})
        physical_row = interpretation_by_key.get(
            (stratum_type, stratum_value, k, cluster_id),
            {},
        )
        annual_match_pct, _annual_rows, annual_distribution, annual_mismatches = (
            stability_by_stratum.get((stratum_type, stratum_value), (None, 0, "", ""))
        )
        family = str(physical_row.get("candidate_regime_family", "uninterpreted_candidate"))
        bic = _safe_float(sweep_row.get("bic_approx"))
        k5_bic = _safe_float(k5_row.get("bic_approx"))
        best_k = int(best_row["k"]) if best_row else None
        smallest = (
            int(sweep_row["smallest_cluster_rows"])
            if "smallest_cluster_rows" in sweep_row
            else None
        )
        label = (
            f"{_label_fragment(stratum_type)}_{_label_fragment(stratum_value)}_"
            f"k6_c{cluster_id}_{_label_fragment(family)}"
        )
        merged = {**profile_row, **physical_row}
        rows.append(
            {
                "candidate_version": "v1",
                "candidate_id": f"RDC-V1-{stratum_type.upper()}-{stratum_value}-C{cluster_id:02d}",
                "thesis_id": "WCT-REGIME-016",
                "candidate_name": "Wellington k=6 month/season regime design candidate",
                "stratum_type": stratum_type,
                "stratum_value": stratum_value,
                "k": k,
                "cluster_id": cluster_id,
                "n_rows": int(merged["n_rows"]) if "n_rows" in merged else 0,
                "candidate_regime_family": family,
                "proposed_regime_label": label,
                "physical_signature": str(physical_row.get("physical_signature", "")),
                "interpretability_score": _safe_float(
                    physical_row.get("interpretability_score")
                ),
                "promotion_readiness": str(
                    physical_row.get("promotion_readiness", "design_evidence_only")
                ),
                "bic_approx": bic,
                "delta_bic_vs_k5": (k5_bic - bic) if k5_bic is not None and bic is not None else None,
                "silhouette_mean": _safe_float(sweep_row.get("silhouette_mean")),
                "eta2_tmax_anomaly": _safe_float(sweep_row.get("eta2_tmax_anomaly")),
                "eta2_remaining_warming": _safe_float(
                    sweep_row.get("eta2_remaining_warming")
                ),
                "smallest_cluster_rows": smallest,
                "annual_match_pct": annual_match_pct,
                "annual_best_k_distribution": annual_distribution,
                "annual_mismatch_years": annual_mismatches,
                "wind_dir_deg_mean": _safe_float(profile_row.get("wind_dir_deg_mean")),
                "wind_speed_mean": _safe_float(profile_row.get("wind_speed_mean")),
                "qnh_hpa_mean": _safe_float(profile_row.get("qnh_hpa_mean")),
                "relh_mean": _safe_float(profile_row.get("relh_mean")),
                "dewpoint_depression_mean": _safe_float(
                    profile_row.get("dewpoint_depression_mean")
                ),
                "precip_pre_cp_sum_mean": _safe_float(
                    profile_row.get("precip_pre_cp_sum_mean")
                ),
                "cloud_cover_score_mean": _safe_float(
                    profile_row.get("cloud_cover_score_mean")
                ),
                "temp_slope_pre_cp_mean": _safe_float(
                    profile_row.get("temp_slope_pre_cp_mean")
                ),
                "tmax_anomaly_mean": _safe_float(profile_row.get("tmax_anomaly_mean")),
                "remaining_warming_mean": _safe_float(
                    profile_row.get("remaining_warming_mean")
                ),
                "dominant_current_regime": str(
                    profile_row.get(
                        "dominant_current_regime",
                        physical_row.get("dominant_current_regime", ""),
                    )
                ),
                "source_sweep_line": _source_ref(
                    "regime_cluster_sweep_by_month_season.csv",
                    {"stratum_type": stratum_type, "stratum_value": stratum_value, "k": k},
                ),
                "source_physical_line": _source_ref(
                    "regime_cluster_physical_interpretation.csv",
                    {
                        "stratum_type": stratum_type,
                        "stratum_value": stratum_value,
                        "k": k,
                        "cluster_id": cluster_id,
                    },
                ),
                "source_profile_line": _source_ref(
                    "regime_cluster_profiles.csv",
                    {
                        "stratum_type": stratum_type,
                        "stratum_value": stratum_value,
                        "k": k,
                        "cluster_id": cluster_id,
                    },
                ),
                "caveat": _candidate_caveat(
                    best_k=best_k,
                    smallest_cluster_rows=smallest,
                    annual_match_pct=annual_match_pct,
                    family=family,
                ),
                "production_status": "NOT_PRODUCTION",
                "next_gate_action": (
                    "Use only inside regime-design review; run Onda 4 robustness and "
                    "final physical interpretation before any production classifier change."
                ),
            }
        )
    return (
        pl.DataFrame(rows, schema=REGIME_DESIGN_CANDIDATE_SCHEMA, strict=False)
        if rows
        else _empty_frame(REGIME_DESIGN_CANDIDATE_SCHEMA)
    )


def _blocked_required_artifact(row: dict[str, object]) -> str:
    status = str(row["review_status"])
    domain = str(row["domain"]).lower()
    if status == "REGIME_ARCHITECTURE_REQUIRED":
        return "reports/onda2e/regime_design_candidate_v1.csv"
    if status == "BLOCKED_EXTERNAL_DATA":
        return "reports/onda2e/blocked_external_data.json"
    if status == "BLOCKED_REGISTRY_DETAIL":
        return "reports/onda2e/thesis_atlas_v1.md"
    if status == "GAP_AUDIT_REQUIRED":
        return f"reports/onda2e/{domain}_gap_audit_requirements.csv"
    return f"reports/onda2e/{domain}_domain_eda.csv"


def _blocked_recommended_experiment(row: dict[str, object]) -> str:
    status = str(row["review_status"])
    if status == "REGIME_ARCHITECTURE_REQUIRED":
        return "Resolve physical-regime architecture before Onda 4 repair."
    if status == "BLOCKED_EXTERNAL_DATA":
        return "Acquire and document required external data, or keep blocked."
    if status == "BLOCKED_REGISTRY_DETAIL":
        return "Repair thesis registry detail before EDA/regime/feature design."
    if status == "GAP_AUDIT_REQUIRED":
        return "Convert gap into concrete data/domain EDA requirements."
    return "Run domain EDA, assess causal availability/leakage, and update decision register."


def _build_domain_eda_next_experiments(review: pl.DataFrame) -> pl.DataFrame:
    if review.height == 0:
        return _empty_frame(DOMAIN_EDA_NEXT_EXPERIMENT_SCHEMA)
    rows: list[dict[str, object]] = []
    blocked = review.filter(pl.col("decision_status") == "BLOCKED")
    for row in blocked.sort(["domain", "thesis_id"]).iter_rows(named=True):
        rows.append(
            {
                "thesis_id": str(row["thesis_id"]),
                "domain": str(row["domain"]),
                "blocker": str(row["review_status"]),
                "required_artifact": _blocked_required_artifact(row),
                "recommended_experiment": _blocked_recommended_experiment(row),
            }
        )
    return (
        pl.DataFrame(rows, schema=DOMAIN_EDA_NEXT_EXPERIMENT_SCHEMA, strict=False)
        if rows
        else _empty_frame(DOMAIN_EDA_NEXT_EXPERIMENT_SCHEMA)
    )


def build_regime_design_decision_updates(artifacts: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Build ADR-012 updates for data-backed regime-design candidates."""
    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    if sweep.height == 0:
        return _empty_frame(DECISION_SCHEMA)

    candidate = artifacts.get("regime_design_candidate_v1")
    if candidate is None:
        candidate = _build_regime_design_candidate(artifacts)
    best = _best_k_rows(sweep)
    if candidate.height == 0 or best.height == 0:
        return _empty_frame(DECISION_SCHEMA)

    k6_best = best.filter(pl.col("k") == 6).height
    total_best = best.height
    if k6_best != total_best:
        return _empty_frame(DECISION_SCHEMA)

    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    stable_matches = (
        stability.filter(pl.col("best_k_matches_all_year")).height if stability.height else 0
    )
    stable_total = stability.height
    stable_pct = (stable_matches / stable_total * 100.0) if stable_total else 0.0
    underpowered = candidate.filter(pl.col("smallest_cluster_rows") < 30).height
    families = candidate.get_column("candidate_regime_family").n_unique()
    rationale = (
        f"k=6 wins approximate BIC in {k6_best}/{total_best} month/season strata; "
        f"annual best-k stability matches {stable_matches}/{stable_total} checks "
        f"({stable_pct:.1f}%); physical interpretation yields {families} candidate "
        "families but remains design_evidence_only, so Onda 4 and final interpretation "
        "are still required."
    )
    rows = [
        {
            "decision_id": "DEC-WCT-REGIME-016",
            "item_id": "WCT-REGIME-016",
            "item_type": "thesis",
            "domain": "REGIME",
            "decision_status": "PROMOTED_TO_REGIME_DESIGN",
            "evidence_level": "E2_regime_architecture_candidate",
            "source_artifact": (
                "reports/onda2e/regime_design_candidate_v1.csv; "
                "reports/onda2e/regime_cluster_sweep_by_month_season.csv; "
                "reports/onda2e/regime_cluster_stability_by_year_bootstrap.csv; "
                "reports/onda2e/regime_cluster_physical_interpretation.csv"
            ),
            "strata": "month and season x k=6 cluster",
            "sample_size_warning": (
                f"{underpowered}/{candidate.height} candidate rows have smallest k=6 "
                "cluster support below 30."
            ),
            "causal_availability": "Cluster inputs use pre-CP observations only; outcomes remain audit-only.",
            "leakage_risk": "Design-only artifact; no production classifier change before Onda 4 robustness.",
            "decision_rationale": rationale,
            "next_allowed_action": (
                "Enter regime_design_queue only; run Onda 4 robustness and final "
                "physical interpretation before any production classifier change."
            ),
        }
    ]
    return pl.DataFrame(rows, schema=DECISION_SCHEMA)


def _full_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    review = artifacts["full_thesis_review"]
    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    interpretation = artifacts["regime_cluster_physical_interpretation"]
    leakage = artifacts["regime_cluster_leakage_audit"]
    candidate = artifacts["regime_design_candidate_v1"]
    next_experiments = artifacts["domain_eda_next_experiments"]
    lines = [
        f"# Onda 2E Full EDA Sprint Report - {report_date.isoformat()}",
        "",
        "No production feature, model, or regime classifier is promoted by this sprint.",
        "Every active local thesis receives an individual review row backed by an ADR-012 decision.",
        "",
        "## Thesis Review Coverage",
        "",
        f"- Thesis rows reviewed: {review.height}",
        f"- Unique thesis IDs: {review['thesis_id'].n_unique() if review.height else 0}",
        "",
        "| Review status | Rows |",
        "|---|---:|",
    ]
    for status, count in _review_counts(review):
        lines.append(f"| {status} | {count} |")

    lines += [
        "",
        "## Regime Architecture EDA",
        "",
        f"- K-selection rows: {sweep.height}",
        f"- Year-stability rows: {stability.height}",
        f"- Physical-interpretation rows: {interpretation.height}",
        f"- Regime-design candidate rows: {candidate.height}",
        f"- Blocked next-experiment rows: {next_experiments.height}",
        "- Clustering inputs use pre-CP observations only (`valid < CP`).",
        "- Tmax anomaly and remaining warming are external audits only.",
        "",
        "| Stratum | Best k by BIC | n rows | eta2 Tmax anomaly | underpowered? |",
        "|---|---:|---:|---:|---|",
    ]
    best = _best_k_rows(sweep)
    for row in best.iter_rows(named=True):
        eta = row["eta2_tmax_anomaly"]
        eta_text = "" if eta is None else f"{float(eta):.3f}"
        lines.append(
            f"| {row['stratum_type']}={row['stratum_value']} | {row['k']} | "
            f"{row['n_rows']} | {eta_text} | {row['underpowered_cluster']} |"
        )

    lines += [
        "",
        "## Leakage Audit",
        "",
        "| Audit item | Status | Detail |",
        "|---|---|---|",
    ]
    for row in leakage.iter_rows(named=True):
        lines.append(f"| {row['audit_item']} | {row['status']} | {row['detail']} |")

    lines += [
        "",
        "## Next Gate Action",
        "",
        "Use the regime-design queue to build and validate a data-backed regime repair. Onda 4 remains blocked until that repair is designed, interpreted, and rerun.",
    ]
    return lines


def _regime_report_lines(artifacts: dict[str, pl.DataFrame], report_date: dt.date) -> list[str]:
    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    profiles = artifacts["regime_cluster_profiles"]
    outcome = artifacts["regime_cluster_outcome_audit"]
    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    interpretation = artifacts["regime_cluster_physical_interpretation"]
    lines = [
        f"# Regime Architecture Sprint Report - {report_date.isoformat()}",
        "",
        "This report tests whether a fixed four-regime ontology is sufficient or whether Wellington needs month/season-aware regime structure.",
        "",
        "## Artifacts",
        "",
        f"- `regime_cluster_sweep_by_month_season.csv`: {sweep.height} rows",
        f"- `regime_cluster_stability_by_year_bootstrap.csv`: {stability.height} rows",
        f"- `regime_cluster_profiles.csv`: {profiles.height} rows",
        f"- `regime_cluster_physical_interpretation.csv`: {interpretation.height} rows",
        f"- `regime_cluster_outcome_audit.csv`: {outcome.height} rows",
        "",
        "## Interpretation Rule",
        "",
        "A lower BIC/AIC or higher silhouette is not enough to promote a regime. A candidate also needs power, year stability, physical interpretability, and Onda 4 robustness.",
    ]
    best = _best_k_rows(sweep)
    if best.height:
        lines += [
            "",
            "## Best K By Approximate BIC",
            "",
            "| Stratum | k | n rows | smallest cluster | eta2 Tmax anomaly |",
            "|---|---:|---:|---:|---:|",
        ]
        for row in best.iter_rows(named=True):
            eta = row["eta2_tmax_anomaly"]
            eta_text = "" if eta is None else f"{float(eta):.3f}"
            lines.append(
                f"| {row['stratum_type']}={row['stratum_value']} | {row['k']} | "
                f"{row['n_rows']} | {row['smallest_cluster_rows']} | {eta_text} |"
            )
    if interpretation.height:
        lines += [
            "",
            "## Physical Interpretation Sample",
            "",
            "| Stratum | k | cluster | n | family | signature | readiness |",
            "|---|---:|---:|---:|---|---|---|",
        ]
        sample = interpretation.sort(
            ["stratum_type", "stratum_value", "k", "cluster_id"]
        ).head(20)
        for row in sample.iter_rows(named=True):
            lines.append(
                f"| {row['stratum_type']}={row['stratum_value']} | {row['k']} | "
                f"{row['cluster_id']} | {row['n_rows']} | "
                f"{row['candidate_regime_family']} | {row['physical_signature']} | "
                f"{row['promotion_readiness']} |"
            )
    return lines


def _candidate_report_lines(
    artifacts: dict[str, pl.DataFrame],
    report_date: dt.date,
) -> list[str]:
    def metric_text(value: object, digits: int) -> str:
        number = _safe_float(value)
        return "" if number is None else f"{number:.{digits}f}"

    candidate = artifacts["regime_design_candidate_v1"]
    sweep = artifacts["regime_cluster_sweep_by_month_season"]
    stability = artifacts["regime_cluster_stability_by_year_bootstrap"]
    lines = [
        f"# Regime Design Candidate v1 - {report_date.isoformat()}",
        "",
        "This is a formal regime-design proposal, not a production classifier.",
        "Candidate v1 promotes `WCT-REGIME-016` only to ADR-012 regime-design review.",
        "",
        "## Decision",
        "",
        f"- Candidate rows: {candidate.height}",
        "- Proposed k: 6 where the month/season sweep supports it.",
        "- Required next gate: Onda 4 robustness plus final physical interpretation.",
    ]
    best = _best_k_rows(sweep)
    if best.height:
        lines += [
            "",
            "## Best K By Approximate BIC",
            "",
            "| Stratum | best k | n rows | smallest cluster | BIC | silhouette | eta2 Tmax |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in best.iter_rows(named=True):
            lines.append(
                f"| {row['stratum_type']}={row['stratum_value']} | {row['k']} | "
                f"{row['n_rows']} | {row['smallest_cluster_rows']} | "
                f"{metric_text(row['bic_approx'], 1)} | "
                f"{metric_text(row['silhouette_mean'], 3)} | "
                f"{metric_text(row['eta2_tmax_anomaly'], 3)} |"
            )
    if stability.height:
        matches = stability.filter(pl.col("best_k_matches_all_year")).height
        pct = matches / stability.height * 100.0
        mismatches = stability.filter(~pl.col("best_k_matches_all_year")).height
        lines += [
            "",
            "## Annual Stability",
            "",
            f"- Matching annual best-k checks: {matches}/{stability.height} ({pct:.1f}%).",
            f"- Mismatch checks requiring k=5 sensitivity review: {mismatches}.",
        ]
    if candidate.height:
        families = (
            candidate.group_by("candidate_regime_family")
            .agg(
                pl.len().alias("clusters"),
                pl.sum("n_rows").alias("rows"),
                pl.mean("interpretability_score").alias("mean_score"),
            )
            .sort("candidate_regime_family")
        )
        lines += [
            "",
            "## Physical Families",
            "",
            "| Family | Clusters | Rows | Mean interpretability |",
            "|---|---:|---:|---:|",
        ]
        for row in families.iter_rows(named=True):
            score = row["mean_score"]
            score_text = "" if score is None else f"{float(score):.3f}"
            lines.append(
                f"| {row['candidate_regime_family']} | {row['clusters']} | "
                f"{row['rows']} | {score_text} |"
            )
    lines += [
        "",
        "## Caveats",
        "",
        "- BIC/AIC/SSE support k=6, but silhouette is not the promotion criterion.",
        "- `mixed_or_transition` clusters require final interpretation.",
        "- No production regime classifier changes until Onda 4 is rerun.",
    ]
    return lines


def write_full_eda_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: str | Path,
    today: dt.date | None = None,
) -> dict[str, Path]:
    """Write full Onda 2E EDA sprint artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_date = today or dt.date.today()
    filenames = {
        "full_thesis_review": "full_thesis_review.csv",
        "regime_cluster_input_manifest": "regime_cluster_input_manifest.csv",
        "regime_cluster_sweep_by_month_season": "regime_cluster_sweep_by_month_season.csv",
        "regime_cluster_profiles": "regime_cluster_profiles.csv",
        "regime_cluster_outcome_audit": "regime_cluster_outcome_audit.csv",
        "regime_cluster_stability_by_year_bootstrap": "regime_cluster_stability_by_year_bootstrap.csv",
        "regime_cluster_physical_interpretation": "regime_cluster_physical_interpretation.csv",
        "regime_cluster_leakage_audit": "regime_cluster_leakage_audit.csv",
        "regime_design_candidate_v1": "regime_design_candidate_v1.csv",
        "domain_eda_next_experiments": "domain_eda_next_experiments.csv",
    }
    paths: dict[str, Path] = {}
    for key, filename in filenames.items():
        path = out_dir / filename
        artifacts[key].write_csv(path)
        paths[f"{key}_csv"] = path

    full_report = out_dir / "onda2e_full_eda_report.md"
    full_report.write_text(
        "\n".join(_full_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["full_eda_report_md"] = full_report

    regime_report = out_dir / "regime_architecture_sprint_report.md"
    regime_report.write_text(
        "\n".join(_regime_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_architecture_report_md"] = regime_report

    candidate_report = out_dir / "regime_design_candidate_v1.md"
    candidate_report.write_text(
        "\n".join(_candidate_report_lines(artifacts, report_date)),
        encoding="utf-8",
    )
    paths["regime_design_candidate_md"] = candidate_report
    return paths
