import datetime as dt
import json

from solarstorm.baselines._ladder import LadderResult
from solarstorm.eval._leaderboard import build_leaderboard, export_leaderboard


def test_build_leaderboard_groups_by_cp():
    results = [
        LadderResult(level="L0", name="persistence", cp="23:00", mae=1.5, n=30),
        LadderResult(level="L2", name="climatology", cp="23:00", mae=1.3, n=30),
    ]
    segments = {}
    board = build_leaderboard(
        results=results, segments=segments,
        window_start=dt.date(2026, 5, 1), window_end=dt.date(2026, 6, 1),
    )
    assert "23:00" in board["by_cp"]
    assert len(board["by_cp"]["23:00"]) == 2


def test_export_leaderboard_writes_json(tmp_path):
    board = {
        "generated_at": "2026-06-04T00:00:00",
        "window": {"start": "2026-05-01", "end": "2026-06-01"},
        "by_cp": {},
        "segments": {},
        "gates": {},
        "summary": "test",
    }
    out_path = tmp_path / "leaderboard"
    export_leaderboard(board, out_path)
    json_files = list(out_path.glob("*-leaderboard.json"))
    assert json_files
    assert (out_path / "latest-leaderboard.json").exists()
    assert (out_path / "latest-leaderboard.md").exists()
    data = json.loads((out_path / "latest-leaderboard.json").read_text())
    assert data["summary"] == "test"
