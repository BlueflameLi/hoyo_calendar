"""DTO for the Hoyolab announcement content endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AnnouncementWithContent(BaseModel):
    ann_id: int
    content_type: Optional[int] = None
    title: str
    subtitle: str
    banner: str
    content: str
    lang: str
    img: Optional[str] = None
    href: Optional[str] = None
    pic_list: Optional[list] = None
    remind_text: str


class AnnContentData(BaseModel):
    content_items: list[AnnouncementWithContent] = Field(alias="list")
    total: int
    pic_list: list[AnnouncementWithContent]
    pic_total: int


class AnnContentRe(BaseModel):
    retcode: int
    message: str
    data: AnnContentData
