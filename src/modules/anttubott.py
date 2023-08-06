"""
Saves anttuboy's messages in a data folder so that anttubott can use them. Can be easily edited to store other
user's messages and files; just edit ANTTU_IDS.

The messages are stored on data/anttuboy.json and the files are stored on data/anttubott/
"""

from __future__ import annotations
import asyncio
import discord
import os
import json
from dataclasses import field, dataclass, asdict
from src.basemodule import BaseModule

ANTTU_IDS: list[int] = [424582449666719745, 295540519616905216, 660316187594457089]
# these words will trigger a ban if found in anttubott's messages
BAN_TRIGGERS: list[str] = ["bann", "Ban", "BAN", "vaan ban", "Pls ban", "ban Pliist", "ban Tulil", "confiremd ban",
                           "ban tälle", "tämä henkilö haluaa ban", "bänn", "Bän", "ja bän"]
# and they will be ignored if any of these is found in the messages
BAN_IGNORES: list[str] = ["BANNAA MUA", "voitko", "bannaa ny heti anttua", "bannaa @", "saanko luvan bännää",
                          "voidaanko", "voinko", "voisit vaa bänniä", "oisko", "haluutko", "haluatko", "ääntä",
                          "voiks", "tällä siin servus", "kannattaa", "keimo heimoa", "haluun sinulta bännit",
                          "nii voi olla helppo bänni", "luuletko", "Anna bännit", "Miks annat", "koita ite bännää",
                          "saanko luvan bännää"]


@dataclass
class Attachment:
    id: int
    filename: str


@dataclass
class Msg:
    id: int
    text: str
    attachments: list[Attachment] = field(default_factory=list)

    @classmethod
    def from_json(cls, json_data: dict) -> Msg:
        attachments: list[Attachment] = [Attachment(x.get('id'), x.get('filename')) \
                                         for x in json_data.get('attachments')]
        return cls(id=json_data.get('id'), text=json_data.get('text'), attachments=attachments)

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class Plugin(BaseModule):
    enabled: bool = True
    anttu_messages: list[Msg] = field(default_factory=list)
    increment: int = 0

    def __post_init__(self):
        if not os.path.exists(f'data/anttubott/'):
            os.mkdir(f'data/anttubott/')
        try:
            with open('data/anttuboy.json', 'r', encoding='utf-8') as f:
                messages: list[dict[str, int | str | dict]] = json.load(f)
                for message in messages:
                    self.anttu_messages.append(Msg.from_json(message))
        except FileNotFoundError:
            with open('data/anttuboy.json', 'w') as f:
                json.dump([], f)

    async def on_ready(self):
        pass

    def load_anttumessages(self):
        with open('data/anttuboy.json', 'r') as f:
            messages: list[dict[str, int | str | list]] = json.load(f)
            for message in messages:
                self.anttu_messages.append(Msg.from_json(message))

    def save_anttumessages(self):
        messages: list[dict[str, int | str | list]] = [x.to_json() for x in self.anttu_messages]
        with open('data/anttuboy.json', 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)

    async def anttubott_ban_triggers(self, message: discord.Message):
        # no one to ban
        if not message.mentions:
            return

        ban_trigger_found: bool = False
        for ban_trigger in BAN_TRIGGERS:
            if ban_trigger in message.content:
                ban_trigger_found = True
                break
        if not ban_trigger_found:
            return

        ban_ignore_found: bool = False
        for ban_ignore in BAN_IGNORES:
            if ban_ignore in message.content:
                ban_ignore_found = True
                break
        if ban_ignore_found:
            return

        target_discord_user: discord.User = message.mentions[0]
        target_user = self.bot.get_user_by_id(target_discord_user.id)
        if not target_user:
            return

        if target_user.is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
            await message.reply(self.bot.localizations.BAN_CANT_BAN.format(target_user.name))
            return

        await message.channel.send(self.bot.localizations.ANTTU_BAN_ANNOUNCE.format(target_discord_user.mention))
        await asyncio.sleep(5)
        await message.channel.send(self.bot.localizations.BAN_ANNOUNCE_5S.format(target_discord_user.mention))
        await asyncio.sleep(5)
        reason: str = self.bot.localizations.ANTTU_BAN_REASON
        try:
            await target_discord_user.send(
                self.bot.localizations.BAN_DM.format(self.bot.config.DEFAULT_BAN_LENGTH_HOURS, reason)
            )
        except:
            pass
        try:
            await message.guild.ban(target_discord_user, reason=reason, delete_message_days=0)
            await message.channel.send(
                self.bot.localizations.BAN_CHANNEL_ANNOUNCE.format(target_user.name,
                                                                   self.bot.config.DEFAULT_BAN_LENGTH_HOURS,
                                                                   reason, message.author.mention))
        except:
            await message.channel.send(self.bot.localizations.BAN_CANT_BAN.format(target_user.name))

    @staticmethod
    def is_anttuboy(id: int) -> bool:
        return id in ANTTU_IDS

    async def on_message(self, message: discord.Message):
        if not self.is_anttuboy(message.author.id):
            if message.author.id == 623974457404293130:
                await self.anttubott_ban_triggers(message)
            return
        if message.channel.id not in self.bot.config.LEVEL_CHANNELS:
            return

        await self.save_message(message)

        self.increment += 1
        if self.increment // 10:
            self.increment = 0
            self.save_anttumessages()

    async def save_message(self, message: discord.Message):
        attachments: list[Attachment] = []
        for attachment in message.attachments:
            await attachment.save(f'data/anttubott/{attachment.id}_{attachment.filename}')
            attachments.append(Attachment(attachment.id, attachment.filename))
        self.anttu_messages.append(Msg(message.id, message.content, attachments))

    async def refresh_anttumessages(self):
        messages: list[dict[str, int | str]] = self.bot.database.get_messages_by_user(ANTTU_IDS)
        saved_messages: list[int] = [x.id for x in self.anttu_messages]
        message_ids: list[int] = [x['id'] for x in messages]
        i: int = 0
        async for msg in self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL).history(limit=20000000):
            if not self.is_anttuboy(msg.author.id) and msg.id not in message_ids:
                continue
            await self.save_message(msg)
            i += 1
            print(i, msg.content)

        async for msg in self.bot.server.get_channel(self.bot.config.CHANNEL_GENERAL2).history(limit=20000000):
            if not self.is_anttuboy(msg.author.id) and msg.id not in message_ids:
                continue

            await self.save_message(msg)
            i += 1
            print(i)

        self.save_anttumessages()
