"""Helpers for retrieving special program livestream information."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import pytz

from clients.miyoushe import MiyousheClient
from parsers.text import extract_floats, extract_inner_text, remove_html_tags

_TZ = pytz.timezone("Asia/Shanghai")
_KEYWORD = "前瞻特别节目预告"


@dataclass(frozen=True)
class SpecialProgramSource:
    gids: int
    type_id: int
    page_size: int = 20


@dataclass(frozen=True)
class SpecialProgramInfo:
    code: Optional[str]
    name: Optional[str]
    start_time: Optional[datetime]


_SOURCES = {
    "genshin": SpecialProgramSource(gids=2, type_id=2),
    "sr": SpecialProgramSource(gids=6, type_id=2),
    "zzz": SpecialProgramSource(gids=8, type_id=3, page_size=40),
}

_TIME_PATTERN = re.compile(
    r"(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日(?:[^\d]|\s)*(?P<hour>\d{1,2}):(?P<minute>\d{2})"
)


async def fetch_special_program_info(
    client: MiyousheClient,
    *,
    game_id: str,
) -> Optional[SpecialProgramInfo]:
    """Return metadata for the latest special program livestream if available."""

    source = _SOURCES.get(game_id)
    if source is None:
        return None

    news_payload = await client.fetch_news_list(
        gids=source.gids,
        type_id=source.type_id,
        page_size=source.page_size,
    )
    if news_payload.get("retcode") not in (0, None):
        return None
    posts = (news_payload.get("data") or {}).get("list") or []

    for entry in posts:
        post_info = entry.get("post") or {}
        subject = post_info.get("subject", "")
        if _KEYWORD not in subject:
            continue

        post_id = post_info.get("post_id")
        if not post_id:
            continue

        anchor_time = _convert_timestamp(post_info.get("created_at"))
        code, name = _extract_title_metadata(subject)

        detail_payload = await client.fetch_post_detail(gids=source.gids, post_id=str(post_id))
        if detail_payload.get("retcode") not in (0, None):
            continue
        start_time = _extract_time_from_detail(detail_payload, anchor_time)
        if start_time is None:
            continue

        return SpecialProgramInfo(code=code, name=name, start_time=start_time)

    return None


def _convert_timestamp(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(timestamp, tz=_TZ)


def _extract_time_from_detail(detail_payload: dict[str, Any], anchor: Optional[datetime]) -> Optional[datetime]:
    post_data = (detail_payload.get("data") or {}).get("post") or {}
    post_meta = post_data.get("post") or {}
    created_at = post_meta.get("created_at")

    base_time = anchor
    if base_time is None and created_at:
        try:
            base_time = datetime.fromtimestamp(int(created_at), tz=_TZ)
        except (TypeError, ValueError):
            base_time = None

    content = post_meta.get("content") or ""
    structured = post_meta.get("structured_content") or ""
    text_content = remove_html_tags(content) + " " + remove_html_tags(structured)

    match = _TIME_PATTERN.search(text_content)
    if not match:
        return None

    try:
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
    except (TypeError, ValueError):
        return None

    if base_time is None:
        now = datetime.now(_TZ)
        year = now.year
        try:
            candidate = _TZ.localize(datetime(year, month, day, hour, minute, 0, 0))
        except ValueError:
            return None
        if candidate < now - timedelta(days=180):
            try:
                candidate = candidate.replace(year=candidate.year + 1)
            except ValueError:
                return None
        elif candidate > now + timedelta(days=180):
            try:
                candidate = candidate.replace(year=candidate.year - 1)
            except ValueError:
                return None
        return candidate

    try:
        candidate = base_time.replace(
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None

    # Handle year rollover (e.g. announcement at year end for next-year stream).
    if candidate < base_time - timedelta(days=180):
        try:
            candidate = candidate.replace(year=candidate.year + 1)
        except ValueError:
            return None
    elif candidate > base_time + timedelta(days=180):
        try:
            candidate = candidate.replace(year=candidate.year - 1)
        except ValueError:
            return None

    return candidate


def _extract_title_metadata(subject: str) -> tuple[Optional[str], Optional[str]]:
    clean_subject = remove_html_tags(subject)
    floats = extract_floats(clean_subject)
    code = str(floats[0]) if floats else None

    name_match = re.findall(r"「([^」]+)」", clean_subject)
    if name_match:
        name = name_match[-1].strip() or None
    else:
        inner_text = extract_inner_text(clean_subject) or clean_subject.strip()
        name = inner_text or None

    return code, name
