from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    token: str
    python_bin: str
    scripts_dir: Path
    actions_file: Path
    frontend_dir: Path
    log_dir: Path


def load_settings() -> Settings:
    token = os.environ.get("DASHBOARD_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "DASHBOARD_TOKEN is not set. Copy backend/.env.example to backend/.env and fill it in."
        )

    log_dir = Path(os.path.expanduser(os.environ.get("LOG_DIR", "~/.dashboard")))
    log_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        token=token,
        python_bin=os.environ.get("PYTHON_BIN", "python3"),
        scripts_dir=BACKEND_DIR / "scripts",
        actions_file=BACKEND_DIR / "actions.toml",
        frontend_dir=ROOT_DIR / "frontend",
        log_dir=log_dir,
    )
