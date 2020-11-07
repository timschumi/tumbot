import datetime
import time
import re
from typing import Pattern
import asyncio
from discord.ext import commands, tasks


class Birthdays(commands.Cog):
    DATEPATTERN: Pattern[str] = re.compile(r"(((0?[1-9])|([12][0-9]))\."  # 01.-29.
                                           r"((0?[1-9])|(1[0-2]))\.?)"  # all months have 1..29 days
                                           r"|"
                                           r"(30\.((0?[13-9])|(1[0-2]))\.?)"  # all months with 30 days
                                           r"|"
                                           r"(31\.((0?[13578])|(10)|(12))\.?)")  # all months with 31 days

    def __init__(self, bot):
        self.bot = bot
        self._var_channel = self.bot.conf.register('birthday.channel',
                                                   description="The channel where birthday messages are sent to.")
        self.congratulate.start()

    def cog_unload(self):
        self.congratulate.cancel()

    @commands.group(aliases=['birth', 'birthday', 'birthdate', 'geburtstag'], invoke_without_command=True)
    async def birthdays(self, ctx):
        """Manages birthdays"""

        await ctx.send_help(ctx.command)

    @birthdays.command()
    async def list(self, ctx, query=""):
        """Lists all birthdays

        `query` is either a date or a user-id.
        """

        with self.bot.db.get(ctx.guild.id) as db:
            if len(query) == 0:  # No Query
                results = db.execute("SELECT userId, day, month FROM birthdays ORDER BY month, day").fetchall()
            elif self.DATEPATTERN.fullmatch(query) is not None:  # Birthday as Query
                day, month = query.strip(".").split(".")
                results = db.execute(
                    "SELECT userId, day, month FROM birthdays WHERE day = ? AND month = ? ORDER BY month, day",
                    (day, month)).fetchall()
            else:  # Username as Query
                results = db.execute(
                    "SELECT userId, day, month FROM birthdays WHERE userId LIKE ? ORDER BY month, day",
                    (query,)).fetchall()

        if len(results) == 0:
            await ctx.send("No entries found.")
            return

        lines = []

        for result in results:
            user = ctx.guild.get_member(result[0])
            lines.append(f"{result[1]:02}.{result[2]:02}. -> {user.display_name if user else result[0]}")

        await self.bot.send_paginated(ctx, lines, textfmt="```{}```")

    @birthdays.command()
    async def add(self, ctx, birthdate):
        """Adds a birthday (DD.MM.) for the calling user"""

        if self.DATEPATTERN.fullmatch(birthdate) is None:
            await ctx.send("Usage: <!birthday add DD.MM.> (of course with a valid date)")
            return
        day, month = birthdate.strip(".").split(".")

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT OR REPLACE INTO birthdays (userId, day, month) VALUES (?, ?, ?)",
                       (ctx.author.id, day, month))

        await ctx.message.add_reaction('\U00002705')

    def get_current_date(self) -> [int, int]:
        date = datetime.datetime.now()
        return date.day, date.month

    @tasks.loop(hours=24)
    async def congratulate(self):
        day, month = self.get_current_date()
        for guild in self.bot.guilds:
            text = f"Geburtstage am {day}.{month}.:"
            users = self.bot.db.get(guild.id).execute(
                "SELECT userId FROM birthdays WHERE day = ? AND month = ?", (day, month)).fetchall()
            if len(users) == 0:
                return
            for user in users:
                text += f"\n    :tada: :fireworks: :partying_face: **Alles Gute zum Geburtstag**, <@{user[0]}> " \
                        f":partying_face: :fireworks: :tada: "

            channel = self._var_channel.get(guild.id)

            if channel is None:
                return

            channel = await self.bot.fetch_channel(channel)

            await channel.send(text)

    @congratulate.before_loop
    async def congratulate_align(self):
        current = datetime.datetime.now()
        next_time = current + datetime.timedelta(days=1)  # Tomorrow
        next_time = datetime.datetime(next_time.year, next_time.month, next_time.day, 0, 1, 0, 0)  # Clip to 00:01

        # Convert into timestamps
        current = time.mktime(current.timetuple())
        next_time = time.mktime(next_time.timetuple())

        # Sleep until then
        await asyncio.sleep(next_time - current)


def setup(bot):
    bot.add_cog(Birthdays(bot))
