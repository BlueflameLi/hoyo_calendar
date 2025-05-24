from pydantic import BaseModel, Field
from typing import Optional


class AnnWithContent(BaseModel):
    ann_id: int
    content_type: Optional[int] = None  # pic ann
    title: str
    subtitle: str
    banner: str
    content: str  # HTML content
    lang: str
    img: Optional[str] = None  # pic ann
    href: Optional[str] = None  # pic ann
    pic_list: Optional[list] = None  # pic ann
    remind_text: str


class AnnContentData(BaseModel):
    content_items: list[AnnWithContent] = Field(alias="list")
    total: int
    pic_list: list[AnnWithContent]
    pic_total: int


class AnnContentRe(BaseModel):
    retcode: int
    message: str
    data: AnnContentData
