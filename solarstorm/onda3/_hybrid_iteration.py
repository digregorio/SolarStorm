"""P1 horizon hybrid model: remaining-warming target with NWP anchor blend."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.honest_eval import (
    apply_physical_floor,
    assign_remaining_warming_strata,
    build_floor_violation_audit,
    build_honest_comparison,
    build_honest_gates,
    build_kcp_long,
    fit_honest_null,
    predict_honest_null,
)
from solarstorm.onda3._baseline_model import _ridge_predict
from solarstorm.onda3._interactions import add_binary_macro_interaction_features
from solarstorm.onda3._pooled_iteration import (
    CP_INDEX,
    _encode_features,
    _markdown_table,
    add_pooled_temporal_features,
    normalize_pooled_cp_column,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
HYBRID_ITERATION_ID = "onda3_p1_horizon_hybrid"
OM_ANCHOR_SOURCE = "om_prev_d1_day_max_c"
OM_FEATURE_COLUMNS = ("om_anchor_max", "om_anchor_delta", "om_anchor_delta_x_lead")
DECISION_READY_P2 = "READY_FOR_P2_DISTRIBUTION_DESIGN"
DECISION_LOCAL_REFERENCE = "KEEP_HYBRID_LOCAL_AS_REFERENCE"
DECISION_KEEP_REVIEW = "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
FREEZE_LINE = (
    "No production, EV, pricing, shadow trading, or execution work is unlocked."
)
HYBRID_FILENAMES = {
    "onda3_hybrid_model_results_v1": "onda3_hybrid_model_results_v1.csv",
    "onda3_hybrid_predictions_v1": "onda3_hybrid_predictions_v1.csv",
    "onda3_hybrid_feature_audit_v1": "onda3_hybrid_feature_audit_v1.csv",
    "onda3_hybrid_gates_v1": "onda3_hybrid_gates_v1.csv",
    "onda3_hybrid_honest_by_cp_v1": "onda3_hybrid_honest_by_cp_v1.csv",
    "onda3_hybrid_decision_v1": "onda3_hybrid_decision_v1.csv",
}


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def build_hybrid_matrix(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    assignments: pl.DataFrame | None = None,
    open_meteo: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build the CP-level P1 matrix with k_cp target and NWP anchor features."""
    features = normalize_pooled_cp_column(_ensure_date(features))
    labels = _ensure_date(labels)
    kcp = build_kcp_long(labels)
    matrix = (
        features.join(kcp, on=["date_local", "cp"], how="inner")
        .join(
            labels.select(["date_local", "tmax_int"]),
            on="date_local",
            how="inner",
        )
        .drop_nulls(["k_cp", "tmax_int"])
        .with_columns(
            (pl.col("tmax_int") - pl.col("k_cp")).alias("remaining_warming"),
            pl.col("cp")
            .replace_strict({cp: 3 - index for cp, index in CP_INDEX.items()})
            .alias("cp_lead_rank"),
        )
    )
    if assignments is not None and not assignments.is_empty():
        assignments = normalize_pooled_cp_column(_ensure_date(assignments))
        matrix = matrix.join(
            assignments.select(["date_local", "cp", "binary_macro_regime_label"]),
            on=["date_local", "cp"],
            how="left",
        )
    if open_meteo is not None and not open_meteo.is_empty():
        open_meteo = normalize_pooled_cp_column(_ensure_date(open_meteo))
        keys = open_meteo.select(["date_local", "cp"])
        if keys.height != keys.unique().height:
            raise ValueError("duplicate (date_local, cp) keys in open_meteo frame")
        matrix = matrix.join(
            open_meteo.select(
                ["date_local", "cp", pl.col(OM_ANCHOR_SOURCE).alias("om_anchor_max")]
            ),
            on=["date_local", "cp"],
            how="left",
        )
    else:
        matrix = matrix.with_columns(pl.lit(None, dtype=pl.Float64).alias("om_anchor_max"))
    return matrix.with_columns(
        (pl.col("om_anchor_max") - pl.col("k_cp")).alias("om_anchor_delta"),
    ).with_columns(
        (pl.col("om_anchor_delta") * pl.col("cp_lead_rank") / 3.0).alias(
            "om_anchor_delta_x_lead"
        )
    )


