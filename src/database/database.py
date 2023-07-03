from __future__ import annotations
import sqlite3
from sqlite3 import Error
from .database_model import database_model
from src.objects import *
import src.functions as functions
import asyncio
from datetime import datetime, time, timedelta
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bot import Bot

DATABASE_NAME = "data/kristitty.db"


@dataclass
class Database:
    bot: Bot
    connection: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None
    tmp_dbs: list[dict[str, list]] = None
    current_tmpDB: int = 0
    saving_db: int | None = None
    database_counter: int = 0
    sync_interval: int = 2000

    def __post_init__(self):
        self.tmp_dbs = [{}, {}]
        self.connection = sqlite3.connect(DATABASE_NAME)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def setup_database(self):
        print("Setupping database")
        self.saving_db = 0
        for table in database_model:
            self.tmp_dbs[0][table.name] = []
            self.tmp_dbs[1][table.name] = []
            columns_and_types: str = ""
            values: str = ""
            columns: str = ""
            questions: str = ""
            vals = ()
            for i in range(len(table.columns)):
                if i > 0:
                    columns += ", "
                    columns_and_types += ", "
                    values += ", "
                    questions += ", "
                questions += "?"
                columns_and_types += table.columns[i].name + " " + table.columns[i].type
                if table.columns[i].default is None:
                    values += "null"
                else:
                    values += table.columns[i].default
                vals += table.columns[i].default,
                columns += table.columns[i].name
            self.cursor.execute("CREATE TABLE IF NOT EXISTS " + table.name + " (" + columns_and_types + ");")

        self.connection.commit()

        self.saving_db = None
        print("Database setupped!")

    def get_reactions(self) -> list[Reaction]:
        print("Fetching reactions from db...")
        self.cursor.execute("SELECT * from Reactions ORDER BY message_id DESC")
        reactions: list = self.cursor.fetchall()
        reacts: list = []
        for reaction in reactions:
            reacts.append(Reaction(reaction['message_id'], reaction['emoji_id'], reaction['count'], True))
        print("Reactions fetched")
        return reacts

    def get_last_post_id(self) -> int:
        self.cursor.execute("SELECT MAX(id) FROM Messages")
        val = self.cursor.fetchone()[0]
        return 0 if not val else val

    def get_users(self) -> list[User]:
        print("Getting users from db...")
        self.cursor.execute("SELECT * " +
                            "FROM User " +
                            "JOIN UserStats ON User.id=UserStats.user_id " +
                            "LEFT JOIN ActivityDates ON User.id=ActivityDates.user_id;")
        db_users: list = self.cursor.fetchall()
        users: dict[str, User] = {}
        for user in db_users:
            user_id = str(user["user_id"])
            if user_id not in users:
                user_stats = Stats(
                    user_id=user['user_id'],
                    time_in_voice=user['time_in_voice'],
                    points=user['points'],
                    first_post_time=user['first_post_time'],
                    gif_count=user['gif_count'],
                    emoji_count=user['emoji_count'],
                    bot_command_count=user['bot_command_count'],
                    total_post_length=user['total_post_length'],
                    mentioned_times=user['mentioned_times'],
                    files_sent=user['files_sent'],
                    longest_streak=user['longest_streak'],
                    last_post_time=user['last_post_time'],
                    is_in_database=True
                )

                usr = User(
                    id=user['id'],
                    name=user['name'],
                    bot=user['bot'],
                    profile_filename=user['profile_filename'],
                    identifier=user['identifier'],
                    stats=user_stats, is_in_database=True)

                users[user_id] = usr
            ad = ActivityDate(
                user_id=user['user_id'],
                year=user['year'],
                month=user['month'],
                day=user['day'],
                message_points=user['message_points'],
                voice_points=user['voice_points'])
            users[user_id].stats.add_activitydate(ad)
        print("Users gotten...")
        return [value for value in users.values()]

    def add_user(self, user: User):
        self.tmp_dbs[self.current_tmpDB]['User'].append(user)
        self.tmp_dbs[self.current_tmpDB]['UserStats'].append(user.stats)

    def get_messages_by_user(self, user_id: int | list[int]) -> list[dict[str, int | str]]:
        user_id: list[int] = [user_id] if isinstance(user_id, int) else user_id
        self.cursor.execute(
            f"SELECT id, attachments FROM Messages WHERE user_id IN ({','.join(['?'] * len(user_id))})",
            user_id
        )
        messages: list[dict[str, int | str]] = []
        for msg in self.cursor.fetchall():
            messages.append({
                'id': msg['id'],
                'attachments': msg['attachments']
            })
        return messages

    def get_daylist(self) -> list[dict[str, int]]:
        self.cursor.execute(
            "SELECT year, month, day FROM ActivityDates GROUP BY year, month, day ORDER BY year, month, day")
        val: list = self.cursor.fetchall()
        daylist: list = []
        dt: datetime = functions.get_midnight()
        curr_day: dict = {'year': dt.year, 'month': dt.month, 'day': dt.day}
        found: bool = False
        for v in val:
            daylist.append({'year': v['year'], 'month': v['month'], 'day': v['day']})
            if curr_day['year'] == v['year'] and curr_day['month'] == v['month'] and curr_day['day'] == v['day']:
                found = True
                break
        if not found:
            daylist.append({'year': curr_day['year'], 'month': curr_day['month'], 'day': curr_day['day']})
        return daylist

    def db_save(self):
        if self.saving_db is not None and self.saving_db == self.current_tmpDB:
            self.current_tmpDB = 1 if not self.current_tmpDB else 0
        self.update_userstats()
        self.save_database()

    def new_utc_day(self):
        """Called when new day in UTC."""
        midnight: int = functions.dt2ts(functions.get_midnight())
        previous_midnight: int = functions.dt2ts(functions.get_midnight() - timedelta(days=1))
        mn: datetime = functions.get_midnight()
        p_mn: datetime = functions.get_midnight() - timedelta(days=1)

        found: bool = False
        for day in self.bot.daylist:
            if day['year'] == mn.year and day['month'] == mn.month and day['day'] == mn.day:
                found = True
                break
        if not found:
            self.bot.daylist.append({'year': mn.year, 'month': mn.month, 'day': mn.day})

        self.cursor.execute(
            "SELECT user_id, SUM(activity_points) as act_points " +
            "FROM Messages WHERE created_at>=? AND created_at<? GROUP BY user_id;", (previous_midnight, midnight))
        messages: list = self.cursor.fetchall()
        users: dict[str, Points] = {}
        for msg in messages:
            user_id: str = str(msg['user_id'])
            if user_id not in users:
                users[user_id] = Points(0, 0)
            users[user_id].message_points += msg['act_points'] or 0

        self.cursor.execute("SELECT user_id, SUM(activity_points) as act_points " +
                            "FROM VoiceDates WHERE end_time>=? AND end_time<? GROUP BY user_id;",
                            (previous_midnight, midnight))
        voice_dates: list = self.cursor.fetchall()
        for vd in voice_dates:
            user_id: str = str(vd['user_id'])
            if user_id not in users:
                users[user_id] = Points(0, 0)
            users[user_id].voice_points += vd['act_points']

        activity_dates: list[ActivityDate] = []
        print("Inserting activitydates...")
        for user in users:
            if not users[user].message_points and not users[user].voice_points:
                continue
            activity_dates.append(ActivityDate(user_id=int(user), year=p_mn.year, month=p_mn.month, day=p_mn.day,
                                               message_points=users[user].message_points,
                                               voice_points=users[user].voice_points))
            self.cursor.execute(
                "INSERT INTO ActivityDates (user_id, year, month, day, message_points, voice_points) " +
                "VALUES (?, ?, ?, ?, ?, ?)",
                (int(user), p_mn.year, p_mn.month, p_mn.day, users[user].message_points, users[user].voice_points))
        self.connection.commit()

        print("Adding user activitydates...")
        usrs: list[User.id] = [x.user_id for x in activity_dates]
        for user in self.bot.users:
            if user.id not in usrs:
                user.stats.add_activitydate(ActivityDate(0, 0, user.id, p_mn.year, p_mn.month, p_mn.day))
            else:
                for ad in activity_dates:
                    if ad.user_id == user.id:
                        user.stats.add_activitydate(ad)
                        break

    def update_userstats(self):
        user_id_list = [x.user_id for x in self.tmp_dbs[self.current_tmpDB]['UserStats']]
        for user in self.bot.users:
            if user.stats.should_update and user.id not in user_id_list:
                self.tmp_dbs[self.current_tmpDB]['UserStats'].append(user.stats)

    def add_message(self, message: Message):
        self.tmp_dbs[self.current_tmpDB]['Messages'].append(message)

    def add_reaction(self, reaction: Reaction):
        self.tmp_dbs[self.current_tmpDB]['Reactions'].append(reaction)

    def add_voicedate(self, voicedate: VoiceDate):
        self.tmp_dbs[self.current_tmpDB]['VoiceDates'].append(voicedate)

    def add_raw_reaction(self, reaction: Reaction):
        found: bool = False
        for react in self.tmp_dbs[self.current_tmpDB]['Reactions']:
            if react.message_id == reaction.message_id and react.emoji_id == reaction.emoji_id:
                found = True
                break
        if not found:
            self.tmp_dbs[self.current_tmpDB]['Reactions'].append(reaction)

    def update_database(self, table: str, elem: User | Reaction | Message | VoiceDate | Stats):
        if table == 'User':
            if not elem.is_in_database:
                try:
                    self.cursor.execute(
                        "INSERT INTO " + table + " (id, name, bot, profile_filename, identifier) VALUES (?, ?, ?, ?,?)",
                        (elem.id, elem.name, elem.bot, elem.profile_filename, elem.identifier))
                    elem.is_in_database = True
                except sqlite3.IntegrityError as e:
                    pass
                elem.is_in_database = True
            else:
                self.cursor.execute(
                    "UPDATE " + table + " SET name=?, profile_filename=?, identifier=? WHERE id=?;",
                    (elem.name, elem.profile_filename, elem.identifier, elem.id))

        elif table == 'Reactions':
            if not elem.is_in_database:
                self.cursor.execute("INSERT INTO " + table + " (message_id, emoji_id, count) VALUES (?, ?, ?)",
                                    (elem.message_id, elem.emoji_id, elem.count))
            else:
                self.cursor.execute("UPDATE " + table + " SET count=? WHERE message_id=? AND emoji_id=?",
                                    (elem.count, elem.message_id, elem.emoji_id))
            elem.is_in_database = True

        elif table == 'Messages':
            try:
                self.cursor.execute(
                    "INSERT INTO " + table + " (id, attachments, user_id, jump_url, reference, created_at, " +
                    "mentions_everyone, mentioned_user_id, length, is_gif, has_emoji, " +
                    "is_bot_command, activity_points)" +
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (elem.id, elem.attachments, elem.user_id, elem.jump_url, elem.reference,
                     elem.created_at.timestamp(), elem.mentions_everyone, elem.mentioned_user_id,
                     elem.length, elem.is_gif, elem.has_emoji, elem.is_bot_command, elem.activity_points))
            except sqlite3.IntegrityError as e:
                pass

        elif table == 'VoiceDates':
            self.cursor.execute(
                "INSERT INTO " + table + " (user_id, start_time, end_time, activity_points) VALUES (?, ?, ?, ?)",
                (elem.user_id, elem.start_time, elem.end_time, elem.activity_points))

        elif table == 'UserStats':
            try:
                if not elem.is_in_database:
                    self.cursor.execute(
                        "INSERT INTO " + table + " (user_id, time_in_voice, points, first_post_time, gif_count, " +
                        "emoji_count, bot_command_count, total_post_length, mentioned_times, " +
                        "files_sent, longest_streak, last_post_time) " +
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                            elem.user_id, elem.time_in_voice, elem.points, elem.first_post_time, elem.gif_count,
                            elem.emoji_count, elem.bot_command_count, elem.total_post_length, elem.mentioned_times,
                            elem.files_sent, elem.longest_streak, elem.last_post_time))
                elif elem.should_update:
                    self.cursor.execute(
                        "UPDATE " + table + " SET time_in_voice=?, points=?, first_post_time=?, gif_count=?, " +
                        "emoji_count=?, bot_command_count=?, total_post_length=?, " +
                        "mentioned_times=?, files_sent=?, longest_streak=?, last_post_time=?" +
                        " WHERE user_id=?", (
                            elem.time_in_voice, elem.points, elem.first_post_time, elem.gif_count, elem.emoji_count,
                            elem.bot_command_count, elem.total_post_length, elem.mentioned_times, elem.files_sent,
                            elem.longest_streak, elem.last_post_time, elem.user_id))

                elem.is_in_database = True
                elem.should_update = False
            except sqlite3.IntegrityError as e:
                pass

    def save_database(self):
        old_db = self.current_tmpDB
        self.saving_db = self.current_tmpDB
        for table in self.tmp_dbs[old_db]:
            if len(self.tmp_dbs[old_db][table]) == 0:
                continue
            for elem in self.tmp_dbs[old_db][table]:
                self.update_database(table, elem)
            self.tmp_dbs[old_db][table][:] = []
            self.connection.commit()
            self.saving_db = None
