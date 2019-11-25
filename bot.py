from discord.ext.commands import Bot as DBot
import sqlite3
from threading import Thread
import math
import time
import os

class Bot(DBot):
    def __init__(self, db, **options):
        super().__init__(**options)
        self.db = db
        self.jobs = {}
        self.run_jobs = True

    async def close(self):
        print("Shutting down!")
        self.run_jobs = False
        await super().close()
        self.db.close_all()

    def run(self, token):
        self.job_runner = Thread(target=self.job_runner_func)
        self.job_runner.start()

        super().run(token)

    def job_runner_func(self):
        while self.run_jobs:
            for timer in self.jobs.keys():
                if math.floor(time.time()) % timer == 0:
                    for job in self.jobs[timer]:
                        try:
                            job()
                        except Exception as e:
                            print("Error: {}".format(e))
            time.sleep(1)

    def register_job(self, timer, f):
        print("Registering job {} to run every {} seconds".format(f.__name__, timer))
        self.jobs.setdefault(timer, []).append(f)

    def dbconf_get(self, guild_id, name, default=None):
        result = self.db.get(guild_id).execute("SELECT value FROM config WHERE name = ?", (name,)).fetchall()

        if len(result) < 1:
            return default

        return str(result[0][0])

    def dbconf_set(self, guild_id, name, value):
        saved = self.dbconf_get(guild_id, name)

        if saved == None:
            with self.db.get(guild_id) as db:
                db.execute("INSERT INTO config(name, value) VALUES(?, ?)", (name, value))
            return

        if str(saved) == str(value):
            return

        with self.db.get(guild_id) as db:
            db.execute("UPDATE config SET value = ? WHERE name = ?", (value, name))
