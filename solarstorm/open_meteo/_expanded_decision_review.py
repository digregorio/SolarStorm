from __future__ import annotations

from pathlib import Path

import polars as pl

from solarstorm.open_meteo._availability import PRODUCTION_STATUS

OPEN_METEO_EXPANDED_DECISION_REVIEW_FILENAMES = {
    "open_meteo_expanded_policy_rows_v1": "open_meteo_expanded_policy_rows_v1.csv",
    "open_meteo_expanded_policy_metrics_v1": "open_meteo_expanded_policy_metrics_v1.csv",
    "open_meteo_expanded_policy_slice_metrics_v1": (
        "open_meteo_expanded_policy_slice_metrics_v1.csv"
    ),
    "open_meteo_expanded_policy_decision_v1": (
        "open_meteo_expanded_policy_decision_v1.csv"
    ),
}

POLICY_CANDIDATES = {
    "always_season": "om_family_season_bias_corrected",
    "always_recent": "om_family_recent_bias_corrected",
    "always_augmented": "open_meteo_augmented_onda3f",
}


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _normalize_cp(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("cp")
    if dtype == pl.Time:
        return frame.with_columns(pl.col("cp").dt.strftime("%H:%M").alias("cp"))
    return frame.with_columns(pl.col("cp").cast(pl.Utf8))


def _safe_pct(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) * 100.0 / float(denominator)


def _selected_policy_rows(predictions: pl.DataFrame, selection: pl.DataFrame) -> pl.DataFrame:
    selection_lookup = selection.select(["outer_test_year", "selected_candidate_id"]).unique()
    return (
        predictions.join(selection_lookup, on="outer_test_year", how="inner")
        .filter(pl.col("candidate_id") == pl.col("selected_candidate_id"))
        .drop("selected_candidate_id")
        .with_columns(
            pl.lit("selected_policy").alias("policy_id"),
            pl.lit("Selected by nested validation").alias("policy_label"),
        )
    )


def _static_policy_rows(predictions: pl.DataFrame, policy_id: str, candidate_id: str) -> pl.DataFrame:
    return predictions.filter(pl.col("candidate_id") == candidate_id).with_columns(
        pl.lit(policy_id).alias("policy_id"),
        pl.lit(policy_id.replace("_", " ")).alias("policy_label"),
    )


def _build_policy_rows(predictions: pl.DataFrame, selection: pl.DataFrame) -> pl.DataFrame:
    required = {
        "date_local",
        "cp",
        "stage",
        "outer_test_year",
        "candidate_id",
        "actual",
        "prediction",
        "absolute_error",
        "exact_bracket",
    }
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"missing required prediction columns: {sorted(missing)}")
    if "selected_candidate_id" not in selection.columns:
        raise ValueError("missing required selection column: selected_candidate_id")

    base = _normalize_cp(_ensure_date(predictions)).filter(pl.col("stage") == "test")
    if base.is_empty():
        return pl.DataFrame()
    frames = [_selected_policy_rows(base, selection)]
    frames.extend(
        _static_policy_rows(base, policy_id, candidate_id)
        for policy_id, candidate_id in POLICY_CANDIDATES.items()
    )
    rows = pl.concat([frame for frame in frames if not frame.is_empty()], how="diagonal_relaxed")
    if "calendar_year" not in rows.columns:
        rows = rows.with_columns(pl.col("date_local").dt.year().alias("calendar_year"))
    if "month" not in rows.columns:
        rows = rows.with_columns(pl.col("date_local").dt.strftime("%Y-%m").alias("month"))
    if "binary_macro_regime_label" not in rows.columns:
        rows = rows.with_columns(pl.lit("unknown").alias("binary_macro_regime_label"))
    return rows.with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status")).sort(
        ["policy_id", "date_local", "cp"]
    )


def _metric_row(frame: pl.DataFrame, *, policy_id: str) -> dict[str, object]:
    n_cp_rows = frame.height
    n_days = frame.select("date_local").unique().height
    exact_count = int(frame["exact_bracket"].cast(pl.Int8).sum())
    any_cp_days = 0
    for _, day_frame in frame.group_by("date_local", maintain_order=True):
        if bool(day_frame["exact_bracket"].cast(pl.Int8).max()):
            any_cp_days += 1
    cp23 = frame.filter(pl.col("cp") == "23:00")
    cp23_exact = int(cp23["exact_bracket"].cast(pl.Int8).sum()) if cp23.height else 0
    return {
        "policy_id": policy_id,
        "n_days": n_days,
        "n_cp_rows": n_cp_rows,
        "mae": float(frame["absolute_error"].cast(pl.Float64).mean()),
        "exact_bracket_pct": _safe_pct(exact_count, n_cp_rows),
        "any_cp_exact_pct": _safe_pct(any_cp_days, n_days),
        "cp23_exact_pct": _safe_pct(cp23_exact, cp23.height),
        "production_status": PRODUCTION_STATUS,
    }


