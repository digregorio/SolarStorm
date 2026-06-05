"""Shadow Runner: executes forecasts for CP20-23 over date ranges (Phase 5.1).

Design:
- Uses subprocess.run to invoke `tmax forecast --model auto --serve-residuals`
- Output: artifacts/shadow_ops/forecasts/{date_local}.jsonl (one file per date)
- Atomic writes: write to .tmp then rename
- Idempotent: skip if output file already exists (with force=True to override)
- Schema validation: each record validated against REQUIRED_FORECAST_FIELDS

Wave 1 extension (--with-decisions):
- After forecasts are generated, optionally invokes `tmax decide --forecast-json`
- Output: artifacts/shadow_ops/decisions/{date_local}.jsonl (one file per date)
- ALWAYS passes --dry-run to the decide CLI (never places live orders).
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


from core.ops.schemas import ShadowForecastRecord, ShadowSchemaError, validate_record


# Default checkpoints to run (CP20-23 = 20:00, 21:00, 22:00, 23:00 UTC).
DEFAULT_CPS: tuple[int, ...] = (20, 21, 22, 23)

# Default output root for shadow ops artifacts.
DEFAULT_SHADOW_ROOT = Path("artifacts/shadow_ops")


@dataclass(frozen=True)
class ShadowRunnerConfig:
    """Configuration for the shadow runner.

    Attributes:
        shadow_root: Root directory for shadow ops output.
        cps: Tuple of checkpoint hours (UTC) to run.
        force: If True, overwrite existing output files.
        timeout_s: Subprocess timeout in seconds.
        python_executable: Python interpreter to use (default: sys.executable).
        with_decisions: If True, generate decision artifacts after forecasts.
        station_yaml: Path to station config for the decide CLI.
        csv_path: Path to observations CSV for forecast and decide subprocesses.
    """

    shadow_root: Path = DEFAULT_SHADOW_ROOT
    cps: tuple[int, ...] = DEFAULT_CPS
    force: bool = False
    timeout_s: int = 120
    python_executable: str = field(default_factory=lambda: sys.executable)
    with_decisions: bool = False
    station_yaml: Path = field(default_factory=lambda: Path("nzwn/config/station.yaml"))
    csv_path: Path = field(default_factory=lambda: Path("NZWN.csv"))


@dataclass(frozen=True)
class ShadowRunResult:
    """Result of running forecasts for a single date.

    Attributes:
        date_local: The date that was forecasted.
        output_path: Path to the JSONL output file (if written).
        records: List of validated forecast records.
        skipped: If True, the date was skipped (already exists).
        errors: List of (cp, error_message) tuples for failed forecast checkpoints.
        decision_errors: List of (cp, error_message) tuples for failed decision generation.
    """

    date_local: date
    output_path: Path | None = None
    records: list[ShadowForecastRecord] = field(default_factory=list)
    skipped: bool = False
    errors: list[tuple[int, str]] = field(default_factory=list)
    decision_errors: list[tuple[int, str]] = field(default_factory=list)

    @property
    def n_success(self) -> int:
        return len(self.records)

    @property
    def n_failed(self) -> int:
        return len(self.errors)

    @property
    def n_decision_failed(self) -> int:
        return len(self.decision_errors)


class ShadowRunnerError(Exception):
    """Raised when the shadow runner encounters a fatal error."""


def _output_path(shadow_root: Path, d: date) -> Path:
    """Compute the output JSONL path for a given date."""
    forecasts_dir = shadow_root / "forecasts"
    return forecasts_dir / f"{d.isoformat()}.jsonl"


def _decisions_path(shadow_root: Path, d: date) -> Path:
    """Compute the decisions JSONL path for a given date."""
    decisions_dir = shadow_root / "decisions"
    return decisions_dir / f"{d.isoformat()}.jsonl"


def _build_forecast_command(
    python_exec: str,
    target_date: date,
    cp: int,
    out_root: Path,
    csv_path: Path,
) -> list[str]:
    """Build the subprocess command for a single forecast."""
    return [
        python_exec,
        "-m",
        "tmax",
        "forecast",
        "--date",
        target_date.isoformat(),
        "--cp",
        str(cp),
        "--csv",
        str(csv_path),
        "--model",
        "auto",
        "--serve-residuals",
        "--out-root",
        str(out_root),
        "--dry-run",
    ]


def _parse_cli_json(stdout: str) -> dict:
    """Parse the JSON output from a tmax CLI command that may print a banner.

    CLI commands send diagnostic banners to stderr and the JSON record to stdout.
    We find the first '{' which starts the JSON object.
    """
    start = stdout.find("{")
    if start == -1:
        raise ShadowRunnerError(f"No JSON found in CLI output: {stdout[:200]}")
    return json.loads(stdout[start:])


def _parse_forecast_output(stdout: str) -> dict:
    """Parse the JSON output from `tmax forecast --dry-run`.

    Deprecated alias for _parse_cli_json. Kept for backward compatibility.
    """
    return _parse_cli_json(stdout)


def _atomic_write(path: Path, lines: list[str]) -> None:
    """Write lines to a file atomically (write to .tmp, then rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="ascii") as fh:
        for line in lines:
            fh.write(line + "\n")
    tmp_path.replace(path)


