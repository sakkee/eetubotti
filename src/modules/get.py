"""
Get/roll/getme/checkem plugin.

Commands:
    !tuplat
    !get
"""

import discord
import random
from dataclasses import dataclass
from src.objects import User
from src.basemodule import BaseModule


@dataclass
class Plugin(BaseModule):
    async def on_ready(self):
        @self.bot.commands.register(command_name='tuplat', function=self.double,
                                    description=self.bot.localizations.DOUBLE_DESCRIPTION,
                                    commands_per_day=15, timeout=5)
        async def double(interaction: discord.Interaction):
            await self.bot.commands.commands['tuplat'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        @self.bot.commands.register(command_name='get', function=self.get,
                                    description=self.bot.localizations.GET_DESCRIPTION,
                                    commands_per_day=15, timeout=5)
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
            await self.bot.commands.message(self.bot.localizations.DOUBLE_NO_WIN.format(number),
                                            message, interaction, delete_after=8)
            return
        await self.bot.commands.message(self.bot.localizations.DOUBLE_WIN.format(number), message, interaction)

    async def get(self, user: User, message: discord.Message | None = None,
                  interaction: discord.Interaction | None = None, **kwargs):
        number: str = str(random.randrange(1000000))
        number = "0" + number if len(number) == 1 else number
        if len(number) < 1 or number[-1] != number[-2]:
            await self.bot.commands.message(self.bot.localizations.DOUBLE_NO_WIN.format(number),
                                            message, interaction, delete_after=8)
            return
        if len(number) >= 6 and number[-1] == number[-2] == number[-3] == number[-4] == number[-5] == number[-6]:
            await self.bot.commands.message(self.bot.localizations.GET_BIG_WIN.format(number), message, interaction)
            return
        if len(number) >= 5 and number[-1] == number[-2] == number[-3] == number[-4] == number[-5]:
            await self.bot.commands.message(self.bot.localizations.GET_PENTAS.format(number), message, interaction)
            return
        if len(number) >= 4 and number[-1] == number[-2] == number[-3] == number[-4]:
            await self.bot.commands.message(self.bot.localizations.GET_QUADROS.format(number), message, interaction)
            return
        if len(number) >= 3 and number[-1] == number[-2] == number[-3]:
            await self.bot.commands.message(self.bot.localizations.GET_TRIPLE.format(number), message, interaction)
            return
        await self.bot.commands.message(self.bot.localizations.DOUBLE_WIN.format(number), message, interaction)
