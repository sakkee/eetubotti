from __future__ import annotations
from dataclasses import dataclass
import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class Discord_Events:
    bot: Bot

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        pass

    def link_events(self):
        self.bot.client.event(self.bot.on_message)
        self.bot.client.event(self.bot.on_raw_reaction_add)
        self.bot.client.event(self.on_raw_reaction_remove)
        self.bot.client.event(self.bot.on_voice_state_update)
        self.bot.client.event(self.bot.on_member_join)
        self.bot.client.event(self.bot.on_member_remove)
        self.bot.client.event(self.bot.on_ready)
        self.bot.client.event(self.bot.on_message_edit)
        self.bot.client.event(self.bot.on_member_unban)
        self.bot.client.event(self.bot.on_member_ban)
        self.bot.client.event(self.bot.on_member_update)
