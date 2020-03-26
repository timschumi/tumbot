import discord
from discord.ext import commands


class Autokick(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blocks = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add(self, user):
        try:
            self.blocks.append(int(user))
        except Exception:
            pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, user):
        try:
            self.blocks.remove(int(user))
        except Exception:
            pass

    @commands.Cog.listener
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.blocks:
            await member.move_to(None)


def setup(bot):
    bot.add_cog(Autokick(bot))
