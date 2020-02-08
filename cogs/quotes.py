import random

from discord.ext import commands

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        with self.bot.db.get(ctx.guild.id) as db:
            quote = db.execute("SELECT content FROM quotes ORDER BY RANDOM() LIMIT 1").fetchall()

        if len(quote) == 0:
            await ctx.send("No quotes found!")
            return

        await ctx.send(quote[0][0])

    @quote.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, content):
        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO quotes (content) VALUES (?)", (content, ))

        await ctx.message.add_reaction('\U00002705')

def setup(bot):
    bot.add_cog(Quotes(bot))
