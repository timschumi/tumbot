import time

from discord.ext import commands, tasks


class DBotStats(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self._bot = bot
        self._running_commands = {}

    @commands.Cog.listener()
    async def on_message(self, _message):
        # pylint: disable=missing-function-docstring
        self._bot.statsd.incr("messages")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # pylint: disable=missing-function-docstring
        self._bot.statsd.incr("commands")

        translated_command_name = ctx.command.qualified_name.replace(" ", ".")
        self._bot.statsd.incr(f"command.{translated_command_name}")
        self._running_commands[ctx.message.id] = {
            "name": translated_command_name,
            "start": time.time(),
        }

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        # pylint: disable=missing-function-docstring
        self._bot.statsd.incr("command_completions")

        if ctx.message.id in self._running_commands:
            name = self._running_commands[ctx.message.id]["name"]
            start = self._running_commands[ctx.message.id]["start"]
            del self._running_commands[ctx.message.id]

            self._bot.statsd.timing(
                f"command.{name}", int((time.time() - start) * 1000)
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, _error):
        # pylint: disable=missing-function-docstring
        self._bot.statsd.incr("command_errors")

        if ctx.message.id in self._running_commands:
            name = self._running_commands[ctx.message.id]["name"]
            start = self._running_commands[ctx.message.id]["start"]
            del self._running_commands[ctx.message.id]

            self._bot.statsd.timing(
                f"command.{name}", int((time.time() - start) * 1000)
            )

    @commands.Cog.listener()
    async def on_ready(self):
        # pylint: disable=missing-function-docstring
        await self._bot.wait_until_ready()
        self.refresh_statistics.start()

    @tasks.loop(seconds=30)
    async def refresh_statistics(self):
        # pylint: disable=missing-function-docstring

        with self._bot.statsd.timer("refresh_statistics"):
            self._bot.statsd.gauge("guilds", len(self._bot.guilds))
            self._bot.statsd.gauge(
                "channels", sum([len(guild.channels) for guild in self._bot.guilds])
            )
            self._bot.statsd.gauge(
                "users", sum([len(guild.members) for guild in self._bot.guilds])
            )


async def setup(bot):
    # pylint: disable=missing-function-docstring

    if not hasattr(bot, "statsd"):
        return

    await bot.add_cog(DBotStats(bot))
