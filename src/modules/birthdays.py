"""
This module keeps track of the birthdays. The birthdays are stored in data/birthdays.json.

Commands:
    !synttärit
    !synttärisankarit
"""

from __future__ import annotations
import discord
import json
from datetime import datetime, date
from dateutil.tz import gettz
from dataclasses import field, dataclass, asdict
from src.objects import User
import src.functions as functions
from src.basemodule import BaseModule

BIRTHDAY_UPDATE_INTERVAL: int = 6 * 30 * 24 * 60 * 60  # 6 months


@dataclass
class Birthday:
    year: int = 0
    month: int = 0
    day: int = 0
    timestamp: int = 0

    @classmethod
    def from_json(cls, json_data: dict) -> Birthday:
        return cls(year=json_data.get('year'), month=json_data.get('month'),
                   day=json_data.get('day'), timestamp=json_data.get('timestamp'))

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class Plugin(BaseModule):
    birthdays: dict[int, Birthday] = field(default_factory=dict)

    def load_birthdays(self):
        try:
            with open('data/birthdays.json', 'r') as f:
                birthdays = json.load(f)
                for user_id in birthdays:
                    self.birthdays[int(user_id)] = Birthday.from_json(birthdays[user_id])
        except FileNotFoundError:
            pass

    def save_birthdays(self):
        with open('data/birthdays.json', 'w') as f:
            birthdays = {}
            for user_id in self.birthdays:
                birthdays[str(user_id)] = self.birthdays[user_id].to_json()
            json.dump(birthdays, f)

    async def on_new_day(self, date_now: datetime):
        await self.sync_birthdays(date_now)

    async def on_ready(self):
        self.load_birthdays()

        @self.bot.commands.register(command_name='synttärit', function=self.birthday,
                                    description=self.bot.localizations.BIRTHDAY_DESCRIPTION, commands_per_day=10,
                                    timeout=10)
        async def birthday(interaction: discord.Interaction, käyttäjä: discord.User = None, päivä: int = 0,
                           kuukausi: int = 0, vuosi: int = 0):
            await self.bot.commands.commands['synttärit'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä,
                birthday=f"{päivä}.{kuukausi}.{vuosi}"
            )

        @self.bot.commands.register(command_name='synttärisankarit', function=self.next_birthdays,
                                    description=self.bot.localizations.NEXT_BIRTHDAYS_DESCRIPTION,
                                    commands_per_day=10, timeout=10)
        async def next_birthdays(interaction: discord.Interaction):
            await self.bot.commands.commands['synttärisankarit'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        await self.sync_birthdays(datetime.now(tz=gettz(self.bot.config.TIMEZONE)))

    async def birthday(self, user: User, message: discord.Message | None = None,
                       interaction: discord.Interaction | None = None,
                       target_user: User | None = None,
                       birthday: str | None = ''):
        if not target_user:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        date_now: datetime = datetime.now(tz=gettz(self.bot.config.TIMEZONE))
        try:
            birthday = message.content.split()[1] if (message and '.' in message.content.split()[1]) else birthday
        except IndexError:
            pass
        if target_user == user and birthday and birthday != '0.0.0':
            if user.id in self.birthdays and \
                    date_now.timestamp() - self.birthdays.get(user.id).timestamp < BIRTHDAY_UPDATE_INTERVAL:
                ok_day = functions.utc_to_local(datetime.fromtimestamp(self.birthdays[user.id].timestamp),
                                                self.bot.config.TIMEZONE)
                ok_delta = date_now - ok_day
                days_until = BIRTHDAY_UPDATE_INTERVAL / 60 / 60 / 24 - ok_delta.days
                msg = self.bot.localizations.BIRTHDAY_WAIT.format(int(days_until))
                await self.bot.commands.error(msg, message, interaction)
                return

            try:
                birthday_date = functions.utc_to_local(datetime.strptime(birthday.split()[0], '%d.%m.%Y'),
                                                       self.bot.config.TIMEZONE)
                delta = date_now - birthday_date
                if delta.days < 13 * 365:
                    await self.bot.commands.error(self.bot.localizations.BIRTHDAY_UNDERAGE, message, interaction)
                    return
                elif delta.days > 90 * 365:
                    await self.bot.commands.error(self.bot.localizations.BIRTHDAY_TOO_OLD, message, interaction)
                    return
                birthday_obj = Birthday(birthday_date.year, birthday_date.month, birthday_date.day,
                                        int(date_now.timestamp()))
                self.birthdays[user.id] = birthday_obj
                msg = self.bot.localizations.BIRTHDAY_SET.format(birthday_obj.day, birthday_obj.month)
                self.save_birthdays()
                await self.bot.commands.message(msg, message, interaction)
                return
            except Exception as e:
                print(e)
                await self.bot.commands.error(self.bot.localizations.BIRTHDAY_ERROR, message, interaction)
                return
        if target_user.id not in self.birthdays or self.birthdays[target_user.id].year == 0:
            msg = self.bot.localizations.BIRTHDAY_NOT_YET_SET.format(target_user.name)
            await self.bot.commands.error(msg, message, interaction)
            return

        usr_birthday: Birthday = self.birthdays[target_user.id]
        target_birthday = date(year=date_now.year, month=usr_birthday.month, day=usr_birthday.day)
        if target_birthday < date_now.date():
            target_birthday = date(date_now.year + 1, month=usr_birthday.month, day=usr_birthday.day)
        difference = target_birthday - date_now.date()
        msg = self.bot.localizations.BIRTHDAY_TODAY.format(target_user.name) if not difference.days else \
            self.bot.localizations.BIRTHDAY_DELTA.format(target_user.name, target_birthday.day,
                                                         target_birthday.month, difference.days)
        await self.bot.commands.message(msg, message, interaction, delete_after=10)

    def get_birthday(self, user: User) -> Birthday | None:
        return self.birthdays.get(user.id, None)

    def has_birthday(self, user, date_now: datetime) -> bool:
        birthday: Birthday = self.get_birthday(user)
        if not birthday:
            return False
        if date_now.month != birthday.month or date_now.day != birthday.day:
            return False
        return True

    async def sync_birthdays(self, date_now: datetime):
        birthday_role: discord.Role = self.bot.server.get_role(self.bot.config.ROLE_BIRTHDAY)

        for usr in self.bot.users:
            if not usr.is_in_guild:
                continue
            if self.bot.config.ROLE_BIRTHDAY in usr.roles and not self.has_birthday(usr, date_now):
                member = await self.bot.server.fetch_member(usr.id)
                await member.remove_roles(birthday_role)
            elif self.bot.config.ROLE_BIRTHDAY not in usr.roles and self.has_birthday(usr, date_now):
                member = await self.bot.server.fetch_member(usr.id)
                await member.add_roles(birthday_role)

                if member.id == 212594150124552192:
                    await self.bot.client.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                        self.bot.localizations.BIRTHDAY_ANNOUNCE_JUSU.format(member.mention),
                        file=discord.File(open('assets/birthdays/gondola_birthday.mp4', 'rb'),
                                          filename='synttarit.mp4'))
                else:
                    await self.bot.client.get_channel(self.bot.config.CHANNEL_GENERAL).send(
                        self.bot.localizations.BIRTHDAY_ANNOUNCE.format(member.mention),
                        file=discord.File(open('assets/birthdays/gondola_birthday.mp4', 'rb'),
                                          filename="synttarit.mp4"))

    async def next_birthdays(self, user: User, message: discord.Message | None = None,
                             interaction: discord.Interaction | None = None, **kwargs):
        birthdays: list[tuple[int, datetime]] = [(x, datetime(2000, self.birthdays[x].month, self.birthdays[x].day))
                                                 for x in self.birthdays if self.birthdays[x].year]
        sorted_birthdays: list[tuple[int, datetime]] = sorted(birthdays, key=lambda x: x[1])
        next_birthdays: list[int] = []
        datenow = datetime.today()
        for birthday in sorted_birthdays:
            if birthday[1].month < datenow.month:
                continue
            if birthday[1].month == datenow.month and birthday[1].day < datenow.day:
                continue
            next_birthdays.append(birthday[0])
        for birthday in sorted_birthdays:
            if birthday[1].month > datenow.month:
                break
            if birthday[1].month == datenow.month and birthday[1].day > datenow.day:
                break
            next_birthdays.append(birthday[0])
        counter: int = 1
        constructing_string = self.bot.localizations.NEXT_BIRTHDAYS_TITLE
        for user_id in next_birthdays:
            if counter > 10:
                break
            user: User = self.bot.get_user_by_id(user_id)
            if not user or not user.is_in_guild:
                continue
            birthday: Birthday = self.birthdays[user_id]
            constructing_string += self.bot.localizations.NEXT_BIRTHDAYS_ROW.format(birthday.day, birthday.month,
                                                                                    user.name)
            counter += 1
        await self.bot.commands.message(constructing_string, message, interaction, delete_after=15)
