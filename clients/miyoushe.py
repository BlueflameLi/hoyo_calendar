"""Async client for MiYouShe (HoYoLAB CN) news APIs."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from settings import Settings

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://bbs.mihoyo.com/",
}


class MiyousheClient:
    """Lightweight HTTP client for MiYouShe painter/post endpoints."""

    _NEWS_URL = "https://bbs-api-static.miyoushe.com/painter/wapi/getNewsList"
    _POST_URL = "https://bbs-api.miyoushe.com/post/wapi/getPostFull"

    def __init__(self, settings: Settings):
        self._client = httpx.AsyncClient(timeout=settings.http_timeout_seconds, headers=HEADERS)

    async def __aenter__(self) -> "MiyousheClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._client.aclose()

    async def fetch_news_list(
        self,
        *,
        gids: int,
        type_id: int,
        last_id: str = "",
        page_size: int = 20,
        retries: int = 3,
    ) -> dict:
        params = {
            "client_type": 4,
            "gids": gids,
            "last_id": last_id,
            "page_size": page_size,
            "type": type_id,
        }
        return await self._request_with_retry(self._NEWS_URL, params=params, retries=retries)

    async def fetch_post_detail(
        self,
        *,
        gids: int,
        post_id: str,
        retries: int = 3,
    ) -> dict:
        params = {
            "gids": gids,
            "post_id": post_id,
            "read": 1,
        }
        return await self._request_with_retry(self._POST_URL, params=params, retries=retries)

    async def _request_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any],
        retries: int,
    ) -> dict:
        attempt = 0
        delay = 1.0
        last_error: Exception | None = None
        while attempt < retries:
            try:
                response = await self._client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as exc:  # includes timeouts, network issues
                last_error = exc
                attempt += 1
                if attempt >= retries:
                    break
                logger.warning(
                    "MiYouShe request failed ({url}) attempt {attempt}/{retries}, retrying in {delay}s: {error}",
                    url=url,
                    attempt=attempt,
                    retries=retries,
                    delay=delay,
                    error=exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)
        assert last_error is not None
        raise last_error
