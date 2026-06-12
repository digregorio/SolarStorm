"""Frozen H1-H4 gate matrix for the P0 honest evaluation harness."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
EXPECTED_CPS = ("20:00", "21:00", "22:00", "23:00")
FORECAST_STRATUM = "forecast_2_plus"
H2_MIN_ROWS = 30
DECISION_PASS = "HONEST_EVALUATION_PASSED"
DECISION_HONEST_BLOCK = "BLOCK_MODEL_PROMOTION_HONEST_NULL"
DECISION_REVIEW = "KEEP_IN_HONEST_EVALUATION_REVIEW"


def _pass_block(value: bool) -> str:
    return "PASS" if value else "BLOCK"


def _h1_pass(by_cp: pl.DataFrame) -> tuple[bool, str]:
    present = set(by_cp["cp"].to_list()) if "cp" in by_cp.columns else set()
    missing = [cp for cp in EXPECTED_CPS if cp not in present]
    if missing:
        return False, f"missing CP rows: {','.join(missing)}"
    failing = by_cp.filter(~pl.col("model_beats_null"))
    if not failing.is_empty():
        return False, "model MAE is not below honest-null MAE at every CP"
    return True, "model MAE is below honest-null MAE at every CP"


def _h2_pass(
    *, by_stratum: pl.DataFrame | None, by_stratum_cp: pl.DataFrame
) -> tuple[bool, str]:
    if by_stratum is not None and not by_stratum.is_empty():
        overall = by_stratum.filter(pl.col("rw_stratum") == FORECAST_STRATUM)
        if overall.is_empty() or not bool(overall["model_beats_null"][0]):
            return False, "model does not beat honest null overall on forecast_2_plus"
    support = by_stratum_cp.filter(
        (pl.col("rw_stratum") == FORECAST_STRATUM)
        & (pl.col("n_rows") >= H2_MIN_ROWS)
    )
    if support.is_empty():
        return False, "no forecast_2_plus CP rows meet minimum support"
    failing = support.filter(~pl.col("model_beats_null"))
    if not failing.is_empty():
        return False, "model does not beat honest null on every supported CP"
    return True, "model beats honest null on supported forecast_2_plus CP rows"


def _h3_pass(floor_audit: pl.DataFrame) -> tuple[bool, str]:
    overall = floor_audit.filter(pl.col("cp") == "ALL")
    if overall.is_empty() or "n_clamped_violations" not in floor_audit.columns:
        return False, "floor audit missing ALL row or clamped-violation column"
    raw = overall["n_raw_violations"][0] if "n_raw_violations" in overall.columns else 0
    clamped = overall["n_clamped_violations"][0]
    return (
        clamped == 0,
        f"raw violations reported={raw}; clamped violations={clamped}",
    )


def _h4_pass(by_stratum_cp: pl.DataFrame) -> tuple[bool, str]:
    present = set(by_stratum_cp["cp"].to_list()) if "cp" in by_stratum_cp.columns else set()
    missing = [cp for cp in EXPECTED_CPS if cp not in present]
    if missing:
        return False, f"lead degradation table missing CPs: {','.join(missing)}"
    if by_stratum_cp.is_empty():
        return False, "lead degradation table is empty"
    return True, "lead degradation table exists for every CP"


def build_honest_gates(
    *,
    by_cp: pl.DataFrame,
    by_stratum_cp: pl.DataFrame,
    floor_audit: pl.DataFrame,
    by_stratum: pl.DataFrame | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Evaluate frozen H1-H4 gates and return ``(gates, decision)``."""
    h1_ok, h1_detail = _h1_pass(by_cp)
    h2_ok, h2_detail = _h2_pass(
        by_stratum=by_stratum, by_stratum_cp=by_stratum_cp
    )
    h3_ok, h3_detail = _h3_pass(floor_audit)
    h4_ok, h4_detail = _h4_pass(by_stratum_cp)
    rows = [
        {
            "gate_id": "H1",
            "gate_name": "Per-CP honest lift",
            "gate_status": _pass_block(h1_ok),
            "gate_detail": h1_detail,
            "production_status": PRODUCTION_STATUS,
        },
        {
            "gate_id": "H2",
            "gate_name": "Anticipation stratum",
            "gate_status": _pass_block(h2_ok),
            "gate_detail": h2_detail,
            "production_status": PRODUCTION_STATUS,
        },
        {
            "gate_id": "H3",
            "gate_name": "Physical floor",
            "gate_status": _pass_block(h3_ok),
            "gate_detail": h3_detail,
            "production_status": PRODUCTION_STATUS,
        },
        {
            "gate_id": "H4",
            "gate_name": "Lead degradation table",
            "gate_status": _pass_block(h4_ok),
            "gate_detail": h4_detail,
            "production_status": PRODUCTION_STATUS,
        },
    ]
    if not h3_ok or not h4_ok:
        decision_status = DECISION_REVIEW
    elif not h1_ok or not h2_ok:
        decision_status = DECISION_HONEST_BLOCK
    else:
        decision_status = DECISION_PASS
    decision = pl.DataFrame(
        [
            {
                "decision_status": decision_status,
                "decision_rationale": (
                    "Frozen P0 honest-evaluation gates H1-H4 applied ex ante."
                ),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    return pl.DataFrame(rows, strict=False), decision
