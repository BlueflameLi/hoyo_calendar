# This file contains code adapted from game-events-timeline
# Original source: https://github.com/shoyu3/game-events-timeline
# Original author: shoyu3
#
# Modifications:
# - 对 version_begin_time 进行了修正
#
# MIT License

# Copyright (c) 2024 芍芋

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

from bs4 import BeautifulSoup
from datetime import datetime

from src.utils.txt_parser import (
    title_filter,
    remove_html_tags,
    extract_floats,
    extract_clean_time,
    correct_version_start_time,
)
from src.utils.data_parser.ann_time import (
    extract_ys_event_start_time,
    extract_ys_gacha_start_time,
    extract_sr_event_start_time,
    extract_sr_gacha_start_time,
    extract_zzz_event_start_end_time,
    extract_zzz_gacha_start_end_time,
)


def process_ys_announcements(data, content_map, version_now, version_begin_time):
    filtered_list = []

    # Process version announcements
    for item in data["data"]["list"]:
        if item["type_label"] == "游戏公告":
            for announcement in item["list"]:
                clean_title = remove_html_tags(announcement["title"])
                if "版本更新说明" in clean_title:
                    version_now = str(extract_floats(clean_title)[0])
                    announcement["title"] = "原神 " + version_now + " 版本"
                    announcement["bannerImage"] = announcement.get("banner", "")
                    announcement["event_type"] = "version"
                    announcement["start_time"] = correct_version_start_time(
                        announcement["start_time"]
                    )
                    version_begin_time = announcement["start_time"]
                    filtered_list.append(announcement)
                    break

    # Process event and gacha announcements
    for item in data["data"]["list"]:
        if item["type_label"] == "活动公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])

                if "时限内" in clean_title or (
                    announcement["tag_label"] == "活动"
                    and title_filter("ys", clean_title)
                ):
                    process_ys_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif announcement["tag_label"] == "扭蛋":
                    process_ys_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)

    return filtered_list


def process_ys_event(announcement, ann_content, version_now, version_begin_time):
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
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
        except Exception:
            pass


def process_ys_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = ann_content["title"]
    if "祈愿" in clean_title:
        if "神铸赋形" in clean_title:
            pattern = r"「[^」]*·([^」]*)」"
            weapon_names = re.findall(pattern, clean_title)
            clean_title = f"「神铸赋形」武器祈愿: {', '.join(weapon_names)}"
        elif "集录" in clean_title:
            match = re.search(r"「([^」]+)」祈愿", clean_title)
            gacha_name = match.group(1)
            clean_title = f"「{gacha_name}」集录祈愿"
        else:
            match = re.search(r"·(.*)\(", clean_title)
            character_name = match.group(1)
            match = re.search(r"「([^」]+)」祈愿", clean_title)
            gacha_name = match.group(1)
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
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
        except Exception:
            pass


def process_sr_announcements(
    data, content_map, pic_content_map, version_now, version_begin_time
):
    filtered_list = []

    # Process version announcements
    for item in data["data"]["list"]:
        if item["type_label"] == "公告":
            for announcement in item["list"]:
                clean_title = remove_html_tags(announcement["title"])
                if "版本更新说明" in clean_title:
                    version_now = str(extract_floats(clean_title)[0])
                    announcement["title"] = "崩坏：星穹铁道 " + version_now + " 版本"
                    announcement["bannerImage"] = announcement.get("banner", "")
                    announcement["event_type"] = "version"
                    announcement["start_time"] = correct_version_start_time(
                        announcement["start_time"]
                    )
                    version_begin_time = announcement["start_time"]
                    filtered_list.append(announcement)

    # Process event announcements from list
    for item in data["data"]["list"]:
        if item["type_label"] == "公告":
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if title_filter("sr", clean_title):
                    process_sr_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)

    # Process event and gacha announcements from pic_list
    for item in data["data"]["pic_list"]:
        for type_item in item["type_list"]:
            for announcement in type_item["list"]:
                ann_content = pic_content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if title_filter("sr", clean_title):
                    process_sr_pic_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif "跃迁" in clean_title:
                    process_sr_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)

    return filtered_list


def process_sr_event(announcement, ann_content, version_now, version_begin_time):
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
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
        except Exception:
            pass


def process_sr_pic_event(announcement, ann_content, version_now, version_begin_time):
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
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
        except Exception:
            pass


