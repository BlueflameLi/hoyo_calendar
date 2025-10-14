"""Genshin Impact specific parsing rules."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup, Tag

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


_VERSION_HINT_PATTERN = re.compile(
    r"(?:「|『)?((?:\d+\.\d+)|(?:月之[一二三四五六七八九十百零〇]+))(?:」|』)?版本"
)


CONFIG = GameConfig(
    ann_list_url=(
        "https://hk4e-ann-api.mihoyo.com/common/hk4e_cn/announcement/api/"
        "getAnnList?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn"
        "&level=1&platform=pc&region=cn_gf01&uid=1"
    ),
    ann_content_url=(
        "https://hk4e-ann-api.mihoyo.com/common/hk4e_cn/announcement/api/"
        "getAnnContent?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn"
        "&level=1&platform=pc&region=cn_gf01&uid=1"
    ),
    default_post="https://ys.mihoyo.com/main/_nuxt/img/holder.37207c1.jpg",
    icon="icon-yuanshen-heng",
    name=GameName(en="genshin", zh="原神"),
)


class GenshinPlugin(GamePlugin):
    game_id = "genshin"
    config = CONFIG

    def extract_version(self, ann_list: AnnListRe) -> VersionInfo:
        notices = next(
            (item for item in ann_list.data.ann_types if item.type_label == "游戏公告"),
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

        clean_title = remove_html_tags(version_ann.title)
        code = _extract_version_code(clean_title)
        name = extract_inner_text(clean_title) or "未知"
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


def _should_include_activity(title: str) -> bool:
    if "原神" in title and "版本" in title:
        return True
    if "时限内" in title:
        return True
    excluded_keywords = [
        "魔神任务",
        "礼包",
        "纪行",
        "铸境研炼",
        "七圣召唤",
        "限时折扣",
        "首充双倍",
        "千音雅集"
    ]
    return all(keyword not in title for keyword in excluded_keywords)


def _process_announcements(
    data,
    content_map,
    version_now,
    version_begin_time,
    next_version_begin_time,
):
    filtered_list: list[dict[str, Any]] = []
    for item in data["data"]["list"]:
        if item["type_label"] == "活动公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if "时限内" in clean_title or (
                    announcement["tag_label"] == "活动"
                    and _should_include_activity(clean_title)
                ):
                    _process_event(
                        announcement,
                        ann_content,
                        version_now,
                        version_begin_time,
                        next_version_begin_time,
                    )
                    filtered_list.append(announcement)
                elif announcement["tag_label"] == "扭蛋":
                    _process_gacha(
                        announcement,
                        ann_content,
                        version_now,
                        version_begin_time,
                        next_version_begin_time,
                    )
                    filtered_list.append(announcement)
    return filtered_list


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
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M"
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
    clean_title = ann_content["title"]
    if "祈愿" in clean_title:
        if "神铸赋形" in clean_title:
            weapon_names = _extract_weapon_names(clean_title)
            clean_title = f"「神铸赋形」武器祈愿: {', '.join(weapon_names)}"
        elif "集录" in clean_title:
            clean_title = _format_collection_gacha(clean_title)
        else:
            clean_title = _format_character_gacha(clean_title)
    announcement["title"] = clean_title
    announcement["bannerImage"] = ann_content.get("banner", "")
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
            extract_clean_time(start_hint), "%Y/%m/%d %H:%M"
        ).replace(second=0)
        announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass


def _extract_event_start_hint(html_content: str) -> str:
    if "版本更新后" not in html_content:
        match = re.search(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}", html_content)
        if match:
            return match.group()
    soup = BeautifulSoup(html_content, "html.parser")
    reward_time_title = soup.find(string="〓获取奖励时限〓") or soup.find(string="〓活动时间〓")
    if reward_time_title:
        reward_time_paragraph = reward_time_title.find_next("p")
        if reward_time_paragraph:
            time_range = reward_time_paragraph.get_text()
            if "~" in time_range:
                return re.sub(r"<[^>]+>", "", time_range.split("~")[0].strip())
            return re.sub(r"<[^>]+>", "", time_range)
    return ""


def _extract_gacha_start_hint(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    td_element = soup.find("td", {"rowspan": "3"})
    if td_element is None:
        td_element = soup.find("td", {"rowspan": "5"})
        if td_element is None:
            td_element = soup.find("td", {"rowspan": "9"})
            if td_element is None:
                return ""
    time_texts: list[str] = []
    for child in td_element.children:
        if not isinstance(child, Tag):
            continue
        if child.name in {"p", "t"}:
            span = child.find("span")
            time_texts.append(span.get_text() if span else child.get_text())
    time_range = " ".join(time_texts)
    if "~" in time_range:
        return time_range.split("~")[0].strip()
    return time_range


def _extract_weapon_names(title: str) -> list[str]:
    import re

    pattern = r"「[^」]*·([^」]*)」"
    return re.findall(pattern, title)


def _format_collection_gacha(title: str) -> str:
    import re

    match = re.search(r"「([^」]+)」祈愿", title)
    if match:
        gacha_name = match.group(1)
        return f"「{gacha_name}」集录祈愿"
    return title


def _extract_version_code(title: str) -> str:
    plain_title = remove_html_tags(title)
    floats = extract_floats(plain_title)
    if floats:
        return str(floats[0])

    matches = re.findall(r"「([^」]+)」", plain_title)
    if matches:
        candidate = matches[-1].strip()
        if candidate:
            return candidate

    return "0.0"


def _format_character_gacha(title: str) -> str:
    import re

    name_match = re.search(r"·(.*)\(", title)
    gacha_match = re.search(r"「([^」]+)」祈愿", title)
    if name_match and gacha_match:
        character_name = name_match.group(1)
        gacha_name = gacha_match.group(1)
        return f"「{gacha_name}」角色祈愿: {character_name}"
    return title


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
    hint_code = _extract_version_hint_code(start_hint)
    if hint_code is None:
        return None
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


def _extract_version_hint_code(value: str) -> str | None:
    match = _VERSION_HINT_PATTERN.search(value)
    if match:
        return match.group(1)
    digits = re.search(r"(\d+\.\d+)", value)
    if digits:
        return digits.group(1)
    moon_match = re.search(r"月之[一二三四五六七八九十百零〇]+", value)
    if moon_match:
        return moon_match.group(0)
    return None


def _is_same_version(hint_code: str, version_now: str) -> bool:
    hint_num = _parse_version_number(hint_code)
    current_num = _parse_version_number(version_now)
    if hint_num is not None and current_num is not None:
        return hint_num == current_num
    return _normalize_version_code(hint_code) == _normalize_version_code(version_now)


def _is_future_version(hint_code: str, version_now: str) -> bool:
    hint_num = _parse_version_number(hint_code)
    current_num = _parse_version_number(version_now)
    if hint_num is None or current_num is None:
        return False
    return hint_num > current_num


def _parse_version_number(value: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        digits = re.search(r"(\d+\.?\d*)", value)
        if digits:
            try:
                return float(digits.group(1))
            except ValueError:
                return None
    normalized = _normalize_version_code(value)
    if normalized.startswith("月之"):
        numeral = normalized.replace("月之", "")
        number = _parse_chinese_numeral(numeral)
        if number is not None:
            return 100 + number
    return None


def _normalize_version_code(value: str | None) -> str:
    return (value or "").strip()


def _parse_chinese_numeral(text: str) -> int | None:
    if not text:
        return None
    num_map = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    unit_map = {"十": 10, "百": 100, "千": 1000}
    total = 0
    current = 0
    for char in text:
        if char in unit_map:
            multiplier = current if current > 0 else 1
            total += multiplier * unit_map[char]
            current = 0
        else:
            value = num_map.get(char)
            if value is None:
                return None
            current = current * 10 + value
    return total + current
