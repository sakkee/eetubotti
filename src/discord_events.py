from __future__ import annotations
from dataclasses import dataclass
import discord
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class Discord_Events:
    """
    Discord Events module. Please see https://discordpy.readthedocs.io/en/stable/api.html#event-reference

    To add new events:
    1. Create a new function (according to the discord.py's Event Reference) in this module
    2. Add the function to link_events
    3. Add the same function to src/modules/module.py base class
    4. Make sure this module's function calls both the bot.py's function AND each module's function in bot.modules

    Attributes:
        bot (Bot): the main bot object

    Examples:
        events = Discord_Events(self)
        events.link_events()
    """

    bot: Bot

    def link_events(self):
        """Remember to link discord.py's events here when added.

        See Also:
            https://discordpy.readthedocs.io/en/stable/api.html#event-reference"""
        self.bot.client.event(self.on_member_ban)
        self.bot.client.event(self.on_member_join)
        self.bot.client.event(self.on_member_remove)
        self.bot.client.event(self.on_member_unban)
        self.bot.client.event(self.on_member_update)
        self.bot.client.event(self.on_message)
        self.bot.client.event(self.on_message_edit)
        self.bot.client.event(self.on_raw_reaction_add)
        self.bot.client.event(self.on_raw_reaction_remove)
        self.bot.client.event(self.on_ready)
        self.bot.client.event(self.on_voice_state_update)

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self.bot.on_member_ban(guild, user)
        for module in self.bot.modules:
            try:
                await module.on_member_ban(guild, user)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_ban: {e}")

    async def on_member_join(self, member: discord.Member):
        await self.bot.on_member_join(member)
        for module in self.bot.modules:
            try:
                await module.on_member_join(member)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_join: {e}")

    async def on_member_remove(self, member: discord.Member):
        await self.bot.on_member_remove(member)
        for module in self.bot.modules:
            try:
                await module.on_member_remove(member)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_remove: {e}")

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.bot.on_member_unban(guild, user)
        for module in self.bot.modules:
            try:
                await module.on_member_unban(guild, user)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_unban: {e}")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self.bot.on_member_update(before, after)
        for module in self.bot.modules:
            try:
                await module.on_member_update(before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_update: {e}")

    async def on_message(self, message: discord.Message):
        if self.bot.launching:
            return
        await self.bot.on_message(message)
        for module in self.bot.modules:
            try:
                await module.on_message(message)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_message: {e}")

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.bot.on_message_edit(before, after)
        for module in self.bot.modules:
            try:
                await module.on_message_edit(before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_message_edit: {e}")

    async def on_new_day(self, date_now: datetime):
        await self.bot.on_new_day(date_now)
        for module in self.bot.modules:
            try:
                await module.on_new_day(date_now)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_new_day: {e}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.bot.on_raw_reaction_add(payload)
        for module in self.bot.modules:
            try:
                await module.on_raw_reaction_add(payload)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_raw_reaction_add: {e}")

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Not implemented."""

    async def on_ready(self):
        await self.bot.on_ready()
        for module in self.bot.modules:
            try:
                await module.on_ready()
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_ready: {e}")
        self.bot.database.save_database()

        @self.bot.commands.register(command_name='reload_module', function=self.bot.reload_module,
                                    description='Reload module', commands_per_day=200, timeout=5)
        async def reload_module(interaction: discord.Interaction, module_name: str = ""):
            await self.bot.commands.commands['reload_module'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                module_name=module_name
            )

        self.bot.client_tree.copy_global_to(guild=self.bot.server)
        await self.bot.client_tree.sync(guild=self.bot.server)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self.bot.on_voice_state_update(member, before, after)
        for module in self.bot.modules:
            try:
                await module.on_voice_state_update(member, before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_voice_state_update: {e}")
