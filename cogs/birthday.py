import datetime
import urllib
import json
import asyncio
import calendar
from discord.ext import commands
import re


class Birthdays(commands.Cog):
    re.compile("(((0[1-9])|(1[0-9])|(2[0-9])|(3[0-1]))"  # 01-31
               "\."
               "((01)|(03)|(05)|(07)|(08)|(10)|(12))"  # all morhts with 31 days
               "\.)"
               "|"
               "(((0[1-9])|(1[0-9])|(2[0-9])|(30))"  # 01-30
               "\."
               "((04)|(06)|(09)|(11))"  # all morhts with 30 days
               "\.)"
               "|"
               "(((0[1-9])|(1[0-9])|(2[0-9]))"  # 01-29
               "\."
               "02"  # febuary
               "\.)")

    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60 * 60 * 24, self.congratulate)

    @commands.group()
    async def birthdays(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @birthdays.command()
    @commands.has_permissions(manage_messages=True)
    async def setup(self, ctx):
        """
            accepts a json encoded string as input and adds it into the databasse
        :param ctx:
        """
        text = self.get_content(0)
        if text is False:
            await ctx.send(
                "Geburtstags-Message existiert nicht, oder channel ist invalide")
            return
        data = {}
        try:
            data = json.load(text)
        except:
            await ctx.send("Das ist keine JSON Datei")
            return
        for day in data.keys():
            for user in data[day]:
                self.updateBirthday(ctx, user, day)

    def updateBirthday(self, ctx, userId, birthdate):
        with self.bot.db.get(ctx.guild.id) as db:
            messages = db.execute(
                "SELECT userId FROM geburtstage WHERE userId='{}'".format(userId)).fetchall()
            if (len(messages) > 0):
                db.execute("UPDATE geburtstage SET birthday = '{}' WHERE userId = '{}'".format(birthdate, userId))
            else:
                db.execute("INSERT INTO birtdays (userId, birthday) VALUES ('{}', '{}')".format(userId, birthdate))

    @birthdays.command()
    async def add(self, ctx):
        text: str = self.get_content(0)
        if len(text) == 0:
            await ctx.send(
                "Geburtstags-Message existiert nicht, oder channel ist invalide")
            return

        if text

        message = await ctx.send(text)
        self.updateBirthday(ctx,, text)

        def getcurrentdayformated(self):
            return datetime.datetime.now().strftime("%d.%m.")

        def congratulate(self):
            for connection in self.bot.db.get_all():
                currentday = self.getcurrentdayformated()
                messages = connection.execute(
                    "SELECT userId FROM geburtstage WHERE birthday='{}'".format(currentdate)).fetchall()
                for i in messages:
                    asyncio.run_coroutine_threadsafe(self.update_entry(i[3], i[2], i[0], i[1]), self.bot.loop).result()

        async def update_entry(self, channelid, messageid, location, day):
            channel = self.bot.get_channel(channelid)

            if channel is None:
                self.discard_entry(messageid)

            message = await channel.fetch_message(messageid)

            if message is None:
                self.discard_entry(messageid)

            await message.edit(content=self.get_content(location, day))

        def get_content(self, day):
            now = datetime.datetime.now().isocalendar()
            year = now[0]
            week = now[1]
            weekday = now[2]

            if weekday > 5:
                week += 1

            try:
                with urllib.request.urlopen(self.fillURL(location, year, week)) as url:
                    if url.getcode() == 404:
                        return False

                    data = json.loads(url.read().decode())["days"][day - 1]
            except urllib.error.HTTPError:
                print(f"mensa: Got HTTPError while trying to access {self.fillURL(location, year, week)}")
                return False

            text = "Geburtstage am {}\n{}:\n".format(data["date"], calendar.day_abbr[day - 1])

            for i in data["birthdays"]:
                text += "**Alles Gute zum Geburtstag**, {}\n".format(i["name"])
            return text

    def setup(bot):
        bot.add_cog(Birthdays(bot))
