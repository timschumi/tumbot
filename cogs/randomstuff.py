import random

from discord.ext import commands

class Randomstuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def randomstring(self, file):
        return random.choice(open(f"strings/{file}.txt").readlines())

    @commands.command()
    async def quote(self, ctx):
        await ctx.send(self.randomstring("quotes"))

    @commands.command()
    async def exzellenz(self, ctx):
        await ctx.send(random.choice(
            random.choice(self.randomstring("exzellence_noAutocompletion")),
            self.excellence_formating(),
            self.trivial_formating()))

    def excellence_formating(self):
        return "%s ist sehr exzellent.", self.randomstring("exzellenz_autocomplete"))

    def trivial_formating(self):
        return "%s ist trivial.", self.randomstring("exzellenz_autocomplete"))


def setup(bot):
    bot.add_cog(Randomstuff(bot))
