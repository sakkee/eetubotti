'''
The module used for users to create their own text channels through commands.

The text channels are emptied by owner level hour intervals.

Commands:
!kanava (creates user channel)
🔴 (bans user from channel)
!kanava_unban (unbans user from channel)
'''

from __future__ import annotations
from datetime import datetime, timedelta
from dateutil.tz import gettz
import discord
import json
from dataclasses import dataclass, field
from src.basemodule import BaseModule
from src.objects import User
import time
from typing import Any


@dataclass
class TextChannel:
    manager: Plugin
    owner: User
    allowed_users: list[User] = field(default_factory=list)
    banned_users: list[User] = field(default_factory=list)
    id: int = None
    discord_channel: discord.TextChannel | None = None
    pin_message: int = None
    last_message_timestamp: int = 0

    @classmethod
    def from_json(cls, manager: Plugin, data: dict) -> TextChannel:
        return cls(
            manager=manager,
            owner=manager.bot.get_user_by_id(data.get('owner')),
            id=data.get('id'),
            allowed_users=[manager.bot.get_user_by_id(x) for x in data.get('allowed_users')],
            banned_users=[manager.bot.get_user_by_id(x) for x in data.get('banned_users')],
            discord_channel=manager.bot.server.get_channel(data.get('id')),
            pin_message=data.get('pin_message'),
            last_message_timestamp=data.get('last_message_timestamp')
        )

    def asdict(self) -> dict[str, Any]:
        return {
            'owner': self.owner.id,
            'allowed_users': [x.id for x in self.allowed_users],
            'banned_users': [x.id for x in self.banned_users],
            'id': self.id,
            'pin_message': self.pin_message,
            'last_message_timestamp': self.last_message_timestamp
        }


