"""
Module for the stats, points, levels, rank et cetera.

Commands:
    !rank
    !streak
    !top
    !grind
    !grindaajat
"""

from __future__ import annotations

import os.path

import discord
import asyncio
from io import BytesIO
from datetime import datetime
from dataclasses import dataclass, field
from src.objects import User, Stats, Message, Reaction, VoiceDate
import time
from . import rank_card
import src.functions as functions
from src.basemodule import BaseModule

MAXIMUM_POINTS_PER_INTERVAL: int = 256  # how many points at maximum per POINTS_INTERVAL minutes
POINTS_INTERVAL: int = 5  # minutes for the message buffer


@dataclass
class Plugin(BaseModule):
    active_threshold: int = 10000000
    old_mins: int = -1
    current_mins: int = -1
    old_cache: list[Message.content] = field(default_factory=list)
    current_cache: list[Message.content] = field(default_factory=list)
    last_day: datetime = datetime.today()
    starting_day: datetime = datetime.today()
    user_points_new: dict[str, int] = field(default_factory=dict)
    user_points_old: dict[str, int] = field(default_factory=dict)
    users_in_voice: list[User] = field(default_factory=list)

    async def on_ready(self):
        @self.bot.commands.register(command_name='rank', function=self.rank,
                                    description=self.bot.localizations.RANK_DESCRIPTION, commands_per_day=15,
                                    timeout=5)
        async def rank(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['rank'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

        @self.bot.commands.register(command_name='streak', function=self.streak,
                                    description=self.bot.localizations.STREAK_DESCRIPTION, commands_per_day=10,
                                    timeout=5)
        async def streak(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['streak'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

        @self.bot.commands.register(command_name='top', function=self.top,
                                    description=self.bot.localizations.TOP_DESCRIPTION, commands_per_day=5,
                                    timeout=30)
        async def top(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['top'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

        @self.bot.commands.register(command_name='grind', function=self.activity,
                                    description=self.bot.localizations.ACTIVITY_DESCRIPTION, commands_per_day=10,
                                    timeout=5)
        async def grind(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['grind'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

        @self.bot.commands.register(command_name='grindaajat', function=self.activity_top,
                                    description=self.bot.localizations.ACTIVITY_TOP_DESCRIPTION,
                                    commands_per_day=5,
                                    timeout=5)
        async def grinders(interaction: discord.Interaction):
            await self.bot.commands.commands['grindaajat'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        await self.sync_messages(self.bot.database.get_last_post_id())
        await self.update_actives()
        for user in self.bot.users:
            await self.refresh_level_roles(user)

    async def on_new_day(self, date_now: datetime):
        await self.update_actives()
        for user in self.bot.users:
            await self.refresh_level_roles(user)

    async def rank(self, user: User, message: discord.Message | None = None,
                   interaction: discord.Interaction | None = None,
                   target_user: User | None = None,
                   **kwargs):
        if not target_user or not self.bot.get_user_by_id(target_user.id) or target_user.bot:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        point_list: list[tuple[User.id, Stats.points]] = []
        for usr in self.bot.users:
            if usr.id == 456226577798135808 or usr.bot:  # the id is deleted user...
                continue
            point_list.append((usr.id, usr.stats.points))
        sorted_list: list[tuple[User.id, Stats.points]] = sorted(point_list, key=lambda x: -int(x[1]))
        i: int = 1
        for k in sorted_list:
            if k[0] == target_user.id:
                break
            i += 1

        xp_now, xp_next = functions.get_xp_over(target_user.stats.points)
        rank: int = i
        level: int = target_user.level
        identifier: User.identifier = target_user.identifier
        profile_filepath: User.profile_filename = target_user.profile_filename
        if not os.path.isfile(profile_filepath):
            target_user.profile_filename = await self.bot.get_user_file(self.bot.server.get_member(target_user.id))
            profile_filepath = target_user.profile_filename
        fp = rank_card.Card.create_card(xp_now, xp_next, rank, level, target_user.name, identifier, profile_filepath)
        # try:
        with BytesIO() as image_binary:
            fp.save(image_binary, 'PNG')
            image_binary.seek(0)
            await self.bot.commands.message(
                message=message, interaction=interaction,
                file=discord.File(fp=image_binary, filename='hengitat_nyt_manuaalisesti.png'), delete_after=15)
        # except Exception as e:
        #    await self.bot.commands.error(msg=self.bot.localizations.ON_ERROR,
        #                                   message=message, interaction=interaction)

    async def streak(self, user: User, message: discord.Message | None = None,
                     interaction: discord.Interaction | None = None,
                     target_user: User | None = None,
                     **kwargs):
        if not target_user or not self.bot.get_user_by_id(target_user.id):
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        streak: int = functions.get_user_streak(target_user, self.bot.daylist)
        await self.bot.commands.message(self.bot.localizations.STREAK_SCORE.format(target_user.name, streak),
                                        message, interaction, delete_after=10)

    async def top(self, user: User, message: discord.Message | None = None,
                  interaction: discord.Interaction | None = None, **kwargs):
        point_list: list[list[User.id, Stats.points]] = []
        for usr in self.bot.users:
            if usr.id == 456226577798135808 or usr.bot:
                continue
            point_list.append([usr.id, usr.stats.points])
        sorted_list = sorted(point_list, key=lambda x: -int(x[1]))
        i: int = 0
        sendable_message: str = self.bot.localizations.ACTIVITY_TOP
        for k in sorted_list:
            i += 1
            if i > 15:
                break
            usr = self.bot.get_user_by_id(int(k[0]))
            sendable_message += self.bot.localizations.ACTIVITY_ROW.format(i, usr.name, usr.level)
        await self.bot.commands.message(sendable_message, message, interaction, delete_after=25)

    async def activity(self, user: User, message: discord.Message | None = None,
                       interaction: discord.Interaction | None = None,
                       target_user: User | None = None,
                       **kwargs):
        if not target_user or not self.bot.get_user_by_id(target_user.id):
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        next_threshold: int = functions.get_next_activity_threshold(self.bot.users, self.bot.daylist)
        user_points: int = functions.get_last_14_day_points(target_user, self.bot.daylist)
        msg = self.bot.localizations.ACTIVE_YES.format(target_user.name, user_points, next_threshold) if \
            user_points >= next_threshold else \
            self.bot.localizations.ACTIVE_NO.format(target_user.name, user_points, next_threshold)
        await self.bot.commands.message(msg, message, interaction, delete_after=12)

    async def activity_top(self, user: User, message: discord.Message | None = None,
                           interaction: discord.Interaction | None = None, **kwargs):
        actives = functions.get_actives(self.bot.users, self.bot.daylist, day_count=14, active_count=20)
        days = self.bot.daylist[::-1][1:14 + 1]
        if not days:
            await self.bot.commands.error(self.bot.localizations.ON_ERROR, message, interaction)
            return
        last_day: str = f"{days[0]['day']}.{days[0]['month']}.{days[0]['year']}"
        first_day: str = f"{days[len(days) - 1]['day']}."
        if days[len(days) - 1]["month"] != days[0]["month"]:
            first_day += f"{days[len(days) - 1]['month']}."
        if days[len(days) - 1]["year"] != days[0]["year"]:
            first_day += f"{days[len(days) - 1]['year']}"
        sendable_message: str = self.bot.localizations.ACTIVE_ROW_TITLE.format(first_day, last_day)
        i: int = 1
        for active in actives:
            if i == 16:
                sendable_message += self.bot.localizations.ACTIVE_ROW_NO_TITLE
            sendable_message += self.bot.localizations.GRIND_ROW.format(i, active[0].name, f'{active[1]:,}')
            i += 1
        await self.bot.commands.message(sendable_message, message, interaction, delete_after=25)

    async def update_actives(self):
        active_role: discord.Role = self.bot.server.get_role(self.bot.config.ROLE_ACTIVE)
        self.active_threshold = functions.get_active_threshold(self.bot.users, self.bot.daylist)
        active_users: list[User] = [x[0] for x in
                                    functions.get_actives(self.bot.users, self.bot.daylist, 14, 15, False)]

        for user in self.bot.users:
            if not user.is_in_guild or user.id in self.bot.config.IGNORE_LEVEL_USERS:
                continue
            member: discord.Member = self.bot.server.get_member(user.id)
            try:
                if self.bot.config.ROLE_ACTIVE not in user.roles and user in active_users:
                    await member.add_roles(active_role)

                elif self.bot.config.ROLE_ACTIVE in user.roles and user not in active_users:
                    await member.remove_roles(active_role)

                if self.bot.config.ROLE_ACTIVE_SQUAD in user.roles and \
                        (time.time() - user.stats.last_post_time > 24 * 60 * 60 * 3
                         or self.bot.config.ROLE_SQUAD not in user.roles):
                    await member.remove_roles(self.bot.server.get_role(self.bot.config.ROLE_ACTIVE_SQUAD))
            except discord.errors.Forbidden:
                print(f"Error! Could not edit {member.name} roles. Likely reason is that the bot's role is too low.")
                print("Please make the bot's role the top-most role in the server.")

    async def on_member_join(self, member: discord.Member):
        user = self.bot.get_user_by_id(member.id)
        user.is_in_guild = True
        await asyncio.sleep(15)
        active_users: list[User] = [x[0] for x in
                                    functions.get_actives(self.bot.users, self.bot.daylist, 14, 15, False)]
        active_role: discord.Role = self.bot.server.get_role(self.bot.config.ROLE_ACTIVE)
        member: discord.Member = await self.bot.server.fetch_member(user.id)
        await self.refresh_level_roles(user)
        if user in active_users:
            await member.add_roles(active_role)

    async def new_message(self, elem: discord.Message, old: bool = False):
        await self.bot.add_if_user_not_exist(elem.author, is_message=True)
        ref_id: discord.Message.id = elem.reference.message_id if elem.reference else None
        mentioned_user: discord.User.id = elem.mentions[0].id if len(elem.mentions) > 0 else None

        message = Message(
            id=elem.id,
            content=elem.content,
            attachments=len(elem.attachments),
            user_id=elem.author.id,
            jump_url=elem.jump_url,
            reference=ref_id,
            created_at=elem.created_at,
            mentions_everyone=elem.mention_everyone,
            mentioned_user_id=mentioned_user
        )

        dt = functions.ts2dt(message.created_at.timestamp())
        mins: int = (dt.hour * 60 + dt.minute) // 5
        sending_streak: bool = False
        if not old:
            cache = self.current_cache
            the_user = self.bot.get_user_by_id(elem.author.id)
            if the_user.stats.activity_points_today == 0 and \
                    (message.attachments > 0 or message.content not in cache):
                the_user.stats.activity_points_today += 1
                sending_streak = True
            if self.bot.config.ROLE_SQUAD in the_user.roles and self.bot.config.ROLE_ACTIVE_SQUAD not in the_user.roles:
                await elem.author.add_roles(self.bot.server.get_role(self.bot.config.ROLE_ACTIVE_SQUAD))

        if (old and mins != self.old_mins) or (not old and mins != self.current_mins):
            if old:
                self.old_cache[:] = []
                self.old_mins = mins
                self.user_points_old.clear()
            else:
                self.current_cache[:] = []
                self.current_mins = mins
                self.user_points_new.clear()

            self.bot.database.db_save()

        cache = self.old_cache if old else self.current_cache

        if not elem.author.bot and (message.content not in cache or message.attachments > 0):
            user_id: str = str(message.user_id)
            user: User = self.bot.get_user_by_id(message.user_id)
            if old:
                if user_id not in self.user_points_old:
                    self.user_points_old[user_id] = 0
                points: int = message.length // 2 + 3
                old_points: int = self.user_points_old[user_id]
                self.user_points_old[user_id] = min(MAXIMUM_POINTS_PER_INTERVAL, self.user_points_old[user_id] + points)
                message_points: int = self.user_points_old[user_id] - old_points
            else:
                if user_id not in self.user_points_new:
                    self.user_points_new[user_id] = 0
                points: int = message.length // 2 + 3
                old_points: int = self.user_points_new[user_id]
                self.user_points_new[user_id] = min(MAXIMUM_POINTS_PER_INTERVAL, self.user_points_new[user_id] + points)
                message_points: int = self.user_points_new[user_id] - old_points

            message.activity_points = message_points
            user.stats.files_sent += message.attachments
            user.stats.total_post_length += message.length
            user.stats.bot_command_count += message.is_bot_command
            user.stats.gif_count += message.is_gif
            user.stats.emoji_count += message.has_emoji
            user.stats.last_post_time = functions.dt2ts(message.created_at)
            user.stats.should_update = True

            if message_points and not user.add_points(message_points) and user.level > 1 and not old:
                await self.refresh_level_roles(user)
                await self.bot.commands.message(
                    msg=self.bot.localizations.NEW_LEVEL.format(elem.author.mention, str(user.level)),
                    message=elem, channel_send=True)

        if old:
            self.old_cache.append(message.content)
        else:
            self.current_cache.append(message.content)
        self.bot.database.add_message(message)

        if len(elem.reactions) > 0:
            for reaction in elem.reactions:
                try:
                    if reaction.emoji.name != 'taa':
                        continue
                except Exception as e:
                    continue
                found: bool = False
                for react in self.bot.reactions:
                    if react.message_id == reaction.message.id and react.emoji_id == reaction.emoji.id:
                        found = True
                        reaction.count += 1
                        self.bot.database.add_reaction(react)
                        break
                if not found:
                    react = Reaction(message_id=elem.id, emoji_id=reaction.emoji.id, count=reaction.count,
                                     is_in_database=False)
                    self.bot.database.add_reaction(react)

        if sending_streak:
            try:
                the_user = self.bot.get_user_by_id(elem.author.id)
                streak = functions.get_user_streak(the_user, self.bot.daylist)
                member = await self.bot.server.fetch_member(the_user.id)
                if self.starting_day.day != self.last_day.day:
                    await elem.channel.send(
                        self.bot.localizations.NEW_STREAK.format(member.mention, str(streak)),
                        delete_after=10.0
                    )
            except Exception as e:
                pass

    async def sync_messages(self, last_post_id: int):
        print(f'Last post id: {str(last_post_id)}')
        print('Fetching until last post found')
        count: int = 0
        for CHANNEL in self.bot.config.LEVEL_CHANNELS:
            async for elem in self.bot.client.get_channel(CHANNEL).history(limit=20000000):
                if elem.id <= last_post_id:
                    break
                self.last_day = elem.created_at
                count += 1
                if elem.author.bot and elem.author.id not in [623974457404293130,
                                                              732616359367802891]:  # anttubot, etyty
                    continue

                await self.new_message(elem, old=True)

        print('Found! Stopping...')

    async def on_message(self, message: discord.Message):
        if (message.author.bot and message.author.id not in [623974457404293130, 732616359367802891]) or \
                message.channel.id not in self.bot.config.LEVEL_CHANNELS or \
                message.channel.guild.id != self.bot.config.SERVER_ID:
            return

        if message.created_at.date() != self.last_day.date() and not self.bot.launching:
            self.last_day = message.created_at

        await self.new_message(message)

    async def refresh_level_roles(self, user: User):
        level_roles: list[int] = self.bot.config.get_level_roles(user.level)
        removable_roles: list[discord.Role] = [
            self.bot.server.get_role(x) for x in user.roles if x in self.bot.config.ALL_LEVEL_ROLES \
                                                               and x not in level_roles
        ]
        addable_roles: list[discord.Role] = [
            self.bot.server.get_role(x) for x in level_roles if x not in user.roles
        ]
        try:
            member = await self.bot.server.fetch_member(user.id)
        except discord.errors.NotFound:
            return
        if member is None or member.bot or member.id in self.bot.config.IGNORE_LEVEL_USERS:  # wasabi exception
            return
        try:
            for role in removable_roles:
                await member.remove_roles(role)
            for role in addable_roles:
                await member.add_roles(role)
        except discord.Forbidden:
            print(f"ERROR! Bot doesn't have permissions to change {user.name}'s roles")

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        user: User = self.bot.get_user_by_id(member.id)
        if user is None:
            return
        if user.bot:
            return
        timestamp: float = functions.get_current_timestamp()

        # user is joining a NON-AFK voice channel from AFK or not from voice at all
        if (before.channel is None or before.channel.id == self.bot.config.CHANNEL_AFK_VOICE_CHANNEL) and \
                after.channel is not None and after.channel.id != self.bot.config.CHANNEL_AFK_VOICE_CHANNEL:
            user.voicedate = VoiceDate(user.id, timestamp, None)
            user.vc_join_time = timestamp
            if user not in self.users_in_voice:
                self.users_in_voice.append(user)
            if len(self.users_in_voice) > 2:
                user.voicedate.mark_active(timestamp)
            elif len(self.users_in_voice) == 2:
                for usr in self.users_in_voice:
                    usr.voicedate.mark_active(timestamp)

        # user is leaving voice or joining AFK channel
        elif before.channel is not None and before.channel.id != self.bot.config.CHANNEL_AFK_VOICE_CHANNEL and \
                (after.channel is None or after.channel.id == self.bot.config.CHANNEL_AFK_VOICE_CHANNEL):
            if user.vc_join_time is None:
                return
            user.voicedate.mark_inactive(timestamp)
            if user in self.users_in_voice:
                self.users_in_voice.remove(user)
            user.vc_join_time = None
            user.stats.time_in_voice += user.voicedate.seconds
            if len(self.users_in_voice) == 1:
                for usr in self.users_in_voice:
                    usr.voicedate.mark_inactive(timestamp)
            activity_points: int = functions.seconds_to_points(user.voicedate.seconds)
            user.voicedate.activity_points = activity_points
            user.stats.should_update = True
            if activity_points > 0 and user.stats.activity_points_today == 0:
                streak = functions.get_user_streak(user, self.bot.daylist)
                if self.starting_day != self.last_day.day:
                    await self.bot.client.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                        self.bot.localizations.NEW_STREAK.format(member.mention, str(streak)),
                        delete_after=10.0
                    )
            user.stats.activity_points_today += activity_points
            if not user.add_points(activity_points):
                await self.refresh_level_roles(user)
                await self.bot.client.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                    self.bot.localizations.NEW_LEVEL.format(member.mention, str(user.level)))
            self.bot.database.add_voicedate(user.voicedate)
            user.voicedate = None
