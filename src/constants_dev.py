SERVER_ID: int = 501769352995930122


class ROLES:
    LEVEL_5: int = 1114619860689899742
    LEVEL_10: int = 329347892399570955
    LEVEL_20: int = 329348410702561281
    LEVEL_30: int = 329348663446994964
    LEVEL_40: int = 702287190155067402
    LEVEL_50: int = 552214075946434563
    LEVEL_60: int = 749241049876004894
    LEVEL_70: int = 702287809695973377

    MUTED: int = 1115297211228622858

    ACTIVE: int = 1114913650533203969
    HOMIE: int = 1109007710684463184
    SQUAD: int = 427190149659623424
    BIRTHDAY: int = 1114908586301214750

    WHITENAME: int = 735482493016342581
    JUSU: int = 850769993499017227
    ADMIN: int = 250676535474913280
    MOD: int = 315487938073067531

    levels: list[int] = [LEVEL_5, LEVEL_10, LEVEL_20, LEVEL_30, LEVEL_40, LEVEL_50, LEVEL_60, LEVEL_70]
    ban_roles: list[int] = [WHITENAME, JUSU, ADMIN]
    immune_to_ban: list[int] = [WHITENAME, JUSU, ADMIN, MOD, SQUAD, HOMIE]

    @classmethod
    def get_levels(cls, level: int) -> list[int]:
        roles: list[int] = []
        if level >= 5:
            roles.append(cls.LEVEL_5)
        for i in range(int(level / 10)):
            roles.append(cls.levels[i + 1])
        return roles


class CHANNELS:
    YLEINEN: int = 501769353503703043
    YLEINEN2: int = 501769353503703043
    BOTTIKOMENNOT: int = 501813337747881995
    CASINO_HIDE_CHANNEL_ID: int = 1114700719937822840
    MEDIA: int = 735898976364265472
    AFK_CHANNEL: int = 880817227291574303


PURGE_CHANNELS: list[int] = [CHANNELS.BOTTIKOMENNOT, CHANNELS.MEDIA]
DEFAULT_BAN_LENGTH: int = 18  # hours
DIRTHDAY_UPDATE_INTERVAL: int = 6 * 30 * 24 * 60 * 60  # 6 months
DEFAULT_TIMEZONE: str = 'Europe/Helsinki'
PURGE_CHANNEL_HOURS: int = 3  # posts older than this are purged in PURGE_CHANNELS

IGNORE_LEVEL_USERS: list[int] = [
    222717898647535617  # wasabi
]


class AdminCommands:
    BAN: int = 1
    KICK: int = 2
    MUTE: int = 3
    TIMEOUT: int = 4
