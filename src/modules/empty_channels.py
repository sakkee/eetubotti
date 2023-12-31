"""
This plugin deletes all the message in the clearable channels (PURGE_CHANNELS) after 3 hours (PURGE_CHANNEL_HOURS).
"""

from datetime import datetime, timedelta
from dateutil.tz import gettz
import discord
from dataclasses import dataclass
from src.basemodule import BaseModule


@dataclass
class Plugin(BaseModule):
    last_check_day: datetime = None

    def __post_init__(self):
        self.last_check_day = datetime.now(tz=gettz(self.bot.config.TIMEZONE)) - timedelta(days=1)

    async def on_message(self, message: discord.Message):
        if message.created_at.hour != self.last_check_day.hour:
            self.last_check_day = message.created_at
            for channel in self.bot.server.channels:
                if channel.id not in self.bot.config.PURGE_CHANNELS:
                    continue
                try:
                    while len(await channel.purge(check=self.is_three_hours_old, oldest_first=True)) > 0:
                        pass
                except Exception as e:
                    print("empty_channels: Error at purging", channel.name, e)
                    pass

    def is_three_hours_old(self, message: discord.Message) -> bool:
        return True if datetime.now(tz=gettz(self.bot.config.TIMEZONE)) - \
                       timedelta(hours=self.bot.config.PURGE_CHANNELS_INTERVAL_HOURS) > \
                       message.created_at else False
