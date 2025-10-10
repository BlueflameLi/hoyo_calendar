"""Helpers to extract structured time information from announcement HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def extract_ys_event_start_time(html_content: str) -> str:
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


def extract_ys_gacha_start_time(html_content: str) -> str:
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
        if getattr(child, "name", None) == "p":
            span = child.find("span")
            time_texts.append(span.get_text() if span else child.get_text())
        elif getattr(child, "name", None) == "t":
            span = child.find("span")
            time_texts.append(span.get_text() if span else child.get_text())
    time_range = " ".join(time_texts)
    if "~" in time_range:
        return time_range.split("~")[0].strip()
    return time_range


def extract_sr_event_start_time(html_content: str) -> str:
    pattern = r"<h1[^>]*>(?:活动时间|限时活动期)</h1>\s*<p[^>]*>(.*?)</p>"
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        time_info = match.group(1)
        cleaned = re.sub(r"&lt;.*?&gt;", "", time_info)
        return cleaned.split("-")[0].strip() if "-" in cleaned else cleaned
    return ""


def extract_sr_gacha_start_time(html_content: str) -> str:
    matches = re.findall(r"时间为(.*?)，包含如下内容", html_content)
    if not matches:
        return ""
    time_range = re.sub(r"&lt;.*?&gt;", "", matches[0].strip())
    return time_range.split("-")[0].strip() if "-" in time_range else time_range


def extract_zzz_event_start_end_time(html_content: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_content, "html.parser")
    activity_time_label = soup.find("p", string=lambda text: text and "【活动时间】" in text)
    if activity_time_label:
        activity_time_p = activity_time_label.find_next("p")
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


def extract_zzz_gacha_start_end_time(html_content: str) -> tuple[str, str]:
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
