"""
IRC-Galleria module. Every day each user gets a random IRC-galleria user they are supposed to be that day.

Commands:
    !irc
"""

from datetime import datetime
import discord
import requests
from pyquery import PyQuery
from src.objects import User, Irc
from src.basemodule import BaseModule

base_link: str = 'https://irc-galleria.net/user/'
random: str = 'https://irc-galleria.net/random'


class Plugin(BaseModule):
    def clear_ircs(self):
        for user in self.bot.users:
            user.irc = None

    async def on_ready(self):
        @self.bot.commands.register(command_name='irc', function=self.ircgalleria,
                                    description=self.bot.localizations.IRC_DESCRIPTION, commands_per_day=5)
        @discord.app_commands.checks.has_permissions(
            embed_links=True
        )
        async def irc(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['irc'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

    async def on_new_day(self, date_now: datetime):
        self.clear_ircs()

    async def ircgalleria(self, user: User, message: discord.Message | None = None,
                          interaction: discord.Interaction | None = None,
                          target_user: User | None = None,
                          **kwargs):
        if not target_user:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        if target_user.irc is not None:
            user_name: str = target_user.irc.name
            photo_link: str = target_user.irc.photo
            link: str = target_user.irc.link
        else:
            headers: dict[str, str] = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
            }
            while True:
                try:    #AMK lopputyö
                    a = requests.get(url=random, headers=headers,timeout=5)
                    pq = PyQuery(a.text)
                    user_name = pq('meta[name=title]').attr('content')
                    if user_name is None:
                        continue
                    link = base_link + user_name
                    photo_link = pq('img.photo').attr('src')
                    target_user.irc = Irc(user_name, link, photo_link)
                    break
                except Exception as e:
                    print(message.content)
                    print(e)
                    break

        embed = discord.Embed(title=self.bot.localizations.IRC_TITLE.format(target_user.name, user_name),
                              url=link)
        embed.set_image(url=photo_link)

        await message.reply(embed=embed, delete_after=30) if message else \
            await interaction.response.send_message(embed=embed, delete_after=30)
        if message:
            await message.delete(delay=30)
