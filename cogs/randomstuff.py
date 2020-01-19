import random

from discord.ext import commands


class Randomstuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def randomstring(self, file):
        return random.choice(open(f"strings/{file}.txt").read().splitlines())

    @commands.command()
    async def quote(self, ctx):
        await ctx.send(self.randomstring("quotes"))

    @commands.command(aliases=['exzellent'])
    async def exzellenz(self, ctx):
        await ctx.send(random.choice((self.randomstring("exzellenz_extra"), self.excellentstring())))

    def excellentstring(self):
        return "{} ist {}.".format(self.randomstring("exzellenz_trivial"), random.choice(("trivial", "sehr exzellent")))

    @commands.command()
    async def pinguinfakt(self, ctx):
        await ctx.send(self.randomstring("pinguinfakten"))

def setup(bot):
    bot.add_cog(Randomstuff(bot))
