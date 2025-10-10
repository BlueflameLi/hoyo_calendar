"""HTTP clients used by the hoyo_calendar pipeline."""

from .hoyolab import HoyolabClient
from .miyoushe import MiyousheClient

__all__ = ["HoyolabClient", "MiyousheClient"]