def build_open_meteo_expanded_policy_metrics(policy_rows: pl.DataFrame) -> pl.DataFrame:
    if policy_rows.is_empty():
        return pl.DataFrame()
    rows = []
    for policy_id, frame in policy_rows.group_by("policy_id", maintain_order=True):
        rows.append(_metric_row(frame, policy_id=str(policy_id[0] if isinstance(policy_id, tuple) else policy_id)))
    return pl.DataFrame(rows, strict=False).sort("policy_id")


def _slice_row(
    frame: pl.DataFrame,
    *,
    policy_id: str,
    slice_type: str,
    slice_name: str,
) -> dict[str, object]:
    row = _metric_row(frame, policy_id=policy_id)
    row["slice_type"] = slice_type
    row["slice_name"] = slice_name
    return row


def _slice_frame(policy_rows: pl.DataFrame, slice_type: str, columns: list[str]) -> pl.DataFrame:
    if policy_rows.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    if not columns:
        for policy_id, frame in policy_rows.group_by("policy_id", maintain_order=True):
            value = policy_id[0] if isinstance(policy_id, tuple) else policy_id
            rows.append(
                _slice_row(
                    frame,
                    policy_id=str(value),
                    slice_type=slice_type,
                    slice_name="overall",
                )
            )
        return pl.DataFrame(rows, strict=False)

    group_columns = ["policy_id", *columns]
    for key, frame in policy_rows.group_by(group_columns, maintain_order=True):
        values = key if isinstance(key, tuple) else (key,)
        policy_id = str(values[0])
        slice_name = "|".join(str(value) for value in values[1:])
        rows.append(
            _slice_row(
                frame,
                policy_id=policy_id,
                slice_type=slice_type,
                slice_name=slice_name,
            )
        )
    return pl.DataFrame(rows, strict=False)


def build_open_meteo_expanded_policy_slice_metrics(
    policy_rows: pl.DataFrame,
) -> pl.DataFrame:
    frames = [
        _slice_frame(policy_rows, "overall", []),
        _slice_frame(policy_rows, "year", ["outer_test_year"]),
        _slice_frame(policy_rows, "month", ["month"]),
        _slice_frame(policy_rows, "cp", ["cp"]),
        _slice_frame(policy_rows, "binary_macro_regime_label", ["binary_macro_regime_label"]),
        _slice_frame(policy_rows, "year_regime", ["outer_test_year", "binary_macro_regime_label"]),
        _slice_frame(policy_rows, "month_cp", ["month", "cp"]),
    ]
    non_empty = [frame for frame in frames if not frame.is_empty()]
    if not non_empty:
        return pl.DataFrame()
    return pl.concat(non_empty, how="diagonal_relaxed").sort(
        ["slice_type", "slice_name", "policy_id"]
    )


def _metric(metrics: pl.DataFrame, policy_id: str, column: str) -> float | None:
    rows = metrics.filter(pl.col("policy_id") == policy_id)
    if rows.is_empty():
        return None
    value = rows.row(0, named=True).get(column)
    return None if value is None else float(value)


def _max_regime_delta(slice_metrics: pl.DataFrame) -> float | None:
    regimes = slice_metrics.filter(pl.col("slice_type") == "binary_macro_regime_label")
    if regimes.is_empty():
        return None
    selected = regimes.filter(pl.col("policy_id") == "selected_policy").select(
        ["slice_name", pl.col("mae").alias("selected_mae")]
    )
    augmented = regimes.filter(pl.col("policy_id") == "always_augmented").select(
        ["slice_name", pl.col("mae").alias("augmented_mae")]
    )
    joined = selected.join(augmented, on="slice_name", how="inner").with_columns(
        (pl.col("selected_mae") - pl.col("augmented_mae")).alias("delta")
    )
    if joined.is_empty():
        return None
    return float(joined["delta"].max())


