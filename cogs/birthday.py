import random
import datetime
import urllib
import json
import asyncio
import calendar
from discord.ext import commands


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60 * 60 * 24, self.congratulate)

    def fillURL(self, location, year, week):
        return f"https://srehwald.github.io/eat-api/{location}/{year}/{week:02d}.json"

    @commands.group()
    async def mensa(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @mensa.command()
    @commands.has_permissions(manage_messages=True)
    async def setup(self, ctx):
        text = self.get_content(0)
        if text is False:
            await ctx.send(
                "Geburtstags-Message existiert nicht, oder channel ist invalide")
            return

        for day in range(1, 6):
            text = self.get_content(location, day)
            if text is False:
                continue

            message = await ctx.send(text)
            with self.bot.db.get(ctx.guild.id) as db:
                db.execute("INSERT INTO mensa (location, day, messageid, channelid) VALUES (?, ?, ?, ?)",
                           (location, day, message.id, ctx.channel.id))

    def congratulate(self):
        for connection in self.bot.db.get_all():
            messages = connection.execute("SELECT location, day, messageid, channelid FROM mensa").fetchall()
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

    def discard_entry(self, messageid):
        for connection in self.bot.db.get_all():
            with connection:
                connection.execute("DELETE FROM mensa WHERE messageid = ?", (messageid,))

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
