"""Persistence helpers for timelines and catalog metadata."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

from models.config import GameConfig
from models.game import GameTimeline


async def load_timeline(base_dir: Path, display_name: str) -> GameTimeline:
    timeline_path = base_dir / display_name / "data.json"
    if not timeline_path.exists():
        return GameTimeline()
    async with aiofiles.open(timeline_path, "r", encoding="utf-8") as handle:
        content = await handle.read()
    if not content.strip():
        return GameTimeline()
    payload = json.loads(content)
    return GameTimeline.model_validate(payload)


async def save_timeline(base_dir: Path, display_name: str, timeline: GameTimeline) -> None:
    target_dir = base_dir / display_name
    target_dir.mkdir(parents=True, exist_ok=True)
    timeline_path = target_dir / "data.json"
    async with aiofiles.open(timeline_path, "w", encoding="utf-8") as handle:
        await handle.write(
            json.dumps(timeline.model_dump(mode="json", by_alias=True), ensure_ascii=False)
        )


def update_catalog(base_dir: Path, config: GameConfig, timeline_changed: bool) -> None:
    catalog_path = base_dir / "data.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    else:
        catalog = {"games": [], "icons": [], "update_time": 0}

    if "games" not in catalog:
        catalog["games"] = []
    if "icons" not in catalog:
        catalog["icons"] = []
    if "update_time" not in catalog:
        catalog["update_time"] = 0

    if config.display_name not in catalog["games"]:
        catalog["games"].append(config.display_name)
    if config.icon not in catalog["icons"]:
        catalog["icons"].append(config.icon)

    if timeline_changed:
        catalog["update_time"] = int(datetime.now().timestamp())

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
