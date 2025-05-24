from pathlib import Path
from pydantic import BaseModel

from .file import TomlFile


class GameName(BaseModel):
    en: str
    zh: str


class Config(BaseModel):
    ann_list_url: str
    ann_content_url: str
    default_post: str
    icon: str
    name: GameName


async def load_config(configs_path: Path) -> list[Config]:
    return [
        Config(**await TomlFile(config_path).read_async())
        for config_path in configs_path.iterdir()
    ]
