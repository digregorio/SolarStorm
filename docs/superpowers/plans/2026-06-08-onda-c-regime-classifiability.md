# Onda C Regime Classifiability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a non-production Onda C benchmark that validates regime classifiability/topology before Onda 3.

**Architecture:** Add a focused classifiability module under `solarstorm/onda2e/`, export its builders/writers, and wire one CLI command. The implementation produces CSV/Markdown artifacts only; it does not train Onda 3 models or write production artifacts.

**Tech Stack:** Python, Polars, NumPy, scikit-learn if already available through the project environment, Typer, pytest, ruff.

---

## File Structure

- Create `solarstorm/onda2e/_regime_classifiability.py`
  - Owns schemas, input validation, method comparison, diagnostics, report writer.
- Modify `solarstorm/onda2e/__init__.py`
  - Exports Onda C helpers.
- Modify `solarstorm/__main__.py`
  - Adds `regime-classifiability-benchmark`.
- Create `tests/test_regime_classifiability.py`
  - Unit and writer tests.
- Modify `tests/test_regime_design_validation.py` or add CLI tests to
  `tests/test_regime_classifiability.py`
  - CLI regression for artifact generation and no production/model files.
- Modify docs:
  - `ROADMAP.md`
  - `docs/decisions/012-evidence-to-decision-gate.md`
  - `docs/regime_model_card.md`
  - `docs/onda4_robustness_plan.md`

---

## Task 1: Schemas And Input Validation

**Files:**
- Create: `solarstorm/onda2e/_regime_classifiability.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Write failing schema/guardrail test**

Add:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from solarstorm.onda2e._regime_classifiability import (
    build_regime_classifiability_artifacts,
)


def _features() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_nw_continuum",
                "wind_dir_deg": 350.0,
                "wind_speed": 15.0,
                "qnh_hpa": 1012.0,
                "relh": 60.0,
                "dewpoint_depression": 8.0,
                "precip_pre_cp_sum": 0.0,
                "cloud_cover_score": 1.0,
                "temp_slope_pre_cp": 0.5,
            },
            {
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "regime_label": "macro_southerly_flow",
                "wind_dir_deg": 180.0,
                "wind_speed": 16.0,
                "qnh_hpa": 1007.0,
                "relh": 85.0,
                "dewpoint_depression": 2.0,
                "precip_pre_cp_sum": 0.1,
                "cloud_cover_score": 3.0,
                "temp_slope_pre_cp": -0.4,
            },
        ]
    )


def _assignments_v21(*, causal_window: str = "valid < CP") -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2.1",
                "date_local": dt.date(2020, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "candidate_regime_label": "macro_nw_continuum",
                "component_entropy": 0.2,
                "component_margin": 0.7,
                "distance_to_candidate": 0.3,
                "assignment_confidence": 0.8,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_nw_continuum",
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": causal_window,
                "production_status": "NOT_PRODUCTION",
            },
            {
                "candidate_version": "v2.1",
                "date_local": dt.date(2022, 1, 1),
                "cp": "20:00",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "candidate_regime_label": "macro_southerly_flow",
                "component_entropy": 0.3,
                "component_margin": 0.6,
                "distance_to_candidate": 0.4,
                "assignment_confidence": 0.7,
                "low_confidence_flag": False,
                "original_macro_regime_label": "macro_southerly_flow",
                "absorbed_from_residual": False,
                "residual_absorption_reason": "Original physical macro retained.",
                "causal_window": causal_window,
                "production_status": "NOT_PRODUCTION",
            },
        ],
        strict=False,
    )


def _comparison_v21() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2.1",
                "macro_regime_label": "macro_nw_continuum",
                "v21_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2.1",
                "macro_regime_label": "macro_southerly_flow",
                "v21_dead_regimes": 0,
                "protected_regression_flag": False,
                "decision_update": "READY_FOR_FULL_ONDA4_RERUN",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )


def _candidate_v2() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "candidate_version": "v2",
                "macro_regime_label": "macro_nw_continuum",
                "subtype_label": "subtype_standard_nw",
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "candidate_version": "v2",
                "macro_regime_label": "macro_southerly_flow",
                "subtype_label": "subtype_frontal_southerly",
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )


def test_onda_c_rejects_non_causal_assignment_window():
    with pytest.raises(ValueError, match="causal_window"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(causal_window="leaky"),
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_rejects_duplicate_assignment_keys():
    duplicated = pl.concat([_assignments_v21(), _assignments_v21()])
    with pytest.raises(ValueError, match="duplicate assignment"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=duplicated,
            candidate_v2=_candidate_v2(),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )


def test_onda_c_requires_candidate_v2_physical_macros():
    with pytest.raises(ValueError, match="candidate_v2"):
        build_regime_classifiability_artifacts(
            features=_features(),
            assignments_v2=_assignments_v21(),
            assignments_v21=_assignments_v21(),
            candidate_v2=pl.DataFrame(
                [
                    {
                        "candidate_version": "v2",
                        "macro_regime_label": "macro_nw_continuum",
                        "subtype_label": "subtype_standard_nw",
                        "production_status": "EXPERIMENT_ONLY",
                    }
                ],
                strict=False,
            ),
            comparison_v21=_comparison_v21(),
            train_end=dt.date(2021, 12, 31),
            test_start=dt.date(2022, 1, 1),
        )
```

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_rejects_non_causal_assignment_window -q
```

Expected: fail because module/function does not exist.

- [ ] **Step 3: Implement minimal validation**

Create `solarstorm/onda2e/_regime_classifiability.py` with schema constants,
decision constants, and `build_regime_classifiability_artifacts(...)`.
Validate:

- v2/v2.1 production status;
- v2.1 `candidate_version`;
- `causal_window`;
- protected macros present;
- duplicate assignment keys on `(candidate_version, date_local, cp)`;
- `candidate_v2` is loaded, experimental, and contains the protected physical
  macros required by the v2/v2.1 comparison;
- comparison `production_status = EXPERIMENT_ONLY`.

Return empty artifact frames with correct schemas after validation.

- [ ] **Step 4: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_rejects_non_causal_assignment_window -q
```

