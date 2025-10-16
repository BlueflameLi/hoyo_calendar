"""Main orchestrator for the hoyo_calendar data pipeline."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime, timedelta

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
    if special_program is not None and special_program.name != version_info.name:
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
    next_version = None

    if version_info.next_version_code is not None or version_info.next_version_name:
        next_version_start_time = (
            version_info.end_time + timedelta(hours=5)
            if version_info.end_time is not None
            else None
        )
        next_version = timeline.upsert_version(
            code=version_info.next_version_code or "",
            name=version_info.next_version_name or "",
            start_time=next_version_start_time,
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
    current_announcements = new_announcements
    future_announcements = []
    if version_info.end_time is not None:
        cutoff = version_info.end_time
        current_announcements = []
        for announcement in new_announcements:
            start_time = announcement.start_time
            if start_time is not None and start_time > cutoff:
                future_announcements.append(announcement)
            else:
                current_announcements.append(announcement)
        if future_announcements and next_version is None:
            current_announcements.extend(future_announcements)
            future_announcements = []
    timeline.inject_announcements(
        code=version_info.code,
        announcements=current_announcements,
    )

    if future_announcements and next_version is not None:
        timeline.inject_announcements(
            code=next_version.code,
            announcements=future_announcements,
        )

    trimmed_count, removed_versions = _prune_expired_entries(
        timeline,
        active_version_code=version_info.code,
        active_version_start=version_info.start_time,
    )

    after_snapshot = timeline.model_dump(mode="json", by_alias=True)
    timeline_changed = before_snapshot != after_snapshot

    if trimmed_count or removed_versions:
        logger.info(
            "{game} pruned {ann_count} expired announcement(s) and removed {version_count} old version(s)",
            game=config.display_name,
            ann_count=trimmed_count,
            version_count=removed_versions,
        )

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
        count=len(current_announcements),
        trimmed=trimmed_count,
        removed_versions=removed_versions,
    )


def _prune_expired_entries(
    timeline,
    *,
    active_version_code: str,
    active_version_start: datetime | None,
) -> tuple[int, int]:
    now = datetime.now()
    removed = 0
    remaining_versions = []
    removed_versions = 0
    for version in timeline.version_list:
        if not version.announcements:
            pass
        else:
            active_announcements = []
            for announcement in version.announcements:
                end_time = announcement.end_time
                if end_time is not None and end_time < now:
                    removed += 1
                    continue
                active_announcements.append(announcement)
            if len(active_announcements) != len(version.announcements):
                version.replace_announcements(active_announcements)

        should_remove_version = False
        if version.code != active_version_code:
            if version.end_time is not None:
                past_active = (
                    active_version_start is not None
                    and version.end_time < active_version_start
                )
                past_now = version.end_time < now
                if past_active or past_now:
                    should_remove_version = True
            elif not version.announcements:
                start_time = getattr(version, "start_time", None)
                if start_time is None or start_time < now:
                    should_remove_version = True

        if should_remove_version:
            removed_versions += 1
            continue

        remaining_versions.append(version)

    if removed_versions:
        timeline.version_list = remaining_versions

    return removed, removed_versions
