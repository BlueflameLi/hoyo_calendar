"""Main orchestrator for the hoyo_calendar data pipeline."""

from __future__ import annotations

import asyncio
from copy import deepcopy

from loguru import logger

from clients import HoyolabClient, MiyousheClient
from games import get_plugin, load_game_configs
from models.config import GameConfig
from exporters.ics import export_ics
from . import storage
from settings import Settings, get_settings
from utils.logging import configure_logging
from .special_program import fetch_special_program_info


async def run_pipeline(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    configure_logging()

    configs = load_game_configs()
    logger.info("Loaded {count} built-in game configuration(s)", count=len(configs))

    async with HoyolabClient(settings) as client, MiyousheClient(settings) as events_client:
        results = await asyncio.gather(
            *[
                _process_game(
                    client=client,
                    events_client=events_client,
                    config=config,
                    settings=settings,
                )
                for config in configs
            ],
            return_exceptions=True,
        )

    for config, result in zip(configs, results, strict=False):
        if isinstance(result, Exception):
            logger.error("Failed to update {game}: {error}", game=config.display_name, error=result)
            raise result


async def _process_game(
    *,
    client: HoyolabClient,
    events_client: MiyousheClient,
    config: GameConfig,
    settings: Settings,
) -> None:
    logger.info("Updating {game}", game=config.display_name)

    timeline = await storage.load_timeline(settings.data_output_dir, config.display_name)
    before_snapshot = deepcopy(timeline.model_dump(mode="json", by_alias=True))

    ann_list = await client.fetch_ann_list(config)
    plugin = get_plugin(config.game_id)
    version_info = plugin.extract_version(ann_list)

    special_program = await fetch_special_program_info(
        events_client,
        game_id=config.game_id,
    )
    if special_program is not None:
        if special_program.code:
            version_info.next_version_code = special_program.code
        elif special_program.start_time is not None:
            version_info.next_version_code = None
        if special_program.name:
            version_info.next_version_name = special_program.name
        if special_program.start_time is not None:
            version_info.next_version_sp_time = special_program.start_time

    current_version = timeline.upsert_version(
        code=version_info.code,
        name=version_info.name,
        banner=version_info.banner,
        start_time=version_info.start_time,
        end_time=version_info.end_time,
    )

    if version_info.next_version_code is not None or version_info.next_version_name:
        timeline.upsert_version(
            code=version_info.next_version_code or "",
            name=version_info.next_version_name or "",
            special_program_time=version_info.next_version_sp_time,
        )

    ann_content = await client.fetch_ann_content(config)
    existing_ids = {announcement.id for announcement in current_version.announcements}
    new_announcements = plugin.parse_announcements(
        version=version_info,
        ann_list=ann_list,
        ann_content=ann_content,
        existing_ids=existing_ids,
        display_name=config.display_name,
    )
    timeline.inject_announcements(
        code=version_info.code,
        announcements=new_announcements,
    )

    after_snapshot = timeline.model_dump(mode="json", by_alias=True)
    timeline_changed = before_snapshot != after_snapshot

    await storage.save_timeline(settings.data_output_dir, config.display_name, timeline)
    storage.update_catalog(settings.data_output_dir, config, timeline_changed)

    await export_ics(
        timeline=timeline,
        config=config,
        base_output=settings.ics_output_dir,
        extra_outputs=settings.extra_ics_dirs,
    )

    logger.info(
        "{game} updated | version {version} | new events {count}",
        game=config.display_name,
        version=version_info.code,
        count=len(new_announcements),
    )
