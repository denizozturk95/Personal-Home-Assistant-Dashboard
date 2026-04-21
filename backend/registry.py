from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Action:
    id: str
    label: str
    icon: str
    script_path: Path
    timeout_s: int


class RegistryError(RuntimeError):
    pass


def load_registry(actions_file: Path, scripts_dir: Path) -> dict[str, Action]:
    if not actions_file.exists():
        raise RegistryError(f"Registry file not found: {actions_file}")

    with actions_file.open("rb") as fh:
        data = tomllib.load(fh)

    raw_actions = data.get("action", [])
    if not isinstance(raw_actions, list) or not raw_actions:
        raise RegistryError("actions.toml must define at least one [[action]] entry")

    scripts_dir = scripts_dir.resolve()
    registry: dict[str, Action] = {}

    for entry in raw_actions:
        action_id = entry.get("id")
        script_name = entry.get("script")
        if not action_id or not script_name:
            raise RegistryError(f"Action entry missing id/script: {entry}")
        if action_id in registry:
            raise RegistryError(f"Duplicate action id: {action_id}")

        script_path = (scripts_dir / script_name).resolve()
        if scripts_dir not in script_path.parents and script_path != scripts_dir:
            raise RegistryError(
                f"Action '{action_id}' script '{script_name}' escapes scripts dir"
            )
        if not script_path.is_file():
            raise RegistryError(
                f"Action '{action_id}' script not found: {script_path}"
            )

        registry[action_id] = Action(
            id=action_id,
            label=entry.get("label", action_id),
            icon=entry.get("icon", "bolt"),
            script_path=script_path,
            timeout_s=int(entry.get("timeout_s", 30)),
        )

    return registry
