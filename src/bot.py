import os
from datetime import datetime
from dateutil.tz import gettz
import importlib
from src.config import CfgParser
from src.events import EventDispatcher, EventHandler
from src.objects import *
from src.basemodule import BaseModule
from src.modules.module_list import module_list
from src.localizations import Localization
from src.database.database import Database
from src.commands import CommandManager


@dataclass
class Bot(EventHandler):
    """The main Bot class that acts as the core.

    This class should handle all the core logic, e.g. including keeping track of time and keeping track of users,
    connection to the Discord servers et cetera.

    Specific code should be only in child modules that are found in src/modules/ without changing the core.
    In case of changing only a child module, you can reload the module by using "reload_module" application command
    on Discord, so no need to restart the bot.

    Attributes:
        token (str): the discord token of the bot.
        launching (bool): whether the bot is still launching. Set False when on_ready is called.
        events (Discord_Events): Event Manager. The events are called from the Event Manager.
        localizations (Localization): Localization Manager. The data is located in assets/localization.json.
        commands (CommandManager): The command manager that handles the core logic of application commands, including
            message commands and slash commands.
         users (list[User]): list of User objects. Includes Users that are no longer in the server.
         daylist (list[dict[str, int]]: the daylist when the server has been active. Used by the stats module.
            This should be removed from this module and moved to the Stats module, but CBA.
        reactions (list[Reaction]): list of all Reactions. NOT USED.
        database (Database): the database handler. All communication with the database must be through this module.
        client (discord.Client): the discord.py's Client module. Read:
            https://discordpy.readthedocs.io/en/stable/api.html#client
        client_tree (discord.app_commands.CommandTree): All slash commands are added to the Command Tree.
            The CommandManager handles this.
        modules (list[Module]): list of all modules in src/module_list.py that are enabled
        server (discord.Guild): the server the bot is used on. Read:
            https://discordpy.readthedocs.io/en/stable/api.html#discord.Guild
        current_day (datetime): The current day's datetime. Used to track when the LOCAL day has changed.
        last_day (datetime): UTC datetime. Used to track when the UTC day has changed.
    """
    token: str = None
    launching: bool = True
    events: EventDispatcher = None
    config: CfgParser = field(default_factory=lambda: CfgParser())
    localizations: Localization = field(default_factory=lambda: Localization('assets/localization.json'))
    commands: CommandManager = None
    users: list[User] = None
    daylist: list[dict[str, int]] = None
    reactions: list[Reaction] = None
    database: Database = None
    client: discord.Client = None
    client_tree: discord.app_commands.CommandTree = None
    modules: list[BaseModule] = field(default_factory=list)
    server: discord.Guild = None
    current_day: datetime = None
    last_day: datetime = datetime.utcnow()

    def __post_init__(self):
        """Initialize the bot. First create the data folder if not exists, then data/profile_images if not exists.

        Create the database manager object and setup the database, get reactions, active days and users. Initialize
        the discord client and refresh the events.
        """
        self.token = self.config.TOKEN
        self.current_day = datetime.now(tz=gettz(self.config.TIMEZONE))
        if not os.path.exists(f'data'):
            os.mkdir(f'data')
        if not os.path.exists(f'data/profile_images'):
            os.mkdir(f'data/profile_images')
        self.refresh_modules()
        self.database = Database(self)
        self.database.setup_database()
        self.reactions = self.database.get_reactions()
        self.daylist = self.database.get_daylist()
        self.users = self.database.get_users()
        self.client = discord.Client(guild_subscriptions=True, intents=discord.Intents.all())
        self.client_tree = discord.app_commands.CommandTree(self.client)
        self.events = EventDispatcher(self)
        self.events.link_events()

    def start(self):
        self.client.run(self.token)

    def refresh_modules(self):
        if not self.commands:
            self.commands = CommandManager(self)
        self.modules[:] = [self.commands]
        for module in module_list:
            if not module.enabled:
                continue
            self.modules.append(module(bot=self))
        self.localizations.load()

    async def reload_module(self, module_name: str, message: discord.Message, interaction: discord.Interaction,
                            **kwargs):
        """Discord slash command used to reload a module when code or module file has been changed. This is used
        to avoid the need for rebooting the bot. Initialized in src/discord_events.py.
        """
        if len(module_name) < 2:
            await self.commands.error(self.localizations.MODULE_NOT_FOUND.format(module_name), message, interaction)
            return

        found_module = None
        for _module in self.modules[1:]:
            if module_name in _module.__class__.__module__:
                found_module = _module
                break
        if not found_module:
            await self.commands.error(self.localizations.MODULE_NOT_FOUND.format(module_name), message, interaction)
            return
        self.modules[:] = [x for x in self.modules if x != found_module]
        i = importlib.import_module(found_module.__class__.__module__)
        plugin = importlib.reload(i)
        self.localizations.load()
        self.modules.append(plugin.Plugin(self))
        await self.modules[-1].on_ready()
        await self.commands.message(self.localizations.MODULE_RELOADED.format(found_module.__class__.__module__),
                                    message, interaction)

    async def sync_users(self):
        print('Syncing users...')
        async for member in self.server.fetch_members(limit=None):
            await self.add_if_user_not_exist(member)
        print('Users synced!')
        await self.client.get_channel(self.config.CHANNEL_GENERAL).send(self.localizations.ON_BOOT)

    async def add_if_user_not_exist(self, member: discord.Member | discord.User, is_message: bool = False):
        """Add User if it doesn't already exist.

        Args:
            member (discord.Member | discord.User): a discord.py's Member or User to be added.
            is_message (bool): whether called from reading a message.
        """
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
            if not is_message:
                user.is_in_guild = True
            if user.name != member.name or user.identifier != member.discriminator:
                user.name = member.name
                user.identifier = member.discriminator
                self.database.add_user(user)
            if not is_message:
                filepath = await self.get_user_file(member)
                if user.profile_filename != filepath:
                    user.profile_filename = filepath
                    self.database.add_user(user)

    def get_user_by_id(self, id: int) -> User | None:
        """Get User by id.

        Args:
            id (int): the User id

        Returns:
            User or None.
        """
        member: User | None = None
        for user in self.users:
            if user.id == id:
                member = user
                break
        return member

    @staticmethod
    async def get_user_file(member: discord.Member) -> str:
        """Download member profile image.

        Args:
            member (discord.Member): the member whose profile image to be downloaded.

        Returns:
            The file path of the downloaded profile image.
        """
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
        self.current_day = datetime.now(tz=gettz(self.config.TIMEZONE))

    async def on_message(self, message: discord.Message):
        # default timezone midnight
        if datetime.now(tz=gettz(self.config.TIMEZONE)).date() != self.current_day.date() and not self.launching:
            await self.events.on_new_day(datetime.now(tz=gettz(self.config.TIMEZONE)))

        # UTC midnight
        if message.created_at.date() != self.last_day.date() and not self.launching:
            self.last_day = message.created_at
            self.database.new_utc_day()

    async def on_ready(self):
        self.launching = False
        self.server = self.client.get_guild(self.config.SERVER_ID)
        await self.sync_users()

    async def on_member_join(self, member: discord.Member):
        user: User = self.get_user_by_id(member.id)
        if user is not None:
            return
        filepath: str = await self.get_user_file(member)
        user = User(id=member.id, name=member.name, bot=int(member.bot), profile_filename=filepath,
                    identifier=member.discriminator, stats=Stats(member.id), is_in_guild=True)
        self.users.append(user)
        self.database.add_user(user)

    async def on_member_remove(self, member: discord.Member):
        user: User = self.get_user_by_id(member.id)
        if user is None:
            return
        user.set_roles(None)
        user.is_in_guild = False
