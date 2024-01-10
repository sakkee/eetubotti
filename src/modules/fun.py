"""
Random fun stuff.

Commands:
    !kissa
    !kissat
    !kissa_top
"""
import json
import re
import discord
from dataclasses import dataclass, field
import src.functions
from src.basemodule import BaseModule
from src.objects import User

# when is bauhaus open
BAUHAUS_OPENING_TIMES: dict[str, dict[str, int]] = {
    'weekday': {'open': 7, 'close': 21},
    'saturday': {'open': 9, 'close': 18},
    'sunday': {'open': 10, 'close': 18}
}
BAUHAUS_TRIGGER_WORDS: list[tuple[str, str]] = [("bauhaus", "kii"), ("bauhaus", "kiinni"), ("bauhaus", "auki")]

# cat points per ranking
CAT_POINTS = [25, 18, 15, 12, 10]


@dataclass
class Plugin(BaseModule):
    cat_rankings: dict[int, dict[str, list[User, User, User, User, User] | int]] = field(default_factory=dict)

    async def on_ready(self):
        self.load_cat_rankings()

        @self.bot.commands.register(command_name='kissat', function=self.kissat,
                                    description=self.bot.localizations.KISSAT_DESCRIPTION, commands_per_day=5,
                                    timeout=1)
        async def kissat(interaction: discord.Interaction, servun_paras_kissa: discord.User, toinen: discord.User,
                         kolmas: discord.User, neljas: discord.User, viides: discord.User):
            await self.bot.commands.commands['kissat'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                servun_paras_kissa=servun_paras_kissa,
                toinen=toinen,
                kolmas=kolmas,
                neljas=neljas,
                viides=viides
            )

        @self.bot.commands.register(command_name='kissa', function=self.kissa,
                                    description=self.bot.localizations.KISSA_DESCRIPTION, commands_per_day=20,
                                    timeout=1)
        async def kissa(interaction: discord.Interaction, käyttäjä: discord.User = None):
            await self.bot.commands.commands['kissa'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                target_user=self.bot.get_user_by_id(käyttäjä.id) if käyttäjä is not None else None
            )

        @self.bot.commands.register(command_name='kissa_top', function=self.kissa_top,
                                    description=self.bot.localizations.KISSA_TOP_DESCRIPTION, commands_per_day=20,
                                    timeout=1)
        async def kissa_top(interaction: discord.Interaction):
            await self.bot.commands.commands['kissa_top'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction
            )

    async def kissa_top(self, user: User, message: discord.Message = None, interaction: discord.Interaction = None,
                        **kwargs):
        kissa_rankings = self.get_kissa_rankings()[:10]
        kissa_rows = ""
        for index, kissa in enumerate(kissa_rankings):
            kissa_rows += self.bot.localizations.KISSA_TOP_ROW.format(index + 1, kissa.name)
        await self.bot.commands.message(self.bot.localizations.KISSA_TOP.format(kissa_rows), message, interaction,
                                        delete_after=30)

    async def kissa(self, user: User, message: discord.Message = None, interaction: discord.Interaction = None,
                    target_user: discord.User = None, **kwargs):
        target_user = user if target_user is None else target_user
        if target_user.id not in self.cat_rankings or not self.cat_rankings[target_user.id]["sum"]:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_KISSA, message, interaction)
            return
        kissa_rankings = self.get_kissa_rankings()
        if target_user not in kissa_rankings:
            await self.bot.commands.error(self.bot.localizations.USER_NOT_KISSA, message, interaction)
            return

        await self.bot.commands.message(self.bot.localizations.KISSA_RANKING.format(
            target_user.name, kissa_rankings.index(target_user) + 1), message, interaction, delete_after=30)

    def get_kissa_rankings(self) -> list[User]:
        # return list of users ordered by their 'sum' in cat_rankings
        user_list: list[tuple[User, int]] = []
        for user_id in self.cat_rankings:
            if self.cat_rankings[user_id]["sum"]:
                user_list.append((self.bot.get_user_by_id(user_id), self.cat_rankings[user_id]["sum"]))

        user_list.sort(key=lambda x: x[1], reverse=True)
        return [user for user, _ in user_list]


    async def kissat(self, user: User, message: discord.Message = None, interaction: discord.Interaction = None,
                     target_user: discord.User = None,
                     servun_paras_kissa: discord.User = None, toinen: discord.User = None, kolmas: discord.User = None,
                     neljas: discord.User = None, viides: discord.User = None, **kwargs):
        kissat = []
        if interaction:
            for kissa in [servun_paras_kissa, toinen, kolmas, neljas, viides]:
                if not kissa or not self.bot.get_user_by_id(kissa.id) or kissa.id == user.id or self.bot.get_user_by_id(kissa.id) in kissat:
                    continue
                kissat.append(self.bot.get_user_by_id(kissa.id))
        elif message:
            id_list: list[int] = [int(x) for x in re.findall(r'\d+', message.content)]
            for id in id_list:
                kissa = self.bot.get_user_by_id(id)
                if kissa is None or kissa.id == user.id or kissa in kissat:
                    continue
                kissat.append(kissa)
        if not kissat:
            await self.bot.commands.error(self.bot.localizations.KISSAT_HELP, message, interaction)
            return
        if user.id in self.cat_rankings:
            self.cat_rankings[user.id]["rankings"][:] = []
        else:
            self.cat_rankings[user.id] = {"rankings": [], "sum": 0}
            self.cat_rankings[user.id]["rankings"] = []
        self.cat_rankings[user.id]["rankings"].extend(kissat)
        user_list: str = ""
        for kissa in kissat:
            if user_list:
                user_list += ", "
            if user.id not in self.cat_rankings:
                self.cat_rankings[user.id] = {"rankings": [], "sum": 0}
            user_list += f"**{kissa.name}**"
        await self.bot.commands.message(self.bot.localizations.KISSAT_SET.format(user.name, user_list), message, interaction)
        self.refresh_cat_rankings()
        top_cats = self.get_kissa_rankings()[:1]

        cat_role: discord.Role = self.bot.server.get_role(self.bot.config.ROLE_CAT)
        if cat_role is None:
            return
        for user in self.bot.users:
            if self.bot.config.ROLE_CAT in user.roles and user not in top_cats:
                discord_user = self.bot.server.get_member(user.id)
                if discord_user is None:
                    continue
                try:
                    await discord_user.remove_roles(cat_role)
                except discord.Forbidden:
                    continue
                except discord.HTTPException:
                    continue
            elif self.bot.config.ROLE_CAT not in user.roles and user in top_cats:
                discord_user = self.bot.server.get_member(user.id)
                if discord_user is None:
                    continue
                try:
                    await discord_user.add_roles(cat_role)
                except discord.Forbidden:
                    continue
                except discord.HTTPException:
                    continue

    def refresh_cat_rankings(self, save: bool = True):
        # calculate sum of points per user in cat rankings
        voted_users = []
        for user_id in self.cat_rankings:
            self.cat_rankings[user_id]["sum"] = 0
            for rank in self.cat_rankings[user_id]["rankings"]:
                if rank.id not in voted_users:
                    voted_users.append(rank.id)
        for voted_user in voted_users:
            if voted_user not in self.cat_rankings:
                self.cat_rankings[voted_user] = {"rankings": [], "sum": 0}
        for user_id in self.cat_rankings:
            for index, user in enumerate(self.cat_rankings[user_id]["rankings"]):
                self.cat_rankings[user.id]["sum"] += CAT_POINTS[index] * self.bot.get_user_by_id(user_id).level
        if save:
            self.save_cat_rankings()

    def load_cat_rankings(self):
        try:
            with open('data/cat_rankings.json', 'r') as f:
                cat_rankings: dict[int, list[int]] = json.load(f)
                for user_id in cat_rankings:
                    self.cat_rankings[int(user_id)] = {"rankings": [], "sum": 0}
                    for ranking in cat_rankings[user_id]["rankings"]:
                        self.cat_rankings[int(user_id)]["rankings"].append(self.bot.get_user_by_id(ranking))
        except FileNotFoundError:
            pass
        self.refresh_cat_rankings(save=False)

    def save_cat_rankings(self):
        with open('data/cat_rankings.json', 'w') as f:
            cat_rankings = {}
            for user_id in self.cat_rankings:
                cat_rankings[str(user_id)] = {"sum": self.cat_rankings[user_id]["sum"], "rankings": []}
                for ranking in self.cat_rankings[user_id]["rankings"]:
                    cat_rankings[str(user_id)]["rankings"].append(ranking.id)
            json.dump(cat_rankings, f)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if self.is_bauhaus_triggered(message.content):
            await self.bot.commands.message(self.get_bauhaus_closing_time(), message, delete_after=20)

    @staticmethod
    def is_bauhaus_triggered(message: discord.Message.content) -> bool:
        msg_lowered = message.lower()
        for trigger in BAUHAUS_TRIGGER_WORDS:
            all_found = len(trigger)
            count = 0
            for trg in trigger:
                if trg in msg_lowered:
                    count += 1
            if count == all_found:
                return True
        return False

    def get_bauhaus_closing_time(self) -> str:
        current_time = src.functions.utc_to_local(src.functions.ts2dt(src.functions.get_current_timestamp()),
                                                  self.bot.config.TIMEZONE)
        weekday = current_time.isoweekday()
        if weekday < 6:
            closing_time = BAUHAUS_OPENING_TIMES['weekday']['close']
        elif weekday == 6:
            closing_time = BAUHAUS_OPENING_TIMES['saturday']['close']
        else:
            closing_time = BAUHAUS_OPENING_TIMES['sunday']['close']
        if closing_time is None:
            return self.bot.localizations.BAUHAUS_NOT_FOUND
        if closing_time == 0:
            return self.bot.localizations.BAUHAUS_CLOSED_TODAY
        elif closing_time > current_time.hour:
            return self.bot.localizations.BAUHAUS_CLOSING_HOUR.format(closing_time)
        elif closing_time <= current_time.hour:
            return self.bot.localizations.BAUHAUS_CLOSED_ALREADY.format(closing_time)
