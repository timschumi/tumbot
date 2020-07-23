import random

from discord.ext import commands


class Randomstuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def randomstring(self, file):
        return random.choice(open(f"strings/{file}.txt").read().splitlines())

    @commands.command(aliases=['exzellent'])
    async def exzellenz(self, ctx):
        await ctx.send(random.choice((self.randomstring("exzellenz_extra"), self.excellentstring())))

    def excellentstring(self):
        return f"{self.randomstring('exzellenz_trivial')} ist {random.choice(('trivial', 'sehr exzellent'))}."

    @commands.command()
    async def pinguinfakt(self, ctx):
        await ctx.send(self.randomstring("pinguinfakten"))
    
    @commands.command(aliases=['source', 'sauce'])    
    async def repo(self, ctx):
        await ctx.send("<https://github.com/timschumi/TUMbot>")


def setup(bot):
    bot.add_cog(Randomstuff(bot))
