"""Frozen gates (G1-G5). Fixed from baseline evaluation, never demotable.

G4 (anti-nowcaster) is hard and non-demotable — the exact gate the old project
demoted to diagnostic (phase4_evaluate.py:95). The lesson is structural.

G4 uses different criteria by lead-time (Jolliffe & Stephenson 2012, Murphy 1987):

- **Morning CPs** (local hour < 12, Tmax still ahead): MAE skill CI test — the
  95% CI lower bound of MAE improvement must be > 0.  Correlation is
  mathematically blind to bias corrections (Murphy 1987), which are the
  primary mechanism of improvement at long lead times.
- **Evening CPs** (local hour >= 12, nowcasting risk): original corr_diff
  threshold — challenger must improve Pearson r by >= 0.05 with CI lo > 0.

References:
  Murphy, A. H. (1987). Skill scores based on the mean square error and their
  relationships to the correlation coefficient. Monthly Weather Review.
  Jolliffe, I. T., & Stephenson, D. B. (2012). Forecast Verification: A
  Practitioner's Guide in Atmospheric Science. Wiley.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from solarstorm._config import TZ_NAME

_SKILL_EPSILON = 1e-9


@dataclass
class GateResult:
    gate: str
    description: str
    passed: bool
    status: str   # "OK", "KILL", "NOT_OPERATIONAL", "COLLAPSE_ALERT", "NOWCAST_SUSPECT", "STAY_OUT"
    detail: str


def _g1_null_not_beaten(model_mae: float, best_null_mae: float) -> GateResult:
    passed = model_mae < best_null_mae - _SKILL_EPSILON
    return GateResult(
        gate="G1", description="Null not beaten = KILL",
        passed=passed,
        status="OK" if passed else "KILL",
        detail=f"model_mae={model_mae:.4f} vs best_null_mae={best_null_mae:.4f}",
    )


def _g2_fallback_dominance(fallback_rate: float) -> GateResult:
    passed = fallback_rate <= 0.50
    return GateResult(
        gate="G2", description="Fallback dominance > 50% = NOT_OPERATIONAL",
        passed=passed,
        status="OK" if passed else "NOT_OPERATIONAL",
        detail=f"fallback_rate={fallback_rate:.4f}",
    )


def _g3_p50_collapse(p50_mode_share: float) -> GateResult:
    passed = p50_mode_share <= 0.50
    return GateResult(
        gate="G3", description="p50 collapse = COLLAPSE_ALERT",
        passed=passed,
        status="OK" if passed else "COLLAPSE_ALERT",
        detail=f"p50_mode_share={p50_mode_share:.4f}",
    )


def _is_morning_cp(cp_str: str, date_local: dt.date | None = None) -> bool:
    """True if the CP local hour is before noon (Tmax still ahead).

    When ``date_local`` is provided, the actual DST offset for that date is used
    (so CP23 = 11:00 NZST in winter is morning, but = 12:00 NZDT in summer is
    not).  Without a date it falls back to a winter (NZST) reference (#9).
    """
    tz = ZoneInfo(TZ_NAME)
    cp_hour = int(cp_str.split(":")[0])
    ref_date = date_local if date_local is not None else dt.date(2025, 6, 15)
    dummy_utc = dt.datetime(ref_date.year, ref_date.month, ref_date.day,
                            cp_hour, 0, tzinfo=dt.UTC)
    local_hour = dummy_utc.astimezone(tz).hour
    return local_hour < 12


def _g4_anti_nowcaster(
    corr_diff: float | None,
    corr_diff_ci95: tuple[float, float] | None = None,
    *,
    skill_ci_lo: float | None = None,
    cp_str: str = "",
    date_local: dt.date | None = None,
) -> GateResult:
    """Anti-nowcaster gate, stratified by lead-time.

    **Morning CPs** (local hour < 12): uses MAE skill CI — ``skill_ci_lo > 0``
    means the 95% CI of MAE improvement excludes zero.  This is the
    statistically-robust test that the challenger genuinely outperforms the
    baseline, without relying on correlation (which is blind to bias
    corrections — Murphy 1987).

    **Evening CPs** (local hour >= 12): uses the original correlation-delta
    threshold — ``corr_diff >= 0.05 and corr_lo > 0`` — because at short lead
    times the nowcasting risk is real and correlation discrimination is the
    appropriate guard.
    """
    is_morning = _is_morning_cp(cp_str, date_local) if cp_str else True

    if is_morning:
        # MAE skill CI test — statistically grounded, immune to bias-blindness
        if skill_ci_lo is None:
            passed = False
            detail = "morning CP — skill_ci_lo unavailable; cannot clear anti-nowcaster gate"
        else:
            passed = skill_ci_lo > _SKILL_EPSILON
            detail = (
                f"morning CP — MAE skill CI lo={skill_ci_lo:.4f} "
                f"({'OK' if passed else 'NOWCAST_SUSPECT — CI includes zero'})"
            )
    else:
        # Evening CP — original correlation-based guard
        if corr_diff is None:
            passed = False
            detail = "evening CP — corr_diff unavailable; cannot clear anti-nowcaster gate"
        elif corr_diff_ci95 is not None:
            lo, hi = corr_diff_ci95
            passed = corr_diff >= 0.05 and lo > 0.0
            detail = f"evening CP — corr_diff={corr_diff:.4f}, ci95=[{lo:.4f}, {hi:.4f}]"
        else:
            passed = corr_diff >= 0.05
            detail = f"evening CP — corr_diff={corr_diff:.4f} (no CI)"

    return GateResult(
        gate="G4", description="Anti-nowcaster — hard, non-demotable",
        passed=passed,
        status="OK" if passed else "NOWCAST_SUSPECT",
        detail=detail,
    )


def _g5_per_cp(cp: str, per_cp_passed: bool) -> GateResult:
    return GateResult(
        gate="G5", description="Best-null per CP",
        passed=per_cp_passed,
        status="OK" if per_cp_passed else "STAY_OUT",
        detail=f"CP={cp}: {'beats null' if per_cp_passed else 'loses to null → stay_out'}",
    )


def apply_all_gates(
    *,
    model_mae: float,
    best_null_mae: float,
    cp: str,
    fallback_rate: float = 0.0,
    p50_mode_share: float = 0.0,
    corr_diff: float | None = None,
    corr_diff_ci95: tuple[float, float] | None = None,
    skill_ci_lo: float | None = None,
    per_cp_passed: bool = True,
    date_local: dt.date | None = None,
) -> dict[str, GateResult]:
    results = {
        "G1": _g1_null_not_beaten(model_mae, best_null_mae),
        "G2": _g2_fallback_dominance(fallback_rate),
        "G3": _g3_p50_collapse(p50_mode_share),
        "G4": _g4_anti_nowcaster(
            corr_diff, corr_diff_ci95,
            skill_ci_lo=skill_ci_lo, cp_str=cp, date_local=date_local,
        ),
        "G5": _g5_per_cp(cp, per_cp_passed),
    }
    return results
