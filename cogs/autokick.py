import discord
from discord.ext import commands


class Autokick(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blocks = []

    @commands.command()
    @commands.is_owner()
    async def add(self, user):
        self.blocks.append(int(user))

    @commands.command()
    @commands.is_owner()
    async def remove(self, user):
        self.blocks.remove(int(user))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if int(member.id) in self.blocks:
            await member.move_to(None)


def setup(bot):
    bot.add_cog(Autokick(bot))
