from __future__ import annotations
import calendar
import datetime
import discord
import pytz
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.objects import User, Stats
    from src.bot import Bot


def utc_to_local(utc_dt: datetime.datetime, timezone: str) -> datetime.datetime:
    """UTC datetime to default timezone datetime.

    Args:
        utc_dt (datetime.datetime): the UTC datetime to be converted to DEFAULT_TIMEZONE.
        timezone (str): the timezone of the bot

    Returns:
        Localized datetime object.
    """
    local_tz = pytz.timezone(timezone)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def dt2ts(dt: datetime.datetime) -> int:
    """Converts a datetime object to UTC timestamp naive datetime will be considered UTC.

    Args:
        dt (datetime.datetime): UTC datetime object

    Returns:
        Timestamp of the UTC datetime object.
    """
    return calendar.timegm(dt.utctimetuple())


def ts2dt(ts: int) -> datetime.datetime:
    """Timestamp to datetime (in UTC).

    Args:
        ts (int): UTC timestamp to be converted.

    Returns:
        UTC datetime object of the timestamp.
    """
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


def get_current_timestamp() -> int:
    """
    Returns:
        A UTC native timestamp.
    """
    return dt2ts(datetime.datetime.now())


def get_midnight() -> datetime.datetime:
    """
    Returns:
        The UTC midnight datetime.
    """
    return datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)


def get_points_till_next_level(level: int) -> int:
    """How many points needed till next level. You can try out different functions.

    Args:
        level (int): the current level.

    Returns:
        How many points needed from level to level + 1.
    """
    return int(7.79 * (level ** 2) + (77.9 * level) + 80)


def get_level(points: int) -> int:
    """Convert points to levels.

    Args:
        points (int): The User points to be converted to levels.

    Returns:
        The level converted from the points.
    """
    level: int = 0
    while True:
        points -= get_points_till_next_level(level)
        if points >= 0:
            level += 1
        else:
            break
    return level


def get_user_streak(user: User, daylist: Bot.daylist) -> int:
    """Calculates the current user streak. Very regarded clusterf that should be changed.

    Args:
        user (User): The User whose streak is being calculated.
        daylist (Bot.daylist): The bot.py daylist.

    Returns:
        The user streak in days.
    """
    reversed_days = daylist[::-1][1:]
    i: int = 1
    for day in reversed_days:
        activity_points = user.stats.get_activity_by_date(day)
        if not activity_points.message_points and not activity_points.voice_points:
            break
        i += 1
    return i


def get_xp_over(points: int) -> tuple[int, int]:
    """Takes total points and returns current xp (on current level) and the needed XP.

    Args:
        points (int): User points.

    Returns:
        A tuple where the first attribute is the current XP of the current level, and the second attribute is
        the needed XP for the next level.
    """
    current_xp: int = 0
    level: int = 0
    while True:
        points -= get_points_till_next_level(level)
        needed_xp = get_points_till_next_level(level)
        if points >= 0:
            current_xp = points
            level += 1
        else:
            break
    return current_xp, needed_xp


def get_actives(users: Bot.users, daylist: Bot.daylist, day_count: int = 14,
                active_count: int = 15, get_current: bool = False) -> list[tuple[User, int]]:
    """Returns the most active users.

    Args:
        users (Bot.users): All users the bot knows about.
        daylist (Bot.daylist): The know days when the server has been active.
        day_count (int): From how many days the top actives will be calculated from.
        active_count (int): How many active persons included.
        get_current (bool): Whether to calculate from today or from yesterday.

    Returns:
        A list of Users and their points from the past days.
    """
    days: list[dict[str, int]] = daylist[::-1][1:day_count + 1]
    points: list[tuple[User, Stats.points]] = []
    for user in users:
        if user.bot:
            continue
        activity_points: int = 0
        for day in days:
            activity_points += user.stats.get_activity_by_date(day).points
        if get_current:
            activity_points += user.stats.activity_points_today
        points.append((user, activity_points))
    sorted_list: list[tuple[User, int]] = sorted(points, key=lambda x: -x[1])[:active_count]
    return sorted_list


def get_active_threshold(users: Bot.users, daylist: Bot.daylist) -> int:
    """How many points needed for the active role.

    Args:
        users (Bot.users): The list of all Users.
        daylist (Bot.daylist): The known days when the server has been active.

    Returns:
        Points needed for the active role today.
    """
    day_count: int = 14
    active_count: int = 15
    actives: list[int] = [x[1] for x in get_actives(users, daylist, day_count, active_count, False)]
    return actives[len(actives) - 1]


def get_next_activity_threshold(users: Bot.users, daylist: Bot.daylist) -> int:
    """How many points needed for active role tomorrow.

    Args:
        users (Bot.users): The list of all Users.
        daylist (Bot.daylist): The known days when the server has been active.

    Returns:
        Points needed for the active role tomorrow.
    """
    day_count: int = 13  # 2 weeks
    activity_count: int = 15  # how many active members to list
    actives: list[int] = [x[1] for x in get_actives(users, daylist, day_count, activity_count, True)]
    return actives[-1]


def get_last_14_day_points(user: User, daylist: Bot.daylist) -> int:
    """Return the points from last 14 days.

    Args:
        user (User): The user whose points are being calculated.
        daylist (Bot.daylist): the known days the server has been active.

    Returns:
        Points from the past 14 days for the user.
    """
    day_count: int = 13
    days = daylist[::-1][1:day_count + 1]
    activity_points: int = 0
    for day in days:
        activity_points += user.stats.get_activity_by_date(day).points
    activity_points += user.stats.activity_points_today
    return activity_points


def check_if_administrator(member: discord.Member, role_full_admin: int = 0) -> bool:
    """Check if the member has administrator permissions on the server."""
    for role in member.roles:
        if role.id == role_full_admin:
            return True
        for permission in role.permissions:
            if permission[0] == 'administrator' and permission[1]:
                return True
    return False


def check_if_can_ban(member: discord.Member, ban_roles: list[int]) -> bool:
    """Check whether the user is allowed to ban people."""
    for role in member.roles:
        if role.id in ban_roles:
            return True
        for permission in role.permissions:
            if permission[0] == 'ban_members' and permission[1]:
                return True
    return False


def seconds_to_points(seconds: int) -> int:
    """Voice active seconds to points."""
    return int(seconds / 10)
