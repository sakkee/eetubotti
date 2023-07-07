from .database_model import Column
from typing import Any
from dataclasses import dataclass
import sqlite3

DATABASE_NAME: str = "data/kristitty.db"


@dataclass
class SqliteDatabase:
    """
    Handles all the communication with sqlite3. Only Database class should use this one.

    Examples:
        sqlite3db = SqliteDatabase()
        sqlite3db.insert('User', {'id': 23232, 'name': 'Ebin', ...})
        sqlite3db.save()
        values = sqlite3db.select('Messages', ['id', 'attachments'], {'user_id IN': [323232, 502323})

    Attributes:
        connection (sqlite3.Connection): sqlite3 database connection.
        cursor (sqlite3.Cursor): sqlite3 database cursor.
    """
    connection: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None

    def __post_init__(self):
        """Establish the database connection."""
        self.connection = sqlite3.connect(DATABASE_NAME)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def save(self):
        """Save the database."""
        self.connection.commit()

    def create_table(self, table_name: str, columns: list[Column]):
        """Create table.

        TODO: Allow update table if exists

        Args:
            table_name (str): name of the table.
            columns (list[Column]): list of Column objects that are to be inserted.
        """

        columns_and_types: str = ""
        for i in range(len(columns)):
            if i > 0:
                columns_and_types += ', '
            columns_and_types += columns[i].name + " " + columns[i].type
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_and_types});")
        self.save()

    def select(self, table_name: str, values: list[str] | str, where: dict[str, Any] | None = None,
               group_by: str | list[str] = None, order_by: str | list[str] = None,
               join_query: str = "", fetchall: bool = True, desc: bool = False) -> list:
        """Select query.

        Args:
            table_name (str): name of the table.
            values (list[str] | str): values that are selected from the table.
            where (dict[str, Any] | None): where query, usage: {'user_id IN': [12, 3], 'name =': 'eeddspeaks'} etc.
            group_by (str | list[str]): GROUP BY param. usage: group_by='year', or group_by=['year', 'month', 'day']
            order_by (str | list[str]): ORDER BY param. usage: order_by='year', or order_by=['year', 'month', 'day']
            join_query (str): SQL join query.
            fetchall (bool): if True, then fetchall() used, else fetchone() used.
            desc (bool): if True, add 'DESC' in the end of the query.

        Returns:
            Rows or row from the resultset.

        Examples:
            select('Messages', ['id', 'attachments'], {'user_id IN': [323232, 502323})
            select('Reactions', '*', order_by='message_id', desc=True)
            select('Messages', 'MAX(id)', fetchall=False)
            select('User', '*', join_query='JOIN UserStats ON User.id=UserStats.user_id LEFT JOIN ActivityDates ON ' +
                'User.id=ActivityDates.user_id')
            select('ActivityDates', ['year', 'month', 'day'], group_by=['year', 'month', 'day'],
                order_by=['year', 'month', 'day'])

        """
        query: str = f"SELECT {', '.join(values) if isinstance(values, list) else values} FROM {table_name} "
        extra_values: tuple = tuple()
        if where:
            query += 'WHERE '
            i: int = 0
            for key in where:
                if i > 0:
                    query += 'AND '
                i += 1
                if key.split(' ')[-1] == 'IN':
                    if not isinstance(where[key], list) and not isinstance(where[key], tuple):
                        where[key] = [where[key]]
                    query += f"{key} ({','.join(['?'] * len(where[key]))}) "
                else:
                    query += f"{key} ? "
                extra_values = extra_values + (where[key],) if not isinstance(where[key], list) and \
                                                               not isinstance(where[key], tuple) else tuple(where[key])
        query += f"{join_query}"
        if group_by:
            query += f"GROUP BY {', '.join(group_by) if isinstance(group_by, list) else group_by} "
        if order_by:
            query += f"ORDER BY {', '.join(order_by) if isinstance(order_by, list) else order_by} "
        query += f"{'DESC' if desc else ''};"

        self.cursor.execute(query, extra_values)
        return self.cursor.fetchall() if fetchall else self.cursor.fetchone()

    def insert(self, table_name: str, values: dict[str, Any]) -> bool:
        """Insert values into a table.

        Args:
            table_name (str): table name into which is inserted
            values (dict[str, Any]): values inserted. example: {'user_id': 5, 'year': 2023, 'points': 322}

        Returns:
            True if successful, False if failed

        Examples:
            insert('ActivityDates', {'user_id': 55, 'year': 2023, 'month': 5, 'day': 30, 'message_points': 69,
                'voice_points': 100})
            insert('User', {'id': 100, 'name': 'Test Guy', 'bot': 0, 'profile_filename': 'ad.jpg', 'identifier': 0})
        """
        try:
            self.cursor.execute(f"INSERT INTO {table_name} ({', '.join(values.keys())}) " +
                                f"VALUES ({','.join(['?'] * len(values))})", tuple(values.values()))
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error at inserting into {table_name} values {tuple(values.values())}: {e}")
        return False

    def update(self, table_name: str, set_values: dict[str, Any], where: dict[str, Any] = None):
        """Update rows in a table.

        Args:
            table_name (str): Table which is updated
            set_values (dict[str, Any]): new values. example: {'name': 'Asd', 'identifier': 50}
            where (dict[str, Any]): WHERE clause which rows to edit. example: {'id': 100}

        Examples:
            update('User', {'name': 'Test', 'profile_filename': 'asd.jpg'}, {'id': 100})
            update('Reactions', {'count': 100}, {'message_id': 1000, 'emoji_id': 1000})
        """
        query: str = f"UPDATE {table_name} SET "
        values: tuple = tuple()
        i: int = 0
        for key in set_values:
            query += f"{key}=?" if i == 0 else f", {key}=?"
            values += set_values[key],
            i += 1
        if where:
            query += " WHERE "
            i = 0
            for key in where:
                query += f"{key}=? " if i == 0 else f" AND {key}=? "
                values += where[key],
                i += 1

        self.cursor.execute(query, values)