def _decision(policy_rows: pl.DataFrame, metrics: pl.DataFrame, slice_metrics: pl.DataFrame) -> pl.DataFrame:
    if policy_rows.is_empty() or metrics.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": "REQUIRE_MORE_FORWARD_COLLECTION_FOR_OPEN_METEO",
                    "decision_rationale": "No test policy rows were available for expanded-surface review.",
                    "n_outer_folds": 0,
                    "best_policy_id": None,
                    "best_policy_mae": None,
                    "selected_mae": None,
                    "augmented_mae": None,
                    "selected_mae_delta_vs_augmented": None,
                    "selected_exact_delta_vs_augmented_pct": None,
                    "selected_cp23_exact_delta_vs_augmented_pct": None,
                    "max_regime_mae_delta_selected_vs_augmented": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )

    best_policy = metrics.sort(["mae", "policy_id"]).row(0, named=True)
    n_outer_folds = policy_rows.filter(pl.col("policy_id") == "selected_policy").select(
        "outer_test_year"
    ).unique().height
    selected_mae = _metric(metrics, "selected_policy", "mae")
    augmented_mae = _metric(metrics, "always_augmented", "mae")
    selected_exact = _metric(metrics, "selected_policy", "exact_bracket_pct")
    augmented_exact = _metric(metrics, "always_augmented", "exact_bracket_pct")
    selected_cp23 = _metric(metrics, "selected_policy", "cp23_exact_pct")
    augmented_cp23 = _metric(metrics, "always_augmented", "cp23_exact_pct")
    mae_delta = (
        None if selected_mae is None or augmented_mae is None else selected_mae - augmented_mae
    )
    exact_delta = (
        None
        if selected_exact is None or augmented_exact is None
        else selected_exact - augmented_exact
    )
    cp23_delta = (
        None if selected_cp23 is None or augmented_cp23 is None else selected_cp23 - augmented_cp23
    )
    max_regime_delta = _max_regime_delta(slice_metrics)

    if n_outer_folds < 2:
        status = "REQUIRE_MORE_FORWARD_COLLECTION_FOR_OPEN_METEO"
        rationale = "Expanded Open-Meteo review has fewer than two outer folds."
    elif (
        mae_delta is not None
        and mae_delta <= -0.01
        and (exact_delta is None or exact_delta >= -1.0)
        and (cp23_delta is None or cp23_delta >= -1.0)
        and (max_regime_delta is None or max_regime_delta <= 0.025)
    ):
        status = "PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
        rationale = (
            "Selected expanded calibrated policy improves MAE versus augmented "
            "without material bracket or binary-regime degradation."
        )
    else:
        status = "KEEP_OPEN_METEO_AUGMENTED_ONDA3F_AS_EXPERIMENTAL_BASELINE"
        rationale = (
            "Expanded calibrated policy did not clear the stability gates versus "
            "the current augmented experimental baseline."
        )

    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "n_outer_folds": n_outer_folds,
                "best_policy_id": best_policy["policy_id"],
                "best_policy_mae": best_policy["mae"],
                "selected_mae": selected_mae,
                "augmented_mae": augmented_mae,
                "selected_mae_delta_vs_augmented": mae_delta,
                "selected_exact_delta_vs_augmented_pct": exact_delta,
                "selected_cp23_exact_delta_vs_augmented_pct": cp23_delta,
                "max_regime_mae_delta_selected_vs_augmented": max_regime_delta,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_expanded_decision_review_artifacts(
    *,
    predictions: pl.DataFrame,
    selection: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    policy_rows = _build_policy_rows(predictions, selection)
    metrics = build_open_meteo_expanded_policy_metrics(policy_rows)
    slice_metrics = build_open_meteo_expanded_policy_slice_metrics(policy_rows)
    return {
        "open_meteo_expanded_policy_rows_v1": policy_rows,
        "open_meteo_expanded_policy_metrics_v1": metrics,
        "open_meteo_expanded_policy_slice_metrics_v1": slice_metrics,
        "open_meteo_expanded_policy_decision_v1": _decision(
            policy_rows,
            metrics,
            slice_metrics,
        ),
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


def render_open_meteo_expanded_decision_review_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo OM-M13 Expanded-Surface Decision Review",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Experiment-only audit of the expanded two-fold Open-Meteo surface. "
                "Policies compared: selected nested candidate, always-season, "
                "always-recent, and always-augmented."
            ),
            (
                "No production, EV, pricing, shadow trading, or execution work is "
                "unlocked by this artifact."
            ),
            "## Decision",
            _markdown_table(artifacts["open_meteo_expanded_policy_decision_v1"]),
            "## Overall Policy Metrics",
            _markdown_table(artifacts["open_meteo_expanded_policy_metrics_v1"]),
            "## Slice Metrics",
            _markdown_table(
                artifacts["open_meteo_expanded_policy_slice_metrics_v1"],
                max_rows=120,
            ),
        ]
    ) + "\n"


def write_open_meteo_expanded_decision_review_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in OPEN_METEO_EXPANDED_DECISION_REVIEW_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "open_meteo_expanded_decision_review_report_v1.md"
    report_path.write_text(
        render_open_meteo_expanded_decision_review_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_expanded_decision_review_report_md"] = report_path
    return paths
