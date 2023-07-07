"""
The database model used by Database class.

Usage in Database.setup_database.
"""

from dataclasses import dataclass


@dataclass
class Column:
    name: str
    type: str
    default: str | None = None


@dataclass
class Table:
    name: str
    columns: list[Column]


database_model: list[Table] = [
    Table('User', [
        Column('id', 'INTEGER PRIMARY KEY NOT NULL UNIQUE'),
        Column('name', 'VARCHAR(32) NOT NULL'),
        Column('bot', 'INTEGER', '0'),
        Column('profile_filename', 'VARCHAR(128)'),
        Column('identifier', 'VARCHAR(4)', '0')
    ]),

    Table('Reactions', [
        Column('message_id', 'INTEGER NOT NULL'),
        Column('emoji_id', 'INTEGER'),
        Column('count', 'INTEGER')
    ]),

    Table('Messages', [
        Column('id', 'INTEGER PRIMARY KEY NOT NULL UNIQUE'),
        Column('attachments', 'INTEGER', '0'),
        Column('user_id', 'INTEGER', '0'),
        Column('jump_url', 'VARCHAR(200)', ''),
        Column('reference', 'INTEGER'),
        Column('created_at', 'INTEGER NOT NULL'),
        Column('mentions_everyone', 'INTEGER', '0'),
        Column('mentioned_user_id', 'INTEGER'),
        Column('length', 'INTEGER', '1'),
        Column('is_gif', 'INTEGER', '0'),
        Column('has_emoji', 'INTEGER', '0'),
        Column('is_bot_command', 'INTEGER', '0'),
        Column('activity_points', 'INTEGER', '0')
    ]),

    Table('VoiceDates', [
        Column('user_id', 'INTEGER NOT NULL'),
        Column('start_time', 'INTEGER'),
        Column('end_time', 'INTEGER'),
        Column('activity_points', 'INTEGER', '0')
    ]),

    Table('UserStats', [
        Column('user_id', 'INTEGER PRIMARY KEY NOT NULL UNIQUE'),
        Column('time_in_voice', 'INTEGER', '0'),
        Column('points', 'INTEGER', '0'),
        Column('old_points', 'INTEGER', '0'),
        Column('total_post_length', 'INTEGER', '0'),
        Column('mentioned_times', 'INTEGER', '0'),
        Column('files_sent', 'INTEGER', '0'),
        Column('longest_streak', 'INTEGER', '0'),
        Column('first_post_time', 'INTEGER', '0'),
        Column('last_post_time', 'INTEGER', '0'),
        Column('gif_count', 'INTEGER', '0'),
        Column('emoji_count', 'INTEGER', '0'),
        Column('bot_command_count', 'INTEGER', '0')
    ]),

    Table('Streaks', [
        Column('user_id', 'INTEGER NOT NULL'),
        Column('streak_days', 'INTEGER')
    ]),

    Table('ActivityDates', [
        Column('user_id', 'INTEGER NOT NULL'),
        Column('year', 'INTEGER NOT NULL'),
        Column('month', 'INTEGER NOT NULL'),
        Column('day', 'INTEGER NOT NULL'),
        Column('message_points', 'INTEGER', '0'),
        Column('voice_points', 'INTEGER', '0')
    ])
]
