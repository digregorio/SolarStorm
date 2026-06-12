from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_expanded_decision_review import (
    _promotable_predictions,
    _selection,
)

runner = CliRunner()


def test_open_meteo_expanded_decision_review_cli_writes_artifacts(tmp_path: Path):
    predictions_path = tmp_path / "predictions.csv"
    selection_path = tmp_path / "selection.csv"
    output_dir = tmp_path / "expanded-review"
    _promotable_predictions().write_csv(predictions_path)
    _selection().write_csv(selection_path)

    result = runner.invoke(
        app,
        [
            "open-meteo-expanded-decision-review",
            "--predictions-path",
            str(predictions_path),
            "--selection-path",
            str(selection_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo OM-M13 expanded-surface decision review complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "open_meteo_expanded_decision_review_report_v1.md").exists()
    decision = pl.read_csv(output_dir / "open_meteo_expanded_policy_decision_v1.csv")
    assert decision.row(0, named=True)["decision_status"] == (
        "PROMOTE_EXPANDED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
    )


def test_open_meteo_expanded_decision_review_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-expanded-decision-review",
            "--predictions-path",
            str(tmp_path / "missing.csv"),
            "--selection-path",
            str(tmp_path / "missing-selection.csv"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
