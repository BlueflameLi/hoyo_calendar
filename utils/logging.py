"""Logging helpers for the hoyo_calendar pipeline."""

from __future__ import annotations

from loguru import logger


def configure_logging() -> None:
    """Configure loguru with a consistent format for CLI/CI usage."""

    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
        colorize=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )
