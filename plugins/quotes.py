import random
from discord.ext import commands

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx):
        await ctx.send(random.choice(open("quotes.txt").readlines()))

def setup(bot):
    bot.add_cog(Quotes(bot))