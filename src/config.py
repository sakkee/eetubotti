from dataclasses import dataclass
import os
from typing import Any
import configobj


@dataclass
class CfgParser:
    config: configobj.ConfigObj = None

    def __post_init__(self):
        self.load_config()

    def load_config(self):
        if not os.path.exists('CONFIG'):
            raise Exception('CONFIG file not found! Check DEFAULT_CONFIG and rename it')
        self.config = configobj.ConfigObj(open('CONFIG'))

    def get_config(self, category: str, config_name: str, default_value: Any = None) -> Any:
        return self.config.get(category).get(config_name, default_value)

    def get_category(self, category: str) -> dict[str, Any]:
        return self.config.get(category)

    def set_config(self, category: str, config_name: str, new_value: Any):
        if category not in self.config:
            print(f"Category {category} not found in CONFIG file")
            return
        if config_name not in self.get_category(category):
            print(f"Config {config_name} not found in CONFIG file under the category {category}")
            return
        self.config[category][config_name] = new_value
        self.config.write()

    def get_channel(self, channel_name: str) -> int:
        return int(self.get_config('CHANNELS', channel_name))

    def get_role(self, role_name: str) -> int:
        return int(self.get_config('ROLES', role_name))

    def get_level_roles(self, level: int) -> list[int]:
        level_roles: dict[int, int] = {}
        for role in self.get_category('ROLES'):
            if 'LEVEL_' not in role:
                continue
            role_lvl: int = int(role.split('_')[1])
            level_roles[role_lvl] = int(self.get_config('ROLES', role))

        roles: list[int] = []
        for role_level in level_roles:
            if role_level > level:
                continue
            roles.append(level_roles[role_level])

        return roles

    @property
    def ALL_LEVEL_ROLES(self) -> list[int]:
        level_roles: list[int] = []
        for role in self.get_category('ROLES'):
            if 'LEVEL_' not in role:
                continue
            level_roles.append(int(self.get_config('ROLES', role)))
        return level_roles

    @property
    def ROLE_MUTED(self) -> int:
        return self.get_role('MUTED')

    @property
    def ROLE_ACTIVE(self) -> int:
        return self.get_role('ACTIVE')

    @property
    def ROLE_ACTIVE_SQUAD(self) -> int:
        return self.get_role('ACTIVE_SQUAD')

    @property
    def ROLE_SQUAD(self) -> int:
        return self.get_role('SQUAD')

    @property
    def ROLE_BIRTHDAY(self) -> int:
        return self.get_role('BIRTHDAY')

    @property
    def ROLE_FULL_ADMINISTRATOR(self) -> int:
        return self.get_role('FULL_ADMINISTRATOR')

    @property
    def ROLE_OWNER(self) -> int:
        return self.get_role('OWNER')

    @property
    def ROLE_ADMIN(self) -> int:
        return self.get_role('ADMIN')

    @property
    def ROLE_MOD(self) -> int:
        return self.get_role('MOD')

    @property
    def BAN_ROLES(self) -> list[int]:
        return [int(self.get_role(x)) for x in self.get_config('ROLES', 'BAN_ROLES', [])]

    @property
    def IMMUNE_TO_BAN(self) -> list[int]:
        return [int(self.get_role(x)) for x in self.get_config('ROLES', 'IMMUNE_TO_BAN', [])]

    @property
    def CHANNEL_GENERAL(self) -> int:
        return self.get_channel('GENERAL')

    @property
    def CHANNEL_GENERAL2(self) -> int:
        return self.get_channel('GENERAL2')

    @property
    def CHANNEL_BOTCOMMANDS(self) -> int:
        return self.get_channel('BOTCOMMANDS')

    @property
    def CHANNEL_CASINO_HIDE_CHANNEL(self) -> int:
        return self.get_channel('CASINO_HIDE_CHANNEL')

    @property
    def CHANNEL_MEDIA(self) -> int:
        return self.get_channel('MEDIA')

    @property
    def CHANNEL_AFK_VOICE_CHANNEL(self) -> int:
        return self.get_channel('AFK_VOICE_CHANNEÖ')

    @property
    def PURGE_CHANNELS(self) -> list[int]:
        return [self.get_channel(x) for x in self.get_config('CHANNELS', 'PURGE_CHANNELS', [])]

    @property
    def LEVEL_CHANNELS(self) -> list[int]:
        return [self.get_channel(x) for x in self.get_config('CHANNELS', 'LEVEL_CHANNELS', [])]

    @property
    def DEFAULT_BAN_LENGTH_HOURS(self) -> int:
        return int(self.get_config('MISC', 'DEFAULT_BAN_LENGTH_HOURS', 18))

    @property
    def TIMEZONE(self) -> str:
        return self.get_config('MISC', 'TIMEZONE', 'Europe/Helsinki')

    @property
    def PURGE_CHANNELS_INTERVAL_HOURS(self) -> int:
        return self.get_config('MISC', 'PURGE_CHANNELS_INTERVAL_HOURS', 3)

    @property
    def IGNORE_LEVEL_USERS(self) -> list[int]:
        return [int(x) for x in self.get_config('MISC', 'IGNORE_LEVEL_USERS', [])]

    @property
    def SERVER_ID(self) -> int:
        return int(self.get_config('MISC', 'SERVER_ID'))

    @property
    def TOKEN(self) -> str:
        return self.get_config('MISC', 'TOKEN')
