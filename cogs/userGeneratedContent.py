import random

from discord.ext import commands


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx):
        await ctx.send(random.choice(open("UserGeneratedContent/quotes.txt").readlines()))


class Exzellenz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def exzellenz(self, ctx):
        await ctx.send(random.choice(
            random.choice(open("UserGeneratedContent/excellence_noAutocompletion.txt").readlines()),
            self.excellence_formating(),
            self.trivial_formating()))

    def excellence_formating(self):
        return "%s ist sehr exzellent.", random.choice(
            open("UserGeneratedContent/exzellenz_autocomplete.txt").readlines())

    def trivial_formating(self):
        return "%s ist trivial.", random.choice(open("UserGeneratedContent/exzellenz_autocomplete.txt").readlines())


def setup(bot):
    bot.add_cog(Quotes(bot))
    bot.add_cog(Exzellenz(bot))
