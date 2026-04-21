from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .registry import Action


@dataclass
class RunResult:
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool


async def run_action(action: Action, python_bin: str, log_dir: Path) -> RunResult:
    start = time.monotonic()
    timed_out = False
    stdout_b = b""
    stderr_b = b""
    exit_code: int | None = None

    try:
        proc = await asyncio.create_subprocess_exec(
            python_bin,
            str(action.script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(action.script_path.parent),
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=action.timeout_s
            )
            exit_code = proc.returncode
        except asyncio.TimeoutError:
            timed_out = True
            proc.kill()
            stdout_b, stderr_b = await proc.communicate()
            exit_code = proc.returncode
    except FileNotFoundError as exc:
        return RunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr=f"Could not launch python: {exc}",
            duration_ms=int((time.monotonic() - start) * 1000),
            timed_out=False,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    result = RunResult(
        ok=(exit_code == 0 and not timed_out),
        exit_code=exit_code,
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        duration_ms=duration_ms,
        timed_out=timed_out,
    )

    _append_log(log_dir, action, result)
    return result


def _append_log(log_dir: Path, action: Action, result: RunResult) -> None:
    log_file = log_dir / "run.log"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action.id,
        **{k: v for k, v in asdict(result).items() if k != "stdout" and k != "stderr"},
    }
    try:
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass
