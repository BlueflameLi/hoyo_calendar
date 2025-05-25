from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from src.utils.file import JsonFile
from src.utils.data_parser.ann_info import (
    process_ys_announcements,
    process_sr_announcements,
    process_zzz_announcements,
)
from src.dto.ann_list import AnnListRe
from src.dto.ann_content import AnnContentRe


class Ann(BaseModel):
    id: int
    title: str
    description: str
    game: str
    start_time: datetime
    end_time: datetime
    banner: str
    ann_type: str


class GameVersion(BaseModel):
    name: str
    code: str
    banner: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    sp_time: Optional[datetime] = None
    ann_list: list[Ann] = []


class GameData(BaseModel):
    version_list: list[GameVersion] = []

    def set_version_info(
        self,
        version_code: str,
        name: str = "",
        banner: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sp_time: Optional[datetime] = None,
    ) -> None:
        try:
            version = next(v for v in self.version_list if v.code == version_code)
            if name:
                version.name = name
            if banner:
                version.banner = banner
            if start_time:
                version.start_time = start_time
            if end_time:
                version.end_time = end_time
            if sp_time:
                version.sp_time = sp_time
        except StopIteration:
            new_version = GameVersion(
                code=version_code,
                name=name,
                banner=banner,
                start_time=start_time,
                end_time=end_time,
                sp_time=sp_time,
            )
            self.version_list.append(new_version)

    def update_ann(
        self,
        game: str,
        version_code: str,
        version_begin_time: datetime,
        ann_list_re: AnnListRe,
        ann_content_re: AnnContentRe,
    ) -> None:
        try:
            version = next(v for v in self.version_list if v.code == version_code)
            existing_ids = [ann.id for ann in version.ann_list]
            match game:
                case "genshin":
                    version.ann_list.extend(
                        process_genshin_ann(
                            version_code,
                            version_begin_time,
                            existing_ids,
                            ann_list_re,
                            ann_content_re,
                        )
                    )
                case "sr":
                    version.ann_list.extend(
                        process_sr_ann(
                            version_code,
                            version_begin_time,
                            existing_ids,
                            ann_list_re,
                            ann_content_re,
                        )
                    )
                case "zzz":
                    version.ann_list.extend(
                        process_zzz_ann(
                            version_code,
                            version_begin_time,
                            existing_ids,
                            ann_list_re,
                            ann_content_re,
                        )
                    )
                case _:
                    logger.error(f"Unknown game {game}")
                    return
        except StopIteration:
            logger.error(f"Version {version_code} not found")


def process_genshin_ann(
    version_now: str,
    version_begin_time: datetime,
    existing_ids: list[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
) -> list[Ann]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    dict_filtered_list = process_ys_announcements(
        data=data,
        content_map=content_map,
        version_now=version_now,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    filtered_list = []
    for dict_ann in dict_filtered_list:
        if dict_ann["ann_id"] in existing_ids:
            continue
        filtered_list.append(
            Ann(
                id=dict_ann["ann_id"],
                title=dict_ann["title"],
                description=dict_ann["subtitle"],
                game="原神",
                start_time=datetime.strptime(
                    dict_ann["start_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                end_time=datetime.strptime(
                    dict_ann["end_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                banner=dict_ann["bannerImage"],
                ann_type=dict_ann["event_type"],
            )
        )
        existing_ids.append(dict_ann["ann_id"])
    return filtered_list


def process_sr_ann(
    version_now: str,
    version_begin_time: datetime,
    existing_ids: list[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
) -> list[Ann]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    pic_content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.pic_list
    }
    dict_filtered_list = process_sr_announcements(
        data=data,
        content_map=content_map,
        pic_content_map=pic_content_map,
        version_now=version_now,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    filtered_list = []
    for dict_ann in dict_filtered_list:
        if dict_ann["ann_id"] in existing_ids:
            continue
        filtered_list.append(
            Ann(
                id=dict_ann["ann_id"],
                title=dict_ann["title"],
                description=dict_ann["subtitle"],
                game="崩坏：星穹铁道",
                start_time=datetime.strptime(
                    dict_ann["start_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                end_time=datetime.strptime(
                    dict_ann["end_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                banner=dict_ann["bannerImage"],
                ann_type=dict_ann["event_type"],
            )
        )
        existing_ids.append(dict_ann["ann_id"])
    return filtered_list


def process_zzz_ann(
    version_now: str,
    version_begin_time: datetime,
    existing_ids: list[int],
    ann_list_re: AnnListRe,
    ann_content_re: AnnContentRe,
) -> list[Ann]:
    data = ann_list_re.model_dump(mode="json", by_alias=True)
    content_map = {
        item.ann_id: item.model_dump(mode="json", by_alias=True)
        for item in ann_content_re.data.content_items
    }
    dict_filtered_list = process_zzz_announcements(
        data=data,
        content_map=content_map,
        version_now=version_now,
        version_begin_time=version_begin_time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    filtered_list = []
    for dict_ann in dict_filtered_list:
        if dict_ann["ann_id"] in existing_ids:
            continue
        filtered_list.append(
            Ann(
                id=dict_ann["ann_id"],
                title=dict_ann["title"],
                description=dict_ann["subtitle"],
                game="绝区零",
                start_time=datetime.strptime(
                    dict_ann["start_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                end_time=datetime.strptime(
                    dict_ann["end_time"].replace("T", " "), "%Y-%m-%d %H:%M:%S"
                ),
                banner=dict_ann["bannerImage"],
                ann_type=dict_ann["event_type"],
            )
        )
        existing_ids.append(dict_ann["ann_id"])
    return filtered_list


async def load_game_data(output_floder: Path, game_name_cn: str) -> GameData:
    if not (output_floder / game_name_cn / "data.json").exists():
        return GameData()
    return GameData(
        **await JsonFile(output_floder / game_name_cn / "data.json").read_async()
    )


async def save_game_data(
    output_floder: Path, game_name_cn: str, game_data: GameData
) -> None:
    if not (output_floder / game_name_cn).exists():
        (output_floder / game_name_cn).mkdir(parents=True)
    await JsonFile(output_floder / game_name_cn / "data.json").write_async(
        game_data.model_dump(mode="json")
    )
