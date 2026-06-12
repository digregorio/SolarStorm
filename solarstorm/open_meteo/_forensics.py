from __future__ import annotations

from pathlib import Path

import polars as pl

from solarstorm.open_meteo._availability import PRODUCTION_STATUS

OPEN_METEO_FORENSICS_FILENAMES = {
    "open_meteo_forensics_pairwise_rows_v1": "open_meteo_forensics_pairwise_rows_v1.csv",
    "open_meteo_forensics_slice_delta_v1": "open_meteo_forensics_slice_delta_v1.csv",
    "open_meteo_forensics_bias_adjustment_v1": (
        "open_meteo_forensics_bias_adjustment_v1.csv"
    ),
    "open_meteo_forensics_decision_v1": "open_meteo_forensics_decision_v1.csv",
}

DEFAULT_AUGMENTED_ID = "open_meteo_augmented_onda3f"
DEFAULT_CALIBRATED_ID = "om_family_recent_bias_corrected"


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _safe_pct(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) * 100.0 / float(denominator)


def _candidate_projection(frame: pl.DataFrame, candidate_id: str, prefix: str) -> pl.DataFrame:
    required = [
        "date_local",
        "cp",
        "stage",
        "outer_test_year",
        "evaluation_year",
        "actual",
        "prediction",
        "absolute_error",
        "actual_bracket",
        "pred_bracket",
        "exact_bracket",
        "calendar_year",
    ]
    optional = [
        "month",
        "binary_macro_regime_label",
    ]
    columns = [column for column in [*required, *optional] if column in frame.columns]
    projected = frame.filter(pl.col("candidate_id") == candidate_id).select(columns)
    rename = {
        "prediction": f"{prefix}_prediction",
        "absolute_error": f"{prefix}_absolute_error",
        "pred_bracket": f"{prefix}_pred_bracket",
        "exact_bracket": f"{prefix}_exact_bracket",
    }
    return projected.rename({key: value for key, value in rename.items() if key in projected.columns})


