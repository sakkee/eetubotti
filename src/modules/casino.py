"""
Casino module, to keep track of user balances and the casinos. The casino assets are found in assets/casino/ and the
postable images are in data/casino/.

Commands:
    !kasino
    !saldo
    !saldot
    !give
    !maksuhäiriöt
"""

from dataclasses import field, dataclass
from src.objects import User
import src.functions as functions
from src.basemodule import BaseModule
import os
import discord
import datetime
import asyncio
from PIL import Image, ImageDraw, ImageFont
import string
import random
import json
import shutil


def get_filename(name: str, icon: bool = False) -> str:
    return f'assets/casino/{name}' if not icon else f'assets/casino/icons/{name}'


def get_data_filename(name: str, filetype: str = "png") -> str:
    return f'data/casino/{name}.{filetype}'


class Constants:
    ADMIN_COOLDOWN: int = 5 * 60
    USER_COOLDOWN: int = 60 * 60
    MAX_AMOUNT: int = 1000000
    MIN_AMOUNT: int = 1
    TILESIZE: tuple[int, int] = (39, 51)
    BG_SIZE: tuple[int, int] = (365, 220)
    ROWS: int = 3
    COLUMNS: int = 3
    MAXIMUM: int = 32
    POINTS_TO_BALANCE_MULTIPLIER: int = 10

    WIN_LINES: dict[str, list[tuple[int, int]]] = {
        '1': [(0, 1), (1, 1), (2, 1)],
        '2': [(0, 2), (1, 2), (2, 2)],
        '3': [(0, 0), (1, 0), (2, 0)],
        '4': [(0, 2), (1, 1), (2, 0)],
        '5': [(0, 0), (1, 1), (2, 2)]
    }

    TILE_POSITIONS: list[list[tuple[int, int]]] = [
        [(96, 17), (96, 85), (96, 153)],
        [(161, 17), (161, 85), (161, 153)],
        [(226, 17), (226, 85), (226, 153)]
    ]

    POSSIBLE_WINNING_LINES = {
        (2, 0): ['3', '4'],
        (2, 1): ['1'],
        (2, 2): ['2', '5']
    }


class Images:
    lost_image: Image.Image = Image.open(get_filename('lost.png')).convert('RGBA').resize(Constants.BG_SIZE)
    won_image: Image.Image = Image.open(get_filename('won.png')).convert('RGBA').resize(Constants.BG_SIZE)
    title_image: Image.Image = Image.open(get_filename('title.png')).convert('RGBA').resize(Constants.BG_SIZE)
    bonus_image: Image.Image = Image.open(get_filename('bonus.png')).convert('RGBA').resize(Constants.BG_SIZE)
    font: ImageFont.FreeTypeFont = ImageFont.truetype(get_filename('comicbold.ttf'), 40)
    im_background: Image.Image = Image.open(get_filename('unpulled.png')).convert('RGBA').resize(
        Constants.BG_SIZE)
    anttu_lose: Image.Image = Image.open(get_filename('anttu_bonus_lose.png')).convert('RGBA').resize(Constants.BG_SIZE)
    anttu_win: Image.Image = Image.open(get_filename('anttu_bonus_win.png')).convert('RGBA').resize(Constants.BG_SIZE)

    win_images: dict[str, Image] = {
        '1': Image.open(get_filename('linja1.png')),
        '2': Image.open(get_filename('linja2.png')),
        '3': Image.open(get_filename('linja3.png')),
        '4': Image.open(get_filename('linja4.png')),
        '5': Image.open(get_filename('linja5.png'))
    }
    partial_images = {
        '1': win_images['1'].crop((0, 0, 203, Constants.BG_SIZE[1])),
        '2': win_images['2'].crop((0, 0, 203, Constants.BG_SIZE[1])),
        '3': win_images['3'].crop((0, 0, 203, Constants.BG_SIZE[1])),
        '4': win_images['4'].crop((0, 0, 203, Constants.BG_SIZE[1])),
        '5': win_images['5'].crop((0, 0, 203, Constants.BG_SIZE[1]))
    }


@dataclass
class Chip:
    name: str
    filename: str
    prevelance: int
    win: int
    joker: int
    file: Image = None

    def __post_init__(self):
        self.filename = get_filename(self.filename, True)
        self.file = Image.open(self.filename).resize(Constants.TILESIZE)


