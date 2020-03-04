import datetime
import json
import re
from typing import Pattern

from discord.ext import commands


class Birthdays(commands.Cog):
    DATEPATTERN: Pattern[str] = re.compile(r'(((0[1-9])|(1[0-9])|(2[0-9])|(3[0-1]))\.'  # 01.-31.
                                           r"((01)|(03)|(05)|(07)|(08)|(10)|(12))\.)"  # all months with 31 days
                                           r"|"
                                           r"(((0[1-9])|(1[0-9])|(2[0-9])|(30))\."  # 01.-30.
                                           r"((04)|(06)|(09)|(11))\.)"  # all months with 30 days
                                           r"|"
                                           r"(((0[1-9])|(1[0-9])|(2[0-9]))\."  # 01.-29.
                                           r"02\.)")  # february

    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60 * 60 * 24, self.congratulate)

    @commands.group(aliases=['birth', 'birthday', 'birthdate', 'geburtstag'])
    async def birthdays(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @birthdays.command()
    @commands.has_permissions(manage_messages=True)
    async def setup(self, ctx, json_text):
        """accepts a json encoded string as input and adds it into the database
        Encoding: Birthday[DD.MM.] -> Discord-ID"""

        try:
            data: dict = json.loads(json_text)
        except:
            await ctx.send("Das ist kein valider JSON-String")
            return
        for date in data.keys():
            if self.DATEPATTERN.match(date) is None:
                await ctx.send(
                    "Geburtstag muss <DD.MM.> entsprechen")
                return
            day, month = date.strip(".").split(".")
            for user in data[date]:
                self.update_birthday(ctx, user, day, month)

    @birthdays.command()
    async def add(self, ctx, birthdate):
        """adds a new bithday <DD.MM.> to the database, if possible"""
        if self.DATEPATTERN.match(birthdate) is None:
            await ctx.send("Usage: <!birthday add DD.MM.> (of course with a valid date)")
            return
        day, month = birthdate.strip(".").split(".")
        self.update_birthday(ctx, ctx.message.author.id, day, month)

    def get_current_date(self) -> [int, int]:
        date = datetime.datetime.now()
        return date.day, date.month

    def update_birthday(self, ctx, user_id, day, month):
        with self.bot.db.get(ctx.guild.id) as db:
            db.execute(
                "INSERT OR REPLACE INTO birthdays (userId, date, month) VALUES ({}, {}, {})".format(
                    user_id, day, month))

    async def congratulate(self, ctx):
        day, month = self.get_current_date()
        text = "" \
               "".format(day, month)
        for user in self.get_user_ids(ctx, day, month):
            text += ":tada: :fireworks: :partying_face: **Alles Gute zum Geburtstag**, " \
                    " :partying_face: " \
                    ":fireworks: :tada:\n".format(user)
        await ctx.send(text)

    def get_user_ids(self, ctx, day: int, month: int) -> [int]:
        with self.bot.db.get(ctx.guild.id) as db:
            return db.execute(
                "SELECT userId FROM birthdays WHERE date = {} AND month = {}".format(day, month)).fetchall()


def setup(bot):
    bot.add_cog(Birthdays(bot))
