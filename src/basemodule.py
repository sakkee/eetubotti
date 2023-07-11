from __future__ import annotations
from dataclasses import dataclass
from src.events import EventHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class BaseModule(EventHandler):
    """Base Module Class.

    bot.Bot and the modules in src.modules use this as their base class. The plugins must also implement EventHandler.

    Remember to add the plugins in src.modules.module_list!

    Attributes:
        bot (Bot): main bot object
        enabled (bool): whether this is enabled or not. If False, the module won't be initialized.
        name (str): name of the module. Read from self.__class__.__module__

    See Also:
        https://discordpy.readthedocs.io/en/stable/api.html

    Examples:
        from src.basemodule import BaseModule
        class IRC(BaseModule):
            async def on_ready(self):
                print(f"I'm loaded! My name is {self.name}")
    """
    bot: Bot
    enabled: bool = True
    name: str = ''

    def __post_init__(self):
        self.name = self.__class__.__module__
