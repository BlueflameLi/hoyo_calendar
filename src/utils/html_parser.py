import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime

req_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    # "Referer": "https://example.com/",  # 替换为目标网站的域名
    "Connection": "keep-alive",
}


def remove_html_tags(text):
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text).strip()


def extract_clean_time(html_time_str):
    soup = BeautifulSoup(html_time_str, "html.parser")
    clean_time_str = soup.get_text().strip()
    return clean_time_str


def extract_floats(text):
    float_pattern = r"-?\d+\.\d+"
    floats = re.findall(float_pattern, text)
    return [float(f) for f in floats]


def title_filter(game, title):
    games = {"ys": "原神", "sr": "崩坏：星穹铁道", "zzz": "绝区零"}
    if games[game] in title and "版本" in title:
        return True
    if game == "ys":
        return "时限内" in title or (
            all(
                keyword not in title
                for keyword in [
                    "魔神任务",
                    "礼包",
                    "纪行",
                    "铸境研炼",
                    "七圣召唤",
                    "限时折扣",
                ]
            )
        )
    elif game == "sr":
        return "等奖励" in title and "模拟宇宙" not in title
    elif game == "zzz":
        return (
            "活动说明" in title
            and "全新放送" not in title
            and "『嗯呢』从天降" not in title
            and "特别访客" not in title
        )
    return False


# def extract_event_start_time(html_content: str, game: str) -> str:
#     match game:
#         case "genshin":
#             return extract_ys_event_start_time(html_content)
#         case "sr":
#             return extract_sr_event_start_time(html_content)
#         case "zzz":
#             return extract_zzz_event_start_end_time(html_content)
#         case _:
#             return ""


# def extract_gacha_start_time(html_content: str, game: str) -> str:
# match game:
#     case "genshin":
#         return extract_ys_gacha_start_time(html_content)
#     case "sr":
#         return extract_sr_gacha_start_time(html_content)
#     case "zzz":
#         return extract_zzz_gacha_start_end_time(html_content)
#     case _:
#         return ""


def fetch_all_announcements(session) -> dict:
    ann_list_urls = {
        "ys": "https://hk4e-ann-api.mihoyo.com/common/hk4e_cn/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn&level=1&platform=pc&region=cn_gf01&uid=1",
        "sr": "https://hkrpg-ann-api.mihoyo.com/common/hkrpg_cn/announcement/api/getAnnList?game=hkrpg&game_biz=hkrpg_cn&lang=zh-cn&bundle_id=hkrpg_cn&level=1&platform=pc&region=prod_gf_cn&uid=1",
        "zzz": "https://announcement-api.mihoyo.com/common/nap_cn/announcement/api/getAnnList?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn&level=1&platform=pc&region=prod_gf_cn&uid=1",
    }
    ann_content_urls = {
        "ys": "https://hk4e-ann-api.mihoyo.com/common/hk4e_cn/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn&level=1&platform=pc&region=cn_gf01&uid=1",
        "sr": "https://hkrpg-ann-api.mihoyo.com/common/hkrpg_cn/announcement/api/getAnnContent?game=hkrpg&game_biz=hkrpg_cn&lang=zh-cn&bundle_id=hkrpg_cn&level=1&platform=pc&region=prod_gf_cn&uid=1",
        "zzz": "https://announcement-api.mihoyo.com/common/nap_cn/announcement/api/getAnnContent?game=nap&game_biz=nap_cn&lang=zh-cn&bundle_id=nap_cn&level=1&platform=pc&region=prod_gf_cn&uid=1",
    }

    all_announcements = {}
    for game, url in ann_list_urls.items():
        try:
            announcements = fetch_game_announcements(
                session, game, url, ann_content_urls.get(game)
            )
            if announcements:
                all_announcements[game] = announcements
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {game} announcements: {repr(e)}")

    return all_announcements


def fetch_game_announcements(session, game, list_url, content_url=None):
    version_now = "1.0"
    version_begin_time = "2024-11-01 00:00:01"
    response = session.get(list_url, timeout=(5, 30), headers=req_headers)
    response.raise_for_status()
    data = response.json()

    if game != "ww" and content_url:
        ann_content_response = session.get(
            content_url, timeout=(5, 30), headers=req_headers
        )
        ann_content_response.raise_for_status()
        ann_content_data = ann_content_response.json()
        content_map = {
            item["ann_id"]: item for item in ann_content_data["data"]["list"]
        }
        pic_content_map = {
            item["ann_id"]: item for item in ann_content_data["data"]["pic_list"]
        }
    else:
        content_map = {}
        pic_content_map = {}

    filtered_list = []

    if game == "ys":
        filtered_list = process_ys_announcements(
            data, content_map, version_now, version_begin_time
        )
    elif game == "sr":
        filtered_list = process_sr_announcements(
            data, content_map, pic_content_map, version_now, version_begin_time
        )
    elif game == "zzz":
        filtered_list = process_zzz_announcements(
            data, content_map, version_now, version_begin_time
        )

    return filtered_list


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
            clean_title = f"【神铸赋形】武器祈愿: {', '.join(weapon_names)}"
        elif "集录" in clean_title:
            match = re.search(r"「([^」]+)」祈愿", clean_title)
            gacha_name = match.group(1)
            clean_title = f"【{gacha_name}】集录祈愿"
        else:
            match = re.search(r"·(.*)\(", clean_title)
            character_name = match.group(1)
            match = re.search(r"「([^」]+)」祈愿", clean_title)
            gacha_name = match.group(1)
            clean_title = f"【{gacha_name}】角色祈愿: {character_name}"

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
        f"【{', '.join(role_gacha_names)}】角色、光锥跃迁: "
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
            f"【{', '.join(gacha_names)}】代理人、音擎调频: {', '.join(all_names)}"
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


