"""Interfaces and shared models for game-specific logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from dto import AnnContentRe, AnnListRe
from models.game import Announcement
from models.config import GameConfig


@dataclass(slots=True)
class VersionInfo:
    """Lightweight representation of a game's version metadata."""

    code: str
    name: str
    banner: str
    start_time: datetime | None
    end_time: datetime | None
    next_version_code: str | None = None
    next_version_name: str | None = None
    next_version_sp_time: datetime | None = None


class GamePlugin(Protocol):
    """Abstraction for game-specific behaviour."""

    game_id: str
    config: GameConfig

    def extract_version(self, ann_list: AnnListRe) -> VersionInfo:
        """Return the active version information for the supplied announcement list."""
        ...

    def parse_announcements(
        self,
        *,
        version: VersionInfo,
        ann_list: AnnListRe,
        ann_content: AnnContentRe,
        existing_ids: set[int],
        display_name: str,
    ) -> list[Announcement]:
        """Return announcement objects for the current version."""
        ...


def parse_time(value: str | None) -> datetime | None:
    """Parse the ISO-like timestamps returned by Hoyolab."""

    if value in (None, ""):
        return None
    value = value.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
