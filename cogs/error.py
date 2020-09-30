import sys
import traceback

from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error, force=False):
        # Skippen, wenn wir einen lokalen Handler haben
        if hasattr(ctx.command, 'on_error') and not force:
            return

        error = getattr(error, 'original', error)

        # Manche Fehler einfach ignorieren
        ignored = (commands.UserInputError, commands.CommandNotFound)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Dieser Befehl kann nicht in DMs benutzt werden.')
            return

        # Hat der Aufrufer nicht genug Rechte?
        if isinstance(error, (commands.errors.MissingPermissions, commands.errors.NotOwner)):
            await ctx.message.add_reaction('\U0001F6AB')
            return

        # Standard handler: Einfach den Traceback ausgeben
        print(f'Fehler beim Ausführen des Befehls `{ctx.command}`:', file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.message.add_reaction('\U0001F525')


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
