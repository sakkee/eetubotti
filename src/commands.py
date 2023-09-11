from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from collections.abc import Callable
import time
import re
from src.objects import User
import discord
from src.basemodule import BaseModule


@dataclass
class Command:
    """Command class used for all commands (!commands and /commands). Checks the permissions, cooldowns, thresholds.

    Args:
        manager (CommandManager): The Command Manager.
        command_name (str): name of the command, e.g. 'rank', 'irc', 'top' etc
        fnc (Callable): the function which is executed (part of the module classes)
        disabled (bool): The command is disabled.
        commands_per_day (int): How many times the user can use the command on other channels than bot command channel.
        bot_channel_commands (int): How many times the user can use the command on the bot command channel.
        timeout (int): Cooldown of how many seconds the user must wait before using the command again.
        allow_low_levels (bool): Low level users are allowed to use the command in other channels than the
            bot command channel.
        allow_low_levels_in_bot_channel (bool): The low level users are allowed to use the command in the bot command
            channel.
        requires_fulladmin (bool): Requires server highest administration permissions.
        requires_banrole (bool): Requires ban role permission.

    Attributes:
        thresholds (dict[User.id, int]): keep track of the times the command has been used by the user today.
        timeouts (dict[User.id, float]): keep track of the cooldowns to prevent command spam
    """
    manager: CommandManager
    command_name: str
    fnc: Callable
    thresholds: dict[User.id, int] = field(default_factory=dict)
    disabled: bool = False
    commands_per_day: int = 20
    bot_channel_commands: int = 100
    timeout: int = 5
    timeouts: dict[User.id, float] = field(default_factory=dict)
    allow_low_levels: bool = False
    allow_low_levels_in_bot_channel = True
    requires_fulladmin: bool = False
    requires_banrole: bool = False

    def __post_init__(self):
        self.bot_channel_commands = self.commands_per_day * 3

    def user_has_permissions(self, user: User, message: discord.Message | None = None,
                             interaction: discord.Interaction | None = None) -> tuple[bool, str]:
        """Check whether the user is permissioned to use the command.

        Args:
            user (User): The user who has used the command.
            message (discord.Message | None): the message which called the command.
            interaction (discord.Interaction | None): the interaction which called the command.

        Returns:
            Two attributes, where the first is whether the user is permissioned to use the command, and the second
            is the error message.
        """
        msg: str = ''
        if self.disabled:
            return False, msg
        id: User.id = user.id
        if (message and message.channel.id == self.manager.bot.config.CHANNEL_GENERAL) or \
                (interaction and interaction.channel_id == self.manager.bot.config.CHANNEL_GENERAL):
            # yleinen channel
            self.thresholds[id] = 1 if id not in self.thresholds else self.thresholds[id] + 1
            if self.thresholds[id] > self.commands_per_day:
                if self.thresholds[id] < self.commands_per_day * 2:
                    msg = self.manager.bot.localizations.TOO_MANY_COMMANDS.format(
                        self.command_name,
                        self.manager.bot.client.get_channel(self.manager.bot.config.CHANNEL_BOTCOMMANDS).mention)
                return False, msg

        else:
            # other channel than yleinen
            self.thresholds[id] = 1 if id not in self.thresholds else self.thresholds[id] + 1
            if self.thresholds[id] > self.bot_channel_commands:
                msg = self.manager.bot.localizations.TOO_MANY_COMMANDS_1.format(self.command_name)
                return False, msg

        if user.level < 10 and self.manager.bot.config.ROLE_SQUAD not in user.roles and \
                self.manager.bot.config.ROLE_FULL_ADMINISTRATOR not in user.roles:
            if (not self.allow_low_levels and
                (message and message.channel.id == self.manager.bot.config.CHANNEL_GENERAL) or
                (interaction and interaction.channel_id == self.manager.bot.config.CHANNEL_GENERAL)) or \
                    not self.allow_low_levels_in_bot_channel:
                return False, self.manager.bot.localizations.TOO_LOW_LEVEL.format(
                    self.manager.bot.client.get_channel(self.manager.bot.config.CHANNEL_BOTCOMMANDS).mention)

        if self.requires_fulladmin or self.requires_banrole:
            is_admin: bool = False
            for x in user.roles:
                if (x not in self.manager.bot.config.BAN_ROLES and self.requires_banrole) or \
                        (x != self.manager.bot.config.ROLE_FULL_ADMINISTRATOR and self.requires_fulladmin):
                    continue
                is_admin = True
                break

            if not is_admin:
                return False, self.manager.bot.localizations.NOT_OWNER

        if self.timeout != 0:
            if id in self.timeouts:
                if self.timeouts[id] + self.timeout < time.time():
                    del self.timeouts[id]
                else:
                    timeout_time: int = int(self.timeouts[id] + self.timeout - time.time()) + 1
                    if timeout_time < 60:
                        timescale: str = self.manager.bot.localizations.WAIT_SECOND if timeout_time == 1 else \
                            self.manager.bot.localizations.WAIT_SECONDS
                    else:
                        timeouts: list[str] = f'{timeout_time / 60}'.split('.')
                        trailing_str: str = ''
                        if len(timeouts) == 2:
                            seconds: int = int(float(f'0.{timeouts[1]}') * 60)
                            if seconds == 1:
                                trailing_str += f' {seconds} {self.manager.bot.localizations.WAIT_SECOND}'
                            elif seconds > 1:
                                trailing_str += f' {seconds} {self.manager.bot.localizations.WAIT_SECONDS}'

                        timescale = self.manager.bot.localizations.WAIT_MINUTE \
                            if f'{round(timeout_time / 60, 1):g}' == '1' \
                            else self.manager.bot.localizations.WAIT_MINUTES
                        timescale += trailing_str
                        timeout_time: str = timeouts[0]

                    return False, self.manager.bot.localizations.WAIT.format(timeout_time, timescale)
            self.timeouts[id] = time.time()
        return True, msg

    async def execute(self, user: User, message: discord.Message | None = None,
                      interaction: discord.Interaction | None = None,
                      target_user: discord.User = None,
                      **kwargs):
        """Execute the command.

        Args:
            user (User): The user who has used the command.
            message (discord.Message | None): the message which called the command.
            interaction (discord.Interaction | None): the interaction which called the command.
            target_user (discord.User | None): the target user of the command.
        """
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
class CommandManager(BaseModule):
    """Command Manager that handles all the commands.

    All commands are registered to this class. This module must be the first initialized in the bot's modules.

    Attributes:
        commands (dict[str, Command]): dictionary object of commands. etc {'rank': Command...}
        point_commands (dict[str, str]): dictionary that holds the !commands and ?commands. etc:
            {'?ban': 'ban', '!rank': 'rank'}
    """
    commands: dict[str, Command] = field(default_factory=dict)
    point_commands: dict[str, str] = field(default_factory=dict)

    def clear_thresholds(self):
        for command in self.commands:
            self.commands[command].thresholds.clear()

    async def on_new_day(self, date_now: datetime):
        self.clear_thresholds()

    def register(self, command_name: str, function: Callable, description: str = '', timeout: int = 15,
                 commands_per_day: int = 15):
        """Register a command to the Command Manager.

        USE THIS AS A DECORATOR!

        Args:
            command_name (str): The name of the command. E.g. 'rank', 'irc', 'rakkaus'.
            function (Callable): the function which is called if the user is permissioned to use the command.
            description (str): The description of the command that's visible in the Discord's slash commands tab.
            timeout (int): How many seconds the user must wait to use the command.
            commands_per_day (int): The times the user can use the command per day.

        Examples:
            @self.bot.commands.register(command_name='rakkaus', function=self.love,
                                   description=self.bot.localizations.LOVE_DESCRIPTION, commands_per_day=6)
            async def love(interaction: discord.Interaction, käyttäjä: discord.User = None):
                await self.bot.commands.commands['rakkaus'].execute(
                    user=self.bot.get_user_by_id(interaction.user.id),
                    interaction=interaction,
                    target_user=käyttäjä
                )


            @self.bot.commands.register(command_name='rank', function=self.rank,
                                    description=self.bot.localizations.RANK_DESCRIPTION, commands_per_day=15,
                                    timeout=5)
            async def rank(interaction: discord.Interaction, käyttäjä: discord.User = None):
                await self.bot.commands.commands['rank'].execute(
                    user=self.bot.get_user_by_id(interaction.user.id),
                    interaction=interaction,
                    target_user=käyttäjä
                )
        """

        def decorator(fnc: Callable):
            """Decorates the executable function and adds it to the Bot's Command Tree."""
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
                guild=discord.Object(self.bot.config.SERVER_ID),
                override=True
            )
            return fnc

        return decorator

    async def error(self, msg: str = None, message: discord.Message = None, interaction: discord.Interaction = None):
        """Send an error message. On default deletes the message and the command after 8 seconds.

        Args:
            msg (str): The string to be sent.
            message (discord.Message | None): Message to which to reply.
            interaction (discord.Interaction | None): Discord interaction to which to reply.
        """
        msg = self.bot.localizations.ON_ERROR if not msg else msg
        await message.reply(msg, delete_after=8.0) if message else \
            await interaction.response.send_message(msg, delete_after=8.0)
        if message:
            try:
                await message.delete(delay=8.0)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                print(f"Error! Can't delete message {message.id}")

    async def message(self, msg: str = '', message: discord.Message = None, interaction: discord.Interaction = None,
                      file: discord.File | discord.utils.MISSING | None = discord.utils.MISSING,
                      channel_send: bool = False, delete_after: int = 0) -> discord.Message | \
                                                                            discord.Interaction.response:
        """Send a message.

        Args:
            msg (str): The string to be sent.
            message (discord.Message | None): Message to which to reply.
            interaction (discord.Interaction | None): Discord interaction to which to reply.
            file (discord.File | discord.utils.MISSING | None): The file to be sent.
            channel_send (bool): Whether to send the message on a channel rather than as a reply to a message.
            delete_after (int): The response is deleted after this. If 0, it no delete used.

        Returns:
            A discord.Message or a discord.Interaction.response object which was sent.
        """
        file = discord.utils.MISSING if not file else file
        delete_after = None if (delete_after == 0 or
                                (message and message.channel.id == self.bot.config.CHANNEL_BOTCOMMANDS)
                                or (interaction and interaction.channel.id == self.bot.config.CHANNEL_BOTCOMMANDS)) \
            else delete_after
        if message and delete_after:
            try:
                await message.delete(delay=delete_after)
            except discord.Forbidden:
                print(f"Error! Bot doesn't have permissions to delete message {message.id}!")
            except discord.NotFound:
                pass
        if not channel_send:
            try:
                return await message.reply(msg, file=file, delete_after=delete_after) if message else \
                    await interaction.response.send_message(msg, file=file, delete_after=delete_after)
            except discord.Forbidden:
                print(f"Error! Bot doesn't have proper permissions to reply to a message or interaction")

        else:
            try:
                return await message.channel.send(msg, file=file, delete_after=delete_after) if message else \
                    await interaction.channel.send(msg, file=file, delete_after=delete_after)
            except discord.Forbidden:
                channel_name: str = message.channel.name if message else interaction.channel.name
                print(f"Error! Bot doesn't have proper permissions to send to channel {channel_name}")

    async def on_message(self, message: discord.Message):
        """Parse the message and check whether it has an application command on it. Also gets the target user."""
        if message.author.bot and message.author.id not in [623974457404293130, 732616359367802891]:
            return
        if len(message.content.split()) > 0 and message.content.split()[0] in self.point_commands:
            targetting_user_str: str = message.content.split()[1] if len(message.content.split()) > 1 else None
            target_user = self.get_target_user(targetting_user_str)
            await self.commands[message.content.split()[0][1:]].execute(
                self.bot.get_user_by_id(message.author.id), message=message, target_user=target_user)

    def get_target_user(self, text: str) -> User | None:
        """Get user from a text."""

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
