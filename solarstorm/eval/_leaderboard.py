"""Leaderboard: the permanent scoreboard artifact (P5)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from solarstorm.baselines._ladder import LadderResult


def build_leaderboard(
    *,
    results: list[LadderResult],
    segments: dict[str, list[LadderResult]],
    window_start: dt.date,
    window_end: dt.date,
    gates: dict | None = None,
) -> dict:
    by_cp: dict[str, list[dict]] = {}
    for r in results:
        by_cp.setdefault(r.cp, []).append({
            "level": r.level, "name": r.name,
            "mae": r.mae, "rmse": r.rmse, "bias": r.bias,
            "bracket_match": r.bracket_match, "rps": r.rps,
            "fallback_rate": r.fallback_rate, "n": r.n,
        })

    best_nulls = {}
    for cp, entries in by_cp.items():
        best = min(entries, key=lambda e: e["mae"])
        best_nulls[cp] = best["name"]

    return {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "window": {"start": window_start.isoformat(), "end": window_end.isoformat()},
        "by_cp": by_cp,
        "best_nulls": best_nulls,
        "segments": {k: [{"name": r.name, "mae": r.mae, "n": r.n} for r in v]
                      for k, v in segments.items()},
        "gates": gates or {},
        "summary": (
            f"Best null varies by CP. "
            f"{len(results)} aggregated baseline results across {len(by_cp)} CPs."
        ),
    }


def export_leaderboard(board: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    now_utc = dt.datetime.now(dt.UTC)
    stamp = now_utc.strftime("%Y-%m-%dT%H%MZ")
    today = dt.date.today().isoformat()
    json_path = output_dir / f"{stamp}-leaderboard.json"
    md_path = output_dir / f"{stamp}-leaderboard.md"

    # Also write/overwrite a convenience "latest" alias (P5: artifact is the
    # timestamped file; latest is a pointer, not the artifact).
    latest_json = output_dir / "latest-leaderboard.json"
    latest_md = output_dir / "latest-leaderboard.md"

    json_path.write_text(json.dumps(board, indent=2, default=str), encoding="utf-8")
    latest_json.write_text(json.dumps(board, indent=2, default=str), encoding="utf-8")

    lines = [
        f"# SolarStorm Baseline Leaderboard — {today}",
        f"Window: {board['window']['start']} to {board['window']['end']}",
        "",
    ]
    for cp, entries in board.get("by_cp", {}).items():
        best = board["best_nulls"].get(cp, "?")
        lines.append(f"## CP={cp} (best null: {best})")
        for e in entries:
            fb = f"fallback={e['fallback_rate']:.0%}" if e.get("fallback_rate") is not None else ""
            n_info = f"n={e['n']}" if e.get("n", 0) > 0 else ""
            lines.append(f"- {e['level']} {e['name']}: MAE={e['mae']:.2f}  "
                         f"RMSE={e['rmse']:.2f}  bias={e['bias']:+.2f}  "
                         f"BM={e['bracket_match']:.2f}  {fb}  {n_info}")
        lines.append("")

    if board.get("segments"):
        lines.append("## Segments")
        for seg_name, seg_entries in board["segments"].items():
            lines.append(f"### {seg_name}")
            for e in seg_entries:
                cp_info = f"CP={e['cp']}" if e.get("cp") else ""
                lines.append(f"- {e['name']} ({cp_info}): MAE={e['mae']:.2f}  n={e['n']}")
        lines.append("")

    # Gates section
    if board.get("gates"):
        lines.append("## Gates")
        for cp, entries in board["gates"].items():
            lines.append(f"### CP={cp}")
            for name, gate_results in entries.items():
                passed = sum(1 for g in gate_results.values() if g["passed"])
                total = len(gate_results)
                lines.append(f"- **{name}**: {passed}/{total} passed")
                for gname, g in gate_results.items():
                    icon = "+" if g["passed"] else "X"
                    lines.append(f"  - {icon} {gname}: {g['status']} — {g['detail']}")
        lines.append("")

    # Feature null section
    if board.get("feature_nulls"):
        lines.append("## Baseline+Feature Nulls")
        for entry in board["feature_nulls"]:
            corr = f"  corr_diff={entry['corr_diff']:.4f}" if entry.get("corr_diff") is not None else ""
            lines.append(f"- feature {entry['name']} (CP={entry['cp']}): MAE={entry['mae']:.2f}  n={entry['n']}{corr}")
        lines.append("")

    lines.append(f"\n{board['summary']}")
    md_text = "\n".join(lines)
    md_path.write_text(md_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")

    return json_path, md_path
