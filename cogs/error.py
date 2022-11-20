import logging
import sys

from discord.ext import commands


class ErrorHandler(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error, force=False):
        """Common handlers for command errors"""

        # Skippen, wenn wir einen lokalen Handler haben
        if hasattr(ctx.command, "on_error") and not force:
            return

        error = getattr(error, "original", error)

        # Manche Fehler einfach ignorieren
        ignored = (commands.UserInputError, commands.CommandNotFound)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("Dieser Befehl kann nicht in DMs benutzt werden.")
            return

        # Hat der Aufrufer nicht genug Rechte?
        perm_errors = (
            commands.errors.MissingPermissions,
            commands.errors.NotOwner,
            commands.errors.CheckFailure,
        )
        if isinstance(error, perm_errors):
            await ctx.message.add_reaction("\U0001F6AB")
            return

        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(error)
            return

        logging.error("Error while running command '%s'", ctx.command, exc_info=error)
        await ctx.message.add_reaction("\U0001F525")


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(ErrorHandler(bot))
