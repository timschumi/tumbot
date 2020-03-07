import os
import sqlite3
import pathlib
import glob
import re

class DbMgr:
    DB_PATTERN = 'db/{}.db'
    SCHEMA_PATTERN = 'db/schema_{}.sql'

    def __init__(self):
        self.db_handles = {}

    def open(self, guild):
        guild = str(guild)
        if guild in self.db_handles:
            return

        self.db_handles[guild] = self.create_new_conn(guild)
        self.upgrade_db(self.db_handles[guild])

    def get(self, guild):
        guild = str(guild)
        self.open(guild)

        return self.db_handles[guild]

    def get_all(self):
        for file in glob.glob("db/*.db"):
            search = re.search('/([0-9]+?)\.db', file)
            if search is None or search.group(1) is None:
                continue

            self.open(search.group(1))

        return list(self.db_handles.values())

    def create_new_conn(self, guild):
        connection = sqlite3.connect(self.DB_PATTERN.format(guild), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def upgrade_db(self, connection):
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]

        while(os.path.isfile(self.SCHEMA_PATTERN.format(user_version + 1))):
            with open(self.SCHEMA_PATTERN.format(user_version + 1)) as file:
                connection.executescript(file.read())
            user_version += 1

    def close(self, guild, commit=True):
        guild = str(guild)
        if guild in self.db_handles:
            if commit:
                self.db_handles[guild].commit()
            self.db_handles[guild].close()
            self.db_handles.pop(guild, None)

    def close_all(self):
        while len(self.db_handles) > 0:
            self.close(list(self.db_handles.keys())[0])