# Minimum fields required for a decision record to be considered valid.
# Includes mandatory linkage fields (forecast -> decision) per Wave 1 spec.
MINIMUM_DECISION_FIELDS: tuple[str, ...] = (
    "run_id",
    "date_local",
    "cp_utc",
    "odds_status",
    "forecast_run_id",
    "forecast_model_version",
    "forecast_file",
)


def _is_decisions_complete(
    jsonl_path: Path,
    expected_date: date,
    expected_cps: tuple[int, ...],
) -> bool:
    """Check if a decisions JSONL file has valid records for ALL expected CPs.

    Rejects:
    - Missing mandatory fields (including linkage fields).
    - Wrong date_local.
    - Duplicate CPs.
    - Wrong number of valid lines (must equal len(expected_cps)).

    Args:
        jsonl_path: Path to the decisions JSONL file.
        expected_date: The date_local that all records must have.
        expected_cps: Tuple of expected CP hours (UTC).
    """
    if not jsonl_path.exists():
        return False
    found_cps: set[int] = set()
    valid_line_count = 0
    expected_date_iso = expected_date.isoformat()
    try:
        with open(jsonl_path, "r", encoding="ascii") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                # Validate minimum required fields.
                missing = [f for f in MINIMUM_DECISION_FIELDS if f not in raw]
                if missing:
                    return False
                # Validate date_local matches expected date.
                record_date = str(raw.get("date_local", ""))
                if record_date != expected_date_iso:
                    return False
                # Extract CP hour from cp_utc.
                cp_utc_str = str(raw.get("cp_utc", ""))
                if "T" in cp_utc_str:
                    hour = int(cp_utc_str.split("T")[1].split(":")[0])
                    if hour in found_cps:
                        return False  # Duplicate CP -> not complete.
                    found_cps.add(hour)
                valid_line_count += 1
    except (json.JSONDecodeError, ValueError, KeyError, OSError):
        return False
    # Exact match: all expected CPs present, no duplicates, correct line count.
    return found_cps == set(expected_cps) and valid_line_count == len(expected_cps)


def _is_complete(
    jsonl_path: Path,
    expected_date: date,
    expected_cps: tuple[int, ...],
) -> bool:
    """Check if a JSONL file has valid records for ALL expected CPs on the expected date.

    A file is 'complete' when it has exactly len(expected_cps) valid records,
    each with:
    - A distinct CP hour matching the expected set (exact match, not superset)
    - date_local matching the expected_date

    Partial files (fewer CPs, wrong date, or records that fail schema validation)
    are NOT complete.

    Args:
        jsonl_path: Path to the JSONL file.
        expected_date: The date_local that all records must have.
        expected_cps: Tuple of expected CP hours (UTC).
    """
    if not jsonl_path.exists():
        return False
    found_cps: set[int] = set()
    expected_date_iso = expected_date.isoformat()
    try:
        with open(jsonl_path, "r", encoding="ascii") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                validate_record(raw)
                # Validate date_local matches expected date.
                record_date = str(raw.get("date_local", ""))
                if record_date != expected_date_iso:
                    return False  # Wrong date -> not complete.
                # Extract CP hour from cp_utc.
                cp_utc_str = str(raw.get("cp_utc", ""))
                if "T" in cp_utc_str:
                    hour = int(cp_utc_str.split("T")[1].split(":")[0])
                    found_cps.add(hour)
    except (json.JSONDecodeError, ShadowSchemaError, ValueError, KeyError, OSError):
        return False  # Any parse/validation error -> not complete
    # Exact set match: all expected CPs present, no extras.
    return found_cps == set(expected_cps)