def _build_pairwise_rows(
    predictions: pl.DataFrame,
    *,
    augmented_candidate_id: str,
    calibrated_candidate_id: str,
) -> pl.DataFrame:
    base = _ensure_date(predictions).filter(pl.col("stage") == "test")
    augmented = _candidate_projection(base, augmented_candidate_id, "augmented")
    calibrated = _candidate_projection(base, calibrated_candidate_id, "calibrated")
    joined = augmented.join(
        calibrated.select(
            [
                "date_local",
                "cp",
                "stage",
                "outer_test_year",
                "evaluation_year",
                "calibrated_prediction",
                "calibrated_absolute_error",
                "calibrated_pred_bracket",
                "calibrated_exact_bracket",
            ]
        ),
        on=["date_local", "cp", "stage", "outer_test_year", "evaluation_year"],
        how="inner",
    )
    if joined.is_empty():
        return joined
    if "month" not in joined.columns:
        joined = joined.with_columns(pl.col("date_local").dt.strftime("%Y-%m").alias("month"))
    if "binary_macro_regime_label" not in joined.columns:
        joined = joined.with_columns(pl.lit("unknown").alias("binary_macro_regime_label"))
    return joined.with_columns(
        (pl.col("calibrated_absolute_error") - pl.col("augmented_absolute_error")).alias(
            "mae_delta_calibrated_minus_augmented"
        ),
        (
            pl.col("calibrated_prediction").cast(pl.Float64)
            - pl.col("augmented_prediction").cast(pl.Float64)
        ).alias("prediction_delta_calibrated_minus_augmented"),
        (
            pl.col("calibrated_exact_bracket").cast(pl.Int8)
            - pl.col("augmented_exact_bracket").cast(pl.Int8)
        ).alias("exact_delta_calibrated_minus_augmented"),
        (pl.col("calibrated_absolute_error") < pl.col("augmented_absolute_error")).alias(
            "calibrated_wins_mae"
        ),
        (pl.col("augmented_absolute_error") < pl.col("calibrated_absolute_error")).alias(
            "augmented_wins_mae"
        ),
        (
            pl.col("augmented_exact_bracket") & ~pl.col("calibrated_exact_bracket")
        ).alias("bracket_lost_by_calibration"),
        (
            pl.col("calibrated_exact_bracket") & ~pl.col("augmented_exact_bracket")
        ).alias("bracket_gained_by_calibration"),
        (
            pl.col("calibrated_prediction").cast(pl.Float64)
            - pl.col("actual").cast(pl.Float64)
        ).alias("calibrated_signed_error"),
        (
            pl.col("augmented_prediction").cast(pl.Float64)
            - pl.col("actual").cast(pl.Float64)
        ).alias("augmented_signed_error"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )


def _slice_frame(pairwise: pl.DataFrame, slice_type: str, columns: list[str]) -> pl.DataFrame:
    if pairwise.is_empty():
        return pl.DataFrame()
    if columns:
        grouped = pairwise.group_by(columns, maintain_order=True)
        rows = []
        for key, frame in grouped:
            values = key if isinstance(key, tuple) else (key,)
            slice_name = "|".join(str(value) for value in values)
            rows.append(_slice_row(frame, slice_type=slice_type, slice_name=slice_name))
        return pl.DataFrame(rows, strict=False)
    return pl.DataFrame([_slice_row(pairwise, slice_type=slice_type, slice_name="overall")], strict=False)


def _slice_row(frame: pl.DataFrame, *, slice_type: str, slice_name: str) -> dict[str, object]:
    n_rows = frame.height
    augmented_exact = int(frame["augmented_exact_bracket"].cast(pl.Int8).sum())
    calibrated_exact = int(frame["calibrated_exact_bracket"].cast(pl.Int8).sum())
    return {
        "slice_type": slice_type,
        "slice_name": slice_name,
        "n_rows": n_rows,
        "augmented_mae": float(frame["augmented_absolute_error"].mean()),
        "calibrated_mae": float(frame["calibrated_absolute_error"].mean()),
        "mae_delta_calibrated_minus_augmented": float(
            frame["mae_delta_calibrated_minus_augmented"].mean()
        ),
        "augmented_exact_pct": _safe_pct(augmented_exact, n_rows),
        "calibrated_exact_pct": _safe_pct(calibrated_exact, n_rows),
        "exact_delta_calibrated_minus_augmented_pct": _safe_pct(
            calibrated_exact - augmented_exact,
            n_rows,
        ),
        "calibrated_wins_mae_pct": _safe_pct(
            int(frame["calibrated_wins_mae"].cast(pl.Int8).sum()),
            n_rows,
        ),
        "augmented_wins_mae_pct": _safe_pct(
            int(frame["augmented_wins_mae"].cast(pl.Int8).sum()),
            n_rows,
        ),
        "bracket_lost_by_calibration_pct": _safe_pct(
            int(frame["bracket_lost_by_calibration"].cast(pl.Int8).sum()),
            n_rows,
        ),
        "bracket_gained_by_calibration_pct": _safe_pct(
            int(frame["bracket_gained_by_calibration"].cast(pl.Int8).sum()),
            n_rows,
        ),
        "augmented_signed_bias": float(frame["augmented_signed_error"].mean()),
        "calibrated_signed_bias": float(frame["calibrated_signed_error"].mean()),
        "production_status": PRODUCTION_STATUS,
    }


def build_open_meteo_forensics_slice_delta(pairwise: pl.DataFrame) -> pl.DataFrame:
    frames = [
        _slice_frame(pairwise, "overall", []),
        _slice_frame(pairwise, "year", ["calendar_year"]),
        _slice_frame(pairwise, "month", ["month"]),
        _slice_frame(pairwise, "cp", ["cp"]),
        _slice_frame(pairwise, "binary_macro_regime_label", ["binary_macro_regime_label"]),
        _slice_frame(pairwise, "year_cp", ["calendar_year", "cp"]),
        _slice_frame(pairwise, "year_regime", ["calendar_year", "binary_macro_regime_label"]),
        _slice_frame(pairwise, "month_cp", ["month", "cp"]),
    ]
    non_empty = [frame for frame in frames if not frame.is_empty()]
    if not non_empty:
        return pl.DataFrame()
    return pl.concat(non_empty, how="diagonal_relaxed").sort(
        ["slice_type", "slice_name"]
    )


def _bias_adjustment_summary(
    pairwise: pl.DataFrame,
    calibrated_candidates: pl.DataFrame | None,
    *,
    calibrated_candidate_id: str,
) -> pl.DataFrame:
    if calibrated_candidates is None or calibrated_candidates.is_empty() or pairwise.is_empty():
        return pl.DataFrame()
    candidates = _ensure_date(calibrated_candidates).filter(
        pl.col("candidate_id") == calibrated_candidate_id
    )
    wanted = [
        "date_local",
        "cp",
        "bias_adjustment",
        "bias_samples",
        "n_provider_families",
        "calibration_status",
    ]
    available = [column for column in wanted if column in candidates.columns]
    if not {"date_local", "cp"}.issubset(set(available)):
        return pl.DataFrame()
    joined = pairwise.join(candidates.select(available), on=["date_local", "cp"], how="left")
    rows = []
    for slice_type, columns in [
        ("overall", []),
        ("year", ["calendar_year"]),
        ("binary_macro_regime_label", ["binary_macro_regime_label"]),
        ("calibration_status", ["calibration_status"]),
    ]:
        frames = [(("overall",), joined)] if not columns else list(joined.group_by(columns, maintain_order=True))
        for key, frame in frames:
            values = key if isinstance(key, tuple) else (key,)
            numeric_bias = frame["bias_adjustment"].cast(pl.Float64, strict=False)
            numeric_samples = frame["bias_samples"].cast(pl.Float64, strict=False)
            rows.append(
                {
                    "slice_type": slice_type,
                    "slice_name": "|".join(str(value) for value in values),
                    "n_rows": frame.height,
                    "mean_bias_adjustment": float(numeric_bias.mean()) if numeric_bias.drop_nulls().len() else None,
                    "mean_abs_bias_adjustment": float(numeric_bias.abs().mean()) if numeric_bias.drop_nulls().len() else None,
                    "mean_bias_samples": float(numeric_samples.mean()) if numeric_samples.drop_nulls().len() else None,
                    "mean_delta_mae": float(frame["mae_delta_calibrated_minus_augmented"].mean()),
                    "bracket_lost_by_calibration_pct": _safe_pct(
                        int(frame["bracket_lost_by_calibration"].cast(pl.Int8).sum()),
                        frame.height,
                    ),
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _decision(slice_delta: pl.DataFrame, pairwise: pl.DataFrame) -> pl.DataFrame:
    if slice_delta.is_empty():
        status = "OPEN_METEO_FORENSICS_BLOCKED_NO_COMMON_ROWS"
        rationale = "No paired rows were available for the requested candidates."
        return pl.DataFrame(
            [
                {
                    "decision_status": status,
                    "decision_rationale": rationale,
                    "n_paired_rows": 0,
                    "overall_mae_delta_calibrated_minus_augmented": None,
                    "overall_exact_delta_calibrated_minus_augmented_pct": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    overall = slice_delta.filter(pl.col("slice_type") == "overall").row(0, named=True)
    status = "KEEP_OPEN_METEO_FORENSICS_REVIEW"
    rationale = (
        "Open-Meteo augmented Onda 3F and calibrated candidates show different "
        "error/bracket tradeoffs; keep promotion frozen until slice causes are resolved."
    )
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "n_paired_rows": pairwise.height,
                "overall_mae_delta_calibrated_minus_augmented": overall[
                    "mae_delta_calibrated_minus_augmented"
                ],
                "overall_exact_delta_calibrated_minus_augmented_pct": overall[
                    "exact_delta_calibrated_minus_augmented_pct"
                ],
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_forensics_artifacts(
    *,
    predictions: pl.DataFrame,
    calibrated_candidates: pl.DataFrame | None = None,
    augmented_candidate_id: str = DEFAULT_AUGMENTED_ID,
    calibrated_candidate_id: str = DEFAULT_CALIBRATED_ID,
) -> dict[str, pl.DataFrame]:
    pairwise = _build_pairwise_rows(
        predictions,
        augmented_candidate_id=augmented_candidate_id,
        calibrated_candidate_id=calibrated_candidate_id,
    )
    slice_delta = build_open_meteo_forensics_slice_delta(pairwise)
    bias_adjustment = _bias_adjustment_summary(
        pairwise,
        calibrated_candidates,
        calibrated_candidate_id=calibrated_candidate_id,
    )
    return {
        "open_meteo_forensics_pairwise_rows_v1": pairwise,
        "open_meteo_forensics_slice_delta_v1": slice_delta,
        "open_meteo_forensics_bias_adjustment_v1": bias_adjustment,
        "open_meteo_forensics_decision_v1": _decision(slice_delta, pairwise),
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| "
        + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns)
        + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_open_meteo_forensics_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo OM-M6 Forensic Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Paired forensic comparison of Open-Meteo augmented Onda 3F "
                "against the selected calibrated multi-provider candidate on "
                "identical test rows."
            ),
            "## Decision",
            _markdown_table(artifacts["open_meteo_forensics_decision_v1"]),
            "## Slice Delta",
            _markdown_table(artifacts["open_meteo_forensics_slice_delta_v1"], max_rows=80),
            "## Bias Adjustment",
            _markdown_table(
                artifacts["open_meteo_forensics_bias_adjustment_v1"],
                max_rows=50,
            ),
        ]
    ) + "\n"


def write_open_meteo_forensics_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in OPEN_METEO_FORENSICS_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_forensics_report_v1.md"
    report_path.write_text(
        render_open_meteo_forensics_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_forensics_report_md"] = report_path
    return paths
