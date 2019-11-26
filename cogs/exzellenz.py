import random

from discord.ext import commands


class Exzellenz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def exzellenz(self, ctx):
        await ctx.send(random.choice(open("exzellenz.txt").readlines()))


def setup(bot):
    bot.add_cog(Exzellenz(bot))
