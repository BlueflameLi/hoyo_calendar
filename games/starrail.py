"""Honkai: Star Rail specific parsing rules."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup

from dto import AnnContentRe, AnnListRe
from models.config import GameConfig, GameName
from models.game import Announcement
from .base import GamePlugin, VersionInfo, parse_time
from parsers.text import (
    extract_clean_time,
    extract_floats,
    extract_inner_text,
    remove_html_tags,
)


_VERSION_HINT_PATTERN = re.compile(r"(\d+\.\d+)\s*版本")


CONFIG = GameConfig(
    ann_list_url=(
        "https://hkrpg-ann-api.mihoyo.com/common/hkrpg_cn/announcement/api/"
        "getAnnList?game=hkrpg&game_biz=hkrpg_cn&lang=zh-cn&bundle_id=hkrpg_cn"
        "&level=1&platform=pc&region=prod_gf_cn&uid=1"
    ),
    ann_content_url=(
        "https://hkrpg-ann-api.mihoyo.com/common/hkrpg_cn/announcement/api/"
        "getAnnContent?game=hkrpg&game_biz=hkrpg_cn&lang=zh-cn&bundle_id=hkrpg_cn"
        "&level=1&platform=pc&region=prod_gf_cn&uid=1"
    ),
    default_post=(
        "https://webstatic.mihoyo.com/upload/op-public/2023/01/24/"
        "b74ae5e3a8e8b021b67ea26e27a215f2_184072581688764639.png"
    ),
    icon="icon-benghuai-hei",
    name=GameName(en="sr", zh="崩坏：星穹铁道"),
)


class StarRailPlugin(GamePlugin):
    game_id = "sr"
    config = CONFIG

    def extract_version(self, ann_list: AnnListRe) -> VersionInfo:
        notices = next(
            (item for item in ann_list.data.ann_types if item.type_label == "公告"),
            None,
        )
        if notices is None:
            return VersionInfo(code="0.0", name="未知", banner="", start_time=None, end_time=None)

        target_keyword = "版本更新说明"
        version_ann = next(
            (
                ann
                for ann in notices.ann_list
                if target_keyword in remove_html_tags(ann.title)
            ),
            None,
        )
        if version_ann is None:
            return VersionInfo(code="0.0", name="未知", banner="", start_time=None, end_time=None)

        floats = extract_floats(remove_html_tags(version_ann.title))
        code = str(floats[0]) if floats else "0.0"
        name = extract_inner_text(remove_html_tags(version_ann.title)) or "未知"
        start = version_ann.start_time.replace(hour=11, minute=0, second=0)
        end = version_ann.end_time.replace(hour=6, minute=0, second=0)

        next_code = next_name = next_sp_time = None

        return VersionInfo(
            code=code,
            name=name,
            banner=version_ann.banner,
            start_time=start,
            end_time=end,
            next_version_code=next_code,
            next_version_name=next_name,
            next_version_sp_time=next_sp_time,
        )

    def parse_announcements(
        self,
        *,
        version: VersionInfo,
        ann_list: AnnListRe,
        ann_content: AnnContentRe,
        existing_ids: set[int],
        display_name: str,
    ) -> list[Announcement]:
        data = ann_list.model_dump(mode="json", by_alias=True)
        content_map = {
            item.ann_id: item.model_dump(mode="json", by_alias=True)
            for item in ann_content.data.content_items
        }
        pic_content_map = {
            item.ann_id: item.model_dump(mode="json", by_alias=True)
            for item in ann_content.data.pic_list
        }
        next_version_begin = _guess_next_version_begin(
            version_begin=version.start_time,
            version_end=version.end_time,
        )
        filtered = _process_announcements(
            data=data,
            content_map=content_map,
            pic_content_map=pic_content_map,
            version_now=version.code,
            version_begin_time=version.start_time,
            next_version_begin_time=next_version_begin,
        )
        announcements: list[Announcement] = []
        for raw in filtered:
            if raw["ann_id"] in existing_ids:
                continue
            start = parse_time(raw.get("start_time")) or version.start_time
            end = parse_time(raw.get("end_time"))
            announcements.append(
                Announcement(
                    id=raw["ann_id"],
                    title=raw["title"],
                    description=raw["subtitle"],
                    game=display_name,
                    start_time=start or datetime.now(),
                    end_time=end,
                    banner=raw.get("bannerImage", ""),
                    ann_type=raw["event_type"],
                )
            )
            existing_ids.add(raw["ann_id"])
        return announcements
def _process_announcements(
    data,
    content_map,
    pic_content_map,
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    filtered_list: list[dict[str, Any]] = []
    for item in data["data"]["list"]:
        if item["type_label"] == "公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if _should_include_event(clean_title):
                    _process_event(
                        announcement,
                        ann_content,
                        version_now,
                        version_begin_time,
                        next_version_begin_time,
                    )
                    filtered_list.append(announcement)
    for item in data["data"]["pic_list"]:
        for type_item in item["type_list"]:
            for announcement in type_item["list"]:
                ann_content = pic_content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if _should_include_event(clean_title):
                    _process_pic_event(
                        announcement,
                        ann_content,
                        version_now,
                        version_begin_time,
                        next_version_begin_time,
                    )
                    filtered_list.append(announcement)
                elif "跃迁" in clean_title:
                    _process_gacha(
                        announcement,
                        ann_content,
                        version_now,
                        version_begin_time,
                        next_version_begin_time,
                    )
                    filtered_list.append(announcement)
    return filtered_list


def _should_include_event(title: str) -> bool:
    if "崩坏：星穹铁道" in title and "版本" in title:
        return True
    return "等奖励" in title  and "模拟宇宙" not in title or "位面分裂" in title or "参与活动获取" in title


def _process_event(
    announcement,
    ann_content,
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"
    start_hint = _extract_event_start_hint(ann_content["content"])
    anchor_start = _resolve_version_start_hint(
        start_hint,
        version_now,
        version_begin_time,
        next_version_begin_time,
    )
    if anchor_start is not None:
        announcement["start_time"] = anchor_start.strftime("%Y-%m-%d %H:%M:%S")
        return
    try:
        date_obj = datetime.strptime(
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass


def _process_pic_event(
    announcement,
    ann_content,
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("img", "")
    announcement["event_type"] = "event"
    start_hint = _extract_event_start_hint(ann_content["content"])
    anchor_start = _resolve_version_start_hint(
        start_hint,
        version_now,
        version_begin_time,
        next_version_begin_time,
    )
    if anchor_start is not None:
        announcement["start_time"] = anchor_start.strftime("%Y-%m-%d %H:%M:%S")
        return
    try:
        date_obj = datetime.strptime(
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass


def _process_gacha(
    announcement,
    ann_content,
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    clean_title = remove_html_tags(announcement["title"])
    clean_title = _format_gacha_title(ann_content["content"], clean_title)
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("img", "")
    announcement["event_type"] = "gacha"
    start_hint = _extract_gacha_start_hint(ann_content["content"])
    anchor_start = _resolve_version_start_hint(
        start_hint,
        version_now,
        version_begin_time,
        next_version_begin_time,
    )
    if anchor_start is not None:
        announcement["start_time"] = anchor_start.strftime("%Y-%m-%d %H:%M:%S")
        return
    try:
        date_obj = datetime.strptime(
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass


def _format_gacha_title(content: str, fallback: str) -> str:
    import re

    soup = BeautifulSoup(content, "html.parser")
    headings = soup.find_all("h1")
    names = [
        heading.get_text(strip=True)
        for heading in headings
        if "活动跃迁" in heading.get_text()
    ]
    gacha_names = [name.replace("活动跃迁", "").strip("「」") for name in names]
    role_names = list(
        dict.fromkeys(re.findall(r"限定5星角色「([^（」]+)", content))
    )
    light_cones = list(
        dict.fromkeys(re.findall(r"限定5星光锥「([^（」]+)", content))
    )
    if gacha_names or role_names or light_cones:
        joined_gacha = ", ".join(gacha_names) if gacha_names else fallback
        return (
            f"「{joined_gacha}」角色、光锥跃迁: "
            f"{', '.join(role_names + light_cones)}"
        )
    return fallback


def _extract_event_start_hint(html_content: str) -> str:
    pattern = r"<h1[^>]*>(?:活动时间|限时活动期)</h1>\s*<p[^>]*>(.*?)</p>"
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        time_info = match.group(1)
        cleaned = re.sub(r"&lt;.*?&gt;", "", time_info)
        return cleaned.split("-")[0].strip() if "-" in cleaned else cleaned
    return ""


def _extract_gacha_start_hint(html_content: str) -> str:
    matches = re.findall(r"时间为(.*?)，包含如下内容", html_content)
    if not matches:
        return ""
    time_range = re.sub(r"&lt;.*?&gt;", "", matches[0].strip())
    return time_range.split("-")[0].strip() if "-" in time_range else time_range


def _guess_next_version_begin(
    *, version_begin: datetime | None, version_end: datetime | None
) -> datetime | None:
    if isinstance(version_end, datetime):
        return version_end + timedelta(hours=5)
    _ = version_begin
    return None


def _resolve_version_start_hint(
    start_hint: str,
    version_now: str,
    version_begin_time: datetime | None,
    next_version_begin_time: datetime | None,
) -> datetime | None:
    if not start_hint:
        return None
    match = _VERSION_HINT_PATTERN.search(start_hint)
    if match is None:
        return None
    hint_code = match.group(1)
    if (
        isinstance(version_begin_time, datetime)
        and _is_same_version(hint_code, version_now)
    ):
        return version_begin_time
    if (
        isinstance(next_version_begin_time, datetime)
        and _is_future_version(hint_code, version_now)
    ):
        return next_version_begin_time
    return None


def _is_same_version(hint_code: str, version_now: str) -> bool:
    return _parse_version_number(hint_code) == _parse_version_number(version_now)


def _is_future_version(hint_code: str, version_now: str) -> bool:
    hint_num = _parse_version_number(hint_code)
    current_num = _parse_version_number(version_now)
    if hint_num is None or current_num is None:
        return False
    return hint_num > current_num


def _parse_version_number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        match = re.search(r"(\d+\.?\d*)", value or "")
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None
