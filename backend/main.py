from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .registry import Action, load_registry
from .runner import run_action
from .settings import load_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    app.state.settings = settings
    app.state.registry = load_registry(settings.actions_file, settings.scripts_dir)
    yield


app = FastAPI(title="Home Dashboard", lifespan=lifespan)


def require_token(request: Request) -> None:
    expected = request.app.state.settings.token
    header = request.headers.get("authorization", "")
    scheme, _, provided = header.partition(" ")
    if scheme.lower() != "bearer" or not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_action(action_id: str, request: Request) -> Action:
    registry: dict[str, Action] = request.app.state.registry
    action = registry.get(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id}")
    return action


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/actions", dependencies=[Depends(require_token)])
async def list_actions(request: Request) -> dict[str, list[dict]]:
    registry: dict[str, Action] = request.app.state.registry
    return {
        "actions": [
            {"id": a.id, "label": a.label, "icon": a.icon}
            for a in registry.values()
        ]
    }


@app.post("/api/run/{action_id}", dependencies=[Depends(require_token)])
async def run(action_id: str, request: Request) -> JSONResponse:
    action = get_action(action_id, request)
    settings = request.app.state.settings
    result = await run_action(action, settings.python_bin, settings.log_dir)
    status_code = 200 if result.ok else 500
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": result.ok,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "timed_out": result.timed_out,
        },
    )


def _mount_frontend(app: FastAPI) -> None:
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


_mount_frontend(app)
