import pytz
import zlib
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from icalendar import Calendar, Event


class GameEvent(BaseModel):
    type: str
    name: str
    start: datetime
    end: datetime
    describe: str


class Version(BaseModel):
    name: str
    version: str
    special_program: datetime
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
        end: datetime | None = None,
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
            f"{(zlib.crc32((name+start.isoformat()).encode('utf-8')) & 0xFFFFFFFF):08x}@trrw.tech",
        )


class MyCalendar(Calendar):
    def __init__(self):
        super().__init__()
        self.events = []  # type: ignore
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
        self.events.append(event)
        if not continuous and end is not None:
            end_event = CalEvent(
                f"{name}结束",
                end,
                f"活动结束\n{description}",
                location,
            )
            self.add_component(end_event)
            self.events.append(end_event)

    def __add__(self, other):
        if not isinstance(other, MyCalendar):
            raise TypeError(
                "Unsupported operand type for +: 'MyCalendar' and '{}'".format(
                    type(other).__name__
                )
            )
        for event in other.events:
            self.add_component(event)
            self.events.append(event)
        return self