def extract_ys_event_start_time(html_content: str) -> str:
    if "版本更新后" not in html_content:
        pattern = r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}"
        match = re.search(pattern, html_content)
        if match:
            first_datetime = match.group()
            return first_datetime
    soup = BeautifulSoup(html_content, "html.parser")
    reward_time_title = soup.find(string="〓获取奖励时限〓") or soup.find(
        string="〓活动时间〓"
    )
    if reward_time_title:
        reward_time_paragraph = reward_time_title.find_next("p")
        if reward_time_paragraph:
            time_range = reward_time_paragraph.get_text()
            if "~" in time_range:
                text = re.sub("<[^>]+>", "", time_range.split("~")[0].strip())
                return text
            return re.sub("<[^>]+>", "", time_range)
    return ""


def extract_ys_gacha_start_time(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    td_element = soup.find("td", {"rowspan": "3"})
    if td_element is None:
        td_element = soup.find("td", {"rowspan": "5"})
        if td_element is None:
            td_element = soup.find("td", {"rowspan": "9"})
            if td_element is None:
                return ""
            # raise Exception(str(html_content))
    time_texts = []
    for child in td_element.children:
        if child.name == "p":
            span = child.find("span")
            if span:
                time_texts.append(span.get_text())
            else:
                time_texts.append(child.get_text())
        elif child.name == "t":
            span = child.find("span")
            if span:
                time_texts.append(span.get_text())
            else:
                time_texts.append(child.get_text())
    time_range = " ".join(time_texts)
    # print(time_range)
    if "~" in time_range:
        return time_range.split("~")[0].strip()
    return time_range


def extract_sr_event_start_time(html_content):
    pattern = r"<h1[^>]*>(?:活动时间|限时活动期)</h1>\s*<p[^>]*>(.*?)</p>"
    match = re.search(pattern, html_content, re.DOTALL)
    # logging.info(f'{pattern} {html_content} {match}')

    if match:
        time_info = match.group(1)
        cleaned_time_info = re.sub("&lt;.*?&gt;", "", time_info)
        if "-" in cleaned_time_info:
            return cleaned_time_info.split("-")[0].strip()
        return cleaned_time_info
    else:
        return ""


def extract_sr_gacha_start_time(html_content):
    pattern = r"时间为(.*?)，包含如下内容"
    matches = re.findall(pattern, html_content)
    time_range = re.sub("&lt;.*?&gt;", "", matches[0].strip())
    if "-" in time_range:
        return time_range.split("-")[0].strip()
    return time_range


def extract_zzz_event_start_end_time(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    activity_time_label = soup.find(
        "p", string=lambda text: text and "【活动时间】" in text
    )

    if activity_time_label:
        activity_time_p = activity_time_label.find_next("p")
        if activity_time_p:
            activity_time_text = activity_time_p.get_text(strip=True)
            # 处理分隔符（支持 - 或 ~）
            if "-" in activity_time_text:
                start, end = activity_time_text.split("-", 1)
            elif "~" in activity_time_text:
                start, end = activity_time_text.split("~", 1)
            else:
                return activity_time_text, ""  # 返回默认值

            # 清理时间字符串
            start = start.replace("（服务器时间）", "").strip()
            end = end.replace("（服务器时间）", "").strip()
            return start, end

    return "", ""


def extract_zzz_gacha_start_end_time(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if table is None:
        raise Exception(html_content)

    tbody = table.find("tbody")
    rows = tbody.find_all("tr")

    # 查找包含时间的行（通常是第一个 <tr> 之后的 <tr>）
    time_row = rows[1] if len(rows) > 1 else None
    if not time_row:
        return "", ""

    # 查找包含时间的单元格（通常是带有 rowspan 的 <td>）
    time_cell = time_row.find("td", {"rowspan": True})
    if not time_cell:
        return "", ""

    # 提取所有时间文本（可能包含多个活动的开始和结束时间）
    time_texts = [p.get_text(strip=True) for p in time_cell.find_all("p")]

    # 如果没有足够的时间信息，返回空字符串
    if len(time_texts) < 2:
        return "", ""

    # 提取第一个活动的时间（通常是第一个 <p>）
    start_time = time_texts[0]

    # 尝试提取结束时间（可能是最后一个 <p> 或倒数第二个 <p>）
    end_time = time_texts[-1] if len(time_texts) >= 2 else ""

    # 清理时间格式（去除多余的空格和换行）
    start_time = re.sub(r"\s+", " ", start_time).strip()
    end_time = re.sub(r"\s+", " ", end_time).strip()

    return start_time, end_time