Expected: pass.

---

## Task 2: Distance-Softmax v2/v2.1 Baseline Rows

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Write failing artifact schema test**

Add a test asserting:

- `regime_classifiability_assignments` contains methods
  `distance_softmax_v2` and `distance_softmax_v21`;
- every row has `production_status = EXPERIMENT_ONLY`;
- comparison decision is not `READY_FOR_ONDA3_DESIGN_REVIEW` unless diagnostics
  pass.

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_builds_distance_softmax_baseline_artifacts -q
```

Expected: fail because artifact rows are empty.

- [ ] **Step 3: Implement distance baseline conversion**

Map v2 and v2.1 assignment rows into `regime_classifiability_assignments`.
Use:

- `assigned_label = candidate_regime_label`;
- `assigned_component = component_argmax` when present, else subtype;
- entropy/margin/confidence from existing columns;
- train/test fold from date relative to `train_end`/`test_start`;
- `production_status = EXPERIMENT_ONLY`.

Build metrics grouped by method/macro/CP.

- [ ] **Step 4: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_builds_distance_softmax_baseline_artifacts -q
```

Expected: pass.

---

## Task 3: Train-Only GMM, SOM, And Michelangeli Diagnostics

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Write failing train-only and stability test**

Add a test with train and test dates. Assert diagnostics include:

- `train_test_leakage_check = PASS`;
- `train_only_gmm` rows exist only when both train and test have enough rows;
- `som_topological` rows exist or a diagnostic explains the deterministic
  projection fallback;
- `michelangeli_stability` metrics exist with `temporal_stability` and
  `fold_stability` populated;
- no `.pkl`, `.pickle`, `.joblib`, or model files are written.

- [ ] **Step 2: Run red test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_gmm_som_michelangeli_are_train_only_and_do_not_write_models -q
```

Expected: fail because methods are not implemented.

- [ ] **Step 3: Implement minimal train-only and stability methods**

Use standardized causal numeric columns available in features. If scikit-learn
is present, use `GaussianMixture`, `silhouette_score`,
`davies_bouldin_score`, `calinski_harabasz_score`, `normalized_mutual_info_score`,
and `adjusted_rand_score`. If SOM library is absent, implement
`som_topological` as a non-production PCA/grid projection diagnostic using
train-fitted standardization and deterministic 2D projection; record the method
as topology diagnostic, not production SOM.

Implement `michelangeli_stability` as a non-production weather-regime
classifiability diagnostic:

- compute train-fold macro centroids on standardized causal features;
- bootstrap train rows with fixed seeds;
- reassign held-out/test rows by nearest centroid for each bootstrap;
- report temporal/fold stability as mean pairwise agreement and ARI/NMI vs
  v2.1 labels;
- write only CSV rows, never serialized estimators.

- [ ] **Step 4: Run green test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_onda_c_gmm_som_michelangeli_are_train_only_and_do_not_write_models -q
```

Expected: pass.

---

## Task 4: Writer And Report

**Files:**
- Modify: `solarstorm/onda2e/_regime_classifiability.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Write failing writer test**

Assert writer creates:

- `regime_classifiability_assignments_v1.csv`
- `regime_classifiability_metrics_v1.csv`
- `regime_classifiability_comparison_v1.csv`
- `regime_classifiability_diagnostics_v1.csv`
- `regime_classifiability_report_v1.md`

Assert report contains:

```text
Onda C Regime Classifiability
not a production classifier
Onda C comes before Onda 3
```

Assert `regime_classifiability_comparison_v1.csv` uses only the allowed
decision enum:

```python
{
    "READY_FOR_ONDA3_DESIGN_REVIEW",
    "KEEP_IN_REGIME_DESIGN_REVIEW",
    "BLOCK_ONDA_C_PROMOTION",
}
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_write_regime_classifiability_artifacts -q
```

Expected: fail because writer does not exist.

- [ ] **Step 3: Implement writer**

Add `write_regime_classifiability_artifacts(artifacts, output_dir, today=None)`.
Write all CSVs and Markdown report. Validate comparison decisions before
writing; raise `ValueError("decision_update")` if any value is outside the
allowed enum.

- [ ] **Step 4: Run green writer test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_write_regime_classifiability_artifacts -q
```

