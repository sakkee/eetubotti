"""
The moderation plugin. Handles bans, mutes and timeouts.

Commands:
    ?ban
    🔴 as a reaction to a message (3 hour ban)
"""

import discord
import json
from dataclasses import field, dataclass
from datetime import datetime, timedelta
from dateutil.tz import gettz
import src.functions as functions
from src.objects import User
import time
from src.basemodule import BaseModule

DEFAULT_BAN_LENGTH: int = 12
DEFAULT_EMOJI_BAN_LENGTH: int = 3
DEFAULT_MUTE_LENGTH: int = 3


@dataclass
class Plugin(BaseModule):
    ban_list: dict[discord.User, float] = field(default_factory=dict)
    mute_list: dict[discord.User, float] = field(default_factory=dict)
    timeout_list: dict[discord.User, float] = field(default_factory=dict)
    last_checked: float = 0.0

    async def on_ready(self):
        try:
            with open('data/bans.json', 'r') as f:
                bans = json.load(f)
                for user_id in bans:
                    user: discord.User = await self.bot.client.fetch_user(int(user_id))
                    self.ban_list[user] = bans[user_id]

        except FileNotFoundError:
            pass
        await self.fetch_bans()

        @self.bot.commands.register(command_name='ban', function=self.ban_user,
                                    description=self.bot.localizations.BAN_DESCRIPTION,
                                    commands_per_day=10, timeout=5)
        async def ban(interaction: discord.Interaction, käyttäjä: discord.User, syy: str = '',
                      tunnit: int = DEFAULT_BAN_LENGTH):
            await self.bot.commands.commands['ban'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä,
                reason=syy,
                hours=tunnit
            )

    async def ban_user(self, user: User, message: discord.Message | None = None,
                       interaction: discord.Interaction | None = None,
                       target_user: User | None = None, reason: str = '', hours: int = DEFAULT_BAN_LENGTH,
                       **kwargs):
        if not functions.check_if_can_ban(message.author if message else interaction.user,
                                          self.bot.config.BAN_ROLES):
            await self.bot.commands.error(self.bot.localizations.BAN_NO_PERMISSION, message, interaction)
            return
        if target_user.is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
            await self.bot.commands.error(self.bot.localizations.BAN_CANT_BAN.format(target_user.name),
                                          message, interaction)
            return
        if user == target_user:
            await self.bot.commands.error(self.bot.localizations.BAN_DESCRIPTION, message, interaction)
            return
        if not target_user.is_in_guild:
            await self.bot.commands.error(self.bot.localizations.BAN_NOT_IN_GUILD.format(target_user.name),
                                          message, interaction)
            return

        if message and len(message.content.split(' ')) > 2:
            content_list: list[str] = message.content.split(' ')
            reason: str = ' '.join(content_list[2:])
            if content_list[-1].isnumeric():
                hours = int(content_list[-1])
        hours = max(1, min(18, hours))
        reason = self.bot.localizations.BAN_DEFAULT_REASON if not reason else reason
        member: discord.Member = await self.bot.server.fetch_member(target_user.id)

        if not member:
            await self.bot.commands.error(self.bot.localizations.BAN_NOT_IN_GUILD.format(member.name), message,
                                          interaction)
            return

        await self.bot.send_dm(member, self.bot.localizations.BAN_DM.format(hours, reason))

        try:
            await self.bot.server.ban(member, delete_message_days=0, reason=reason)
            banned_user: discord.User = await self.bot.client.fetch_user(target_user.id)
            if banned_user in self.ban_list:
                del self.ban_list[banned_user]
            self.ban_list[banned_user] = time.time() + hours * 60 * 60
            self.save_bans()

            await self.bot.commands.message(self.bot.localizations.BAN_CHANNEL_ANNOUNCE
                                            .format(member.name, hours, reason, user.name),
                                            message, interaction, channel_send=True)
            if interaction:
                await interaction.response.send_message('meni bänneille')

        except discord.Forbidden:
            print(f"Error! Don't have permissions to ban user {member.name}")
            await self.bot.commands.error(self.bot.localizations.ON_ERROR, message, interaction)

    def save_bans(self):
        with open('data/bans.json', 'w') as f:
            ban_list: dict[str, float] = {}
            for memb in self.ban_list:
                ban_list[str(memb.id)] = self.ban_list[memb]
            json.dump(ban_list, f)

    async def fetch_bans(self):
        unbanned_users: list[User] = []
        for user in self.ban_list:
            try:
                if not await self.bot.server.fetch_ban(user):
                    unbanned_users.append(user)
                    continue
            except discord.errors.NotFound:
                unbanned_users.append(user)
                continue
        for unbanned_user in unbanned_users:
            del self.ban_list[unbanned_user]
        async for ban in self.bot.server.bans():
            if ban.user not in self.ban_list:
                self.ban_list[ban.user] = time.time() + DEFAULT_BAN_LENGTH * 60 * 60
        await self.check_unbans()

    async def check_unbans(self):
        if time.time() < self.last_checked + 5:
            return
        self.last_checked = time.time()
        to_unban: list[discord.User] = []
        for user in self.ban_list:
            if time.time() > self.ban_list[user]:
                to_unban.append(user)
        for user in to_unban:
            try:
                del self.ban_list[user]
                await self.bot.server.unban(user)
                await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.UNBANNED_MEMBER.format(user.name))
            except Exception as e:
                print("couldnt unban", e)
                await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.ON_ERROR)
        if to_unban:
            self.save_bans()
        await self.check_mutes()

    async def check_mutes(self):
        mute_role: discord.Role = self.bot.server.get_role(self.bot.config.ROLE_MUTED)

        to_unmute: list[discord.User] = []
        for user in self.mute_list:
            if time.time() > self.mute_list[user]:
                to_unmute.append(user)
        for user in to_unmute:
            try:
                del self.mute_list[user]
                member: discord.Member = self.bot.server.get_member(user.id)
                await member.remove_roles(mute_role)
                await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.MEMBER_UNMUTED.format(member.name))
            except Exception as e:
                print("couldn't unmute", e)
                await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.ON_ERROR)

        to_untimeout: list[discord.User] = []
        for user in self.timeout_list:
            if time.time() > self.timeout_list[user]:
                to_untimeout.append(user)

        for user in to_unmute:
            try:
                del self.timeout_list[user]
                member: discord.Member = self.bot.server.get_member(user.id)
                await member.edit(timed_out_until=None)
            except Exception as e:
                print("couldn't untimeout", e)
                await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.ON_ERROR)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != '🔴' or not functions.check_if_can_ban(payload.member, self.bot.config.BAN_ROLES):
            return
        if self.bot.client.get_channel(payload.channel_id).category.id == self.bot.config.USER_CHANNEL_CATEGORY:
            return
        message: discord.Message = await self.bot.client.get_channel(payload.channel_id).fetch_message(
            payload.message_id)
        message_content: str = message.content[:256] if message.content else ""
        member: discord.Member = message.author
        if member.bot or self.bot.get_user_by_id(member.id).is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
            await self.bot.commands.error(self.bot.localizations.BAN_CANT_BAN.format(member.name), message, None)
            return
        hours: int = DEFAULT_EMOJI_BAN_LENGTH
        reason: str = message_content
        try:
            await self.bot.server.ban(member, delete_message_days=0, reason=reason)
            await self.bot.commands.message(self.bot.localizations.BAN_CHANNEL_ANNOUNCE
                                            .format(member.name, hours, reason, payload.member.name),
                                            message, None, channel_send=True)
            banned_user: discord.User = await self.bot.client.fetch_user(member.id)
            if banned_user in self.ban_list:
                del self.ban_list[banned_user]
            self.ban_list[banned_user] = time.time() + hours * 60 * 60
            self.save_bans()

        except discord.Forbidden:
            print(f"Error! Can't ban user {member.name}")
            await self.bot.commands.error(self.bot.localizations.ON_ERROR, message, None)

    async def on_message(self, message: discord.Message):
        await self.check_unbans()
        if message.channel.id not in [self.bot.config.CHANNEL_GENERAL, self.bot.config.CHANNEL_GENERAL2]:
            return
        if message.author.id == 270904126974590976:
            await message.delete()
            await message.channel.send(f"<#{self.bot.config.CHANNEL_BOTCOMMANDS}>", delete_after=3.0)
        if "http" in message.content and not message.author.bot and self.bot.get_user_by_id(
            message.author.id).level < 5 and \
                not self.bot.get_user_by_id(message.author.id).is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
            await message.delete()
            a = await message.channel.send(self.bot.localizations.NO_LINKS_IN_GENERAL
                                           .format(message.author.mention, self.bot.config.CHANNEL_MEDIA),
                                           delete_after=8.0)
            return
        if len(message.content.split("\n")) <= 30:
            return
        try:
            if not len(message.embeds) or len(message.embeds[0].description) <= 20 or len(
                    message.embeds[0].description.split("\n")) <= 30:
                return
        except IndexError:
            return
        if not self.bot.get_user_by_id(message.author.id):
            return
        if self.bot.get_user_by_id(message.author.id).is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
            return
        await message.delete()
        await message.channel.send(self.bot.localizations.TOO_LONG_MSG, delete_after=8.0)

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if user in self.ban_list:
            del self.ban_list[user]
            self.save_bans()

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        hours: int = DEFAULT_BAN_LENGTH * 60 * 60
        if user in self.ban_list:
            await self.bot.send_dm(
                user, self.bot.localizations.BAN_DM.format(hours, self.bot.localizations.BAN_DEFAULT_REASON))
            return
        self.ban_list[user] = time.time() + DEFAULT_BAN_LENGTH * 60 * 60
        self.save_bans()

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        member: discord.Member = self.bot.server.get_member(after.id)
        if self.bot.config.ROLE_MUTED in [x.id for x in after.roles] \
                and self.bot.config.ROLE_MUTED not in [x.id for x in before.roles]:
            self.mute_list[member._user] = time.time() + DEFAULT_MUTE_LENGTH * 60 * 60
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                self.bot.localizations.MEMBER_MUTED.format(after.name, DEFAULT_MUTE_LENGTH))
        if self.bot.config.ROLE_MUTED in [x.id for x in before.roles] \
                and self.bot.config.ROLE_MUTED not in [x.id for x in after.roles] and \
                after in self.mute_list:
            del self.mute_list[member._user]
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                self.bot.localizations.MEMBER_UNMUTED.format(after.name), delete_after=15.0)
        if after.timed_out_until and not before.timed_out_until:
            delta_seconds: float = min(
                (after.timed_out_until - datetime.now(tz=gettz(self.bot.config.TIMEZONE))).total_seconds(),
                DEFAULT_MUTE_LENGTH * 60 * 60)
            if after.timed_out_until > datetime.now(tz=gettz(self.bot.config.TIMEZONE)) \
                    + timedelta(seconds=delta_seconds):
                await after.edit(timed_out_until=datetime.now(tz=gettz(self.bot.config.TIMEZONE)) + \
                                                 timedelta(seconds=delta_seconds))
            self.timeout_list[member._user] = time.time() + delta_seconds
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                self.bot.localizations.MEMBER_TIMEDOUT.format(after.name, round(delta_seconds / 60)))
        if before.timed_out_until and not after.timed_out_until:
            del self.timeout_list[member._user]
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                self.bot.localizations.MEMBER_UNTIMEOUT.format(after.name), delete_after=15.0)
