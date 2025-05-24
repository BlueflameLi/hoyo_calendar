import pytz
import zlib

from loguru import logger
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from icalendar import Calendar, Event
from collections import defaultdict

from src.utils.data import GameData
from src.utils.file import ICS_File


class GameEvent(BaseModel):
    type: str
    name: str
    start: datetime
    end: datetime
    describe: str


class Version(BaseModel):
    name: str
    version: str
    special_program: Optional[datetime] = None
    update_time: Optional[datetime] = None
    wish_name: str
    wish: Optional[list[GameEvent]] = None
    event: Optional[list[GameEvent]] = None


class CalEvent(Event):
    def __init__(
        self,
        name: str,
        start: datetime,
        description: str,
        location: str,
        end: Optional[datetime] = None,
        continuous: bool = False,
    ):
        super().__init__()
        self.add("summary", name)
        self.add(
            "dtstart",
            start.replace(tzinfo=pytz.timezone("Asia/Shanghai")),
        )
        if not continuous and end is not None:
            self.add(
                "dtend",
                end.replace(tzinfo=pytz.timezone("Asia/Shanghai")),
            )
        self.add("description", description)
        self.add("location", location)
        self.add("transp", "TRANSPARENT")
        self.add(
            "uid",
            f"{(zlib.crc32((name + start.isoformat()).encode('utf-8')) & 0xFFFFFFFF):08x}@trrw.tech",
        )


class MyCalendar(Calendar):
    def __init__(self):
        super().__init__()
        self._my_events = []
        self.init_cal()

    def init_cal(self):
        self.add("prodid", "-//Trrrrw/hoyo_calendar//GitHub/CN")
        self.add("version", "2.0")
        self.add("calscale", "GREGORIAN")
        self.add("method", "PUBLISH")

    def add_event(
        self,
        name: str,
        start: datetime,
        description: str,
        location: str,
        end: datetime | None = None,
        continuous: bool = False,
    ) -> None:
        event = CalEvent(
            name,
            start,
            description,
            location,
            end if continuous else None,
        )
        self.add_component(event)
        self._my_events.append(event)
        if not continuous and end is not None:
            end_event = CalEvent(
                f"{name}结束",
                end,
                f"活动结束\n{description}",
                location,
            )
            self.add_component(end_event)
            self._my_events.append(end_event)

    def __add__(self, other):
        if not isinstance(other, MyCalendar):
            raise TypeError(
                "Unsupported operand type for +: 'MyCalendar' and '{}'".format(
                    type(other).__name__
                )
            )
        for event in other._my_events:
            self.add_component(event)
            self._my_events.append(event)
        return self


async def export_ics(data: GameData, game: str, ics_folder: Path) -> None:
    if not ics_folder.exists():
        ics_folder.mkdir(parents=True)
    wish_names = {"原神": "祈愿", "崩坏：星穹铁道": "活动跃迁", "绝区零": "调频"}
    versions_data = []
    for version in data.version_list:
        start_time = version.start_time
        update_time = start_time.replace(hour=6) if start_time is not None else None
        wish = [
            GameEvent(
                type=wish_names[game],
                name=ann.title,
                start=ann.start_time,
                end=ann.end_time,
                describe=ann.description,
            )
            for ann in version.ann_list
            if ann.ann_type == "gacha"
        ]
        event = [
            GameEvent(
                type="活动",
                name=ann.title,
                start=ann.start_time,
                end=ann.end_time,
                describe=ann.description,
            )
            for ann in version.ann_list
            if ann.ann_type == "event"
        ]
        versions_data.append(
            Version(
                name=version.name,
                version=version.code,
                special_program=version.sp_time,
                update_time=update_time,
                wish_name=wish_names[game],
                wish=wish,
                event=event,
            )
        )
    await generate_ics(ics_folder, game, versions_data, continuous=False)
    await generate_ics(ics_folder, game, versions_data, continuous=True)


async def generate_ics(
    output_folder: Path,
    game_name: str,
    versions_data: list[Version],
    continuous: bool = False,
) -> None:
    ics_path = Path(
        f"{output_folder}/{'continuous/' if continuous else ''}{game_name}.ics"
    )
    calendars = to_calendar(versions_data, game_name, continuous=continuous)
    await ICS_File(ics_path).write_async(calendars["all"])
    calendars.pop("all", None)
    for key, dif_calendar in calendars.items():
        ics_path = Path(
            f"{output_folder}/{'continuous/' if continuous else ''}{game_name}/{key}.ics"
        )
        await ICS_File(ics_path).write_async(dif_calendar)


def to_calendar(
    versions_data: list[Version],
    game_name: str,
    continuous: bool = False,
) -> dict[str, MyCalendar]:
    calendars: dict[str, MyCalendar] = defaultdict(MyCalendar)
    for version in versions_data:
        if version.special_program is not None:
            calendars["前瞻特别节目"].add_event(
                f"{version.version}版本「{version.name}」前瞻特别节目",
                version.special_program,
                f"{version.version}版本「{version.name}」前瞻特别节目",
                f"{game_name}-前瞻特别节目",
            )
        if version.update_time is not None:
            calendars["版本更新"].add_event(
                f"{version.version}版本更新维护",
                version.update_time,
                f"{version.version}版本更新维护",
                f"{game_name}-版本更新",
                version.update_time + timedelta(hours=5),
                continuous=True,
            )
        if version.wish is not None:
            for wish in version.wish:
                calendars[version.wish_name].add_event(
                    f"{wish.type}{version.wish_name}：{wish.name}",
                    wish.start,
                    f"{wish.type}{version.wish_name}：{wish.describe}",
                    f"{game_name}-{version.wish_name}",
                    wish.end,
                    continuous=continuous,
                )
        if version.event is not None:
            for event in version.event:
                calendars[event.type].add_event(
                    event.name,
                    event.start,
                    event.describe,
                    f"{game_name}-{event.type}",
                    event.end,
                    continuous=continuous,
                )
    all_events_cal = MyCalendar()
    for dif_calendar in calendars.values():
        all_events_cal += dif_calendar
    calendars["all"] += all_events_cal
    return calendars
