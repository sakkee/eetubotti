import asyncio
import discord
import json
from dataclasses import field, dataclass
from src.localizations import Localizations
from src.objects import User
from .module import Module


@dataclass
class Plugin(Module):
    loves: dict[int, User] = field(default_factory=dict)

    async def on_ready(self):
        self.load_loves()

        @self.bot.commands.register(command_name='rakkaus', function=self.love,
                                    description=Localizations.get('LOVE_DESCRIPTION'), commands_per_day=6)
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
            await self.bot.commands.error(Localizations.get('USER_NOT_FOUND'), message, interaction)
            return

        if user.id not in self.loves and target_user.id == user.id:
            await self.bot.commands.error(Localizations.get('NO_LOVE'), message, interaction)
            return

        if target_user.id != user.id:
            self.loves[user.id] = self.bot.get_user_by_id(target_user.id)
            self.save_loves()
        if self.loves[user.id].id not in self.loves or self.loves[self.loves[user.id].id].id != user.id:
            msg = Localizations.get('WRONG_LOVE').format(f'<@{user.id}>', user.name,
                                                         self.loves[user.id].name)
        else:
            msg = Localizations.get('LOVING').format(f'<@{user.id}>', user.name,
                                                     f'<@{self.loves[user.id].id}>', self.loves[user.id].name)
        await self.bot.commands.message(msg, message, interaction)

    def load_loves(self):
        try:
            with open('data/loves.json', 'r') as f:
                loves = json.load(f)
                for user_id in loves:
                    self.loves[int(user_id)] = self.bot.get_user_by_id(loves[user_id])
        except FileNotFoundError:
            pass

    def save_loves(self):
        with open('data/loves.json', 'w') as f:
            loves = {}
            for user_id in self.loves:
                loves[user_id] = self.loves[user_id].id
            json.dump(loves, f)
