"""
Random fun stuff.
"""

import discord
from dataclasses import dataclass
import src.functions
from src.basemodule import BaseModule

# when is bauhaus open
BAUHAUS_OPENING_TIMES: dict[str, dict[str, int]] = {
    'weekday': {'open': 7, 'close': 21},
    'saturday': {'open': 9, 'close': 18},
    'sunday': {'open': 10, 'close': 18}
}
BAUHAUS_TRIGGER_WORDS: list[tuple[str, str]] = [("bauhaus", "kii"), ("bauhaus", "kiinni"), ("bauhaus", "auki")]


@dataclass
class Plugin(BaseModule):
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.is_bauhaus_triggered(message.content):
            await self.bot.commands.message(self.get_bauhaus_closing_time(), message, delete_after=20)

    @staticmethod
    def is_bauhaus_triggered(message: discord.Message.content) -> bool:
        msg_lowered = message.lower()
        for trigger in BAUHAUS_TRIGGER_WORDS:
            all_found = len(trigger)
            count = 0
            for trg in trigger:
                if trg in msg_lowered:
                    count += 1
            if count == all_found:
                return True
        return False

    def get_bauhaus_closing_time(self) -> str:
        current_time = src.functions.utc_to_local(src.functions.ts2dt(src.functions.get_current_timestamp()),
                                                  self.bot.config.TIMEZONE)
        weekday = current_time.isoweekday()
        if weekday < 6:
            closing_time = BAUHAUS_OPENING_TIMES['weekday']['close']
        elif weekday == 6:
            closing_time = BAUHAUS_OPENING_TIMES['saturday']['close']
        else:
            closing_time = BAUHAUS_OPENING_TIMES['sunday']['close']
        if closing_time is None:
            return self.bot.localizations.BAUHAUS_NOT_FOUND
        if closing_time == 0:
            return self.bot.localizations.BAUHAUS_CLOSED_TODAY
        elif closing_time > current_time.hour:
            return self.bot.localizations.BAUHAUS_CLOSING_HOUR.format(closing_time)
        elif closing_time <= current_time.hour:
            return self.bot.localizations.BAUHAUS_CLOSED_ALREADY.format(closing_time)
