import discord
from discord.ext import commands


class Autokick(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.blocks = []

    @commands.command()
    @commands.is_owner()
    async def add(self, ctx, user: discord.Member):
        """Blocks a user from joining a new voice-chat"""

        self.blocks.append(user.id)

    @commands.command()
    @commands.is_owner()
    async def remove(self, ctx, user: discord.Member):
        """Removes a previously set voice-chat block"""

        self.blocks.remove(user.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id in self.blocks:
            await member.move_to(None)


def setup(bot):
    bot.add_cog(Autokick(bot))
