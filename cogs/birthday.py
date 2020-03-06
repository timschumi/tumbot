import datetime
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
    BIRTHDAY_CHANNEL_ID = 666653781366145028

    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60 * 60 * 24, self.congratulate)

    @commands.group(aliases=['birth', 'birthday', 'birthdate', 'geburtstag'])
    async def birthdays(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @birthdays.command()
    @commands.has_permissions(manage_messages=True)
    async def list(self, ctx, querry=""):
        """lists all birthdays (birthdays or userid are possible, jet optional querries)"""
        with self.bot.db.get(self.BIRTHDAY_CHANNEL_ID) as db:
            if len(querry) is 0:  # No Querry
                results = db.execute("SELECT userId, day, month FROM birthdays").fetchall()
                text = ""
                for result in results:
                    text += "User: {}\t->\t{}.{}.\n".format(result[0], result[1], result[2])
                await ctx.send(text)
            elif self.DATEPATTERN.match(querry) is not None:  # Birthday as Querry
                day, month = querry.strip(".").split(".")
                results = db.execute(
                    "SELECT userId, day, month FROM birthdays WHERE day = {} AND month = {}".format(day,
                                                                                                    month)).fetchall()
                if len(results) is 0:
                    await ctx.send("No Birthday at {}.{}.".format(day, month))
                    return
                text = ""
                for result in results:
                    text += "User: {}\t->\t{}.{}.\n".format(result[0], result[1], result[2])
                await ctx.send(text)
            else:  # Username as Querry
                results = db.execute(
                    "SELECT userId, day, month FROM birthdays WHERE userId LIKE '{}'".format(querry)).fetchall()
                print(results)
                if len(results) is 0:
                    await ctx.send("No UserID matches this request")
                    return
                await ctx.send("User: {}\t->\t{}.{}.\n".format(results[0][0], results[0][1], results[0][2]))

    @birthdays.command()
    async def add(self, ctx, birthdate):
        """adds a new bithday <DD.MM.> to the database, if possible"""
        if self.DATEPATTERN.match(birthdate) is None:
            await ctx.send("Usage: <!birthday add DD.MM.> (of course with a valid date)")
            return
        day, month = birthdate.strip(".").split(".")
        self.update_birthday(ctx.message.author.id, day, month)
        await ctx.message.add_reaction('\U00002705')

    def get_current_date(self) -> [int, int]:
        date = datetime.datetime.now()
        return date.day, date.month

    def update_birthday(self, user_id, day, month):
        with self.bot.db.get(self.BIRTHDAY_CHANNEL_ID) as db:
            db.execute("INSERT OR REPLACE INTO birthdays (userId, day, month) VALUES ('{}', {}, {})".format(
                user_id, day, month))

    async def congratulate(self):
        day, month = self.get_current_date()
        text = "Geburtstage am {}.{}.:".format(day, month)
        users = self.get_user_ids(day, month)
        if len(users) == 0:
            return
        for user in self.get_user_ids(day, month):
            text += ":tada: :fireworks: :partying_face: **Alles Gute zum Geburtstag**, <@!{}>" \
                    " :partying_face: :fireworks: :tada:\n".format(user)
        await self.bot.fetch_channel(self.BIRTHDAY_CHANNEL_ID).send(text)

    def get_user_ids(self, day: int, month: int) -> [int]:
        with self.bot.db.get(self.BIRTHDAY_CHANNEL_ID) as db:
            return db.execute(
                "SELECT userId FROM birthdays WHERE day = {} AND month = {}".format(day, month)).fetchall()


def setup(bot):
    bot.add_cog(Birthdays(bot))