@dataclass
class Plugin(BaseModule):
    category: discord.CategoryChannel = None
    text_channels: list[TextChannel] = field(default_factory=list)
    last_check_hour: datetime = None

    def __post_init__(self):
        self.last_check_hour = datetime.now(tz=gettz(self.bot.config.TIMEZONE)) - timedelta(days=1)

    async def on_ready(self):
        self.load_channels()
        self.category = next((category for category in self.bot.server.categories if
                              category.id == self.bot.config.USER_CHANNEL_CATEGORY), None)
        if not self.category:
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL) \
                .send(self.bot.localizations.NO_USER_CATEGORY_EXISTS)
            return

        @self.bot.commands.register('kanava', function=self.create_text_channel,
                                    description=self.bot.localizations.CREATE_CHANNEL_DESCRIPTION, commands_per_day=10,
                                    timeout=10)
        async def kanava(interaction: discord.Interaction):
            await self.bot.commands.commands['kanava'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        @self.bot.commands.register('kanava_unban', function=self.channel_unban,
                                    description=self.bot.localizations.UNBAN_ON_CHANNEL, commands_per_day=20,
                                    timeout=5)
        async def kanava_uusi(interaction: discord.Interaction, käyttäjä: discord.User):
            await self.bot.commands.commands['kanava_unban'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

    async def channel_unban(self, user: User, message: discord.Message = None, interaction: discord.Interaction = None,
                            target_user: User = None):
        channel: TextChannel | None = self.get_channel_by_owner(user_id=user.id)
        if not channel:
            await self.bot.commands.error(self.bot.localizations.NOT_A_CHANNEL_OWNER, message, interaction)
            return

        if not target_user:
            await self.bot.commands.error(self.bot.localizations.UNBAN_ON_CHANNEL, message, interaction)
            return
        await self.unban_from_channel(target_user, channel)
        await self.bot.commands.message(
            self.bot.localizations.UNBANNED_FROM_CHANNEL.format(target_user.name, user.name),
            message, interaction)

    async def create_text_channel(self, user: User, message: discord.Message = None,
                                  interaction: discord.Interaction = None, target_user: User = None):
        if user.level < self.bot.config.MIN_CHANNEL_CREATE_LEVEL:
            await self.bot.commands.error(
                self.bot.localizations.TOO_LOW_LEVEL_CHANNEL_CREATE.format(self.bot.config.MIN_CHANNEL_CREATE_LEVEL),
                message, interaction)
            return
        if self.bot.config.PREVENT_CHANNEL_CREATION_ROLE in user.roles:
            return
        member: discord.Member | discord.User = self.bot.server.get_member(user.id) or self.bot.client.get_user(user.id)
        channel: TextChannel | None = self.get_channel_by_owner(user)
        if not channel:
            channel = TextChannel(self, user)
            self.text_channels.append(channel)
        if not channel.id:
            # channel doesn't exist
            new_channel: discord.TextChannel = await self.bot.server.create_text_channel(user.name,
                                                                                         category=self.category,
                                                                                         nsfw=True)
            channel.id = new_channel.id
            channel.discord_channel = new_channel
            commands: str = '> **!kanava**: luo oma kanava (jos tämä poistetaan) tai korjaa permissionit\n'
            commands += '> **🔴**: bännää käyttäjä tältä kanavalta\n'
            commands += '> **!kanava_unban** {käyttäjä}: päästää käyttäjän kanavalle taas'
            first_post: discord.Message = await new_channel.send(
                self.bot.localizations.NEW_CHANNEL_TEMPLATE.format(member.mention, commands))
            channel.pin_message = first_post.id
            await first_post.pin()

        await channel.discord_channel.set_permissions(member, read_messages=True, send_messages=True,
                                                      manage_messages=True, manage_permissions=True,
                                                      manage_channels=True, manage_threads=True)
        await channel.discord_channel.set_permissions(self.bot.server.get_role(self.bot.config.ROLE_LEVEL_20),
                                                      view_channel=True, send_messages=True)
        await self.bot.commands.message(
            self.bot.localizations.YOUR_TEXT_CHANNEL.format(channel.discord_channel.mention), message, interaction)
        self.save_channels()

    def load_channels(self):
        try:
            with open('data/user_channels.json', 'r') as f:
                user_channels = json.load(f)
                for channel in user_channels:
                    try:
                        text_channel: TextChannel = TextChannel.from_json(self, channel)
                        if not text_channel.discord_channel:
                            continue
                        self.text_channels.append(text_channel)
                    except AttributeError:
                        continue
                self.save_channels()
        except FileNotFoundError:
            pass

    def save_channels(self):
        with open('data/user_channels.json', 'w') as f:
            user_channels: list[dict[str, Any]] = [x.asdict() for x in self.text_channels]
            json.dump(user_channels, f)

    def get_channel_by_owner(self, user: User | None = None, user_id: User.id | None = None) -> TextChannel | None:
        user_id = user.id if user else user_id
        return next((channel for channel in self.text_channels if channel.owner.id == user_id), None)

    def get_channel_by_id(self, channel_id: int) -> TextChannel | None:
        return next((channel for channel in self.text_channels if channel.id == channel_id), None)

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        channel: TextChannel | None = self.get_channel_by_id(channel.id)
        if not channel:
            return
        self.text_channels.remove(channel)
        self.save_channels()

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != '🔴':
            return
        channel: TextChannel | None = self.get_channel_by_id(payload.channel_id)
        if not channel:
            return
        if payload.member.id != channel.owner.id:
            return
        if payload.member.id == self.bot.client.user.id:
            return
        message: discord.Message = await channel.discord_channel.fetch_message(payload.message_id)
        await self.ban_from_channel(self.bot.get_user_by_id(message.author.id), channel, message.author)

    async def ban_from_channel(self, user: User, channel: TextChannel, member: discord.Member | discord.User):
        if user in channel.banned_users:
            return
        if user == channel.owner:
            return
        if self.bot.config.ROLE_FULL_ADMINISTRATOR in user.roles:
            return
        await channel.discord_channel.set_permissions(member, view_channel=False, send_messages=False)
        channel.banned_users.append(user)
        self.save_channels()
        await channel.discord_channel.send(self.bot.localizations.BANNED_FROM_CHANNEL.format(user.name))

    async def unban_from_channel(self, user: User, channel: TextChannel):
        if user in channel.banned_users:
            channel.banned_users.remove(user)
            self.save_channels()
        member: discord.Member | discord.User = self.bot.server.get_member(user.id) or self.bot.client.get_user(user.id)
        await channel.discord_channel.set_permissions(member, view_channel=True, send_messages=True)

    async def on_member_join(self, member: discord.Member):
        for channel in self.text_channels:
            if self.bot.get_user_by_id(member.id) in channel.banned_users:
                await channel.discord_channel.set_permissions(member, view_channel=False, send_messages=False)

    async def on_message(self, message: discord.Message):
        text_channel: TextChannel | None = self.get_channel_by_id(message.channel.id)
        if text_channel:
            text_channel.last_message_timestamp = message.created_at.timestamp()

        if self.last_check_hour.hour == message.created_at.hour:
            return
        self.last_check_hour = message.created_at

        for channel in self.text_channels:
            if time.time() - channel.last_message_timestamp >= \
                    self.bot.config.DELETE_CHANNEL_AFTER_INACTIVITY_HOURS * 3600:
                await channel.discord_channel.delete(reason='Deleted due to inactivity')
                continue
            try:
                while len(await channel.discord_channel.purge(check=self.is_to_be_deleted, oldest_first=True)) > 0:
                    pass
            except Exception as e:
                print("user_channels: Error at purging", channel.discord_channel.name, e)

    def is_to_be_deleted(self, message: discord.Message) -> bool:
        channel: TextChannel = self.get_channel_by_id(message.channel.id)
        if not channel or message.id == channel.pin_message:
            return False

        return True if datetime.now(tz=gettz(self.bot.config.TIMEZONE)) - \
                       timedelta(hours=channel.owner.level) > \
                       message.created_at else False

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        channel: TextChannel | None = self.get_channel_by_id(after.id)
        if not channel:
            return
        real_name: str = channel.owner.name.lower().replace('.', '').replace(' ', '').replace('#', '').replace(',', '')
        if after.name != real_name:
            print(f"ERROR! {after.name} != {real_name}")
            await channel.discord_channel.edit(name=real_name)
        if not channel.discord_channel.is_nsfw():
            await channel.discord_channel.edit(nsfw=True)
        if after.type != discord.ChannelType.text:
            await channel.discord_channel.edit(type=discord.ChannelType.text)
        for permission in after.overwrites:
            for perm in iter(after.overwrites.get(permission)):
                if perm[0] != 'mention_everyone' or not perm[1]:
                    continue
                if permission.id == channel.owner.id:
                    await channel.discord_channel.set_permissions(
                        permission, mention_everyone=False, send_tts_messages=False, read_messages=True,
                        send_messages=True, manage_messages=True, manage_permissions=True,
                        manage_channels=True, manage_threads=True)
                    break

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if self.bot.config.PREVENT_CHANNEL_CREATION_ROLE in [x.id for x in after.roles] and \
                self.bot.config.PREVENT_CHANNEL_CREATION_ROLE not in [x.id for x in before.roles]:
            channel: TextChannel | None = self.get_channel_by_owner(user_id=after.id)
            if not channel:
                return
            self.text_channels.remove(channel)
            self.save_channels()
            await channel.discord_channel.delete(reason=f'{after.name} sai roolin mikä estää omat kanavat')
            await self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                f'Poistin just **{after.name}**:n oman tekstikanavan kun hänelle annettiin rooli mikä estää ne'
            )