@dataclass
class Plugin(BaseModule):
    casino_times: dict = field(default_factory=dict)
    casino_order: list[int] = field(default_factory=lambda: [0, 1, 2, 3])
    warned: bool = False
    chips: list[Chip] = field(default_factory=list)
    casino_hide: discord.TextChannel = None  # the channel where to hide the images to make casino smooth
    unpulled_casino_url: str = None  # link to the unpulled image of the casino
    bonus_casino_url: str = None  # link to the bonus image of the casino
    balances: dict[int, dict[str, int]] = field(default_factory=lambda: {})

    def __post_init__(self):
        if not os.path.exists(f'data/casino/'):
            os.mkdir(f'data/casino/')
        shutil.copyfile(get_filename('unpulled.png'), get_data_filename('unpulled'))
        shutil.copyfile(get_filename('bonus.png'), get_data_filename('bonus'))

        with open(get_filename('pelimerkit.json')) as f:
            chips = json.load(f)
            for chip in chips:
                self.chips.append(Chip(**chip))

    async def on_ready(self):
        if not os.path.exists(get_data_filename('balances', 'json')):
            self.init_balances()
        else:
            self.load_balances()

        self.casino_hide = self.bot.client.get_channel(self.bot.config.CHANNEL_CASINO_HIDE_CHANNEL)

        @self.bot.commands.register(command_name='kasino', function=self.casino,
                                    description=self.bot.localizations.CASINO_DESCRIPTION, commands_per_day=30,
                                    timeout=600, level_required=10)
        async def kasino(interaction: discord.Interaction, summa: int = 100000):
            await self.bot.commands.commands['kasino'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                sum=summa
            )

        @self.bot.commands.register(command_name='saldo', function=self.balance,
                                    description=self.bot.localizations.BALANCE_DESCRIPTION, commands_per_day=30,
                                    timeout=3)
        async def balance(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['saldo'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä
            )

        @self.bot.commands.register(command_name='saldot', function=self.top_balances,
                                    description=self.bot.localizations.BALANCES_DESCRIPTION, commands_per_day=5,
                                    timeout=30)
        async def top_balances(interaction: discord.Interaction):
            await self.bot.commands.commands['saldot'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

        @self.bot.commands.register(command_name='give', function=self.give,
                                    description=self.bot.localizations.GIVE_DESCRIPTION, commands_per_day=10,
                                    timeout=3)
        async def give(interaction: discord.Interaction, käyttäjä: discord.User, summa: int = Constants.MAX_AMOUNT):
            await self.bot.commands.commands['give'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=käyttäjä,
                sum=summa
            )

        @self.bot.commands.register(command_name='maksuhäiriöt', function=self.low_balances,
                                    description=self.bot.localizations.LOW_BALANCES_DESCRIPTION,
                                    commands_per_day=5, timeout=30)
        async def top_balances(interaction: discord.Interaction):
            await self.bot.commands.commands['maksuhäiriöt'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

    async def low_balances(self, user: User, message: discord.Message | None = None,
                           interaction: discord.Interaction | None = None, **kwargs):
        balance_list: list[tuple[str, int]] = [(x.name, self.get_user_balance(x)) for x in self.bot.users]
        sorted_balance_list: list[tuple[str, int]] = sorted(balance_list, key=lambda tup: tup[1])[:10]
        msg: str = self.bot.localizations.LOW_BALANCES_TITLE
        for i in range(len(sorted_balance_list)):
            if sorted_balance_list[i][1] >= 0:
                break
            msg += self.bot.localizations.BALANCES_ROW.format(i, sorted_balance_list[i][0],
                                                              '{:,}'.format(sorted_balance_list[i][1]))
        await self.bot.commands.message(msg, message, interaction, delete_after=25)

    async def give(self, user: User, message: discord.Message | None = None,
                   interaction: discord.Interaction | None = None,
                   target_user: discord.User | None = None, sum: int = Constants.MAX_AMOUNT):
        if self.get_user_balance(user) < 0:
            await self.bot.commands.error(self.bot.localizations.GIVE_TOO_POOR, message, interaction)
            return
        if not target_user:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        if target_user == user:
            await self.bot.commands.error(self.bot.localizations.GIVE_CANT_SELF, message, interaction)
            return
        if message:
            contents: list[str] = message.content.lower().split(' ')
            if len(contents) < 3:
                # no sum given
                # self.reset_cooldown(user)
                await self.bot.commands.error(self.bot.localizations.GIVE_GUIDE, message)
                return
            try:
                sum = int(contents[2])
            except ValueError:
                # self.reset_cooldown(user)
                await self.bot.commands.error(self.bot.localizations.GIVE_GUIDE, message)
                return
        sum = min(self.get_user_balance(user), sum)
        if sum < 10000:
            await self.bot.commands.error(self.bot.localizations.GIVE_MUST_BE_OVER_10000, message, interaction)
            return
        self.balances[user.id]['points'] -= sum
        if target_user.id not in self.balances:
            self.balances[target_user.id] = {'points': self.user_points_to_balance(target_user.stats.points) + sum,
                                             'reduce_points': self.user_points_to_balance(target_user.stats.points)}
        self.balances[target_user.id]['points'] += sum
        self.save_balances()
        await self.bot.commands.message(self.bot.localizations.GIVE_SUCCESS
                                        .format(user.name, target_user.name, '{:,}'.format(sum)), message, interaction)

    async def top_balances(self, user: User, message: discord.Message | None = None,
                           interaction: discord.Interaction | None = None, **kwargs):
        balance_list: list[tuple[str, int]] = [(x.name, self.get_user_balance(x)) for x in self.bot.users]
        sorted_balance_list: list[tuple[str, int]] = sorted(balance_list, key=lambda tup: -tup[1])[:10]
        msg: str = self.bot.localizations.BALANCES_TITLE
        for i in range(len(sorted_balance_list)):
            msg += self.bot.localizations.BALANCES_ROW.format(i, sorted_balance_list[i][0],
                                                              '{:,}'.format(sorted_balance_list[i][1]))
        await self.bot.commands.message(msg, message, interaction, delete_after=25)

    async def balance(self, user: User, message: discord.Message | None = None,
                      interaction: discord.Interaction | None = None, target_user: User | None = None):
        if not target_user:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_FOUND, message, interaction)
            return
        if target_user.id not in self.balances:
            self.balances[target_user.id] = {'points': self.user_points_to_balance(target_user.stats.points),
                                             'reduce_points': self.user_points_to_balance(target_user.stats.points)}
        await self.bot.commands.message(
            self.bot.localizations.BALANCE_RESPONSE.format(target_user.name,
                                                           '{:,}'.format(self.get_user_balance(target_user))),
            message, interaction, delete_after=10)

    async def casino(self, user: User, message: discord.Message | None = None,
                     interaction: discord.Interaction | None = None,
                     sum: int = Constants.MAX_AMOUNT,
                     **kwargs):
        if message:
            contents: list[str] = message.content.lower().split(' ')
            if len(contents) < 2:
                # no sum given
                self.reset_cooldown(user)
                await self.bot.commands.error(self.bot.localizations.CASINO_GUIDE, message)
                return
            if contents[1] != 'max':
                try:
                    sum = int(contents[1])
                    if sum > Constants.MAX_AMOUNT or sum < Constants.MIN_AMOUNT:
                        self.reset_cooldown(user)
                        await self.bot.commands.error(
                            self.bot.localizations.CASINO_WRONG_SUM.format(Constants.MIN_AMOUNT, Constants.MAX_AMOUNT),
                            message)
                        return
                except ValueError:
                    self.reset_cooldown(user)
                    await self.bot.commands.error(self.bot.localizations.CASINO_GUIDE, message)
                    return

        # parse betting sum
        play_amount: int = min(self.get_user_balance(user), max(min(sum, Constants.MAX_AMOUNT), Constants.MIN_AMOUNT))
        if play_amount < Constants.MIN_AMOUNT:
            await self.bot.commands.error(self.bot.localizations.TOO_LOW_BALANCE, message, interaction)
            return

        # manage casino cooldown to prevent multiple casinos the same time on the same channel
        ts = functions.get_current_timestamp()
        ch_id: str = str(message.channel.id) if message else str(interaction.channel_id)
        if ch_id not in self.casino_times:
            self.casino_times[ch_id] = 0
        if ts - self.casino_times[ch_id] <= 30:
            self.reset_cooldown(user)
            if not self.warned:
                self.warned = True
                await self.bot.commands.error(self.bot.localizations.CASINO_ONGOING, message, interaction)
            elif message:
                await message.delete()
            return
        self.casino_times[ch_id] = ts
        self.warned = False

        # roll casino, check wins and partial wins
        chosen_reels: list[list[Chip]] = self.get_chosen_tiles(self.chips)
        wins: dict[str, Chip] = self.check_wins(chosen_reels)
        partial_wins = self.check_partial_wins(chosen_reels)

        self.balances[user.id]['points'] -= play_amount

        anttu_bonus: int = 1
        if wins:
            roll = random.randint(0, 99)
            anttu_bonus = 0 if roll < 15 else 2 if roll >= 85 else 1  # 15% chance for anttulose, 15% for anttu double

        # build PIL images and save them on data/casino/
        files: list[str] = [get_data_filename('unpulled')]
        win_screen: Image.Image | None = None
        looped_spots: list[tuple[int, int]] = []
        for i in range(Constants.COLUMNS):
            for j in range(Constants.ROWS):
                looped_spots.append((i, j))
                if i == 1 and j == 2 and not partial_wins:
                    continue
                if i == 0 and j < 2:
                    continue
                if i == 2 and j < 2:
                    found = False
                    for possible_wins in Constants.POSSIBLE_WINNING_LINES[(i, j)]:
                        if possible_wins in partial_wins:
                            found = True
                    if not found:
                        continue
                    if j == 0 and '1' not in partial_wins and '2' not in partial_wins and '5' not in partial_wins:
                        continue
                    if j == 1 and '2' not in partial_wins and '5' not in partial_wins:
                        continue
                bg: Image = Images.im_background.copy()

                if i >= 1 and partial_wins:
                    for partial_win in partial_wins:
                        if partial_win == '3' and i == 1:
                            bg.paste(Images.partial_images[partial_win], (0, 0), Images.partial_images[partial_win])
                        elif partial_win == '2' and ((i == 1 and j == 2) or (i == 2 and j < 2)):
                            bg.paste(Images.partial_images[partial_win], (0, 0), Images.partial_images[partial_win])
                        elif partial_win == '1' and ((i == 1 and j >= 1) or (i == 2 and j < 1)):
                            bg.paste(Images.partial_images[partial_win], (0, 0), Images.partial_images[partial_win])
                        elif partial_win == '4' and i == 1 and j >= 1:
                            bg.paste(Images.partial_images[partial_win], (0, 0), Images.partial_images[partial_win])
                        elif partial_win == '5' and ((i == 1 and j >= 1) or (i == 2 and j < 2)):
                            bg.paste(Images.partial_images[partial_win], (0, 0), Images.partial_images[partial_win])

                if i == 2 and wins:
                    for win in wins:
                        if win == '3' or win == '4':
                            bg.paste(Images.win_images[win], (0, 0), Images.win_images[win])
                        elif win == '1' and j >= 1:
                            bg.paste(Images.win_images[win], (0, 0), Images.win_images[win])
                        elif (win == '2' or win == '5') and j == 2:
                            bg.paste(Images.win_images[win], (0, 0), Images.win_images[win])

                for spot in looped_spots:
                    bg.paste(chosen_reels[spot[0]][spot[1]].file, Constants.TILE_POSITIONS[spot[0]][spot[1]])
                filename = get_data_filename(self.randomword(10))
                bg.save(filename, **bg.info)
                files.append(filename)
                if i == 2 and j == 2:
                    win_screen = bg
        amount: int = 0
        filename: str = get_data_filename(self.randomword(10))
        bg: Image.Image = win_screen.copy()
        if len(wins) == 0:
            bg.paste(Images.lost_image, (0, 0), Images.lost_image)
        else:
            bg: Image.Image = win_screen.copy()
            bg.paste(Images.won_image, (0, 0), Images.won_image)
            for win in wins:
                amount += wins[win].win * play_amount
            bg.paste(Images.title_image, (0, 0), Images.title_image)
            title_message = '{:,}'.format(amount)
            d = ImageDraw.Draw(bg)
            w = d.textlength(title_message, font=Images.font)
            d.text(((Constants.BG_SIZE[0] - w) / 2, 131), title_message, fill=(255, 255, 255), font=Images.font,
                   stroke_width=-1, stroke_fill=(0, 0, 0))
        bg.save(filename, **bg.info)
        files.append(filename)

        if len(wins) and anttu_bonus != 1:
            filename = get_data_filename("bonus")
            if not os.path.exists(filename):
                bonus_bg: Image.Image = Images.bonus_image.copy()
                bonus_bg.save(filename, **bonus_bg.info)
            files.append(filename)

            bg: Image.Image = win_screen.copy()
            filename = get_data_filename(self.randomword(10))
            bg.save(filename, **bg.info)
            files.append(filename)

            anttu_bg: Image.Image = bg.copy()
            anttu_bg.paste(Images.anttu_lose, (0, 178), Images.anttu_lose)
            filename = get_data_filename(self.randomword(10))
            anttu_bg.save(filename, **anttu_bg.info)
            files.append(filename)

            anttu_bg: Image.Image = bg.copy()
            anttu_bg.paste(Images.anttu_lose, (0, 140), Images.anttu_lose)
            filename = get_data_filename(self.randomword(10))
            anttu_bg.save(filename, **anttu_bg.info)
            files.append(filename)

            anttu_bonus_img: Image.Image = win_screen.copy()
            anttu_bonus_img.paste(Images.anttu_lose if not anttu_bonus else Images.anttu_win, (0, 0),
                                  Images.anttu_lose if not anttu_bonus else Images.anttu_win)

            filename = get_data_filename(self.randomword(10))
            anttu_bonus_img.save(filename, **anttu_bonus_img.info)
            files.append(filename)

            anttu_final: Image.Image = win_screen.copy()
            amount *= anttu_bonus
            if amount:
                anttu_final.paste(Images.anttu_win, (0, -95), Images.anttu_win)
                anttu_final.paste(Images.title_image, (0, 0), Images.title_image)
                title_message = '{:,}'.format(amount)
                d = ImageDraw.Draw(anttu_final)
                w = d.textlength(title_message, font=Images.font)
                d.text(((Constants.BG_SIZE[0] - w) / 2, 131), title_message, fill=(255, 255, 255), font=Images.font,
                       stroke_width=1, stroke_fill=(0, 0, 0))

            else:
                anttu_final.paste(Images.anttu_lose, (0, 60), Images.anttu_lose)
                anttu_final.paste(Images.lost_image, (0, 0), Images.lost_image)
            filename = get_data_filename(self.randomword(10))
            anttu_final.save(filename, **anttu_final.info)
            files.append(filename)

        # respond to interaction
        if interaction:
            await interaction.response.send_message(self.bot.localizations.CASINO_LAUNCH.format(user.name),
                                                    delete_after=5.0)

        # build the image urls
        # we need to first send the images on Discord (on a hidden channel), then post them again as Embeds
        # this is needed to prevent glitching and making sure Discord has the images cached
        urls: list[str] = []
        if not self.unpulled_casino_url:
            # unpulled image hasn't been posted...
            post: discord.Message = await self.casino_hide.send(file=discord.File(files[0]))
            self.unpulled_casino_url = post.attachments[0].url
            embed = discord.Embed(title=self.bot.localizations.CASINO_EMBED_TITLE.format(user.name),
                                  description=self.bot.localizations.CASINO_EMBED_DESCRIPTION
                                  .format(play_amount, self.get_user_balance(user) + play_amount)
                                  )
            embed.set_image(url=self.unpulled_casino_url)
            await self.casino_hide.send(embed=embed)
        urls.append(self.unpulled_casino_url)

        embed: discord.Embed = discord.Embed(
            title=self.bot.localizations.CASINO_EMBED_TITLE.format(user.name),
            description=self.bot.localizations.CASINO_EMBED_DESCRIPTION
            .format('{:,}'.format(play_amount), '{:,}'.format(self.get_user_balance(user) + play_amount))
        )
        embed.set_image(url=self.unpulled_casino_url)
        casino_post: discord.Message = await message.channel.send(embed=embed) if message else \
            await interaction.channel.send(embed=embed)
        i: int = 1
        for f in files[1:]:
            if 'bonus.png' in f:
                if not self.bonus_casino_url:
                    # bonus image hasn't been posted...
                    post: discord.Message = await self.casino_hide.send(file=discord.File(f))
                    self.bonus_casino_url = post.attachments[0].url
                    embed = discord.Embed(title=self.bot.localizations.CASINO_EMBED_TITLE.format(user.name),
                                          description=self.bot.localizations.CASINO_EMBED_DESCRIPTION
                                          .format(play_amount, self.get_user_balance(user) + play_amount)
                                          )
                    embed.set_image(url=self.bonus_casino_url)
                    await self.casino_hide.send(embed=embed)
                urls.append(self.bonus_casino_url)
                url = self.bonus_casino_url
            else:
                delete_after: int = 25 if (f != files[-1] or len(wins) == 0) else 0
                post: discord.Message = await self.casino_hide.send(file=discord.File(f), delete_after=delete_after)
                urls.append(post.attachments[0].url)
                embed = discord.Embed(title=self.bot.localizations.CASINO_EMBED_TITLE.format(user.name),
                                      description=self.bot.localizations.CASINO_EMBED_DESCRIPTION
                                      .format('{:,}'.format(play_amount),
                                              '{:,}'.format(self.get_user_balance(user) + play_amount)))
                embed.set_image(url=post.attachments[0].url)
                await self.casino_hide.send(embed=embed, delete_after=25.0)
                await asyncio.sleep(0.6)
                url = post.attachments[0].url

            embed = discord.Embed(title=self.bot.localizations.CASINO_EMBED_TITLE.format(user.name),
                                  description=self.bot.localizations.CASINO_EMBED_DESCRIPTION
                                  .format('{:,}'.format(play_amount),
                                          '{:,}'.format(self.get_user_balance(user) + play_amount if i < len(files) - 1 \
                                                            else self.get_user_balance(user) + amount)))
            embed.set_image(url=url)
            await casino_post.edit(embed=embed)
            await asyncio.sleep(2)
            i += 1

            if i == len(files):
                if amount != 0:
                    self.balances[user.id]['points'] += amount
                    self.save_balances()
                if len(wins) > 0 and amount >= 0:
                    loc_text = self.bot.localizations.CASINO_WIN.format(
                        self.bot.client.get_user(user.id).mention, '{:,}'.format(amount)) if anttu_bonus == 1 else \
                        self.bot.localizations.CASINO_WIN_ANTTU.format(self.bot.client.get_user(user.id).mention,
                                                                       '{:,}'.format(amount)) if anttu_bonus == 2 else \
                            self.bot.localizations.CASINO_WIN_ANTTU_LOSE.format(
                                self.bot.client.get_user(user.id).mention)
                    msg = await self.bot.commands.message(loc_text, message, interaction, channel_send=True)
                elif len(wins) > 0 > amount:
                    msg = await self.bot.commands.message(self.bot.localizations.CASINO_WIN_BAN.format(
                        self.bot.client.get_user(user.id).mention), message, interaction, channel_send=True)
                    await asyncio.sleep(10)
                else:
                    msg = await self.bot.commands.message(self.bot.localizations.CASINO_LOSE.format(
                        self.bot.client.get_user(user.id).mention), message, interaction, channel_send=True)

        # reset cooldown
        self.casino_times[ch_id] = 0
        await asyncio.sleep(4)

        # reset cooldown
        self.casino_times[ch_id] = 0

        try:
            if message:
                await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        finally:
            await casino_post.delete()
            if len(wins) == 0:
                await msg.delete()
        i: int = 0
        for file in files[1:]:
            i += 1
            if i == len(files[1:]) and len(wins) > 0:
                continue
            # remove unnecessary files
            try:
                os.remove(file)
            except OSError:
                pass

        # user won negative sum, thus ban
        if amount < 0:
            if message:
                if self.bot.get_user_by_id(message.author.id).is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
                    await message.channel.send("no enpä bännää ku äijä on suojeltu,,mulkku")
                    return
            else:
                if self.bot.get_user_by_id(interaction.user.id).is_ban_protected(self.bot.config.IMMUNE_TO_BAN):
                    await interaction.channel.send("no enpä bännää ku äijä on suojeltu,,mulkku")
                    return

            await message.guild.ban(message.author, delete_message_days=0, reason='Megiskasino bän') if message else \
                await interaction.guild.ban(interaction.user, delete_message_days=0, reason='Megiskasino bän')

    def reset_cooldown(self, user: User):
        if user.id in self.bot.commands.commands['kasino'].timeouts:
            self.bot.commands.commands['kasino'].timeouts[user.id] = 0

    @staticmethod
    def get_random_numbers(max: int, count: int) -> list[int]:
        return_list: list[int] = []
        for i in range(count):
            rd = random.randrange(max)
            while rd in return_list:
                rd = random.randrange(max)
            return_list.append(rd)
        return return_list

    @staticmethod
    def create_reels(assets: list[Chip]) -> list:
        reels: list = []
        for i in range(Constants.COLUMNS):
            positions: dict[str, Chip] = {}
            for chip in assets:
                for j in range(chip.prevelance):
                    rd = random.randrange(Constants.MAXIMUM)
                    while str(rd) in positions:
                        rd = random.randrange(Constants.MAXIMUM)
                    positions[str(rd)] = chip
            positions: list[str] = sorted(positions.items())
            reels.append([x[1] for x in positions])
        return reels

    @staticmethod
    def randomword(length: int) -> str:
        letters: str = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    def get_chosen_tiles(self, chips: list[Chip]) -> list[list[Chip]]:
        reels = self.create_reels(chips)
        chosen_reels = []
        for i in range(Constants.COLUMNS):
            curr_list = []
            for rd in self.get_random_numbers(Constants.MAXIMUM, Constants.ROWS):
                curr_list.append(reels[i][rd])
            chosen_reels.append(curr_list)
        return chosen_reels

    @staticmethod
    def check_wins(tiles: list[list[Chip]]) -> dict[str, Chip]:
        lines: dict[str, Chip] = {}
        for line in Constants.WIN_LINES:
            first_tile: Chip | None = None
            lost: bool = False
            for pos in Constants.WIN_LINES[line]:
                tile = tiles[pos[0]][pos[1]]
                if first_tile is None or (first_tile.joker and not tile.joker):
                    first_tile = tile
                if first_tile.name != tile.name and not tile.joker:
                    lost = True
            if not lost:
                lines[line] = first_tile
        return lines

    @staticmethod
    def check_partial_wins(tiles: list[list[Chip]]) -> list[str]:
        partial_wins: list[str] = []
        for line in Constants.WIN_LINES:
            first_tile: Chip | None = None
            lost: bool = False
            i: int = 0
            for pos in Constants.WIN_LINES[line]:
                if i >= 2:
                    break
                tile = tiles[pos[0]][pos[1]]
                if first_tile is None or (first_tile.joker and not tile.joker):
                    first_tile = tile
                if first_tile.name != tile.name and not tile.joker:
                    lost = True
                i += 1
            if not lost:
                partial_wins.append(line)
        return partial_wins

    async def on_new_day(self, date_now: datetime):
        for file in os.listdir('data/casino/'):
            if 'unpulled' not in file and '.png' in file and 'bonus.png' not in file:
                os.remove(f'data/casino/{file}')

    def init_balances(self):
        """Balances.json was not found; thus we create the balances.

        On default, balances are gotten from the user points.
        """
        for user in self.bot.users:
            self.balances[user.id] = {'points': self.user_points_to_balance(user.stats.points),
                                      'reduce_points': self.user_points_to_balance(user.stats.points)}
        self.save_balances()

    def save_balances(self):
        with open(get_data_filename('balances', 'json'), 'w') as f:
            balances: dict[str, dict[str, int]] = {}
            for user_id in self.balances:
                balances[str(user_id)] = self.balances[user_id]
            json.dump(balances, f)

    def load_balances(self):
        with open(get_data_filename('balances', 'json'), 'r') as f:
            balances = json.load(f)
            for user_id in balances:
                self.balances[int(user_id)] = balances[user_id]

    async def on_member_join(self, member: discord.Member):
        if member.id not in self.balances:
            self.balances[member.id] = {'points': 0, 'reduce_points': 0}

    @staticmethod
    def user_points_to_balance(points: int) -> int:
        return points * Constants.POINTS_TO_BALANCE_MULTIPLIER

    def get_user_balance(self, user: User) -> int:
        try:
            return self.balances[user.id].get('points') \
                - self.balances[user.id].get('reduce_points') \
                + self.user_points_to_balance(user.stats.points)
        except KeyError:
            return 0
