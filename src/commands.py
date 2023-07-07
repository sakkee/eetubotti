from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from collections.abc import Callable, Awaitable, Coroutine
import time
import re
from src.localizations import Localizations
from src.objects import User
from src.constants import CHANNELS, ROLES, SERVER_ID
import discord
from src.modules.module import Module


@dataclass
class Command:
    manager: Plugin
    command_name: str
    fnc: Callable
    thresholds: dict[str, int] = field(default_factory=dict)
    disabled: bool = False
    commands_per_day: int = 20
    bot_channel_commands: int = 100
    timeout: int = 5
    timeouts: dict[str, float] = field(default_factory=dict)
    allow_low_levels: bool = False
    allow_low_levels_in_bot_channel = True
    requires_whitename: bool = False
    requires_banrole: bool = False

    def __post_init__(self):
        self.bot_channel_commands = self.commands_per_day * 3

    def user_has_permissions(self, user: User, message: discord.Message | None = None,
                             interaction: discord.Interaction | None = None) -> tuple[bool, str]:
        msg: str = ''
        if self.disabled:
            return False, msg
        id: str = str(user.id)
        if (message and message.channel.id == CHANNELS.YLEINEN) or \
                (interaction and interaction.channel_id == CHANNELS.YLEINEN):
            # yleinen channel
            self.thresholds[id] = 1 if id not in self.thresholds else self.thresholds[id] + 1
            if self.thresholds[id] > self.commands_per_day:
                if self.thresholds[id] < self.commands_per_day * 2:
                    msg = Localizations.get('TOO_MANY_COMMANDS').format(
                        self.command_name,
                        self.manager.bot.client.get_channel(CHANNELS.BOTTIKOMENNOT).mention)
                return False, msg

        else:
            # other channel than yleinen
            self.thresholds[id] = 1 if id not in self.thresholds else self.thresholds[id] + 1
            if self.thresholds[id] > self.bot_channel_commands:
                msg = Localizations.get('TOO_MANY_COMMANDS_1').format(self.command_name)
                return False, msg

        if ROLES.LEVEL_10 not in user.roles and ROLES.SQUAD not in user.roles and ROLES.WHITENAME not in user.roles:
            if (not self.allow_low_levels and
                (message and message.channel.id == CHANNELS.YLEINEN) or
                (interaction and interaction.channel_id == CHANNELS.YLEINEN)) or \
                    not self.allow_low_levels_in_bot_channel:
                return False, Localizations.get('TOO_LOW_LEVEL').format(
                    self.manager.bot.client.get_channel(CHANNELS.BOTTIKOMENNOT).mention)

        if self.requires_whitename or self.requires_banrole:
            is_admin: bool = False
            for x in user.roles:
                if (x not in ROLES.ban_roles and self.requires_banrole) or \
                        (x != ROLES.WHITENAME and self.requires_whitename):
                    continue
                is_admin = True
                break

            if not is_admin:
                return False, Localizations.get('NOT_OWNER')

        if self.timeout != 0:
            if id in self.timeouts:
                if self.timeouts[id] + self.timeout < time.time():
                    del self.timeouts[id]
                else:
                    timeout_time: int = int(self.timeouts[id] + self.timeout - time.time()) + 1
                    if timeout_time < 60:
                        timescale: str = Localizations.get('WAIT_SECOND') if timeout_time == 1 else \
                            Localizations.get('WAIT_SECONDS')
                    else:
                        timeouts: list[str] = f'{timeout_time / 60}'.split('.')
                        trailing_str: str = ''
                        if len(timeouts) == 2:
                            seconds: int = int(float(f'0.{timeouts[1]}') * 60)
                            if seconds == 1:
                                trailing_str += f' {seconds} {Localizations.get("WAIT_SECOND")}'
                            elif seconds > 1:
                                trailing_str += f' {seconds} {Localizations.get("WAIT_SECONDS")}'

                        timescale = Localizations.get('WAIT_MINUTE') if f'{round(timeout_time / 60, 1):g}' == '1' \
                            else Localizations.get('WAIT_MINUTES')
                        timescale += trailing_str
                        timeout_time: str = timeouts[0]

                    return False, Localizations.get('WAIT').format(timeout_time, timescale)
            self.timeouts[id] = time.time()
        return True, msg

    async def execute(self, user: User, message: discord.Message | None = None,
                      interaction: discord.Interaction | None = None,
                      target_user: discord.User = None,
                      **kwargs):
        has_permissions, reason = self.user_has_permissions(user, message, interaction)
        if not has_permissions:
            if reason:
                await message.reply(reason, delete_after=8.0) if message else \
                    await interaction.response.send_message(reason, delete_after=8.0, ephemeral=True)
            if message:
                await message.delete(delay=8.0)
            return

        target: User = self.manager.bot.get_user_by_id(target_user.id) if target_user else \
            self.manager.bot.get_user_by_id(user.id)

        await self.fnc(user=user, message=message, interaction=interaction,
                       target_user=target, **kwargs)


