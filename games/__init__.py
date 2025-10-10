"""Game plugin registry."""

from __future__ import annotations

from functools import lru_cache

from models.config import GameConfig
from .base import GamePlugin
from .genshin import GenshinPlugin
from .starrail import StarRailPlugin
from .zenless import ZenlessPlugin


@lru_cache(maxsize=1)
def _plugins() -> dict[str, GamePlugin]:
    return {
        plugin.game_id: plugin
        for plugin in (GenshinPlugin(), StarRailPlugin(), ZenlessPlugin())
    }


def get_plugin(game_id: str) -> GamePlugin:
    plugins = _plugins()
    if game_id not in plugins:
        raise KeyError(f"No plugin registered for game '{game_id}'")
    return plugins[game_id]


def available_games() -> list[str]:
    return list(_plugins().keys())


def load_game_configs() -> list[GameConfig]:
    return [plugin.config.model_copy(deep=True) for plugin in _plugins().values()]
