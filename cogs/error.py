import random
from discord.ext import commands
import sys
import traceback


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
        ignored = (commands.UserInputError)
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandNotFound):
            if "ban" in ctx.message.content:
                await ctx.message.add_reaction('\U0001F528')
            elif "kick" in ctx.message.content:
                await ctx.message.add_reaction('\U0001F97E')
            else:
                await ctx.message.add_reaction('\U0001F44F')
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send('Dieser Befehl kann nicht in DMs benutzt werden.')
            return

        # Hat der Aufrufer nicht genug Rechte?
        if isinstance(error, (commands.errors.MissingPermissions, commands.errors.NotOwner)):
            await ctx.message.add_reaction('\U0001F6AB')
            return

        # Standard handler: Einfach den Traceback ausgeben
        print('Fehler beim Ausführen des Befehls `{}`:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.message.add_reaction('\U0001F525')


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
