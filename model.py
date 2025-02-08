import pytz
from pydantic import BaseModel
from datetime import datetime

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
    update_time: datetime
    wish_name: str
    wish: list[GameEvent]
    event: list[GameEvent]


class CalEvent(Event):
    def __init__(
            self,
            name: str,
            start: datetime,
            description: str,
            location: str,
            end: datetime = None
    ):
        super().__init__()
        self.add("summary", name)
        self.add(
            "dtstart",
            start.replace(tzinfo=pytz.timezone("Asia/Shanghai")),
        )
        if end is not None:
            self.add(
                "dtend",
                end.replace(tzinfo=pytz.timezone("Asia/Shanghai")),
            )
        self.add("description", description)
        self.add("location", location)


class MyCalendar(Calendar):
    def __init__(self):
        super().__init__()
        self.events = []

    def add_event(
            self,
            name: str,
            start: datetime,
            description: str,
            location: str,
            end: datetime = None,
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
            raise TypeError("Unsupported operand type for +: 'MyCalendar' and '{}'".format(type(other).__name__))
        for event in other.events:
            self.add_component(event)
            self.events.append(event)
        return self
