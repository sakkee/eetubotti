import asyncio
import discord
import json
import random
from dataclasses import field, dataclass
from src.localizations import Localizations
from src.objects import User
from .module import Module


@dataclass
class Plugin(Module):
    async def on_ready(self):
        @self.bot.commands.register(command_name='tuplat', function=self.double,
                                    description=Localizations.get('DOUBLE_DESCRIPTION'), commands_per_day=15, timeout=5)
        async def double(interaction: discord.Interaction):
            await self.bot.commands.commands['tuplat'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        @self.bot.commands.register(command_name='get', function=self.get,
                                    description=Localizations.get('GET_DESCRIPTION'), commands_per_day=15, timeout=5)
        async def get(interaction: discord.Interaction):
            await self.bot.commands.commands['get'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

    async def double(self, user: User, message: discord.Message | None = None,
                     interaction: discord.Interaction | None = None, **kwargs):
        number: str = str(random.randrange(100))
        number = "0" + number if len(number) == 1 else number
        if len(number) < 1 or number[0] != number[1]:
            await self.bot.commands.error(Localizations.get('DOUBLE_NO_WIN').format(number), message, interaction)
            return
        await self.bot.commands.message(Localizations.get('DOUBLE_WIN').format(number), message, interaction)

    async def get(self, user: User, message: discord.Message | None = None,
                  interaction: discord.Interaction | None = None, **kwargs):
        number: str = str(random.randrange(1000000))
        number = "0" + number if len(number) == 1 else number
        if len(number) < 1 or number[-1] != number[-2]:
            await self.bot.commands.error(Localizations.get('DOUBLE_NO_WIN').format(number), message, interaction)
            return
        if len(number) >= 6 and number[-1] == number[-2] == number[-3] == number[-4] == number[-5] == number[-6]:
            await self.bot.commands.message(Localizations.get('GET_BIG_WIN').format(number), message, interaction)
            return
        if len(number) >= 5 and number[-1] == number[-2] == number[-3] == number[-4] == number[-5]:
            await self.bot.commands.message(Localizations.get('GET_PENTAS').format(number), message, interaction)
            return
        if len(number) >= 4 and number[-1] == number[-2] == number[-3] == number[-4]:
            await self.bot.commands.message(Localizations.get('GET_QUADROS').format(number), message, interaction)
            return
        if len(number) >= 3 and number[-1] == number[-2] == number[-3]:
            await self.bot.commands.message(Localizations.get('GET_TRIPLE').format(number), message, interaction)
            return
        await self.bot.commands.message(Localizations.get('DOUBLE_WIN').format(number), message, interaction)

