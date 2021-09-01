import datetime
import time
import re
from typing import Pattern, Optional
import asyncio

import discord
from discord.ext import commands, tasks

import basedbot


def _get_clean_name(ctx, userid):
    user = ctx.guild.get_member(userid)

    if user is None:
        return userid

    return user.display_name.replace('```', '').strip()


def _get_current_date() -> [int, int]:
    date = datetime.datetime.now()
    return date.day, date.month


class Birthdays(commands.Cog):
    DATEPATTERN: Pattern[str] = re.compile(r"(((0?[1-9])|([12][0-9]))\."  # 01.-29.
                                           r"((0?[1-9])|(1[0-2]))\.?)"  # all months have 1..29 days
                                           r"|"
                                           r"(30\.((0?[13-9])|(1[0-2]))\.?)"  # all months with 30 days
                                           r"|"
                                           r"(31\.((0?[13578])|(10)|(12))\.?)")  # all months with 31 days

    congratulate: tasks.Loop

    def __init__(self, bot):
        self.bot = bot
        self._var_channel = self.bot.conf.var('birthday.channel')
        self._var_role = self.bot.conf.var('birthday.role')
        self.congratulate.start()

    def cog_unload(self):
        self.congratulate.cancel()

    @commands.group(aliases=['birth', 'birthday', 'birthdate', 'geburtstag'], invoke_without_command=True)
    async def birthdays(self, ctx):
        """Manages birthdays"""

        await ctx.send_help(ctx.command)

    @birthdays.command()
    @basedbot.has_permissions("birthday.list")
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
            lines.append(f"{result[1]:02}.{result[2]:02}. -> {_get_clean_name(ctx, result[0])}")

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

    async def _clear_roles(self, guild):
        if not guild.me.guild_permissions.manage_roles:
            return

        with self.bot.db.get(guild.id) as db:
            users = db.execute("SELECT userId, role FROM birthdays WHERE role IS NOT NULL").fetchall()

        for e in users:
            member = guild.get_member(e[0])
            role = guild.get_role(e[1])

            if not member or not role:
                continue

            if role >= guild.me.top_role:
                continue

            await member.remove_roles(role)

            with self.bot.db.get(guild.id) as db:
                db.execute("UPDATE birthdays SET role = NULL WHERE userId = ?", (member.id,))

    def _get_birthday_role(self, guild):
        role = self._var_role.get(guild.id)

        if role is None:
            return None

        return guild.get_role(int(role))

    @tasks.loop(hours=24)
    async def congratulate(self):  # pylint: disable=function-redefined
        day, month = _get_current_date()
        for guild in self.bot.guilds:
            # Clear old birthday roles
            await self._clear_roles(guild)

            role = self._get_birthday_role(guild)

            text = f"Geburtstage am {day}.{month}.:"
            users = self.bot.db.get(guild.id).execute(
                "SELECT userId FROM birthdays WHERE day = ? AND month = ?", (day, month)).fetchall()
            if len(users) == 0:
                continue

            for e in users:
                member = guild.get_member(e[0])

                if not member:
                    continue

                text += f"\n    :tada: :fireworks: :partying_face: **Alles Gute zum Geburtstag**, {member.mention} " \
                        f":partying_face: :fireworks: :tada: "

                if role is not None and guild.me.guild_permissions.manage_roles and guild.me.top_role > role:
                    await member.add_roles(role)

                    with self.bot.db.get(guild.id) as db:
                        db.execute("UPDATE birthdays SET role = ? WHERE userId = ?", (role.id, member.id))

            channel = self._var_channel.get(guild.id)

            if channel is None:
                continue

            channel = await self.bot.fetch_channel(channel)

            await channel.send(text)

    @congratulate.before_loop
    async def congratulate_align(self):
        current = datetime.datetime.now()
        next_time = current + datetime.timedelta(days=1)  # Tomorrow
        next_time = datetime.datetime(next_time.year, next_time.month, next_time.day, 0, 0, 1, 0)  # Clip to 00:00:01

        # Convert into timestamps
        current = time.mktime(current.timetuple())
        next_time = time.mktime(next_time.timetuple())

        # Sleep until then
        await asyncio.sleep(next_time - current)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Delete user from database
        with self.bot.db.get(member.guild.id) as db:
            db.execute("DELETE FROM birthdays WHERE userId = ?", (member.id,))

        return


def setup(bot):
    bot.conf.register('birthday.channel',
                      conv=Optional[discord.TextChannel],
                      description="The channel where birthday messages are sent to.")
    bot.conf.register('birthday.role',
                      conv=Optional[discord.Role],
                      description="The role that birthday-people should get.")
    bot.perm.register('birthday.list',
                      base=True,
                      pretty_name="List birthdays")
    bot.add_cog(Birthdays(bot))
