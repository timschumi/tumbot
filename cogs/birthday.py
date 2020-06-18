import datetime
import re
from typing import Pattern
import asyncio
import discord
from discord.ext import commands


class Birthdays(commands.Cog):
    DATEPATTERN: Pattern[str] = re.compile(r"(((0?[1-9])|([12][0-9]))\."  # 01.-29.
                                           r"((0?[1-9])|(1[0-2]))\.?)"  # all months have 1..29 days
                                           r"|"
                                           r"(30\.((0?[13-9])|(1[0-2]))\.?)"  # all months with 30 days
                                           r"|"
                                           r"(31\.((0?[13578])|(10)|(12))\.?)")  # all months with 31 days

    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job_daily("00:01", self.congratulate_all)

    @commands.group(aliases=['birth', 'birthday', 'birthdate', 'geburtstag'], invoke_without_command=True)
    async def birthdays(self, ctx):
        """Manages birthdays"""

        pass

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

        text = ""
        for result in results:
            user = ctx.guild.get_member(result[0])

            if user is not None:
                line = f"{result[1]:02}.{result[2]:02}. -> {user.display_name}\n"
                # -6: Account for code block
                if len(text) + len(line) >= 2000 - 6:
                    await ctx.send(f"```{text}```")
                    text = ""
                text += line
            else:
                await ctx.send(f"**UserId {result[0]} produced an error!**")
        # text should not be empty, but if somehow the ctx.guild.get_member(r) would return None i.e. if the
        # Database somehow has a fault, this could happen
        if len(text) > 0:
            await ctx.send(f"```{text}```")

    @birthdays.command()
    async def add(self, ctx, birthdate):
        """Adds a birthday (DD.MM.) for the calling user"""

        if self.DATEPATTERN.fullmatch(birthdate) is None:
            await ctx.send("Usage: <!birthday add DD.MM.> (of course with a valid date)")
            return
        day, month = birthdate.strip(".").split(".")

        # Update message channel if needed
        if self.bot.dbconf_get(ctx.guild.id, "birthday_channel") is None:
            self.bot.dbconf_set(ctx.guild.id, "birthday_channel", ctx.channel.id)

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT OR REPLACE INTO birthdays (userId, day, month) VALUES (?, ?, ?)",
                       (ctx.author.id, day, month))

        await ctx.message.add_reaction('\U00002705')

    @birthdays.command()
    @commands.has_permissions(manage_messages=True)
    async def channel(self, ctx, target: discord.TextChannel = None):
        """Sets a new output channel for birthday messages"""

        if target is not None:
            self.bot.dbconf_set(ctx.guild.id, "birthday_channel", target.id)
            await ctx.message.add_reaction('\U00002705')
            return

        channel_id = self.bot.dbconf_get(ctx.guild.id, "birthday_channel")

        if channel_id is None:
            await ctx.send("No channel set!")
            return

        channel = await self.bot.fetch_channel(channel_id)

        if channel is None:
            await ctx.send(f"Could not resolve saved channel ({channel_id}).")
            return

        await ctx.send(f"Current birthday channel: {channel.mention}")
        return

    def get_current_date(self) -> [int, int]:
        date = datetime.datetime.now()
        return date.day, date.month

    def congratulate_all(self):
        day, month = self.get_current_date()
        for conn in self.bot.db.get_all():
            asyncio.run_coroutine_threadsafe(self.congratulate(conn, day, month), self.bot.loop).result()

    async def congratulate(self, conn, day, month):
        text = f"Geburtstage am {day}.{month}.:"
        users = conn.execute(
            "SELECT userId FROM birthdays WHERE day = ? AND month = ?", (day, month)).fetchall()
        if len(users) == 0:
            return
        for user in users:
            text += f"\n    :tada: :fireworks: :partying_face: **Alles Gute zum Geburtstag**, <@{user[0]}> " \
                    f":partying_face: :fireworks: :tada: "

        # This is essentially what dbconf_get does, but we don't have the guild ID :/
        channel = conn.execute("SELECT value FROM config WHERE name = 'birthday_channel'").fetchall()

        # If channel isn't set
        if len(channel) < 1:
            return

        channel = await self.bot.fetch_channel(channel[0][0])

        await channel.send(text)


def setup(bot):
    bot.add_cog(Birthdays(bot))
