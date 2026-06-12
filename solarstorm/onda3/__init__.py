"""Onda 3 baseline-first model experiment helpers."""

from __future__ import annotations

from solarstorm.onda3._artifacts import write_onda3_baseline_artifacts
from solarstorm.onda3._audit_comparison import (
    build_onda3_audit_comparison,
    load_onda3_audit_prediction_inputs,
    write_onda3_audit_comparison_artifacts,
)
from solarstorm.onda3._baseline_model import run_onda3_baseline_model
from solarstorm.onda3._design_matrix import build_onda3_design_matrix
from solarstorm.onda3._evaluation import build_onda3_slice_diagnostics
from solarstorm.onda3._feature_manifest import build_onda3_feature_manifest
from solarstorm.onda3._interaction_artifacts import write_onda3_interaction_artifacts
from solarstorm.onda3._interactions import (
    add_binary_macro_interaction_features,
    build_interaction_feature_manifest,
    build_onda3_interaction_iteration,
)
from solarstorm.onda3._model_attempt_review import (
    build_onda3_model_attempt_review,
    write_onda3_model_attempt_review_artifacts,
)
from solarstorm.onda3._nested_validation import (
    build_onda3_nested_validation,
    select_onda3h_feature_columns,
    write_onda3_nested_validation_artifacts,
)
from solarstorm.onda3._next_artifacts import write_onda3_next_artifacts
from solarstorm.onda3._next_iteration import build_onda3_next_iteration
from solarstorm.onda3._pooled_iteration import (
    add_pooled_temporal_features,
    build_onda3_pooled_iteration,
    normalize_pooled_cp_column,
    write_onda3_pooled_artifacts,
)
from solarstorm.onda3._rolling_artifacts import write_onda3_rolling_artifacts
from solarstorm.onda3._rolling_iteration import build_onda3_rolling_iteration
from solarstorm.onda3._train_start_sensitivity import (
    build_onda3_train_start_sensitivity,
    write_onda3_train_start_sensitivity_artifacts,
)

__all__ = [
    "add_binary_macro_interaction_features",
    "add_pooled_temporal_features",
    "build_interaction_feature_manifest",
    "build_onda3_audit_comparison",
    "build_onda3_design_matrix",
    "build_onda3_feature_manifest",
    "build_onda3_interaction_iteration",
    "build_onda3_model_attempt_review",
    "build_onda3_nested_validation",
    "build_onda3_next_iteration",
    "build_onda3_pooled_iteration",
    "build_onda3_rolling_iteration",
    "build_onda3_slice_diagnostics",
    "build_onda3_train_start_sensitivity",
    "load_onda3_audit_prediction_inputs",
    "normalize_pooled_cp_column",
    "run_onda3_baseline_model",
    "select_onda3h_feature_columns",
    "write_onda3_audit_comparison_artifacts",
    "write_onda3_baseline_artifacts",
    "write_onda3_interaction_artifacts",
    "write_onda3_model_attempt_review_artifacts",
    "write_onda3_nested_validation_artifacts",
    "write_onda3_next_artifacts",
    "write_onda3_pooled_artifacts",
    "write_onda3_rolling_artifacts",
    "write_onda3_train_start_sensitivity_artifacts",
]
