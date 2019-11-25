import random
from discord.ext import commands
import sys

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
        ignored = (commands.CommandNotFound, commands.UserInputError)
        if isinstance(error, ignored):
            return

        # Hat der Aufrufer nicht genug Rechte?
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.message.add_reaction('\U0001F6AB')
            return

        # Standard handler: Einfach den Traceback ausgeben
        print('Fehler beim Ausführen des Befehls `{}`:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))