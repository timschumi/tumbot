import random
import datetime
import urllib
import json
import asyncio
import calendar
from discord.ext import commands


class Mensa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60 * 60 * 24, self.update_entries)

    def fillURL(self, location, year, week):
        return f"https://srehwald.github.io/eat-api/{location}/{year}/{week:02d}.json"

    @commands.group()
    async def mensa(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @mensa.command()
    @commands.has_permissions(manage_messages=True)
    async def setup(self, ctx, location):
        text = self.get_content(location, 0)
        if text is False:
            await ctx.send(
                "Speiseplan für Tag 1 konnte nicht abgerufen werden, vermutlich existiert die Location nicht.")
            return

        for day in range(1, 6):
            text = self.get_content(location, day)
            if text is False:
                continue

            message = await ctx.send(text)
            with self.bot.db.get(ctx.guild.id) as db:
                db.execute("INSERT INTO mensa (location, day, messageid, channelid) VALUES (?, ?, ?, ?)",
                           (location, day, message.id, ctx.channel.id))

    def update_entries(self):
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

    def get_content(self, location, day):
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

        text = "Speiseplan {}/{} ({}):\n".format(location, data["date"], calendar.day_abbr[day - 1])

        for i in data["dishes"]:
            text += "    **{}**".format(i["name"])

            if len(i["ingredients"]) != 0:
                text += " ({})".format(','.join(i["ingredients"]))

            text += "\n"

        return text


def setup(bot):
    bot.add_cog(Mensa(bot))
