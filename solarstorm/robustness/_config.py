"""Frozen go/no-go thresholds for Onda 4 robustness hardening."""
from __future__ import annotations

ROBUSTNESS_CONFIG_VERSION = "1.0"

# R1: per-year replication.
R1_MIN_PASSING_YEARS = 5
R1_BLOCK_YEARS = 3

# R2-R5: hard checks inherited from the robustness plan.
R2_DEAD_REGIME_BLOCK = True
R3_LEAK_BLOCK = True
R4_TREND_ALPHA = 0.05
R5_GATE_RERUN_BLOCK = True

# R6-R9: scope guards added after Onda 4 refocus and Onda 2R repair.
R6_ANTI_NOWCAST_BLOCK = True
R7_FIXED_CP_ARTIFACT_BLOCK = True
R8_LATE_SPIKE_WARNING_ONLY = True
R9_LATE_TMAX_BASELINE_BLOCK = True
