from httpx import AsyncClient, MockTransport
from typing import Optional

from ..dto.ann_content import AnnContentRe
from ..dto.ann_list import AnnListRe
from .config import Config
from .env import get_env


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class Api:
    def __init__(self, url: str):
        self.url = url

    async def get(
        self,
        params: Optional[dict] = None,
        transport: Optional[MockTransport] = None,  # 测试用
    ) -> dict:
        async with AsyncClient(transport=transport) as async_client:
            return (
                await async_client.get(self.url, params=params, headers=HEADERS)
            ).json()


async def get_ann_list(config: Config) -> AnnListRe:
    transport = None
    if get_env("DEBUG") and get_env("DEBUG")[0] == "TRUE":
        import json
        from httpx import Response

        with open(
            f"src/temp/{config.name.en}/ann_list.json", "r", encoding="utf-8"
        ) as f:
            mock_response = json.load(f)
        transport = MockTransport(lambda _: Response(200, json=mock_response))
    return AnnListRe(**await Api(config.ann_list_url).get(transport=transport))


async def get_ann_content(config: Config) -> AnnContentRe:
    transport = None
    if get_env("DEBUG") and get_env("DEBUG")[0] == "TRUE":
        import json
        from httpx import Response

        with open(
            f"src/temp/{config.name.en}/ann_content.json", "r", encoding="utf-8"
        ) as f:
            mock_response = json.load(f)
        transport = MockTransport(lambda _: Response(200, json=mock_response))
    return AnnContentRe(**await Api(config.ann_content_url).get(transport=transport))
