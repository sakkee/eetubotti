import os
from datetime import datetime
from dateutil.tz import gettz
import importlib
from src.discord_events import Discord_Events
from src.objects import *
from src.modules.module import Module
from src.modules.module_list import module_list
from src.localizations import Localizations
from src.constants import *
from src.database.database import Database
from src.commands import Plugin as CommandModule


@dataclass
class Bot:
    token: str
    launching: bool = True
    events: Discord_Events = None
    commands: CommandModule = None
    users: list[User] = None
    daylist: list[dict[str, int]] = None
    reactions: list[Reaction] = None
    database: Database = None
    client: discord.Client = None
    client_tree: discord.app_commands.CommandTree = None
    modules: list[Module] = field(default_factory=list)
    users_in_voice: list = field(default_factory=list)
    server: discord.Guild = None
    previous_day: datetime = datetime.now(tz=gettz(DEFAULT_TIMEZONE))
    last_day: datetime = datetime.today()

    def __post_init__(self):
        if not os.path.exists(f'data'):
            os.mkdir(f'data')

        if not os.path.exists(f'data/profile_images'):
            os.mkdir(f'data/profile_images')
        self.refresh_modules()
        self.modules[1].name = "ircci"
        self.database = Database(self)
        self.database.setup_database()
        self.reactions = self.database.get_reactions()
        self.daylist = self.database.get_daylist()
        self.users = self.database.get_users()
        self.client = discord.Client(guild_subscriptions=True, intents=discord.Intents.all())
        self.client_tree = discord.app_commands.CommandTree(self.client)
        self.events = Discord_Events(self)
        self.events.link_events()

    def refresh_modules(self):
        if not self.commands:
            self.commands = CommandModule(self)
        self.modules[:] = [self.commands]
        for module in module_list:
            if not module.enabled:
                continue
            self.modules.append(module(self))

    async def reload_module(self, module_name: str, message: discord.Message, interaction: discord.Interaction,
                            **kwargs):
        if len(module_name) < 2:
            await self.commands.error(Localizations.get('MODULE_NOT_FOUND').format(module_name), message, interaction)
            return

        found_module = None
        for _module in self.modules[1:]:
            if module_name in _module.__class__.__module__:
                found_module = _module
                break
        if not found_module:
            await self.commands.error(Localizations.get('MODULE_NOT_FOUND').format(module_name), message, interaction)
            return
        self.modules[:] = [x for x in self.modules if x != found_module]
        i = importlib.import_module(found_module.__class__.__module__)
        plugin = importlib.reload(i)
        self.modules.append(plugin.Plugin(self))
        await self.modules[-1].on_ready()
        await self.commands.message(Localizations.get('MODULE_RELOADED').format(found_module.__class__.__module__),
                                    message, interaction)

    def start(self):
        self.client.run(self.token)

    async def sync_users(self):
        print('Syncing users...')
        async for member in self.server.fetch_members(limit=None):
            await self.add_if_user_not_exist(member)
        print('Users synced!')
        #await self.client.get_channel(CHANNELS.YLEINEN).send(Localizations.get('ON_BOOT'))

    async def add_if_user_not_exist(self, member: discord.Member | discord.User, message: bool = False):
        if not self.get_user_by_id(member.id):
            filepath = await self.get_user_file(member)
            user_is_in_guild: bool = True if self.server.get_member(member.id) else False
            new_user = User(
                id=member.id,
                name=member.name,
                bot=int(member.bot),
                profile_filename=filepath,
                identifier=member.discriminator,
                stats=Stats(member.id), is_in_guild=user_is_in_guild)
            if isinstance(member, discord.Member):
                new_user.set_roles(member.roles)
            self.users.append(new_user)
            self.database.add_user(new_user)
        else:
            user = self.get_user_by_id(member.id)
            if isinstance(member, discord.Member):
                user.set_roles(member.roles)
            if not message:
                user.is_in_guild = True
            if user.name != member.name or user.identifier != member.discriminator:
                user.name = member.name
                user.identifier = member.discriminator
                self.database.add_user(user)
            if not message:
                filepath = await self.get_user_file(member)
                if user.profile_filename != filepath:
                    user.profile_filename = filepath
                    self.database.add_user(user)

    def get_user_by_id(self, id: int) -> User | None:
        member: User | None = None
        for user in self.users:
            if user.id == id:
                member = user
                break
        return member

    @staticmethod
    async def get_user_file(member: discord.Member) -> str:
        avatar: discord.Asset = member.display_avatar.with_static_format('png').with_size(256)
        filename: str = str(avatar).split('?')[0].split('/')[-1]
        id: int = member.id
        directory: str = 'data/profile_images/{}'.format(id)
        filepath: str = '{}/{}'.format(directory, filename)
        if not os.path.isdir(directory):
            os.mkdir(directory)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                await avatar.save(f)
        return filepath

    async def on_new_day(self, date_now: datetime):
        self.previous_day = datetime.now(tz=gettz(DEFAULT_TIMEZONE))
        for module in self.modules:
            try:
                await module.on_new_day(date_now)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_new_day: {e}")

    async def on_message(self, message: discord.Message):
        if self.launching:
            return

        if datetime.now(tz=gettz(DEFAULT_TIMEZONE)).date() != self.previous_day.date() and not self.launching:
            # default timezone midnight
            await self.on_new_day(datetime.now(tz=gettz(DEFAULT_TIMEZONE)))

        if message.created_at.date() != self.last_day.date() and not self.launching:
            # UTC midnight
            self.last_day = message.created_at
            self.database.new_utc_day()

        for module in self.modules:
            try:
                await module.on_message(message)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_message: {e}")

    async def on_ready(self):
        self.launching = False
        self.server = self.client.get_guild(SERVER_ID)
        await self.sync_users()
        for module in self.modules:
            try:
                await module.on_ready()
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_ready: {e}")

        self.database.save_database()
        self.database.sync_interval = 200

        @self.commands.register(command_name='reload_module', function=self.reload_module,
                                description='Reload module', commands_per_day=200, timeout=5)
        async def reload_module(interaction: discord.Interaction, module_name: str = ""):
            await self.commands.commands['reload_module'].execute(
                user=self.get_user_by_id(interaction.user.id),
                interaction=interaction,
                module_name=module_name
            )

        self.client_tree.copy_global_to(guild=self.server)
        await self.client_tree.sync(guild=self.server)

    async def on_member_join(self, member: discord.Member):
        user: User = self.get_user_by_id(member.id)
        if user is None:
            filepath: str = await self.get_user_file(member)
            user = User(id=member.id, name=member.name, bot=int(member.bot), profile_filename=filepath,
                        identifier=member.discriminator, stats=Stats(member.id), is_in_guild=True)
            self.users.append(user)
            self.database.add_user(user)

        for module in self.modules:
            try:
                await module.on_member_join(member)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_join: {e}")

    async def on_member_remove(self, member: discord.Member):
        user: User = self.get_user_by_id(member.id)
        if user is not None:
            user.set_roles(None)
            user.is_in_guild = False

        for module in self.modules:
            try:
                await module.on_member_remove(member)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_remove: {e}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        for module in self.modules:
            try:
                await module.on_raw_reaction_add(payload)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_raw_reaction_add: {e}")

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        for module in self.modules:
            try:
                await module.on_message_edit(before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_message_edit: {e}")

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        for module in self.modules:
            try:
                await module.on_member_unban(guild, user)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_unban: {e}")

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        for module in self.modules:
            try:
                await module.on_member_ban(guild, user)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_ban: {e}")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        for module in self.modules:
            try:
                await module.on_member_update(before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_member_update: {e}")

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        for module in self.modules:
            try:
                await module.on_voice_state_update(member, before, after)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed on_voice_state_update: {e}")