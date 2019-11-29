import random

from discord.ext import commands

class Randomstuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx):
        await ctx.send(random.choice(open("strings/quotes.txt").readlines()))

    @commands.command()
    async def exzellenz(self, ctx):
        await ctx.send(random.choice(
            random.choice(open("strings/excellence_noAutocompletion.txt").readlines()),
            self.excellence_formating(),
            self.trivial_formating()))

    def excellence_formating(self):
        return "%s ist sehr exzellent.", random.choice(
            open("strings/exzellenz_autocomplete.txt").readlines())

    def trivial_formating(self):
        return "%s ist trivial.", random.choice(open("strings/exzellenz_autocomplete.txt").readlines())


def setup(bot):
    bot.add_cog(Randomstuff(bot))
