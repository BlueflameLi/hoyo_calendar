"""Async client for Hoyolab announcement APIs."""

from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger

from models.config import GameConfig
from dto import AnnContentRe, AnnListRe
from settings import Settings

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class HoyolabClient:
    """Thin wrapper around ``httpx.AsyncClient`` with optional mock support."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=settings.http_timeout_seconds, headers=HEADERS)

    async def __aenter__(self) -> "HoyolabClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._client.aclose()

    async def fetch_ann_list(self, config: GameConfig) -> AnnListRe:
        payload = await self._get(
            url=config.ann_list_url,
            game_id=config.game_id,
            mock_filename="ann_list.json",
        )
        return AnnListRe.model_validate(payload)

    async def fetch_ann_content(self, config: GameConfig) -> AnnContentRe:
        payload = await self._get(
            url=config.ann_content_url,
            game_id=config.game_id,
            mock_filename="ann_content.json",
        )
        return AnnContentRe.model_validate(payload)

    async def _get(self, *, url: str, game_id: str, mock_filename: str) -> Any:
        if self._settings.enable_debug_mocks:
            mock_path = self._settings.debug_data_dir / game_id / mock_filename
            logger.debug("Using mock data for {game}: {path}", game=game_id, path=mock_path)
            with mock_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

        response = await self._client.get(url)
        response.raise_for_status()
        return response.json()
