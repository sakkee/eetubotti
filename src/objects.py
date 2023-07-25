from __future__ import annotations
from dataclasses import dataclass, field
import re
import discord
import src.functions as functions


@dataclass
class User:
    id: int
    stats: Stats
    name: str
    bot: int
    profile_filename: str
    identifier: discord.User.discriminator
    vc_join_time: int | None = None
    level: int = 0
    roles: list[discord.Role.id] = field(default_factory=list)
    is_in_guild: bool = False
    is_in_database: bool = False
    irc: Irc = None
    voicedate: VoiceDate = None

    def __post_init__(self):
        self.refresh_level()

    def set_roles(self, roles: list[discord.Role] | None = None):
        self.roles[:] = []
        if not roles:
            return
        for role in roles:
            self.roles.append(role.id)

    def refresh_level(self) -> int:
        self.level = functions.get_level(self.stats.points)
        return self.level

    def add_points(self, points: int) -> bool:
        """Returns True if new level, else False.
        """
        self.stats.points += points
        self.stats.activity_points_today += points
        self.stats.should_update = True
        return self.level == self.refresh_level()

    def is_ban_protected(self, ban_immune_roles: list[int]) -> bool:
        for role in self.roles:
            if role in ban_immune_roles:
                return True
        return False


@dataclass
class Stats:
    user_id: User.id
    time_in_voice: int = 0
    points: int = 0
    total_post_length: int = 0
    mentioned_times: int = 0
    files_sent: int = 0
    longest_streak: int = 0
    first_post_time: int = 0
    last_post_time: int = 0
    gif_count: int = 0
    emoji_count: int = 0
    bot_command_count: int = 0
    activity_points_today: int = 0
    is_in_database: bool = False
    # {'2018': {'1': {'30': ActivityDate}}}
    activity_dates: dict[str, dict[str, dict[str, Points]]] = field(default_factory=dict)
    should_update: bool = False

    def get_activity_by_date(self, date: dict[str, int]) -> Points:
        try:
            year, month, day = str(date.get('year')), str(date.get('month')), str(date.get('day'))
            if not self.activity_dates.get(year).get(month).get(day):
                return Points(0, 0)
            return self.activity_dates.get(year).get(month).get(day)
        except (KeyError, AttributeError):
            return Points(0, 0)

    def add_activitydate(self, activity_date: ActivityDate):
        self.activity_points_today = 0
        year, month, day = str(activity_date.year), str(activity_date.month), str(activity_date.day)
        if year not in self.activity_dates:
            self.activity_dates[year] = {}
        if month not in self.activity_dates.get(year):
            self.activity_dates[year][month] = {}
        if day not in self.activity_dates.get(year).get(month):
            self.activity_dates[year][month][day] = activity_date


@dataclass
class Message:
    id: discord.Message.id
    user_id: discord.Message.author
    content: discord.Message.content
    attachments: int
    jump_url: discord.Message.jump_url
    reference: discord.Message.id
    created_at: discord.Message.created_at
    mentions_everyone: discord.Message.mention_everyone
    mentioned_user_id: User.id
    activity_points: int = 0
    length: int = 0
    is_gif: int = 0
    has_emoji: int = 0
    is_bot_command: int = 0

    def __post_init__(self):
        self.is_gif = self.check_if_gif(self.content)
        self.has_emoji = self.check_if_emoji(self.content)
        self.is_bot_command = self.check_if_bot_command(self.content)
        self.length = self.calculate_message_length(self.content, self.attachments, self.is_bot_command)

    @staticmethod
    def check_if_bot_command(text: str) -> int:
        if len(text) >= 2 and text[0] in ['?', '.', '!', '/'] and text != len(text) * text[0]:
            return 1
        if 'pls ' in text:
            return 1
        return 0

    @staticmethod
    def calculate_message_length(text: str, has_file: int, is_bot_command: int) -> int:
        text = re.sub(r'^https?:\/\/.*[\r\n]*', '{url}', text, flags=re.MULTILINE)
        text = re.sub(r'<:.*>', '{e}', text, flags=re.MULTILINE)
        text = re.sub(r':[a-zA-Z]+:', '{e}', text, flags=re.MULTILINE)
        text = re.sub(r'<[a-zA-Z0-9@!]+>', '{m}', text, flags=re.MULTILINE)
        i = (text + text).find(text, 1, -1)
        if i != -1:
            text = text[:1]
        text = text.strip()
        text = re.sub(' +', ' ', text)
        text = text[:128]
        length = len(text)
        if has_file:
            length += 10
        if is_bot_command:
            length = 5
        return length

    @staticmethod
    def check_if_gif(content: str) -> int:
        text = re.sub(r'^https?:\/\/.*[\r\n]*', '{url}', content, flags=re.MULTILINE)
        if text == '{url}' and ('gif' in content or 'GIF' in content or 'tenor' in content):
            return 1
        return 0

    @staticmethod
    def check_if_emoji(content: str) -> int:
        text = re.sub(r':[a-zA-Z]+:', '{e}', content, flags=re.MULTILINE)
        if '{e}' in text:
            return 1
        text = re.sub(r'<:.*>', '{e}', text, flags=re.MULTILINE)
        if '{e}' in text:
            return 1
        return 0


@dataclass
class VoiceDate:
    user_id: User.id
    start_time: float
    end_time: float | None
    activity_points: int = 0
    active_times: list[ActiveTime] = field(default_factory=list)

    def get_seconds(self) -> int:
        return int(self.end_time - self.start_time)

    @property
    def seconds(self):
        seconds: int = 0
        for active_time in self.active_times:
            seconds += active_time.seconds
        return seconds

    def add_active_time(self, active_time: ActiveTime):
        self.active_times.append(active_time)

    def mark_active(self, timestamp: float):
        self.add_active_time((ActiveTime(start_time=timestamp)))

    def mark_inactive(self, timestamp: float):
        self.end_time = timestamp
        if len(self.active_times) > 0:
            self.active_times[-1].end_time = timestamp


@dataclass
class ActiveTime:
    start_time: float
    end_time: float | None = None

    @property
    def seconds(self) -> int:
        return int(self.end_time - self.start_time)


@dataclass
class Points:
    message_points: int
    voice_points: int

    @property
    def points(self) -> int:
        return self.message_points + self.voice_points


@dataclass
class ActivityDate(Points):
    user_id: User.id
    year: int
    month: int
    day: int


@dataclass
class Irc:
    name: str
    link: str
    photo: str


class AdminCommands:
    BAN: int = 1
    KICK: int = 2
    MUTE: int = 3
    TIMEOUT: int = 4


@dataclass
class AdminLog:
    admin: User
    timestamp: int
    command: AdminCommands.BAN | AdminCommands.KICK | AdminCommands.MUTE | AdminCommands.TIMEOUT
    target: User = None
    reason: str = ''

    def as_json(self) -> dict:
        return {
            'admin': self.admin.id,
            'timestamp': self.timestamp,
            'command': self.command,
            'target': self.target.id if self.target else None,
            'reason': self.reason
        }


@dataclass
class Reaction:
    message_id: Message.id
    emoji_id: int
    count: int
    is_in_database: bool = False
