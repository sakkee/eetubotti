"""
Saves anttuboy's messages in a data folder so that anttubott can use them. Can be easily edited to store other
user's messages and files; just edit ANTTU_IDS.

The messages are stored on data/anttuboy.json and the files are stored on data/anttubott/
"""

from __future__ import annotations
import discord
import os
import json
from dataclasses import field, dataclass, asdict
from src.constants import CHANNELS, LEVEL_CHANNELS
from .module import Module

ANTTU_IDS: list[int] = [424582449666719745, 295540519616905216, 660316187594457089]


@dataclass
class Attachment:
    id: int = 0
    filename: str = ""


@dataclass
class Msg:
    id: int = 0
    text: str = ""
    attachments: list[Attachment] = field(default_factory=list)

    @classmethod
    def from_json(cls, json_data: dict) -> Msg:
        attachments: list[Attachment] = [Attachment(x.get('id'), x.get('filename')) \
                                         for x in json_data.get('attachments')]
        return cls(id=json_data.get('id'), text=json_data.get('text'), attachments=attachments)

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class Plugin(Module):
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

    @staticmethod
    def is_anttuboy(id: int) -> bool:
        return id in ANTTU_IDS

    async def on_message(self, message: discord.Message):
        if not self.is_anttuboy(message.author.id):
            return
        if message.channel.id not in LEVEL_CHANNELS:
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
        async for msg in self.bot.server.get_channel(CHANNELS.YLEINEN).history(limit=20000000):
            if not self.is_anttuboy(msg.author.id) and msg.id not in message_ids:
                continue
            await self.save_message(msg)
            i += 1
            print(i, msg.content)

        async for msg in self.bot.server.get_channel(CHANNELS.YLEINEN2).history(limit=20000000):
            if not self.is_anttuboy(msg.author.id) and msg.id not in message_ids:
                continue

            await self.save_message(msg)
            i += 1
            print(i)

        self.save_anttumessages()