def run_hybrid_fold(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    model_name: str,
) -> pl.DataFrame:
    """Fit ridge on remaining warming and reconstruct floored Tmax predictions."""
    train_x, test_x = _encode_features(
        train,
        test,
        numeric_feature_columns=numeric_feature_columns,
        categorical_feature_columns=categorical_feature_columns,
    )
    rw_prediction = _ridge_predict(
        train_x,
        train["remaining_warming"].to_numpy(),
        test_x,
    )
    rw_clamped = np.maximum(rw_prediction, 0.0)
    tmax_prediction = test["k_cp"].to_numpy() + rw_clamped
    actual = test["tmax_int"].to_numpy()
    return test.select(["date_local", "cp"]).with_columns(
        pl.Series("actual", actual.astype(np.float64)),
        pl.Series("prediction", tmax_prediction),
        pl.Series("rw_prediction_raw", rw_prediction),
        pl.Series("absolute_error", np.abs(actual - tmax_prediction)),
        pl.lit(model_name).alias("model_name"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )


def _walk_forward_predictions(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    model_name: str,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    prediction_frames: list[pl.DataFrame] = []
    result_rows: list[dict[str, object]] = []
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    for test_year in test_years:
        train = dated.filter(pl.col("_year") < test_year).drop("_year")
        test = dated.filter(pl.col("_year") == test_year).drop("_year")
        if train.is_empty() or test.is_empty():
            continue
        predictions = run_hybrid_fold(
            train,
            test,
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
            model_name=model_name,
        ).with_columns(pl.lit(test_year).alias("test_year"))
        prediction_frames.append(predictions)
        result_rows.append(
            {
                "test_year": test_year,
                "model_name": model_name,
                "n_train": train.height,
                "n_test": test.height,
                "mae": float(predictions["absolute_error"].mean()),
                "exact_rate": float(
                    (predictions["prediction"].round(0) == predictions["actual"]).mean()
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else _empty_predictions()
    )
    return predictions, result_rows


def _empty_predictions() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.Utf8,
            "actual": pl.Float64,
            "prediction": pl.Float64,
            "rw_prediction_raw": pl.Float64,
            "absolute_error": pl.Float64,
            "model_name": pl.Utf8,
            "production_status": pl.Utf8,
            "test_year": pl.Int64,
        }
    )


def _feature_audit(
    *,
    local_numeric: list[str],
    om_numeric: list[str],
    categorical_feature_columns: list[str],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for feature in local_numeric:
        rows.append(
            {
                "feature": feature,
                "candidate": "hybrid_local_only",
                "feature_role": "local_remaining_warming_input",
                "production_status": PRODUCTION_STATUS,
            }
        )
    for feature in om_numeric:
        rows.append(
            {
                "feature": feature,
                "candidate": "hybrid_om_augmented",
                "feature_role": (
                    "nwp_anchor_input"
                    if feature in OM_FEATURE_COLUMNS
                    else "local_remaining_warming_input"
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    for feature in categorical_feature_columns:
        rows.append(
            {
                "feature": feature,
                "candidate": "all",
                "feature_role": "categorical_input",
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def build_onda3_hybrid_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> dict[str, pl.DataFrame]:
    """Run local, OM-augmented, and same-row local-reference candidates."""
    matrix = add_pooled_temporal_features(matrix)
    if "binary_macro_regime_label" in matrix.columns:
        matrix, interaction_columns = add_binary_macro_interaction_features(matrix)
    else:
        interaction_columns = []
    local_numeric = [
        column
        for column in [
            *numeric_feature_columns,
            "k_cp",
            "cp_sin",
            "cp_cos",
            "month_sin",
            "month_cos",
            "doy_sin",
            "doy_cos",
            *interaction_columns,
        ]
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]
    local_numeric = list(dict.fromkeys(local_numeric))
    om_numeric = list(
        dict.fromkeys(
            [*local_numeric, *[column for column in OM_FEATURE_COLUMNS if column in matrix.columns]]
        )
    )
    effective_categorical = [
        column for column in categorical_feature_columns if column in matrix.columns
    ]
    covered = matrix.drop_nulls(list(OM_FEATURE_COLUMNS))

    local_predictions, local_results = _walk_forward_predictions(
        matrix,
        test_years=test_years,
        numeric_feature_columns=local_numeric,
        categorical_feature_columns=effective_categorical,
        model_name="hybrid_local_only",
    )
    om_predictions, om_results = _walk_forward_predictions(
        covered,
        test_years=test_years,
        numeric_feature_columns=om_numeric,
        categorical_feature_columns=effective_categorical,
        model_name="hybrid_om_augmented",
    )
    reference_predictions, reference_results = _walk_forward_predictions(
        covered,
        test_years=test_years,
        numeric_feature_columns=local_numeric,
        categorical_feature_columns=effective_categorical,
        model_name="hybrid_local_only_covered_rows",
    )
    prediction_frames = [
        frame
        for frame in (local_predictions, om_predictions, reference_predictions)
        if not frame.is_empty()
    ]
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else _empty_predictions()
    )
    results = pl.DataFrame(
        [*local_results, *om_results, *reference_results],
        strict=False,
    )
    return {
        "onda3_hybrid_model_results_v1": results,
        "onda3_hybrid_predictions_v1": predictions,
        "onda3_hybrid_feature_audit_v1": _feature_audit(
            local_numeric=local_numeric,
            om_numeric=om_numeric,
            categorical_feature_columns=effective_categorical,
        ),
    }


def _same_row_reference_comparison(
    predictions: pl.DataFrame,
) -> tuple[float | None, float | None, bool]:
    """Pre-registered criterion 2: OM candidate vs same-row local reference MAE."""
    om = predictions.filter(pl.col("model_name") == "hybrid_om_augmented").select(
        [
            "date_local",
            "cp",
            (pl.col("prediction") - pl.col("actual")).abs().alias("om_error"),
        ]
    )
    reference = predictions.filter(
        pl.col("model_name") == "hybrid_local_only_covered_rows"
    ).select(
        [
            "date_local",
            "cp",
            (pl.col("prediction") - pl.col("actual")).abs().alias("reference_error"),
        ]
    )
    aligned = om.join(reference, on=["date_local", "cp"], how="inner")
    if aligned.is_empty():
        return None, None, False
    om_mae = float(aligned["om_error"].mean())
    reference_mae = float(aligned["reference_error"].mean())
    return om_mae, reference_mae, om_mae < reference_mae


def judge_hybrid_candidates(
    *,
    predictions: pl.DataFrame,
    labels: pl.DataFrame,
    train_end_year: int,
) -> dict[str, pl.DataFrame]:
    """Score every candidate with the P0 honest harness."""
    labels = _ensure_date(labels)
    if "test_year" in predictions.columns and predictions.height > 0:
        min_test_year = predictions["test_year"].min()
        if min_test_year is not None and int(min_test_year) <= train_end_year:
            raise ValueError(
                "judged test years overlap the honest-null window: "
                f"min test_year {min_test_year} <= train_end_year {train_end_year}"
            )
    kcp = build_kcp_long(labels)
    null_table = fit_honest_null(labels, train_end_year=train_end_year)
    gate_frames: list[pl.DataFrame] = []
    comparison_frames: list[pl.DataFrame] = []
    passed: dict[str, bool] = {}
    for model_name in sorted(predictions["model_name"].unique().to_list()):
        rows = (
            predictions.filter(pl.col("model_name") == model_name)
            .select(["date_local", "cp", "actual", "prediction"])
            .join(kcp, on=["date_local", "cp"], how="inner")
        )
        scored = assign_remaining_warming_strata(
            apply_physical_floor(predict_honest_null(rows, null_table))
        )
        comparison = build_honest_comparison(scored)
        gates, decision = build_honest_gates(
            by_cp=comparison["by_cp"],
            by_stratum=comparison["by_stratum"],
            by_stratum_cp=comparison["by_stratum_cp"],
            floor_audit=build_floor_violation_audit(scored),
        )
        passed[model_name] = (
            decision.row(0, named=True)["decision_status"]
            == "HONEST_EVALUATION_PASSED"
        )
        gate_frames.append(gates.with_columns(pl.lit(model_name).alias("model_name")))
        comparison_frames.append(
            comparison["by_cp"].with_columns(pl.lit(model_name).alias("model_name"))
        )
    om_same_row_mae, reference_same_row_mae, om_beats_reference = (
        _same_row_reference_comparison(predictions)
    )
    if passed.get("hybrid_om_augmented", False) and om_beats_reference:
        decision_status = DECISION_READY_P2
    elif passed.get("hybrid_local_only", False):
        decision_status = DECISION_LOCAL_REFERENCE
    else:
        decision_status = DECISION_KEEP_REVIEW
    decision = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "decision_rationale": (
                    "P1 hybrid candidates judged by P0 honest gates plus the "
                    "pre-registered same-row MAE comparison against "
                    "hybrid_local_only_covered_rows (spec success criterion 2)."
                ),
                "om_same_row_mae": om_same_row_mae,
                "reference_same_row_mae": reference_same_row_mae,
                "om_beats_reference_same_row": om_beats_reference,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    return {
        "onda3_hybrid_gates_v1": pl.concat(gate_frames, how="diagonal_relaxed"),
        "onda3_hybrid_honest_by_cp_v1": pl.concat(
            comparison_frames,
            how="diagonal_relaxed",
        ),
        "onda3_hybrid_decision_v1": decision,
    }


def render_onda3_hybrid_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    """Render the P1 hybrid report."""

    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Onda 3 P1 Horizon Hybrid Model Report",
            f"Generated: {today.isoformat()}",
            "All outputs remain EXPERIMENT_ONLY.",
            FREEZE_LINE,
            "## Decision",
            _markdown_table(frame("onda3_hybrid_decision_v1")),
            "## Honest Gates per Candidate",
            _markdown_table(frame("onda3_hybrid_gates_v1"), max_rows=40),
            "## Model vs Honest Null by CP per Candidate",
            _markdown_table(frame("onda3_hybrid_honest_by_cp_v1"), max_rows=40),
            "## Model Results",
            _markdown_table(frame("onda3_hybrid_model_results_v1"), max_rows=40),
            "## Feature Audit",
            _markdown_table(frame("onda3_hybrid_feature_audit_v1"), max_rows=60),
        ]
    ) + "\n"


def write_onda3_hybrid_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    """Write P1 hybrid CSV/MD pairs plus the report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in HYBRID_FILENAMES.items():
        if artifact_name not in artifacts:
            continue
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            f"# {artifact_name}\n\n{_markdown_table(artifacts[artifact_name])}\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name}_md"] = md_path
    report_path = output_dir / "onda3_hybrid_model_report_v1.md"
    report_path.write_text(
        render_onda3_hybrid_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_hybrid_report_md"] = report_path
    return paths
