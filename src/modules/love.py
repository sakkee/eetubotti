"""
The love plugin. Users can set whom they love or are with.

Commands:
    !rakkaus
"""
import discord
import json
from dataclasses import field, dataclass
from src.objects import User
from src.basemodule import BaseModule
import random
import time
from datetime import datetime


@dataclass
class Plugin(BaseModule):
    loves: dict[int, int] = field(default_factory=dict)

    def clear_loves(self):
        self.loves.clear()

    async def on_ready(self):
        #self.load_loves()

        @self.bot.commands.register(command_name='rakkaus', function=self.love,
                                    description=self.bot.localizations.LOVE_DESCRIPTION, commands_per_day=6)
        async def love(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['rakkaus'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

    async def love(self, user: User, message: discord.Message | None = None,
                   interaction: discord.Interaction | None = None,
                   target_user: User | None = None,
                   **kwargs):

        if not target_user or not self.bot.get_user_by_id(target_user.id):
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return

        love:int=-1

        if user.id not in self.loves.keys():
            users=[]
            for x in self.bot.users:
                if x.is_in_guild and x.level>10 and time.time() - x.stats.last_post_time < 24*60*60:
                    users.append(x)

            random.shuffle(users)

            love=users[random.randint(0,len(users)-1)].id

            for x in range(50):
                if love in self.loves.keys():
                    random.seed(time.time()+x+(x*3))
                    love=users[random.randint(0,len(users)-1)].id
                    if x==49:   # Ebin fail-safe :-D
                        self.loves[user.id]=user.id
                        love=user.id
                        print(love,user.id)
                else:
                    break


            self.loves[user.id]=love
            self.loves[love]=user.id
        else:
            love=self.loves[user.id]
        
        if love==user.id:
            msg=self.bot.localizations.SELF_LOVE.format(f'<@{user.id}>')
        else:
            msg=self.bot.localizations.LOVING.format(f'<@{user.id}>', user.name,f'<@{love}>',self.bot.get_user_by_id(love).name)

        await self.bot.commands.message(msg,message,interaction)



    async def on_new_day(self, date_now: datetime):
        self.clear_loves()

    """async def love(self, user: User, message: discord.Message | None = None,
                   interaction: discord.Interaction | None = None,
                   target_user: User | None = None,
                   **kwargs):
        if not target_user or not self.bot.get_user_by_id(target_user.id):
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return

        if user.id not in self.loves and target_user.id == user.id:
            await self.bot.commands.error(self.bot.localizations.NO_LOVE, message, interaction)
            return

        if target_user.id != user.id:
            self.loves[user.id] = self.bot.get_user_by_id(target_user.id)
            self.save_loves()
        if self.loves[user.id].id not in self.loves or self.loves[self.loves[user.id].id].id != user.id:
            msg = self.bot.localizations.WRONG_LOVE.format(f'<@{user.id}>', user.name, self.loves[user.id].name)
        else:
            msg = self.bot.localizations.LOVING.format(f'<@{user.id}>', user.name,
                                                       f'<@{self.loves[user.id].id}>', self.loves[user.id].name)
        await self.bot.commands.message(msg, message, interaction)

    def load_loves(self):
        try:
            with open('data/loves.json', 'r') as f:
                loves = json.load(f)
                for user_id in loves:
                    self.loves[int(user_id)] = self.bot.get_user_by_id(loves[user_id])
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            pass

    def save_loves(self):
        with open('data/loves.json', 'w') as f:
            loves = {}
            for user_id in self.loves:
                loves[user_id] = self.loves[user_id].id
            json.dump(loves, f)"""