def process_sr_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    # Extract gacha names
    gacha_names = re.findall(
        r"<h1[^>]*>「([^」]+)」[^<]*活动跃迁</h1>", ann_content["content"]
    )
    # Filter role gacha names
    role_gacha_names = []
    for name in gacha_names:
        if "•" not in name:  # Exclude light cone gacha names
            role_gacha_names.append(name)
        elif "铭心之萃" in name:  # Special case
            role_gacha_names.append(name.split("•")[0])
    role_gacha_names = list(dict.fromkeys(role_gacha_names))

    # Extract characters and light cones
    five_star_characters = re.findall(
        r"限定5星角色「([^（」]+)", ann_content["content"]
    )
    five_star_characters = list(dict.fromkeys(five_star_characters))

    five_star_light_cones = re.findall(
        r"限定5星光锥「([^（」]+)", ann_content["content"]
    )
    five_star_light_cones = list(dict.fromkeys(five_star_light_cones))

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
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
        except Exception:
            pass


def process_zzz_announcements(data, content_map, version_now, version_begin_time):
    filtered_list = []

    # Process version announcements
    for item in data["data"]["list"]:
        if item["type_label"] == "游戏公告":
            for announcement in item["list"]:
                clean_title = remove_html_tags(announcement["title"])
                # print(clean_title)
                if "更新说明" in clean_title and "版本" in clean_title:
                    version_now = str(extract_floats(clean_title)[0])
                    announcement["title"] = "绝区零 " + version_now + " 版本"
                    announcement["bannerImage"] = announcement.get("banner", "")
                    announcement["event_type"] = "version"
                    announcement["start_time"] = correct_version_start_time(
                        announcement["start_time"]
                    )
                    version_begin_time = announcement["start_time"]
                    filtered_list.append(announcement)

    # Process event and gacha announcements
    for item in data["data"]["list"]:
        if item["type_id"] in [3, 4]:
            for announcement in item["list"]:
                ann_content = content_map[announcement["ann_id"]]
                clean_title = remove_html_tags(announcement["title"])
                if (
                    title_filter("zzz", clean_title)
                    and "累计登录7天" not in ann_content["content"]
                ):
                    process_zzz_event(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)
                elif "限时频段" in clean_title:
                    process_zzz_gacha(
                        announcement, ann_content, version_now, version_begin_time
                    )
                    filtered_list.append(announcement)

    return filtered_list


def process_zzz_event(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])
    announcement["title"] = clean_title
    announcement["bannerImage"] = announcement.get("banner", "")
    announcement["event_type"] = "event"

    ann_content_start_time, ann_content_end_time = extract_zzz_event_start_end_time(
        ann_content["content"]
    )
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_end_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["end_time"] = formatted_date
        except Exception:
            pass
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_end_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["end_time"] = formatted_date
        except Exception:
            pass


def process_zzz_gacha(announcement, ann_content, version_now, version_begin_time):
    clean_title = remove_html_tags(announcement["title"])

    # 提取所有调频活动名称（如「飞鸟坠入良夜」「『查无此人』」）
    gacha_names = re.findall(r"「([^」]+)」调频活动", ann_content["content"])

    # 提取所有S级代理人和音擎名称
    s_agents = re.findall(r"限定S级代理人.*?\[(.*?)\(.*?\)\]", ann_content["content"])
    s_weapons = re.findall(r"限定S级音擎.*?\[(.*?)\(.*?\)\]", ann_content["content"])

    # 合并所有名称
    all_names = list(dict.fromkeys(s_agents + s_weapons))
    w_engine_gacha_name = ["喧哗奏鸣", "激荡谐振", "灿烂和声"]
    gacha_names = [x for x in gacha_names if x not in w_engine_gacha_name]

    # 生成新的标题格式
    if gacha_names and all_names:
        clean_title = (
            f"「{', '.join(gacha_names)}」代理人、音擎调频: {', '.join(all_names)}"
        )
    else:
        clean_title = clean_title  # 如果提取失败，保持原样

    announcement["title"] = clean_title
    announcement["event_type"] = "gacha"

    banner_image = announcement.get("banner", "")
    if not banner_image:
        soup = BeautifulSoup(ann_content["content"], "html.parser")
        img_tag = soup.find("img")
        if img_tag and "src" in img_tag.attrs:
            banner_image = img_tag["src"]
    announcement["bannerImage"] = banner_image

    ann_content_start_time, ann_content_end_time = extract_zzz_gacha_start_end_time(
        ann_content["content"]
    )
    if f"{version_now}版本" in ann_content_start_time:
        announcement["start_time"] = version_begin_time
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_end_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["end_time"] = formatted_date
        except Exception:
            pass
    else:
        try:
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_start_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["start_time"] = formatted_date
            date_obj = datetime.strptime(
                extract_clean_time(ann_content_end_time), "%Y/%m/%d %H:%M:%S"
            ).replace(second=0)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            announcement["end_time"] = formatted_date
        except Exception:
            pass