Expected: pass.

---

## Task 5: Exports And CLI

**Files:**
- Modify: `solarstorm/onda2e/__init__.py`
- Modify: `solarstorm/__main__.py`
- Test: `tests/test_regime_classifiability.py`

- [ ] **Step 1: Write failing CLI test**

Use small temp CSV/parquet inputs and invoke:

```powershell
regime-classifiability-benchmark
--features-path <features.parquet>
--assignments-v2-path <v2.csv>
--assignments-v21-path <v21.csv>
--candidate-v2-path <candidate.csv>
--comparison-v21-path <comparison.csv>
--output-dir <tmp>
```

Assert exit code 0 and all artifacts exist.

- [ ] **Step 2: Run red CLI test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_regime_classifiability_cli_writes_artifacts -q
```

Expected: fail because command does not exist.

- [ ] **Step 3: Export helpers and add CLI**

Export:

- `build_regime_classifiability_artifacts`
- `write_regime_classifiability_artifacts`

Add Typer command `regime-classifiability-benchmark`.

- [ ] **Step 4: Run green CLI test**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py::test_regime_classifiability_cli_writes_artifacts -q
```

Expected: pass.

---

## Task 6: Generate Real Onda C Artifacts

**Files:**
- Generated under `reports/regime-classifiability/`

- [ ] **Step 1: Run command on real artifacts**

Run:

```powershell
uv run python -m solarstorm regime-classifiability-benchmark `
  --features-path reports/regime-design/features_candidate_v2_1.parquet `
  --assignments-v2-path reports/regime-design/regime_candidate_assignments_v2.csv `
  --assignments-v21-path reports/regime-design/regime_candidate_assignments_v2_1.csv `
  --candidate-v2-path reports/onda2e/regime_design_candidate_v2.csv `
  --comparison-v21-path reports/regime-design/regime_candidate_v2_v21_comparison.csv `
  --output-dir reports/regime-classifiability
```

- [ ] **Step 2: Audit artifacts**

Run:

```powershell
@'
from pathlib import Path
required = [
    "reports/regime-classifiability/regime_classifiability_assignments_v1.csv",
    "reports/regime-classifiability/regime_classifiability_metrics_v1.csv",
    "reports/regime-classifiability/regime_classifiability_comparison_v1.csv",
    "reports/regime-classifiability/regime_classifiability_diagnostics_v1.csv",
    "reports/regime-classifiability/regime_classifiability_report_v1.md",
]
missing = [p for p in required if not Path(p).exists()]
print("missing", missing)
if missing:
    raise SystemExit(1)
'@ | uv run python -
```

Expected: `missing []`.

---

## Task 7: Documentation Refresh

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/decisions/012-evidence-to-decision-gate.md`
- Modify: `docs/regime_model_card.md`
- Modify: `docs/onda4_robustness_plan.md`

- [ ] **Step 1: Update docs with Onda C result**

Document:

- Onda C artifact paths;
- decision update;
- whether Onda 3 remains blocked or may enter design review;
- no production classifier promotion;
- Onda C did not write Onda 3 model artifacts.

- [ ] **Step 2: Search for stale sequencing**

Run:

```powershell
rg -n "Onda 3 .*unblocked|Onda 3 .*may proceed|Onda 3 .*may begin" ROADMAP.md docs
```

Expected: no unconditional statement bypassing Onda C.

---

## Task 8: Final Verification

- [ ] **Step 1: Run focused tests**

Run:

```powershell
uv run pytest tests/test_regime_classifiability.py tests/test_regime_design_validation.py tests/test_foundation_experiment_results.py tests/test_robustness_cli.py -q
```

- [ ] **Step 2: Run full non-network suite**

Run:

```powershell
uv run pytest -q -m "not network"
```

- [ ] **Step 3: Run ruff**

Run:

```powershell
uv run ruff check .
```

- [ ] **Step 4: Run artifact audit**

Run the audit command from Task 6 and confirm `missing []`.

---

## Parallel Execution Guidance

Use agents only with disjoint write sets:

- Agent A: Task 1 and Task 2 in `_regime_classifiability.py` and
  `tests/test_regime_classifiability.py`.
- Agent B: Task 3 train-only GMM/SOM/Michelangeli diagnostics in the same
  module only after Agent A lands, or in a branch/subtask with explicit merge
  control.
- Main integrator: Task 4/5 writer, exports, CLI.
- Agent C: Task 7 documentation audit after real artifacts exist.

Do not let multiple agents edit `solarstorm/__main__.py` or
`solarstorm/onda2e/__init__.py` at the same time.

## Completion Rule

The sprint is complete only when Onda C artifacts exist, docs preserve the
sequence Opcao A -> Onda C -> Onda 3, no production/model artifacts are created,
and focused tests, full non-network tests, ruff, and artifact audit pass.
