"""Runtime settings for the hoyo_calendar pipeline."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import BaseModel, Field, validator


def _default_repo_root() -> Path:
    """Return the current working directory as project root."""

    return Path.cwd().resolve()


class Settings(BaseModel):
    """Application level settings computed from environment variables."""

    data_output_dir: Path = Field(
        default_factory=lambda: _default_repo_root() / "data"
    )
    ics_output_dir: Path = Field(default_factory=lambda: _default_repo_root() / "ics")
    extra_ics_dirs: List[Path] = Field(default_factory=list)
    enable_debug_mocks: bool = Field(default=False)
    debug_data_dir: Path = Field(
        default_factory=lambda: _default_repo_root() / "mocks"
    )
    http_timeout_seconds: Annotated[float, Field(gt=0)] = 15.0

    class Config:
        arbitrary_types_allowed = True

    @validator(
        "data_output_dir",
        "ics_output_dir",
        "debug_data_dir",
        each_item=False,
    )
    def _expand_path(cls, value: Path) -> Path:  # noqa: D401
        """Ensure all base directories are absolute and exist."""
        return value.resolve()

    @validator("extra_ics_dirs", each_item=True)
    def _expand_extra_dirs(cls, value: Path) -> Path:
        return value.resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance using project defaults."""

    return Settings()
