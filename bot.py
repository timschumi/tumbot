from discord.ext.commands import Bot as DBot
import sqlite3
from threading import Thread
import math
import time

class Bot(DBot):
    def __init__(self, **options):
        super().__init__(**options)
        self.db = self.create_dbconn()
        self.jobs = {}
        self.run_jobs = True

    def create_dbconn(self):
        connection = sqlite3.connect('database.db', check_same_thread=False)
        connection.row_factory = sqlite3.Row

        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if user_version < 2: # Wurde die Datenbank initialisiert?
            with open('database.sql') as file:
                connection.executescript(file.read())

        return connection

    def close_dbconn(self):
        self.db.commit()
        self.db.close()
        self.db = None

    async def close(self):
        print("Shutting down!")
        self.run_jobs = False
        await super().close()
        self.close_dbconn()

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