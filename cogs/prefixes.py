import json

from discord.ext import commands


class Prefixes(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def newprefix(self, ctx, prefix):
        await ctx.channel.purge(limit=1)
        with open('./data/prefixes.json', 'r') as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open('./data/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

        await ctx.send(f'Prefix zu:** {prefix} **geändert', delete_after=bp.deltime)

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = str(message.content).lower()
        if "prefix" in msg and not message.author.bot and "bot" in msg:
            channel = message.channel
            with open('./data/prefixes.json', 'r') as f:
                prefixes = json.load(f)
            await channel.send("Dieser Server hat den Prefix: **" + prefixes[str(message.guild.id)] + "**")

    @commands.Cog.listener()
    async def on_guild_join(self, message):
        guild = message.guild
        with open('./data/prefixes.json', 'r') as f:
            prefixes = json.load(f)

        prefixes[str(guild.id)] = '!'

        with open('./data/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)


def setup(client):
    client.add_cog(Prefixes(client))
