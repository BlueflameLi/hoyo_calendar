"""Zenless Zone Zero specific parsing rules."""

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
        "https://announcement-api.mihoyo.com/common/nap_cn/announcement/api/"
        "getAnnList?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn"
        "&level=1&platform=pc&region=prod_gf_cn&uid=1"
    ),
    ann_content_url=(
        "https://announcement-api.mihoyo.com/common/nap_cn/announcement/api/"
        "getAnnContent?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn"
        "&level=1&platform=pc&region=prod_gf_cn&uid=1"
    ),
    default_post=(
        "https://webstatic.mihoyo.com/upload/op-public/2022/09/17/"
        "a425b5ccb44c72e342cf3a6e488dc445_771169193410538499.jpg"
    ),
    icon="icon-juequling-hei",
    name=GameName(en="zzz", zh="绝区零"),
)


class ZenlessPlugin(GamePlugin):
    game_id = "zzz"
    config = CONFIG

    def extract_version(self, ann_list: AnnListRe) -> VersionInfo:
        notices = next(
            (item for item in ann_list.data.ann_types if item.type_label == "游戏公告"),
            None,
        )
        if notices is None:
            return VersionInfo(code="0.0", name="未知", banner="", start_time=None, end_time=None)

        target_keyword = "更新说明"
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
        for item in ann_content.data.pic_list:
            content_map[item.ann_id] = item.model_dump(mode="json", by_alias=True)
        next_version_begin = _guess_next_version_begin(
            version_begin=version.start_time,
            version_end=version.end_time,
        )
        filtered = _process_announcements(
            data=data,
            content_map=content_map,
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
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    filtered_list: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    def _maybe_collect(announcement: dict[str, Any]) -> None:
        if announcement["ann_id"] in seen_ids:
            return
        ann_content = content_map.get(announcement["ann_id"])
        if ann_content is None:
            return
        clean_title = remove_html_tags(announcement["title"])
        if (
            _should_include_event(clean_title)
            and "累计登录7天" not in ann_content.get("content", "")
        ):
            _process_event(
                announcement,
                ann_content,
                version_now,
                version_begin_time,
                next_version_begin_time,
            )
            filtered_list.append(announcement)
            seen_ids.add(announcement["ann_id"])
        elif "限时频段" in clean_title:
            _process_gacha(
                announcement,
                ann_content,
                version_now,
                version_begin_time,
                next_version_begin_time,
            )
            filtered_list.append(announcement)
            seen_ids.add(announcement["ann_id"])

    for item in data["data"]["list"]:
        if item["type_id"] in [3, 4]:
            for announcement in item["list"]:
                _maybe_collect(announcement)

    for pic_group in data["data"].get("pic_list", []):
        for pic_type in pic_group.get("type_list", []):
            for announcement in pic_type.get("list", []):
                _maybe_collect(announcement)
    return filtered_list


def _should_include_event(title: str) -> bool:
    if "绝区零" in title and "版本" in title:
        return True
    return (
        "活动说明" in title
        and "全新放送" not in title
        and "『嗯呢』从天降" not in title
        and "特别访客" not in title
        and "云·绝区零" not in title
    )


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
    start_hint, end_hint = _extract_event_time_range(ann_content["content"])
    anchor_start = _resolve_version_start_hint(
        start_hint,
        version_now,
        version_begin_time,
        next_version_begin_time,
    )
    if anchor_start is not None:
        announcement["start_time"] = anchor_start.strftime("%Y-%m-%d %H:%M:%S")
        try:
            date_obj = datetime.strptime(
                extract_clean_time(end_hint), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        return

    try:
        start_dt = datetime.strptime(
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        end_dt = datetime.strptime(
            extract_clean_time(end_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        announcement["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        announcement["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
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
    clean_title = _format_gacha_title(clean_title, ann_content["content"])
    announcement["title"] = clean_title
    announcement["event_type"] = "gacha"
    banner_image = announcement.get("banner", "")
    if not banner_image:
        soup = BeautifulSoup(ann_content["content"], "html.parser")
        img_tag = soup.find("img")
        if img_tag and "src" in img_tag.attrs:
            banner_image = img_tag["src"]
    announcement["bannerImage"] = banner_image
    start_hint, end_hint = _extract_gacha_time_range(ann_content["content"])
    anchor_start = _resolve_version_start_hint(
        start_hint,
        version_now,
        version_begin_time,
        next_version_begin_time,
    )
    if anchor_start is not None:
        announcement["start_time"] = anchor_start.strftime("%Y-%m-%d %H:%M:%S")
        try:
            date_obj = datetime.strptime(
                extract_clean_time(end_hint), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        return

    try:
        start_dt = datetime.strptime(
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        end_dt = datetime.strptime(
            extract_clean_time(end_hint), "%Y/%m/%d %H:%M:%S"
        ).replace(second=0)
        announcement["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        announcement["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass


def _format_gacha_title(title: str, content: str) -> str:
    gacha_names = re.findall(r"「([^」]+)」调频活动", content)
    s_agents = re.findall(r"限定S级代理人.*?\[(.*?)\(.*?\)\]", content)
    s_weapons = re.findall(r"限定S级音擎.*?\[(.*?)\(.*?\)\]", content)
    all_names = list(dict.fromkeys(s_agents + s_weapons))
    w_engine_gacha_name = ["喧哗奏鸣", "激荡谐振", "灿烂和声"]
    gacha_names = [name for name in gacha_names if name not in w_engine_gacha_name]
    if gacha_names and all_names:
        return f"「{', '.join(gacha_names)}」代理人、音擎调频: {', '.join(all_names)}"
    return title


def _extract_event_time_range(html_content: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")
    activity_time_p = None
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(strip=True)
        if "【活动时间】" in text:
            activity_time_p = paragraph.find_next("p")
            break
    if activity_time_p:
        text = activity_time_p.get_text(strip=True)
        if "-" in text:
            start, end = text.split("-", 1)
        elif "~" in text:
            start, end = text.split("~", 1)
        else:
            return text, ""
        start = start.replace("（服务器时间）", "").strip()
        end = end.replace("（服务器时间）", "").strip()
        return start, end
    return "", ""


def _extract_gacha_time_range(html_content: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if table is None:
        return "", ""
    tbody = table.find("tbody")
    if tbody is None:
        return "", ""
    rows = tbody.find_all("tr")
    time_row = rows[1] if len(rows) > 1 else None
    if not time_row:
        return "", ""
    time_cell = time_row.find("td", {"rowspan": True})
    if not time_cell:
        return "", ""
    time_texts = [p.get_text(strip=True) for p in time_cell.find_all("p")]
    if len(time_texts) < 2:
        return "", ""
    start_time = re.sub(r"\s+", " ", time_texts[0]).strip()
    end_time = re.sub(r"\s+", " ", time_texts[-1]).strip()
    return start_time, end_time


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
    if isinstance(version_begin_time, datetime) and _is_same_version(hint_code, version_now):
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
