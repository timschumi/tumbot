from discord.ext import commands
import discord


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rr(self, ctx):
        pass

    @rr.command()
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, role: discord.Role):
        pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        pass


def setup(bot):
    bot.add_cog(ReactionRoles(bot))