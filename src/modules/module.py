from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
import discord

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class Module:
    """Base Module Class.

    bot.Bot and the modules in src.modules use this as their base class. The module must have all the events as in
    src.discord_events.

    Remember to add the plugins in src.modules.module_list!

    Attributes:
        bot (Bot): main bot object
        enabled (bool): whether this is enabled or not. If False, the module won't be initialized.
        name (str): name of the module. Read from self.__class__.__module__

    See Also:
        https://discordpy.readthedocs.io/en/stable/api.html

    Examples:
        from src.modules import module
        class IRC(module.Module):
            async def on_ready(self):
                print(f"I'm loaded! My name is {self.name}")
    """
    bot: Bot = None
    enabled: bool = True
    name: str = ''

    def __post_init__(self):
        self.name = self.__class__.__module__

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_ban"""

    async def on_member_join(self, member: discord.Member):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_join"""

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_unban"""

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_update"""

    async def on_member_remove(self, member: discord.Member):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_remove"""

    async def on_message(self, message: discord.Message):
        """New message in a channel. https://discordpy.readthedocs.io/en/stable/api.html#discord.on_message"""

    async def on_new_day(self, date_now: datetime):
        """New day in local time. (not a discord.py event)"""

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_message_edit"""

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_raw_reaction_add"""

    async def on_ready(self):
        """Discord bot is ready. https://discordpy.readthedocs.io/en/stable/api.html#discord.on_ready"""

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        """https://discordpy.readthedocs.io/en/stable/api.html#discord.on_voice_state_update"""
