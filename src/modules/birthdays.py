from __future__ import annotations
import discord
import json
from datetime import datetime, date
from dateutil.tz import gettz
from dataclasses import field, dataclass, asdict
from src.localizations import Localizations
from src.objects import User
from src.constants import DEFAULT_TIMEZONE, SERVER_ID, ROLES, CHANNELS
import src.functions as functions
from .module import Module

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
class Plugin(Module):
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
                                    description=Localizations.get('BIRTHDAY_DESCRIPTION'), commands_per_day=10,
                                    timeout=10)
        async def birthday(interaction: discord.Interaction, käyttäjä: discord.User = None, päivä: int = 0,
                           kuukausi: int = 0, vuosi: int = 0):
            await self.bot.commands.commands['synttärit'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä,
                birthday=f"{päivä}.{kuukausi}.{vuosi}"
            )

        await self.sync_birthdays(datetime.now(tz=gettz(DEFAULT_TIMEZONE)))

    async def birthday(self, user: User, message: discord.Message | None = None,
                       interaction: discord.Interaction | None = None,
                       target_user: User | None = None,
                       birthday: str | None = ''):
        if not target_user:
            await self.bot.commands.error(Localizations.get('USER_NOT_FOUND'), message, interaction)
            return
        date_now: datetime = datetime.now(tz=gettz(DEFAULT_TIMEZONE))
        if target_user == user and birthday and birthday != '0.0.0':
            if user.id in self.birthdays and \
                    date_now.timestamp() - self.birthdays.get(user.id).timestamp < BIRTHDAY_UPDATE_INTERVAL:
                ok_day = functions.utc_to_local(datetime.fromtimestamp(self.birthdays[user.id].timestamp))
                ok_delta = date_now - ok_day
                days_until = BIRTHDAY_UPDATE_INTERVAL / 60 / 60 / 24 - ok_delta.days
                msg = Localizations.get('BIRTHDAY_WAIT').format(int(days_until))
                await self.bot.commands.error(msg, message, interaction)
                return

            try:
                birthday_date = functions.utc_to_local(datetime.strptime(birthday.split()[0], '%d.%m.%Y'))
                delta = date_now - birthday_date
                if delta.days < 13 * 365:
                    await self.bot.commands.error(Localizations.get('BIRTHDAY_UNDERAGE'), message, interaction)
                    return
                elif delta.days > 90 * 365:
                    await self.bot.commands.error(Localizations.get('BIRTHDAY_TOO_OLD'), message, interaction)
                    return
                birthday_obj = Birthday(birthday_date.year, birthday_date.month, birthday_date.day,
                                        int(date_now.timestamp()))
                self.birthdays[user.id] = birthday_obj
                msg = Localizations.get('BIRTHDAY_SET').format(birthday_obj.day, birthday_obj.month)
                self.save_birthdays()
                await self.bot.commands.message(msg, message, interaction)
                return
            except Exception as e:
                print(e)
                await self.bot.commands.error(Localizations.get('BIRTHDAY_ERROR'), message, interaction)
                return
        if target_user.id not in self.birthdays:
            msg = Localizations.get('BIRTHDAY_NOT_YET_SET').format(target_user.name)
            await self.bot.commands.error(msg, message, interaction)
            return

        usr_birthday: Birthday = self.birthdays[target_user.id]
        target_birthday = date(year=date_now.year, month=usr_birthday.month, day=usr_birthday.day)
        if target_birthday < date_now.date():
            target_birthday = date(date_now.year + 1, month=usr_birthday.month, day=usr_birthday.day)
        difference = target_birthday - date_now.date()
        msg = Localizations.get('BIRTHDAY_TODAY').format(target_user.name) if not difference.days else \
            Localizations.get('BIRTHDAY_DELTA').format(target_user.name, target_birthday.day, target_birthday.month,
                                                       difference.days)
        await self.bot.commands.message(msg, message, interaction)

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
        birthday_role: discord.Role = self.bot.server.get_role(ROLES.BIRTHDAY)

        for usr in self.bot.users:
            if not usr.is_in_guild:
                continue
            if ROLES.BIRTHDAY in usr.roles and not self.has_birthday(usr, date_now):
                member = self.bot.server.get_member(usr.id)
                await member.remove_roles(birthday_role)
            elif ROLES.BIRTHDAY not in usr.roles and self.has_birthday(usr, date_now):
                member = self.bot.server.get_member(usr.id)
                await member.add_roles(birthday_role)

                if member.id == 212594150124552192:
                    await self.bot.client.get_channel(CHANNELS.YLEINEN).send(
                        Localizations.get('BIRTHDAY_ANNOUNCE_JUSU').format(member.mention),
                        file=discord.File(open('assets/birthdays/gondola_birthday.mp4', 'rb'),
                                          filename='synttarit.mp4'))
                else:
                    await self.bot.client.get_channel(CHANNELS.YLEINEN).send(
                        Localizations.get('BIRTHDAY_ANNOUNCE').format(member.mention),
                        file=discord.File(open('assets/birthdays/gondola_birthday.mp4', 'rb'),
                                          filename="synttarit.mp4"))
