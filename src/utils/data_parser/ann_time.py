# This file contains code adapted from game-events-timeline
# Original source: https://github.com/shoyu3/game-events-timeline
# Original author: shoyu3
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


def extract_sr_event_start_time(html_content: str) -> str:
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


def extract_sr_gacha_start_time(html_content: str) -> str:
    pattern = r"时间为(.*?)，包含如下内容"
    matches = re.findall(pattern, html_content)
    try:
        time_range = re.sub("&lt;.*?&gt;", "", matches[0].strip())
    except:
        return ""    
    if "-" in time_range:
        return time_range.split("-")[0].strip()
    return time_range


def extract_zzz_event_start_end_time(html_content: str) -> tuple[str, str]:
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


def extract_zzz_gacha_start_end_time(html_content: str) -> tuple[str, str]:
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
