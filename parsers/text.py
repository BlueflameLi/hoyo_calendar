"""Utility helpers for parsing announcement HTML/text content."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup


def remove_html_tags(text: str) -> str:
    clean = re.compile(r"<.*?>")
    return re.sub(clean, "", text).strip()


def extract_floats(text: str) -> list[float]:
    float_pattern = r"-?\d+\.\d+"
    floats = re.findall(float_pattern, text)
    return [float(value) for value in floats]


def extract_inner_text(text: str) -> str:
    match = re.search(r"(?<=「)[^」]*(?=」)", text)
    return match.group(0) if match else ""
 

def extract_clean_time(html_time_str: str) -> str:
    soup = BeautifulSoup(html_time_str, "html.parser")
    return soup.get_text().strip()


def correct_version_start_time(start_time: str) -> str:
    value = datetime.strptime(start_time.replace("T", " "), "%Y-%m-%d %H:%M:%S")
    return datetime.strftime(value.replace(hour=11, minute=0, second=0), "%Y-%m-%d %H:%M:%S")
