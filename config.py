"""Backward compatible exports for configuration helpers."""

from __future__ import annotations

from games import load_game_configs as _load_from_plugins
from models.config import CalendarLabels, GameConfig, GameName

__all__ = [
    "CalendarLabels",
    "GameConfig",
    "GameName",
    "load_game_configs",
]


def load_game_configs() -> list[GameConfig]:
    """Return the built-in game configuration list."""

    return _load_from_plugins()
