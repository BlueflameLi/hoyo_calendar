"""Configuration models for supported games."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GameName(BaseModel):
    en: str
    zh: str


class CalendarLabels(BaseModel):
    event: str = "活动"
    gacha: str = "祈愿"
    update: str = "版本更新"
    special_program: str = "前瞻特别节目"


class GameConfig(BaseModel):
    ann_list_url: str
    ann_content_url: str
    default_post: str
    icon: str
    name: GameName
    calendar: CalendarLabels = Field(default_factory=CalendarLabels)

    @property
    def game_id(self) -> str:
        return self.name.en

    @property
    def display_name(self) -> str:
        return self.name.zh
