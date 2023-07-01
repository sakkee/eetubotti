from datetime import datetime, timedelta
from dateutil.tz import gettz
import discord
from dataclasses import dataclass
from src.constants import *
from .module import Module


@dataclass
class Plugin(Module):
    last_check_day: datetime = datetime.now(tz=gettz(DEFAULT_TIMEZONE)) - timedelta(days=1)

    async def on_message(self, message: discord.Message):
        if message.created_at.hour != self.last_check_day.hour:
            self.last_check_day = message.created_at
            for channel in self.bot.server.channels:
                if channel.id not in PURGE_CHANNELS:
                    continue
                try:
                    print("Purging", channel.name)
                    while len(await channel.purge(check=self.is_three_hours_old, oldest_first=True)) > 0:
                        pass
                except Exception as e:
                    print("purge error", e)
                    pass

    @staticmethod
    def is_three_hours_old(message: discord.Message) -> bool:
        return True if datetime.now(tz=gettz(DEFAULT_TIMEZONE)) - timedelta(hours=PURGE_CHANNEL_HOURS) > \
                       message.created_at else False
