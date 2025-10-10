"""ICS calendar exporter for game timelines."""

from __future__ import annotations

import asyncio
import zlib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import aiofiles
import pytz
from icalendar import Calendar, Event
from loguru import logger

from models.config import GameConfig
from models.game import Announcement, GameTimeline, GameVersion

TIMEZONE = pytz.timezone("Asia/Shanghai")


class CalEvent(Event):
    def __init__(
        self,
        *,
        name: str,
        start: datetime,
        description: str,
        location: str,
        end: datetime | None = None,
    ) -> None:
        super().__init__()
        self.add("summary", name)
        self.add("dtstart", start.astimezone(TIMEZONE))
        if end is not None:
            self.add("dtend", end.astimezone(TIMEZONE))
        self.add("description", description)
        self.add("location", location)
        self.add("transp", "TRANSPARENT")
        uid = zlib.crc32(f"{name}{start.isoformat()}".encode("utf-8")) & 0xFFFFFFFF
        self.add("uid", f"{uid:08x}@hoyo_calendar")


class MyCalendar(Calendar):
    def __init__(self) -> None:
        super().__init__()
        self._events: list[Event] = []
        self.add("prodid", "-//hoyo_calendar//GitHub//CN")
        self.add("version", "2.0")
        self.add("calscale", "GREGORIAN")
        self.add("method", "PUBLISH")

    def add_event(
        self,
        *,
        name: str,
        start: datetime,
        description: str,
        location: str,
        end: datetime | None = None,
        continuous: bool = False,
    ) -> None:
        event = CalEvent(
            name=name,
            start=start,
            description=description,
            location=location,
            end=end if continuous else None,
        )
        self.add_component(event)
        self._events.append(event)
        if not continuous and end is not None:
            end_event = CalEvent(
                name=f"{name}结束",
                start=end,
                description=f"活动结束\n{description}",
                location=location,
            )
            self.add_component(end_event)
            self._events.append(end_event)

    def merge(self, other: "MyCalendar") -> None:
        for event in other._events:
            self.add_component(event)
            self._events.append(event)


async def export_ics(
    *,
    timeline: GameTimeline,
    config: GameConfig,
    base_output: Path,
    extra_outputs: Iterable[Path] = (),
) -> None:
    targets = [base_output, *extra_outputs]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)
        (target / "continuous").mkdir(parents=True, exist_ok=True)
        (target / config.display_name).mkdir(parents=True, exist_ok=True)
        (target / "continuous" / config.display_name).mkdir(parents=True, exist_ok=True)

    version_payloads = _build_version_payloads(timeline, config)

    await asyncio.gather(
        *[
            _write_calendars(target, config, version_payloads, continuous)
            for target in targets
            for continuous in (False, True)
        ]
    )


async def _write_calendars(
    target: Path,
    config: GameConfig,
    versions: list[dict],
    continuous: bool,
) -> None:
    calendars = _to_calendars(versions, config, continuous=continuous)
    all_path = target / ("continuous" if continuous else "") / f"{config.display_name}.ics"
    all_path.parent.mkdir(parents=True, exist_ok=True)
    all_calendar = calendars.pop("all")
    await _write_calendar_file(all_path, all_calendar)

    for key, calendar in calendars.items():
        subdir = target / ("continuous" if continuous else "") / config.display_name
        subdir.mkdir(parents=True, exist_ok=True)
        await _write_calendar_file(subdir / f"{key}.ics", calendar)


async def _write_calendar_file(path: Path, calendar: MyCalendar) -> None:
    async with aiofiles.open(path, "wb") as handle:
        await handle.write(calendar.to_ical())
    logger.debug("Wrote calendar {path}", path=path)


def _build_version_payloads(timeline: GameTimeline, config: GameConfig) -> list[dict]:
    payloads: list[dict] = []
    for version in timeline.version_list:
        payloads.append(
            {
                "name": version.name,
                "code": version.code,
                "banner": version.banner,
                "start": version.start_time,
                "end": version.end_time,
                "special_program": version.special_program_time,
                "announcements": version.announcements,
            }
        )
    return payloads


def _to_calendars(
    versions: list[dict],
    config: GameConfig,
    *,
    continuous: bool,
) -> dict[str, MyCalendar]:
    calendars: dict[str, MyCalendar] = defaultdict(MyCalendar)
    for version in versions:
        _append_version_events(
            calendars=calendars,
            version=version,
            config=config,
            continuous=continuous,
        )
    all_events = MyCalendar()
    for calendar in calendars.values():
        all_events.merge(calendar)
    calendars["all"] = all_events
    return calendars


def _append_version_events(
    *,
    calendars: dict[str, MyCalendar],
    version: dict[str, Any],
    config: GameConfig,
    continuous: bool,
) -> None:
    labels = config.calendar
    version_name = f"{version['code']}版本「{version['name']}」" if version["name"] else version["code"]

    if version.get("special_program") is not None:
        calendars[labels.special_program].add_event(
            name=f"{version_name}前瞻特别节目",
            start=version["special_program"],
            description=f"{version_name}前瞻特别节目",
            location=f"{config.display_name}-{labels.special_program}",
            continuous=continuous,
        )

    version_period_start = version.get("start")
    version_period_end = version.get("end")
    if version_period_start is not None and version_period_end is not None:
        calendars[labels.update].add_event(
            name=f"{version_name}版本",
            start=version_period_start,
            description=f"{version_name}版本",
            location=f"{config.display_name}-{labels.update}",
            end=version_period_end,
            continuous=continuous,
        )

    gacha_label = labels.gacha
    event_label = labels.event

    for announcement in version["announcements"]:
        if announcement.category == "gacha":
            calendars[gacha_label].add_event(
                name=announcement.title,
                start=announcement.start_time,
                description=announcement.title,
                location=f"{config.display_name}-{gacha_label}",
                end=announcement.end_time,
                continuous=continuous,
            )
        elif announcement.category == "event":
            calendars[event_label].add_event(
                name=announcement.title,
                start=announcement.start_time,
                description=announcement.title,
                location=f"{config.display_name}-{event_label}",
                end=announcement.end_time,
                continuous=continuous,
            )


