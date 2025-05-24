# This file contains code adapted from game-events-timeline
# Original source: https://github.com/shoyu3/game-events-timeline
# Original author: shoyu3
#
# Modifications:
# - 添加修正版本开始时间的函数
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

from datetime import datetime
from bs4 import BeautifulSoup


def remove_html_tags(text) -> str:
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text).strip()


def extract_floats(text) -> list[float]:
    float_pattern = r"-?\d+\.\d+"
    floats = re.findall(float_pattern, text)
    return [float(f) for f in floats]


def extract_inner_text(text) -> str:
    pattern = r"(?<=「)[^」]*(?=」)"
    match = re.search(pattern, text)
    if match:
        return str(match.group(0))
    else:
        return ""


def title_filter(game, title):
    games = {"ys": "原神", "sr": "崩坏：星穹铁道", "zzz": "绝区零", "ww": "鸣潮"}
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
    elif game == "ww":
        return (
            title.endswith("活动")
            and "感恩答谢" not in title
            and "签到" not in title
            and "回归" not in title
            and "数据回顾" not in title
        )
    return False


def extract_clean_time(html_time_str):
    soup = BeautifulSoup(html_time_str, "html.parser")
    clean_time_str = soup.get_text().strip()
    return clean_time_str


def correct_version_start_time(start_time: str) -> str:
    return datetime.strftime(
        datetime.strptime(
            start_time.replace("T", " "),
            "%Y-%m-%d %H:%M:%S",
        ).replace(hour=11, minute=0, second=0),
        "%Y-%m-%d %H:%M:%S",
    )
