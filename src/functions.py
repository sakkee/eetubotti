from __future__ import annotations
import calendar
import datetime
import discord
import pytz
from src.constants import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.objects import User, Stats, ActivityDate, Points


def utc_to_local(utc_dt: datetime.datetime) -> datetime.datetime:
    """UTC datetime to default timezone datetime."""
    local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def dt2ts(dt: datetime.datetime) -> int:
    """Converts a datetime object to UTC timestamp naive datetime will be considered UTC."""
    return calendar.timegm(dt.utctimetuple())


def ts2dt(ts: int) -> datetime.datetime:
    """Timestamp to datetime (in UTC)."""
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


def get_current_timestamp() -> int:
    """Returns a UTC native timestamp."""
    return dt2ts(datetime.datetime.now())


def get_midnight() -> datetime.datetime:
    """Returns the UTC midnight datetime."""
    return datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)


def get_points_till_next_level(level: int) -> int:
    """How many points needed till next level. You can try out different functions."""
    return int(7.79 * (level ** 2) + (77.9 * level) + 80)


def activity_to_points(activity: ActivityDate | Points) -> int:
    return activity.voice_points + activity.message_points


def get_level(points: int) -> int:
    """Convert points to levels."""
    level: int = 0
    while True:
        points -= get_points_till_next_level(level)
        if points >= 0:
            level += 1
        else:
            break
    return level


def get_user_streak(user: User, daylist: Stats.activity_dates) -> int:
    """Calculates the current user streak. Very regarded clusterf that should be changed."""
    reversed_days = daylist[::-1][1:]
    i: int = 1
    for day in reversed_days:
        activity_points = user.stats.get_activity_by_date(day)
        if not activity_points.message_points and not activity_points.voice_points:
            break
        i += 1
    return i


def get_xp_over(points: int) -> tuple[int, int]:
    """Takes total points and returns current xp (on current level) and the needed XP."""
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


def get_actives(users: list[User], daylist: Stats.activity_dates, day_count: int = 14,
                active_count: int = 15, get_current: bool = False) -> list[tuple[User, int]]:
    """Returns the active_count number of most active users over day_count days."""
    days: list[dict[str, int]] = daylist[::-1][1:day_count + 1]
    points: list[tuple[User, Stats.points]] = []
    for user in users:
        if user.bot:
            continue
        activity_points: int = 0
        for day in days:
            activity_points += activity_to_points(user.stats.get_activity_by_date(day))
        if get_current:
            activity_points += user.stats.activity_points_today
        points.append((user, activity_points))
    sorted_list: list[tuple[User, int]] = sorted(points, key=lambda x: -x[1])[:active_count]
    return sorted_list


def get_active_threshold(users: list[User], daylist: Stats.activity_dates) -> int:
    day_count: int = 14
    active_count: int = 15
    actives: list[int] = [x[1] for x in get_actives(users, daylist, day_count, active_count, False)]
    return actives[len(actives) - 1]


def get_next_activity_threshold(users: list[User], daylist: Stats.activity_dates) -> int:
    day_count: int = 13  # 2 weeks
    activity_count: int = 15  # how many active members to list
    actives: list[int] = [x[1] for x in get_actives(users, daylist, day_count, activity_count, True)]
    return actives[-1]


def get_last_14_day_points(user: User, daylist: Stats.activity_dates) -> int:
    day_count: int = 13
    days = daylist[::-1][1:day_count + 1]
    activity_points: int = 0
    for day in days:
        activity_points += activity_to_points(user.stats.get_activity_by_date(day))
    activity_points += user.stats.activity_points_today
    return activity_points


def check_if_administrator(member: discord.Member) -> bool:
    for role in member.roles:
        if role.id == ROLES.WHITENAME:
            return True
        for permission in role.permissions:
            if permission[0] == 'administrator' and permission[1]:
                return True
    return False


def check_if_can_ban(member: discord.Member) -> bool:
    for role in member.roles:
        if role.id == ROLES.WHITENAME:
            return True
        for permission in role.permissions:
            if permission[0] == 'ban_members' and permission[1]:
                return True
    return False


def seconds_to_points(seconds: int) -> int:
    return int(seconds/10)
