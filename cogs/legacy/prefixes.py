from discord.ext import commands


class Prefixes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_prefix(self, guild):
        return self.bot.conf.get(guild, 'prefix', '!')

    def set_prefix(self, guild, prefix):
        return self.bot.conf.set(guild, 'prefix', prefix)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def newprefix(self, ctx, prefix):
        await ctx.channel.purge(limit=1)

        self.set_prefix(ctx.guild.id, prefix)

        await ctx.send(f'Prefix zu:** {prefix} **geändert', delete_after=5)

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = str(message.content).lower()
        if "prefix" in msg and not message.author.bot and "bot" in msg:
            await message.channel.send(f"Dieser Server hat den Prefix: **{self.get_prefix(message.guild.id)}**")


def setup(bot):
    bot.add_cog(Prefixes(bot))
