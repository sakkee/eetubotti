"""
All used modules must be imported here.
"""

from typing import Type
from . import (
    module,
    love,
    birthdays,
    stats,
    ircs,
    casino,
    get,
    empty_channels,
    moderation,
    anttubott
)

module_list: list[Type[module.Module]] = [
    ircs.Plugin,
    love.Plugin,
    birthdays.Plugin,
    stats.stats.Plugin,
    casino.Plugin,
    get.Plugin,
    empty_channels.Plugin,
    moderation.Plugin,
    anttubott.Plugin
]