@dataclass
class Plugin(Module):
    commands: dict[str, Command] = field(default_factory=dict)
    point_commands: dict[str, str] = field(default_factory=dict)

    def clear_thresholds(self):
        for command in self.commands:
            self.commands[command].thresholds.clear()

    async def on_new_day(self, date_now: datetime):
        self.clear_thresholds()

    def register(self, command_name: str, function: Callable, description: str = '', timeout: int = 15,
                 commands_per_day: int = 15):
        def decorator(fnc: Callable):
            self.commands[command_name] = Command(self, command_name, function, commands_per_day=commands_per_day,
                                                  timeout=timeout)
            if command_name != 'ban':
                self.point_commands[f'!{command_name}'] = command_name
            else:
                self.point_commands[f'?{command_name}'] = command_name
            self.bot.client_tree.add_command(
                discord.app_commands.Command(
                    name=command_name,
                    description=description,
                    callback=fnc
                ),
                guild=discord.Object(SERVER_ID),
                override=True
            )
            return fnc

        return decorator

    @staticmethod
    async def error(msg: str = Localizations.get('ON_ERROR'), message: discord.Message = None,
                    interaction: discord.Interaction = None):
        await message.reply(msg, delete_after=8.0) if message else \
            await interaction.response.send_message(msg, delete_after=8.0)
        if message:
            await asyncio.sleep(8)
            await message.delete()

    @staticmethod
    async def message(msg: str = '', message: discord.Message = None, interaction: discord.Interaction = None,
                      file: discord.File | discord.utils.MISSING | None = discord.utils.MISSING,
                      channel_send: bool = False, delete_after: int = 0) -> discord.Message | \
                                                                            discord.Interaction.response:
        file = discord.utils.MISSING if not file else file
        delete_after = None if (delete_after == 0 or (message and message.channel.id == CHANNELS.BOTTIKOMENNOT)
                                or (interaction and interaction.channel.id == CHANNELS.BOTTIKOMENNOT)) else delete_after
        if message and delete_after:
            await message.delete(delay=delete_after)
        if not channel_send:
            return await message.reply(msg, file=file, delete_after=delete_after) if message else \
                await interaction.response.send_message(msg, file=file, delete_after=delete_after)
        else:
            return await message.channel.send(msg, file=file, delete_after=delete_after) if message else \
                await interaction.channel.send(msg, file=file, delete_after=delete_after)

    async def on_message(self, message: discord.Message):
        if message.author.bot and message.author.id not in [623974457404293130, 732616359367802891]:
            return
        if len(message.content.split()) > 0 and message.content.split()[0] in self.point_commands:
            targetting_user_str: str = message.content.split()[1] if len(message.content.split()) > 1 else None
            target_user = self.get_target_user(targetting_user_str)
            await self.commands[message.content.split()[0][1:]].execute(
                self.bot.get_user_by_id(message.author.id), message=message, target_user=target_user)

    def get_target_user(self, text: str) -> User | None:
        # empty text
        if not text:
            return None

        # text is a number string (id)
        id = int(text) if text.isdigit() else 0
        if id:
            return self.bot.get_user_by_id(id)

        # get mentions from the text ("hello <@2323232232> how are you"...)
        id_list: list[int] = [int(x) for x in re.findall(r'\d+', text)]
        return self.bot.get_user_by_id(id_list[0]) if id_list else None
