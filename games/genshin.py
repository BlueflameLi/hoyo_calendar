"""Genshin Impact specific parsing rules."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

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
from parsers.time_extractors import (
    extract_ys_event_start_time,
    extract_ys_gacha_start_time,
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

        next_version_ann = _find_special_program(ann_list)
        if next_version_ann:
            next_clean_title = remove_html_tags(next_version_ann.title)
            next_code = _extract_version_code(next_clean_title)
            if next_code == "0.0":
                next_code = None
            next_name = extract_inner_text(next_clean_title) or None
            next_sp_time = next_version_ann.end_time
        else:
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
        filtered = _process_announcements(
            data=data,
            content_map=content_map,
            version_now=version.code,
            version_begin_time=version.start_time,
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


def _find_special_program(ann_list: AnnListRe):
    notices = next(
        (item for item in ann_list.data.ann_types if item.type_label == "活动公告"),
        None,
    )
    if notices is None:
        return None
    for ann in notices.ann_list:
        if "前瞻特别节目" in remove_html_tags(ann.title):
            return ann
    return None


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
    ]
    return all(keyword not in title for keyword in excluded_keywords)


def _process_announcements(data, content_map, version_now, version_begin_time):
    filtered_list: list[dict[str, Any]] = []
    begin_time_str = (
        version_begin_time.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(version_begin_time, datetime)
        else ""
    )
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
                        announcement, ann_content, version_now, begin_time_str
                    )
                    filtered_list.append(announcement)
                elif announcement["tag_label"] == "扭蛋":
                    _process_gacha(
                        announcement, ann_content, version_now, begin_time_str
                    )
                    filtered_list.append(announcement)
    return filtered_list


def _process_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"
    start_hint = extract_ys_event_start_time(ann_content["content"])
    if f"{version_now}版本" in start_hint:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(start_hint), "%Y/%m/%d %H:%M"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_gacha(announcement, ann_content, version_now, version_begin_time):
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
    start_hint = extract_ys_gacha_start_time(ann_content["content"])
    if f"{version_now}版本" in start_hint:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(start_hint), "%Y/%m/%d %H:%M"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


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
