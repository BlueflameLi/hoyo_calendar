"""Domain models representing game timelines and announcements."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field


class Announcement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str
    game: str
    start_time: datetime
    end_time: datetime | None = None
    banner: str = ""
    category: str = Field(alias="ann_type")


class GameVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    code: str
    banner: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    special_program_time: Optional[datetime] = Field(default=None, alias="sp_time")
    announcements: list[Announcement] = Field(default_factory=list, alias="ann_list")

    def upsert_announcement(self, announcement: Announcement) -> None:
        if any(item.id == announcement.id for item in self.announcements):
            return
        self.announcements.append(announcement)

    def replace_announcements(self, announcements: Iterable[Announcement]) -> None:
        self.announcements = list(announcements)


class GameTimeline(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    version_list: list[GameVersion] = Field(default_factory=list)

    def find_version(
        self,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> GameVersion | None:
        if name:
            for version in self.version_list:
                if version.name == name:
                    return version
        if code:
            for version in self.version_list:
                if version.code == code:
                    return version
        return None

    def upsert_version(
        self,
        *,
        code: str,
        name: str = "",
        banner: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        special_program_time: Optional[datetime] = None,
    ) -> GameVersion:
        version = self.find_version(code=code, name=name)
        if version is None:
            version = GameVersion(
                code=code,
                name=name,
                banner=banner,
                start_time=start_time,
                end_time=end_time,
                special_program_time=special_program_time,
            )
            self.version_list.append(version)
            return version
        if code:
            version.code = code
        if name:
            version.name = name
        if banner:
            version.banner = banner
        if start_time:
            version.start_time = start_time
        if end_time:
            version.end_time = end_time

        version.special_program_time = special_program_time
        return version

    def inject_announcements(
        self,
        code: str,
        announcements: Iterable[Announcement],
        replace: bool = False,
    ) -> None:
        version = self.upsert_version(code=code)
        if replace:
            version.replace_announcements(announcements)
            return
        for announcement in announcements:
            version.upsert_announcement(announcement)
