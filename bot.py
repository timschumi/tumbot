from discord.ext import commands
from discord.ext.commands import Bot as DBot
import sqlite3
from threading import Thread
import math
import time
import os
from schedule import Scheduler


class Bot(DBot):
    def __init__(self, db, **options):
        super().__init__(**options)
        self.db = db
        self.jobs = []
        self.run_jobs = True
        self.schedule = Scheduler()

    async def close(self):
        print("Shutting down!")
        self.run_jobs = False
        await super().close()
        self.db.close_all()

    async def on_ready(self):
        print(f"Bot is ready! Logged in as {self.user}.")
        Thread(target=self.job_runner).start()

    def job_runner(self):
        print("Starting background timer runner.")
        while self.run_jobs:
            try:
                self.schedule.run_pending()
            except Exception as e:
                print(f"{type(e).__name__}: {e}")
            time.sleep(10)

    def register_job_daily(self, daytime, f):
        print("Registering job {} to run every day at {}".format(f.__name__, daytime))
        self.schedule.every().day.at(daytime).do(f)

    def register_job(self, timer, f):
        print("Registering job {} to run every {} seconds".format(f.__name__, timer))
        self.schedule.every(timer).seconds.do(f)

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
