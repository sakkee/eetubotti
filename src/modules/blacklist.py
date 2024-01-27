"""
Module to blacklist messages and files so they can't be posted again.

Commands:
    Use ⚫ as a reaction to a message.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import discord
import json
from src.objects import User
import src.functions as functions
import time
from urllib.parse import unquote
from src.basemodule import BaseModule


@dataclass
class BlacklistedFile:
    width: int = 0
    height: int = 0
    size: int = 0

    def is_same(self, attachment: discord.Attachment) -> bool:
        return self.width == attachment.width and self.height == attachment.height and self.size == attachment.size

    def to_json(self) -> dict[str, int]:
        return {
            'width': self.width, 'height': self.height, 'size': self.size
        }


@dataclass
class BlacklistedString:
    text: str


@dataclass
class BlacklistedList:
    blacklisted_strings: list[str]

    def is_blacklisted(self, text: str) -> bool:
        for string in self.blacklisted_strings:
            if string not in text.lower():
                return False
        return True


@dataclass
class Plugin(BaseModule):
    blacklist: list[BlacklistedString] = None
    blacklist_list: list[BlacklistedList] = None
    blacklist_files: list[BlacklistedFile] = None
    being_spammed: list[datetime] = field(default_factory=list)
    kicklist: dict[int, float] = field(default_factory=dict)

    def __post_init__(self):
        try:
            with open('data/blacklist_files.json') as f:
                files = json.load(f)
                self.blacklist_files = [BlacklistedFile(**file) for file in files]
        except FileNotFoundError:
            self.blacklist_files = []
        try:
            with open('data/blacklist.json') as f:
                strings = json.load(f)
                self.blacklist = [BlacklistedString(x) for x in strings]
        except FileNotFoundError:
            self.blacklist = []
        try:
            with open('data/blacklist_list.json') as f:
                lists = json.load(f)
                self.blacklist_list = [BlacklistedList(x) for x in lists]
        except FileNotFoundError:
            self.blacklist_list = []

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "⚫" or not functions.check_if_administrator(payload.member,
                                                                             self.bot.config.ROLE_FULL_ADMINISTRATOR):
            return
        adding: bool = False
        message = await self.bot.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
        added_text: str = ""
        if len(message.attachments):
            for attachment in message.attachments:
                found: bool = False
                for file in self.blacklist_files:
                    if file.is_same(attachment):
                        found = True
                        break
                if found:
                    continue
                adding = True
                added_text += f"height:{attachment.height}, width:{attachment.width}, size:{attachment.size}"
                self.blacklist_files.append(BlacklistedFile(attachment.width, attachment.height, attachment.size))
                with open('data/blacklist_files.json', 'w', encoding='utf-8') as f:
                    json.dump([x.to_json() for x in self.blacklist_files], f, ensure_ascii=True, indent=4)
        elif message.content not in self.blacklist and len(message.content) > 3 and message.content != '':
            adding = True
            if "gfycat" in unquote(message.content) or "imgur" in unquote(message.content):
                blist = message.content.rsplit('/', 1)[-1].split(".")[0]
                added_text = blist + " (original: " + message.content + ")"
                found: bool = False
                for blacklisted_string in self.blacklist:
                    if blacklisted_string.text == blist:
                        found = True
                        break
                if not found:
                    self.blacklist.append(BlacklistedString(unquote(blist)))
            elif message.content[0] == '[' and message.content[-1] == ']':
                the_list: list[str] = message.content[1:len(message.content) - 1].split('|')
                added_text = message.content.lower()
                self.blacklist_list.append(BlacklistedList(the_list))
            else:
                added_text = message.content.lower()
                self.blacklist.append(BlacklistedString(message.content.lower()))
            with open('data/blacklist.json', 'w', encoding='utf-8') as f:
                json.dump([x.text for x in self.blacklist], f, ensure_ascii=False, indent=4)
            with open('data/blacklist_list.json', 'w', encoding='utf-8') as f:
                json.dump([x.blacklisted_strings for x in self.blacklist_list], f, ensure_ascii=False, indent=4)
        await message.delete()
        await message.channel.send(self.bot.localizations.BLACKLISTED.format(message.author.mention), delete_after=10.0)
        if not adding:
            return
        with open('data/blacklist_log.json') as f:
            added = json.load(f)
        added.append(self.bot.localizations.BLACKLISTED_LOG.format(payload.member.name, added_text))
        with open('data/blacklist_log.json', 'w', encoding='utf-8') as f:
            json.dump(added, f, ensure_ascii=True, indent=4)

    def is_blacklisted(self, message: discord.Message) -> tuple[bool, str]:
        blacklisted_content: str = ""
        for blacklisted_string in self.blacklist:
            if blacklisted_string.text.lower() in [message.content.lower(), unquote(message.content.lower())]:
                return True, message.content
        for blacklisted_list in self.blacklist_list:
            if blacklisted_list.is_blacklisted(message.content):
                return True, message.content
        for attachment in message.attachments:
            for blacklisted_file in self.blacklist_files:
                if blacklisted_file.is_same(attachment):
                    return True, f"File: height {blacklisted_file.height} px, " \
                                          f"width {blacklisted_file.width} px, size {blacklisted_file.size}"
        return False, blacklisted_content

    async def on_message(self, message: discord.Message):
        is_blacklisted, blacklisted_content = self.is_blacklisted(message)
        if not is_blacklisted:
            return

        await message.delete()
        if self.is_being_spammed(message.created_at):
            return

        try:
            with open('data/blacklist_userlog.log') as f:
                userlog: list[str] = json.load(f)
        except FileNotFoundError:
            userlog: list[str] = []
        userlog.append(self.bot.localizations.BLACKLISTED_POST.format(message.author.name, blacklisted_content))
        with open('data/blacklist_userlog.log', 'w', encoding='utf-8') as f:
            json.dump(userlog, f, ensure_ascii=False, indent=4)
        await message.channel.send(self.bot.localizations.BLACKLISTED.format(message.author.mention), delete_after=8.0)

        user: User = self.bot.get_user_by_id(message.author.id)
        if not user or not user.is_in_guild or user.level >= 5:
            return

        if user.id in self.kicklist and self.kicklist[user.id] + 600 > time.time():
            await self.bot.send_dm(
                message.author, self.bot.localizations.BLACKLISTED_BAN_DM.format(blacklisted_content))
            await message.guild.ban(message.author,
                                    reason=self.bot.localizations.BLACKLISTED_BAN_LOG
                                    .format(blacklisted_content))
            await message.channel.send(self.bot.localizations.BLACKLISTED_BAN_ANNOUNCE
                                       .format(message.author.mention))
            return
        elif user.id in self.kicklist:
            del self.kicklist[user.id]
        await self.bot.send_dm(message.author, self.bot.localizations.BLACKLISTED_KICK_DM.format(blacklisted_content))
        await message.author.kick(reason=self.bot.localizations.BLACKLISTED_KICK_LOG.format(blacklisted_content))
        self.kicklist[user.id] = time.time()

    def is_being_spammed(self, date: datetime) -> bool:
        self.being_spammed.append(date)
        self.being_spammed[:] = [x for x in self.being_spammed if x + timedelta(seconds=15) >= date]
        return True if len(self.being_spammed) > 5 else False

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        message: discord.Message = after
        is_blacklisted, blacklisted_content = self.is_blacklisted(message)
        if not is_blacklisted:
            return

        await message.delete()
        if self.is_being_spammed(message.created_at):
            return

        try:
            with open('data/blacklist_userlog.log') as f:
                userlog: list[str] = json.load(f)
        except FileNotFoundError:
            userlog: list[str] = []
        userlog.append(self.bot.localizations.BLACKLISTED_POST.format(message.author.name, blacklisted_content))
        with open('data/blacklist_userlog.log', 'w', encoding='utf-8') as f:
            json.dump(userlog, f, ensure_ascii=False, indent=4)
        await message.channel.send(self.bot.localizations.BLACKLISTED.format(message.author.mention), delete_after=8.0)

        user: User = self.bot.get_user_by_id(message.author.id)
        if not user or not user.is_in_guild or user.level >= 5:
            return

        if user.id in self.kicklist and self.kicklist[user.id] + 600 > time.time():
            await self.bot.send_dm(message.author, self.bot.localizations.BLACKLISTED_BAN_DM.format(blacklisted_content))
            await message.guild.ban(message.author,
                                    reason=self.bot.localizations.BLACKLISTED_BAN_LOG.format(blacklisted_content))
            await message.channel.send(self.bot.localizations.BLACKLISTED_BAN_ANNOUNCE.format(message.author.mention))
            return
        elif user.id in self.kicklist:
            del self.kicklist[user.id]
        await self.bot.send_dm(message.author, self.bot.localizations.BLACKLISTED_KICK_DM.format(blacklisted_content))
        await message.author.kick(reason=self.bot.localizations.BLACKLISTED_KICK_LOG.format(blacklisted_content))
        self.kicklist[user.id] = time.time()
