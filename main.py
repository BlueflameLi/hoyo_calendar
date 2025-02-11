import asyncio
import aiofiles
import tomllib

from collections import defaultdict
from pathlib import Path
from icalendar import Calendar
from loguru import logger

from model import Version, MyCalendar


async def read_toml(toml_path: Path) -> Version:
    async with aiofiles.open(toml_path, encoding='utf-8') as toml_file:
        version_dict = tomllib.loads(await toml_file.read())
    return Version(**version_dict)


async def write_ics(ics_path: Path, calendar: Calendar) -> None:
    if not ics_path.exists():
        ics_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(ics_path, 'wb') as ics_file:
        await ics_file.write(calendar.to_ical())


def to_calendar(
        versions_data: list[Version],
        game_name: str,
        continuous: bool = False,
) -> dict[str, MyCalendar]:
    calendars: dict[str, MyCalendar] = defaultdict(MyCalendar)
    for version in versions_data:
        calendars["前瞻特别节目"].add_event(
            f"{version.version}版本「{version.name}」前瞻特别节目",
            version.special_program,
            f"{version.version}版本「{version.name}」前瞻特别节目",
            f"{game_name}-前瞻特别节目"
        )
        if version.update_time is None: continue
        calendars["版本更新"].add_event(
            f"{version.version}版本更新维护",
            version.special_program,
            f"{version.version}版本更新维护",
            f"{game_name}-版本更新"
        )
        for wish in version.wish:
            calendars[version.wish_name].add_event(
                f"{wish.type}{version.wish_name}：{wish.name}",
                wish.start,
                f"{wish.type}{version.wish_name}：{wish.describe}",
                f"{game_name}-{version.wish_name}",
                wish.end if continuous else None
            )
        for event in version.event:
            calendars[event.type].add_event(
                event.name,
                event.start,
                event.describe,
                f"{game_name}-{event.type}",
                event.end if continuous else None
            )
    all_events_cal = MyCalendar()
    for dif_calendar in calendars.values():
        all_events_cal += dif_calendar
    calendars["all"] += all_events_cal
    return calendars


async def generate_ics(
        output_folder: Path,
        game_name: str,
        versions_data: list[Version],
        continuous: bool = False,
) -> None:
    ics_path = Path(f'{output_folder}/{"continuous/" if continuous else ""}{game_name}.ics')
    logger.info(f"开始生成 {ics_path}...")
    calendars = to_calendar(versions_data, game_name, continuous=continuous)
    await write_ics(ics_path, calendars["all"])
    logger.info(f'{ics_path} DONE.')
    calendars.pop("all", None)
    for key, dif_calendar in calendars.items():
        ics_path = Path(f'{output_folder}/{"continuous/" if continuous else ""}{game_name}/{key}.ics')
        await write_ics(ics_path, dif_calendar)
        logger.info(f'{ics_path} DONE.')


async def main(source_files_folder: Path, output_folder: Path) -> None:
    ics_tasks = []
    for game_folder in source_files_folder.iterdir():  # type:Path
        if game_folder.is_dir():
            logger.info(f"开始读取「{game_folder.name}」活动信息")
            tasks = [read_toml(toml_path) for toml_path in game_folder.iterdir() if toml_path.suffix == '.toml']
            versions_data: list[Version] = await asyncio.gather(*tasks)
            logger.info(f"读取到 {len(versions_data)}个「{game_folder.name}」版本")
            ics_tasks.append(generate_ics(output_folder, game_folder.name, versions_data))
            ics_tasks.append(generate_ics(output_folder, game_folder.name, versions_data, True))
    await asyncio.gather(*ics_tasks)


if __name__ == '__main__':
    logger.add("hoyo_calendar.log", mode="w")
    source = Path('source')
    output = Path('ics')
    asyncio.run(main(source, output))
