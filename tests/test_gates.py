"""Tests for frozen gates G1-G5, including G4 morning/evening stratification."""
from solarstorm.eval._gates import _is_morning_cp, apply_all_gates

# --- G1 -----------------------------------------------------------------


def test_g1_null_not_beaten_kills():
    result = apply_all_gates(
        model_mae=2.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.1, corr_diff=0.30,
        skill_ci_lo=1.0,
    )
    assert result["G1"].status == "KILL"
    assert not result["G1"].passed


def test_g1_passes_when_model_beats_null():
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.1, corr_diff=0.30,
        skill_ci_lo=1.0,
    )
    assert result["G1"].passed


# --- G2 -----------------------------------------------------------------


def test_g2_fallback_dominance_fails():
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.73, p50_mode_share=0.1, corr_diff=0.30,
        skill_ci_lo=1.0,
    )
    assert result["G2"].status == "NOT_OPERATIONAL"
    assert not result["G2"].passed


# --- G3 -----------------------------------------------------------------


def test_g3_p50_collapse_alerts():
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.93, corr_diff=0.30,
        skill_ci_lo=1.0,
    )
    assert result["G3"].status == "COLLAPSE_ALERT"


# --- G4: morning CPs (local hour < 12) -----------------------------------


def test_is_morning_cp_all_operational_cps():
    """All four operational CPs (20-23 UTC) are morning in NZST (08-11 local)."""
    assert _is_morning_cp("20:00") is True
    assert _is_morning_cp("21:00") is True
    assert _is_morning_cp("22:00") is True
    assert _is_morning_cp("23:00") is True


def test_is_morning_cp_evening():
    """00:00 UTC = 12:00 NZST (noon, not morning)."""
    assert _is_morning_cp("00:00") is False


def test_g4_morning_passes_with_positive_skill_ci():
    """Morning CP: skill_ci_lo > 0 clears G4."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.1,
        corr_diff=0.04,  # below 0.05, but irrelevant for morning
        skill_ci_lo=1.5,
    )
    assert result["G4"].passed
    assert "morning CP" in result["G4"].detail


def test_g4_morning_fails_with_negative_skill_ci():
    """Morning CP: skill_ci_lo <= 0 fails G4."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.1,
        corr_diff=0.04,
        skill_ci_lo=-0.1,
    )
    assert not result["G4"].passed
    assert result["G4"].status == "NOWCAST_SUSPECT"


def test_g4_morning_fails_with_missing_skill_ci():
    """Morning CP: missing skill_ci_lo fails G4 (non-demotable)."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.0, p50_mode_share=0.1,
        corr_diff=0.04,
        skill_ci_lo=None,
    )
    assert not result["G4"].passed
    assert "unavailable" in result["G4"].detail.lower()


# --- G4: evening CPs (local hour >= 12) ----------------------------------


def test_g4_evening_fails_with_low_corr_diff():
    """Evening CP: corr_diff < 0.05 fails."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="00:00",
        fallback_rate=0.0, p50_mode_share=0.1, corr_diff=-0.01,
    )
    assert result["G4"].status == "NOWCAST_SUSPECT"
    assert not result["G4"].passed


def test_g4_evening_corr_diff_requires_ci95_excludes_zero():
    """Evening CP: CI95 must exclude zero."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="00:00",
        fallback_rate=0.0, p50_mode_share=0.1,
        corr_diff=0.08, corr_diff_ci95=(-0.01, 0.17),
    )
    assert not result["G4"].passed


def test_all_gates_pass_clean_model_evening():
    """All gates pass for a clean model at evening CP."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="00:00",
        fallback_rate=0.1, p50_mode_share=0.2,
        corr_diff=0.25, corr_diff_ci95=(0.10, 0.40),
    )
    assert all(g.passed for g in result.values())


def test_all_gates_pass_clean_model_morning():
    """All gates pass for a clean model at morning CP (uses skill_ci_lo)."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="23:00",
        fallback_rate=0.1, p50_mode_share=0.2,
        corr_diff=0.04,  # low corr_diff doesn't matter for morning
        skill_ci_lo=1.5,  # strong MAE improvement
    )
    assert all(g.passed for g in result.values())


def test_g4_present_and_fails_when_corr_diff_missing():
    """G4 is non-demotable: missing corr_diff surfaces as FAILING G4."""
    result = apply_all_gates(
        model_mae=1.5, best_null_mae=2.0, cp="00:00",
        fallback_rate=0.1, p50_mode_share=0.2,
        corr_diff=None,
    )
    assert "G4" in result
    assert not result["G4"].passed
    assert result["G4"].status == "NOWCAST_SUSPECT"
