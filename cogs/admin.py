from discord.ext import commands

from basedbot import ConfigAccessLevel


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._var_clear_max = self.bot.conf.var('admin.clear_max')

    @commands.command(aliases=['purge'])
    @commands.cooldown(2, 600, type=commands.BucketType.default)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=10):
        """Removes a given amount of messages"""

        if amount <= 0:
            await ctx.send('"Was bist du für ein Idiot" ~ Johannes Stöhr (Betrag <= 0 ist unmöglich!)')
            return

        clear_max = int(self._var_clear_max.get(ctx.guild.id))

        if clear_max != 0 and amount > clear_max:
            await ctx.send(f"You can't remove more than {clear_max} messages!")
            return

        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"**{amount}** Nachrichten wurden von **{ctx.author}** gelöscht.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def flatten(self, ctx):
        """Flattens all the previous texts in this channel into a wall of text"""

        async with ctx.channel.typing():
            messages = await ctx.channel.history(limit=None, oldest_first=True).flatten()
            lines = [m.clean_content for m in messages if m.id != ctx.message.id]
            await self.bot.send_paginated(ctx, lines, linefmt="{} ")


def setup(bot):
    bot.conf.register('admin.clear_max',
                      default="0",
                      conv=int,
                      access=ConfigAccessLevel.OWNER,
                      description="How many messages the clear command can remove (0 = infinite).")
    bot.add_cog(Admin(bot))
