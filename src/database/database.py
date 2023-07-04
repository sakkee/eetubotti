from __future__ import annotations
import sqlite3
from .database_model import database_model
from src.objects import *
import src.functions as functions
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.bot import Bot

DATABASE_NAME: str = "data/kristitty.db"


@dataclass
class Database:
    """
    Database object handling the database connection and logic. All database interactions should occur through
    this class. Database is updated every 5 minutes (at minimum, the bot tracks time by messages).

    Args:
        bot (Bot): The main Bot object.

    Attributes:
        bot (Bot): The main Bot object.
        connection (sqlite3.Connection): sqlite3 database connection.
        cursor (sqlite3.Cursor): sqlite3 database cursor.
        unsaved_changes (dict[str, list]): this object tracks the unsaved changes that are to be updated to the database
            {tablename: [object1, object2, ...]}.
    """
    bot: Bot
    connection: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None
    unsaved_changes: dict[str, list] = field(default_factory=dict)

    def __post_init__(self):
        """Establish the database connection."""
        self.connection = sqlite3.connect(DATABASE_NAME)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def setup_database(self):
        """Setup the database according to database_model.database_model.

        Note: this doesn't allow updating tables yet... If you update existing tables on database_model, you need to
        update them manually. Quite ugly sh*t at the moment, could/should be made more beautiful.

        Check the database_model for the database model.
        """
        print("Setupping database")
        for table in database_model:
            self.unsaved_changes[table.name] = []  # init the table names to unsaved_changes
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
        print("Database setupped!")

    def get_reactions(self) -> list[Reaction]:
        """Get reactions from the database.

        Returns:
            A list of Reaction objects initialized from the Reactions table.
        """
        print("Fetching reactions from db...")
        self.cursor.execute("SELECT * from Reactions ORDER BY message_id DESC")
        reactions: list = self.cursor.fetchall()
        reacts: list[Reaction] = [Reaction(x['message_id'], x['emoji_id'], x['count'], True) for x in reactions]
        print("Reactions fetched")
        return reacts

    def get_last_post_id(self) -> int:
        """Fetch the max id from the Messages table.

        Returns:
            0 if no last post id found from Messages else MAX(id) from Messages table.
        """

        self.cursor.execute("SELECT MAX(id) FROM Messages")
        return self.cursor.fetchone()[0] or 0

    def get_users(self) -> list[User]:
        """Get users from the database.

        Also update the Activity Dates and User Stats to the Users while looping through the users.

        Returns:
            A list of User objects from the database that have their stats and activity dates initialized.
        """
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
        """Add user to the database or update the user in the database.

        Args:
            user (User): A User object to be added to or updated in the database.
        """
        self.unsaved_changes['User'].append(user)
        self.unsaved_changes['UserStats'].append(user.stats)

    def get_messages_by_user(self, user_id: int | list[int]) -> list[dict[str, int | str]]:
        """(NOT REALLY USED) Get messages from Messages table by user ID or a list of user ID's.

        Args:
           user_id (int | list[int]): A User ID or a list of User ID's to get their messages.

       Returns:
           A list of messages from the database according to the user_id variable.
        """
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
        """Creates day list from the ActivityDates (used for streaks).

        Returns:
            A list of date dicts. Example:
            [{'year': 2023, 'month': 6, 'day': 30}, {'year': 2023, 'month': 6, 'day': 29}, ...]
        """
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
        """Check the user stats to be updated, and then save database."""
        self.update_userstats()
        self.save_database()

    def new_utc_day(self):
        """Called when a new day in UTC. Calculates the message points and voice points for the previous day.

        The calculated points are added to the ActivityDates table and the points are added to the users' stats.
        These stats are used to calculate streaks and the activity.
        """
        midnight_timestamp: int = functions.dt2ts(functions.get_midnight())
        previous_midnight_timestamp: int = functions.dt2ts(functions.get_midnight() - timedelta(days=1))
        midnight: datetime = functions.get_midnight()
        previous_midnight: datetime = functions.get_midnight() - timedelta(days=1)

        # add current day to the self.bot.daylist if current day not found
        found: bool = False
        for day in self.bot.daylist:
            if day['year'] == midnight.year and day['month'] == midnight.month and day['day'] == midnight.day:
                found = True
                break
        if not found:
            self.bot.daylist.append({'year': midnight.year, 'month': midnight.month, 'day': midnight.day})

        # get message points for the previous day
        self.cursor.execute(
            "SELECT user_id, SUM(activity_points) as act_points " +
            "FROM Messages WHERE created_at>=? AND created_at<? GROUP BY user_id;",
            (previous_midnight_timestamp, midnight_timestamp))
        messages: list = self.cursor.fetchall()
        users: dict[str, Points] = {}
        for msg in messages:
            user_id: str = str(msg['user_id'])
            if user_id not in users:
                users[user_id] = Points(0, 0)
            users[user_id].message_points += msg['act_points'] or 0

        # get voice points for the previous day
        self.cursor.execute("SELECT user_id, SUM(activity_points) as act_points " +
                            "FROM VoiceDates WHERE end_time>=? AND end_time<? GROUP BY user_id;",
                            (previous_midnight_timestamp, midnight_timestamp))
        voice_dates: list = self.cursor.fetchall()
        for vd in voice_dates:
            user_id: str = str(vd['user_id'])
            if user_id not in users:
                users[user_id] = Points(0, 0)
            users[user_id].voice_points += vd['act_points']

        # update ActivityDates table with the calculated message points and voice points for the previous day
        activity_dates: list[ActivityDate] = []
        print("Inserting activitydates...")
        for user in users:
            if not users[user].message_points and not users[user].voice_points:
                continue
            activity_dates.append(ActivityDate(user_id=int(user),
                                               year=previous_midnight.year,
                                               month=previous_midnight.month,
                                               day=previous_midnight.day,
                                               message_points=users[user].message_points,
                                               voice_points=users[user].voice_points))
            self.cursor.execute(
                "INSERT INTO ActivityDates (user_id, year, month, day, message_points, voice_points) " +
                "VALUES (?, ?, ?, ?, ?, ?)",
                (int(user), previous_midnight.year, previous_midnight.month, previous_midnight.day,
                 users[user].message_points, users[user].voice_points))
        self.connection.commit()  # update the database

        # add new previous day's activity date to the users
        print("Adding user activitydates...")
        usrs: list[User.id] = [x.user_id for x in activity_dates]
        for user in self.bot.users:
            if user.id not in usrs:
                user.stats.add_activitydate(ActivityDate(
                    0, 0, user.id, previous_midnight.year, previous_midnight.month, previous_midnight.day))
            else:
                for ad in activity_dates:
                    if ad.user_id == user.id:
                        user.stats.add_activitydate(ad)
                        break

    def update_userstats(self):
        """Add User.stats to the self.unsaved_changes if they should be updated in the database."""
        user_id_list = [x.user_id for x in self.unsaved_changes['UserStats']]
        for user in self.bot.users:
            if not user.stats.should_update or user.id in user_id_list:
                self.unsaved_changes['UserStats'].append(user.stats)

    def add_message(self, message: Message):
        self.unsaved_changes['Messages'].append(message)

    def add_reaction(self, reaction: Reaction):
        self.unsaved_changes['Reactions'].append(reaction)

    def add_voicedate(self, voicedate: VoiceDate):
        self.unsaved_changes['VoiceDates'].append(voicedate)

    def add_raw_reaction(self, reaction: Reaction):
        found: bool = False
        for react in self.unsaved_changes['Reactions']:
            if react.message_id == reaction.message_id and react.emoji_id == reaction.emoji_id:
                found = True
                break
        if not found:
            self.unsaved_changes['Reactions'].append(reaction)

    def update_database(self, table: str, elem: User | Reaction | Message | VoiceDate | Stats):
        """Insert an element to the database or update the element in the database.

        Args:
            table (str): The name of the table.
            elem (User | Reaction | Message | VoiceDate | Stats): Element to be updated or inserted into the databse.
        """

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
                    "is_bot_command, activity_points) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                        "mentioned_times=?, files_sent=?, longest_streak=?, last_post_time=? " +
                        "WHERE user_id=?", (
                            elem.time_in_voice, elem.points, elem.first_post_time, elem.gif_count, elem.emoji_count,
                            elem.bot_command_count, elem.total_post_length, elem.mentioned_times, elem.files_sent,
                            elem.longest_streak, elem.last_post_time, elem.user_id))

                elem.is_in_database = True
                elem.should_update = False
            except sqlite3.IntegrityError as e:
                pass

    def save_database(self):
        """Save the database. Called every 5 minute (at minimum by Bot object).

        Copy the self.unsaved_changes to copied_changes variable so the self.unsaved_changes changing while
        updating the database won't cause any errors.
        """
        copied_changes: dict[str, list] = {x: self.unsaved_changes[x] for x in self.unsaved_changes}
        for table in self.unsaved_changes:
            self.unsaved_changes[table][:] = []
        for table in copied_changes:
            if len(copied_changes[table]) == 0:
                continue
            for elem in copied_changes[table]:
                self.update_database(table, elem)
        self.connection.commit()
