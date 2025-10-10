"""Game-specific announcement parsers."""

from __future__ import annotations

import re
from datetime import datetime
from bs4 import BeautifulSoup

from dto import AnnContentRe, AnnListRe
from models.game import Announcement

from .text import (
    extract_clean_time,
    extract_floats,
    remove_html_tags,
)
from .time_extractors import (
    extract_sr_event_start_time,
    extract_sr_gacha_start_time,
    extract_ys_event_start_time,
    extract_ys_gacha_start_time,
    extract_zzz_event_start_end_time,
    extract_zzz_gacha_start_end_time,
)


def parse_genshin_announcements(
    *,
    version_code: str,
    version_begin_time: datetime,
    existing_ids: set[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
    game_display_name: str,
) -> list[Announcement]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    filtered = _process_ys_announcements(
        data=data,
        content_map=content_map,
        version_now=version_code,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    announcements: list[Announcement] = []
    for raw in filtered:
        if raw["ann_id"] in existing_ids:
            continue
        start = _parse_time(raw.get("start_time")) or version_begin_time
        end = _parse_time(raw.get("end_time"))
        announcements.append(
            Announcement(
                id=raw["ann_id"],
                title=raw["title"],
                description=raw["subtitle"],
                game=game_display_name,
                start_time=start,
                end_time=end,
                banner=raw.get("bannerImage", ""),
                ann_type=raw["event_type"],
            )
        )
        existing_ids.add(raw["ann_id"])
    return announcements


def parse_starrail_announcements(
    *,
    version_code: str,
    version_begin_time: datetime,
    existing_ids: set[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
    game_display_name: str,
) -> list[Announcement]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    pic_content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.pic_list
    }
    filtered = _process_sr_announcements(
        data=data,
        content_map=content_map,
        pic_content_map=pic_content_map,
        version_now=version_code,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    announcements: list[Announcement] = []
    for raw in filtered:
        if raw["ann_id"] in existing_ids:
            continue
        start = _parse_time(raw.get("start_time")) or version_begin_time
        end = _parse_time(raw.get("end_time"))
        announcements.append(
            Announcement(
                id=raw["ann_id"],
                title=raw["title"],
                description=raw["subtitle"],
                game=game_display_name,
                start_time=start,
                end_time=end,
                banner=raw.get("bannerImage", ""),
                ann_type=raw["event_type"],
            )
        )
        existing_ids.add(raw["ann_id"])
    return announcements


def parse_zenless_announcements(
    *,
    version_code: str,
    version_begin_time: datetime,
    existing_ids: set[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
    game_display_name: str,
) -> list[Announcement]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    filtered = _process_zzz_announcements(
        data=data,
        content_map=content_map,
        version_now=version_code,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    announcements: list[Announcement] = []
    for raw in filtered:
        if raw["ann_id"] in existing_ids:
            continue
        start = _parse_time(raw.get("start_time")) or version_begin_time
        end = _parse_time(raw.get("end_time"))
        announcements.append(
            Announcement(
                id=raw["ann_id"],
                title=raw["title"],
                description=raw["subtitle"],
                game=game_display_name,
                start_time=start,
                end_time=end,
                banner=raw.get("bannerImage", ""),
                ann_type=raw["event_type"],
            )
        )
        existing_ids.add(raw["ann_id"])
    return announcements


# ---- Below: adapted helpers from the original project ----------------------------------


def _should_include_genshin(title: str) -> bool:
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


def _should_include_star_rail(title: str) -> bool:
    if "崩坏：星穹铁道" in title and "版本" in title:
        return True
    return "等奖励" in title and "模拟宇宙" not in title


def _should_include_zenless(title: str) -> bool:
    if "绝区零" in title and "版本" in title:
        return True
    return (
        "活动说明" in title
        and "全新放送" not in title
        and "『嗯呢』从天降" not in title
        and "特别访客" not in title
    )


def _process_ys_announcements(data, content_map, version_now, version_begin_time):
    filtered_list: list[dict] = []
    for item in data["data"]["list"]:
        if item["type_label"] == "活动公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if "时限内" in clean_title or (
                    announcement["tag_label"] == "活动"
                    and _should_include_genshin(clean_title)
                ):
                    _process_ys_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif announcement["tag_label"] == "扭蛋":
                    _process_ys_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
    return filtered_list


def _process_ys_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"
    ann_content_start_time = extract_ys_event_start_time(ann_content["content"])
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_ys_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = ann_content["title"]
    if "祈愿" in clean_title:
        if "神铸赋形" in clean_title:
            pattern = r"「[^」]*·([^」]*)」"
            weapon_names = re.findall(pattern, clean_title)
            clean_title = f"「神铸赋形」武器祈愿: {', '.join(weapon_names)}"
        elif "集录" in clean_title:
            match = re.search(r"「([^」]+)」祈愿", clean_title)
            if match:
                gacha_name = match.group(1)
                clean_title = f"「{gacha_name}」集录祈愿"
        else:
            match = re.search(r"·(.*)\(", clean_title)
            if match:
                character_name = match.group(1)
                gacha_match = re.search(r"「([^」]+)」祈愿", clean_title)
                if gacha_match:
                    gacha_name = gacha_match.group(1)
                    clean_title = f"「{gacha_name}」角色祈愿: {character_name}"
    announcement["title"] = clean_title
    announcement["bannerImage"] = ann_content.get("banner", "")
    announcement["event_type"] = "gacha"
    ann_content_start_time = extract_ys_gacha_start_time(ann_content["content"])
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_sr_announcements(
    data,
    content_map,
    pic_content_map,
    version_now,
    version_begin_time,
):
    filtered_list: list[dict] = []
    for item in data["data"]["list"]:
        if item["type_label"] == "公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if _should_include_star_rail(clean_title):
                    _process_sr_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
    for item in data["data"]["pic_list"]:
        for type_item in item["type_list"]:
            for announcement in type_item["list"]:
                ann_content = pic_content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if _should_include_star_rail(clean_title):
                    _process_sr_pic_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif "跃迁" in clean_title:
                    _process_sr_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
    return filtered_list


def _process_sr_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"
    ann_content_start_time = extract_sr_event_start_time(ann_content["content"])
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_sr_pic_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("img", "")
    announcement["event_type"] = "event"
    ann_content_start_time = extract_sr_event_start_time(ann_content["content"])
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_sr_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    gacha_names = re.findall(r"<h1[^>]*>「([^」]+)」[^<]*活动跃迁</h1>", ann_content["content"])
    role_gacha_names: list[str] = []
    for name in gacha_names:
        if "•" not in name:
            role_gacha_names.append(name)
        elif "铭心之萃" in name:
            role_gacha_names.append(name.split("•")[0])
    role_gacha_names = list(dict.fromkeys(role_gacha_names))
    five_star_characters = list(
        dict.fromkeys(re.findall(r"限定5星角色「([^（」]+)", ann_content["content"]))
    )
    five_star_light_cones = list(
        dict.fromkeys(re.findall(r"限定5星光锥「([^（」]+)", ann_content["content"]))
    )
    clean_title = (
        f"「{', '.join(role_gacha_names)}」角色、光锥跃迁: "
        f"{', '.join(five_star_characters + five_star_light_cones)}"
    )
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("img", "")
    announcement["event_type"] = "gacha"
    ann_content_start_time = extract_sr_gacha_start_time(ann_content["content"])
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["start_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_zzz_announcements(data, content_map, version_now, version_begin_time):
    filtered_list: list[dict] = []
    for item in data["data"]["list"]:
        if item["type_id"] in [3, 4]:
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if (
                    _should_include_zenless(clean_title)
                    and "累计登录7天" not in ann_content["content"]
                ):
                    _process_zzz_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif "限时频段" in clean_title:
                    _process_zzz_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
    return filtered_list


def _process_zzz_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"
    start_time_raw, end_time_raw = extract_zzz_event_start_end_time(
        ann_content["content"]
    )
    if f"{version_now}版本" in start_time_raw:
        announcement["start_time"] = version_begin_time
        try:
            date_obj = datetime.strptime(
                extract_clean_time(end_time_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    else:
        try:
            start_dt = datetime.strptime(
                extract_clean_time(start_time_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(
                extract_clean_time(end_time_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _process_zzz_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    gacha_names = re.findall(r"「([^」]+)」调频活动", ann_content["content"])
    s_agents = re.findall(r"限定S级代理人.*?\[(.*?)\(.*?\)\]", ann_content["content"])
    s_weapons = re.findall(r"限定S级音擎.*?\[(.*?)\(.*?\)\]", ann_content["content"])
    all_names = list(dict.fromkeys(s_agents + s_weapons))
    w_engine_gacha_name = ["喧哗奏鸣", "激荡谐振", "灿烂和声"]
    gacha_names = [name for name in gacha_names if name not in w_engine_gacha_name]
    if gacha_names and all_names:
        clean_title = (
            f"「{', '.join(gacha_names)}」代理人、音擎调频: {', '.join(all_names)}"
        )
    announcement["title"] = clean_title
    announcement["event_type"] = "gacha"
    banner_image = announcement.get("banner", "")
    if not banner_image:
        soup = BeautifulSoup(ann_content["content"], "html.parser")
        img_tag = soup.find("img")
        if img_tag and "src" in img_tag.attrs:
            banner_image = img_tag["src"]
    announcement["bannerImage"] = banner_image
    start_raw, end_raw = extract_zzz_gacha_start_end_time(ann_content["content"])
    if f"{version_now}版本" in start_raw:
        announcement["start_time"] = version_begin_time
        try:
            end_dt = datetime.strptime(
                extract_clean_time(end_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    else:
        try:
            start_dt = datetime.strptime(
                extract_clean_time(start_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["start_time"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(
                extract_clean_time(end_raw), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            announcement["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass


def _parse_time(value: str | None) -> datetime | None:
    if value in (None, ""):
        return None
    value = value.replace("T", " ")
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
