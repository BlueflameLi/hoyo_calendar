from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AnnRe(BaseModel):
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
    pic_type: Optional[int] = None  # pic_ann
    content_type: Optional[int] = None  # pic_ann
    img: Optional[str] = None  # pic_ann
    href_type: Optional[int] = None  # pic_ann
    href: Optional[str] = None  # pic_ann
    pic_list: Optional[list] = None  # pic_ann
    extra_remind: int
    tag_icon_hover: Optional[str] = None  # not_pic_ann
    logout_remind: Optional[int] = None  # not_pic_ann
    logout_remind_ver: Optional[int] = None  # not_pic_ann
    country: Optional[str] = None  # not_pic_ann
    need_remind_text: int
    remind_text: str
    weak_remind: int
    remind_consumption_type: int


class TypeData(BaseModel):
    ann_list: list[AnnRe] = Field(alias="list")
    type_id: int
    type_label: str


class PicType(BaseModel):
    ann_list: list[AnnRe] = Field(alias="list")
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
