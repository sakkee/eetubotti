from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from src.objects import User

import discord

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class Module:
    bot: Bot
    enabled: bool = True  # if false, module won't be called
    name: str = ""

    def __post_init__(self):
        self.name = self.__class__.__module__

    async def on_new_day(self, date_now: datetime):
        pass

    async def on_ready(self):
        pass

    async def on_message(self, message: discord.Message):
        pass

    async def on_member_join(self, member: discord.Member):
        pass

    async def on_member_remove(self, member: discord.Member):
        pass

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        pass

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        pass

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        pass

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        pass

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        pass

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        pass