class ShadowRunner:
    """Executes forecasts for CP20-23 over date ranges.

    Usage:
        runner = ShadowRunner(config)
        result = runner.run_date(date(2025, 1, 15))
        results = runner.run_range(date(2025, 1, 1), date(2025, 1, 7))
    """

    def __init__(self, config: ShadowRunnerConfig | None = None) -> None:
        self.config = config or ShadowRunnerConfig()
        self._forecasts_out = self.config.shadow_root / "forecasts"
        self._forecasts_out.mkdir(parents=True, exist_ok=True)

    def run_date(self, target_date: date) -> ShadowRunResult:
        """Run forecasts for all configured CPs on a single date.

        Args:
            target_date: The local date to forecast.

        Returns:
            ShadowRunResult with records and/or errors.
        """
        out_path = _output_path(self.config.shadow_root, target_date)
        dec_path = _decisions_path(self.config.shadow_root, target_date) if self.config.with_decisions else None

        # --- Idempotency check -------------------------------------------------
        # Only skip if file has ALL expected CPs with valid schema AND the
        # date_local in records matches the target date. Partial files trigger
        # repair.
        forecasts_complete = out_path.exists() and _is_complete(out_path, target_date, self.config.cps)
        decisions_complete = (
            dec_path is not None
            and dec_path.exists()
            and _is_decisions_complete(dec_path, target_date, self.config.cps)
        )

        if not self.config.force and forecasts_complete:
            if not self.config.with_decisions or decisions_complete:
                return ShadowRunResult(date_local=target_date, skipped=True)

        # If forecasts are already complete but decisions are missing/incomplete,
        # load the existing forecasts instead of re-running them.
        records: list[ShadowForecastRecord] = []
        errors: list[tuple[int, str]] = []
        jsonl_lines: list[str] = []

        if forecasts_complete:
            # Load existing forecast records for decision generation.
            with open(out_path, "r", encoding="ascii") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                        record = validate_record(raw)
                        records.append(record)
                        jsonl_lines.append(json.dumps(record.to_dict(), ensure_ascii=True))
                    except (json.JSONDecodeError, ShadowSchemaError):
                        # Corrupt line -> treat as incomplete and re-run.
                        forecasts_complete = False
                        records = []
                        jsonl_lines = []
                        break

        if not forecasts_complete:
            # Generate forecasts (either partial/missing or corrupt).
            records = []
            jsonl_lines = []
            for cp in self.config.cps:
                try:
                    record = self._run_single_cp(target_date, cp)
                    records.append(record)
                    jsonl_lines.append(json.dumps(record.to_dict(), ensure_ascii=True))
                except (ShadowRunnerError, ShadowSchemaError, subprocess.TimeoutExpired,
                        subprocess.CalledProcessError, OSError) as exc:
                    errors.append((cp, f"{type(exc).__name__}: {exc}"))

        # Write output only if we actually generated forecasts (not loaded).
        written_path: Path | None = None
        if not forecasts_complete and jsonl_lines:
            _atomic_write(out_path, jsonl_lines)
            written_path = out_path
        elif forecasts_complete:
            written_path = out_path

        # Wave 1: generate decisions if requested.
        decision_errors: list[tuple[int, str]] = []
        if self.config.with_decisions and written_path is not None:
            decision_lines = self._run_decisions_for_date(target_date, records, decision_errors)
            if decision_lines:
                _atomic_write(dec_path, decision_lines)  # type: ignore[arg-type]

        return ShadowRunResult(
            date_local=target_date,
            output_path=written_path,
            records=records,
            errors=errors,
            decision_errors=decision_errors,
        )

    def _run_single_cp(self, target_date: date, cp: int) -> ShadowForecastRecord:
        """Run forecast for a single checkpoint.

        Args:
            target_date: The local date to forecast.
            cp: Checkpoint hour (UTC).

        Returns:
            Validated ShadowForecastRecord.

        Raises:
            ShadowRunnerError: If the forecast command fails.
            ShadowSchemaError: If the output fails validation.
        """
        cmd = _build_forecast_command(
            self.config.python_executable,
            target_date,
            cp,
            self._forecasts_out,
            self.config.csv_path,
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config.timeout_s,
            check=False,
        )

        if result.returncode != 0:
            stderr_snippet = result.stderr[:500] if result.stderr else "(no stderr)"
            raise ShadowRunnerError(
                f"Forecast failed for CP{cp}: exit {result.returncode}, stderr: {stderr_snippet}"
            )

        # Parse the JSON output from --dry-run.
        raw_record = _parse_forecast_output(result.stdout)

        # Validate schema.
        return validate_record(raw_record)

    def _run_decisions_for_date(
        self,
        target_date: date,
        records: list[ShadowForecastRecord],
        errors: list[tuple[int, str]],
    ) -> list[str]:
        """Generate decision lines for a date using the decide CLI.

        Each forecast record is written to a temporary JSON file, then the decide
        CLI is invoked with --forecast-json and --dry-run.  The --dry-run flag
        guarantees no live orders are placed.

        Every decision row is validated against MINIMUM_DECISION_FIELDS, date_local,
        and CP before being accepted.  Invalid rows are treated as errors and NOT
        written to the JSONL file.

        Args:
            target_date: The date being processed.
            records: Forecast records already validated.
            errors: List to append decision-generation errors to.

        Returns:
            List of JSON strings (decision rows) for the JSONL file.
        """
        lines: list[str] = []
        expected_date_iso = target_date.isoformat()
        for record in records:
            cp_hour = None
            if "T" in record.cp_utc:
                try:
                    cp_hour = int(record.cp_utc.split("T")[1].split(":")[0])
                except (IndexError, ValueError):
                    pass
            # Fallback: cp_utc should always contain "T" for valid ISO datetimes.
            # If extraction fails, use 0 as a marker (this is a degenerate case).
            if cp_hour is None:
                cp_hour = 0
            try:
                decision = self._run_decision_for_record(target_date, cp_hour, record)
                # Validate decision schema before accepting it.
                missing = [f for f in MINIMUM_DECISION_FIELDS if f not in decision]
                if missing:
                    raise ShadowRunnerError(
                        f"Decision for CP{cp_hour} missing fields: {missing}"
                    )
                if str(decision.get("date_local", "")) != expected_date_iso:
                    raise ShadowRunnerError(
                        f"Decision date_local mismatch: expected {expected_date_iso}, "
                        f"got {decision.get('date_local')}"
                    )
                # Validate CP in cp_utc matches the expected cp_hour.
                cp_utc_str = str(decision.get("cp_utc", ""))
                decision_cp = None
                if "T" in cp_utc_str:
                    try:
                        decision_cp = int(cp_utc_str.split("T")[1].split(":")[0])
                    except (IndexError, ValueError):
                        pass
                if decision_cp != cp_hour:
                    raise ShadowRunnerError(
                        f"Decision CP mismatch: expected {cp_hour}, got {decision_cp} "
                        f"from cp_utc {cp_utc_str}"
                    )
                lines.append(json.dumps(decision, ensure_ascii=True))
            except (ShadowRunnerError, subprocess.TimeoutExpired,
                    subprocess.CalledProcessError, OSError, json.JSONDecodeError) as exc:
                errors.append((cp_hour, f"{type(exc).__name__}: {exc}"))
        return lines

    def _run_decision_for_record(
        self,
        target_date: date,
        cp: int,
        record: ShadowForecastRecord,
    ) -> dict:
        """Run decide CLI for a single forecast record.

        Writes the record to a temporary JSON file, invokes the decide CLI with
        --dry-run, and returns the parsed decision dict.

        Args:
            target_date: The local date.
            cp: Checkpoint hour.
            record: Validated forecast record.

        Returns:
            Decision dict from the decide CLI stdout.

        Raises:
            ShadowRunnerError: If the decide command fails or produces no JSON.
        """
        # Write record to a temporary JSON file for --forecast-json.
        # Use a unique suffix to avoid collisions across parallel runners.
        tmp_dir = self.config.shadow_root / "_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        unique = uuid.uuid4().hex[:8]
        tmp_path = tmp_dir / f"{target_date.isoformat()}_cp{cp:02d}_{unique}.json"
        with open(tmp_path, "w", encoding="ascii") as fh:
            json.dump(record.to_dict(), fh, ensure_ascii=True)

        cmd = [
            self.config.python_executable,
            "-m",
            "tmax",
            "decide",
            "--date", target_date.isoformat(),
            "--cp", str(cp),
            "--forecast-json", str(tmp_path),
            "--station-config", str(self.config.station_yaml),
            "--csv", str(self.config.csv_path),
            "--dry-run",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_s,
                check=False,
            )
            if result.returncode != 0:
                stderr_snippet = result.stderr[:500] if result.stderr else "(no stderr)"
                raise ShadowRunnerError(
                    f"Decide failed for CP{cp}: exit {result.returncode}, stderr: {stderr_snippet}"
                )
            return _parse_cli_json(result.stdout)
        finally:
            # Clean up temp file regardless of outcome.
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def run_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[ShadowRunResult]:
        """Run forecasts for a date range (inclusive).

        Args:
            start_date: First date to run.
            end_date: Last date to run (inclusive).

        Returns:
            List of ShadowRunResult, one per date.
        """
        if start_date > end_date:
            raise ShadowRunnerError(f"start_date {start_date} > end_date {end_date}")

        results: list[ShadowRunResult] = []
        current = start_date
        while current <= end_date:
            results.append(self.run_date(current))
            current = date.fromordinal(current.toordinal() + 1)
        return results


__all__ = [
    "DEFAULT_CPS",
    "DEFAULT_SHADOW_ROOT",
    "MINIMUM_DECISION_FIELDS",
    "ShadowRunner",
    "ShadowRunnerConfig",
    "ShadowRunnerError",
    "ShadowRunResult",
]
