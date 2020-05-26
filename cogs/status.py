import asyncio
import urllib

from discord.ext import commands


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.register_job(60, self.status_update)

    @commands.group()
    async def status(self, ctx):
        """Manages website status checks"""

        if ctx.invoked_subcommand is None:
            await ctx.send("Ungültiger command!")

    @status.command()
    @commands.has_permissions(manage_channels=True)
    async def setup(self, ctx, name, url):
        """Adds a new website to the list of status checks"""

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO status (name, url, channelid, status) VALUES (?, ?, ?, ?)",
                       (name, url, ctx.channel.id, self.get_code(url)))

        await ctx.message.add_reaction('\U00002705')

    def get_code(self, url):
        try:
            with urllib.request.urlopen(url) as url:
                return url.getcode()
        except urllib.error.HTTPError as err:
            return err.code

    def status_update(self):
        for connection in self.bot.db.get_all():
            entries = connection.execute("SELECT name, url, channelid, status FROM status").fetchall()
            for i in entries:
                current_code = self.get_code(i[1])
                if i[3] == current_code:
                    continue

                with connection:
                    connection.execute("UPDATE status SET status = ? WHERE url = ?", (current_code, i[1]))

                channel = self.bot.get_channel(i[2])

                asyncio.run_coroutine_threadsafe(
                    channel.send(f"{i[0]} (<{i[1]}>) just changed status: `{i[3]} -> {current_code}`"),
                    self.bot.loop).result()


def setup(bot):
    bot.add_cog(Status(bot))
