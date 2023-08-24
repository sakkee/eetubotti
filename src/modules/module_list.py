"""
All used modules must be imported here.
"""

from typing import Type
from . import (
    love,
    birthdays,
    stats,
    ircs,
    casino,
    get,
    empty_channels,
    moderation,
    anttubott,
    user_channels,
    fun
)
from src.basemodule import BaseModule

module_list: list[Type[BaseModule]] = [
    ircs.Plugin,
    love.Plugin,
    birthdays.Plugin,
    stats.stats.Plugin,
    casino.Plugin,
    get.Plugin,
    empty_channels.Plugin,
    moderation.Plugin,
    anttubott.Plugin,
    user_channels.Plugin,
    fun.Plugin
]
