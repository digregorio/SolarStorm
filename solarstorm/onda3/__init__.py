"""Onda 3 baseline-first model experiment helpers."""

from __future__ import annotations

from solarstorm.onda3._artifacts import write_onda3_baseline_artifacts
from solarstorm.onda3._baseline_model import run_onda3_baseline_model
from solarstorm.onda3._design_matrix import build_onda3_design_matrix
from solarstorm.onda3._evaluation import build_onda3_slice_diagnostics
from solarstorm.onda3._feature_manifest import build_onda3_feature_manifest

__all__ = [
    "build_onda3_design_matrix",
    "build_onda3_feature_manifest",
    "build_onda3_slice_diagnostics",
    "run_onda3_baseline_model",
    "write_onda3_baseline_artifacts",
]
