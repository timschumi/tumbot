import json

from discord.ext import commands

class Prefixes(commands.Cog):

    def __init__(self, client):
        self.client = client

    def get_prefix(self, guild):
        return self.client.dbconf_get(guild, 'prefix', '!')

    def set_prefix(self, guild, prefix):
        return self.client.dbconf_set(guild, 'prefix', prefix)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def newprefix(self, ctx, prefix):
        await ctx.channel.purge(limit=1)

        self.set_prefix(ctx.guild.id, prefix)

        await ctx.send(f'Prefix zu:** {prefix} **geändert', delete_after=bp.deltime)

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = str(message.content).lower()
        if "prefix" in msg and not message.author.bot and "bot" in msg:
            await message.channel.send("Dieser Server hat den Prefix: **" + self.get_prefix(ctx.guild.id) + "**")


def setup(client):
    client.add_cog(Prefixes(client))
