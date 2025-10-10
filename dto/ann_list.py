"""DTO for the Hoyolab announcement list endpoint."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnnouncementRecord(BaseModel):
    ann_id: int
    title: str
    subtitle: str
    banner: str
    content: str
    type_label: str
    tag_label: str
    tag_icon: str
    login_alert: int
    lang: str
    start_time: datetime
    end_time: datetime
    ann_type: int = Field(alias="type")
    remind: int
    alert: int
    tag_start_time: datetime
    tag_end_time: datetime
    remind_ver: int
    has_content: bool
    pic_type: Optional[int] = None
    content_type: Optional[int] = None
    img: Optional[str] = None
    href_type: Optional[int] = None
    href: Optional[str] = None
    pic_list: Optional[list] = None
    extra_remind: int
    tag_icon_hover: Optional[str] = None
    logout_remind: Optional[int] = None
    logout_remind_ver: Optional[int] = None
    country: Optional[str] = None
    need_remind_text: int
    remind_text: str
    weak_remind: int
    remind_consumption_type: int


class TypeData(BaseModel):
    ann_list: list[AnnouncementRecord] = Field(alias="list")
    type_id: int
    type_label: str


class PicType(BaseModel):
    ann_list: list[AnnouncementRecord] = Field(alias="list")
    pic_type: int


class Pic(BaseModel):
    type_list: list[PicType]
    type_id: int
    type_label: str


class AnnListData(BaseModel):
    ann_types: list[TypeData] = Field(alias="list")
    total: int
    type_list: list
    alert: bool
    alert_id: int
    timezone: int
    t: str
    pic_list: list[Pic]
    pic_total: int
    pic_type_list: list
    pic_alert: bool
    pic_alert_id: int
    static_sign: str
    banner: str
    calendar_type: dict


class AnnListRe(BaseModel):
    retcode: int
    message: str
    data: AnnListData
