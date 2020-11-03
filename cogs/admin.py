from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['purge'])
    @commands.cooldown(2, 600, type=commands.BucketType.default)
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount=10):
        """Removes a given amount of messages"""

        if amount <= 0:
            await ctx.send('"Was bist du für ein Idiot" ~ Johannes Stöhr (Betrag <= 0 ist unmöglich!)')
            return
        if amount > 20:
            await ctx.send("Zu großer Betrag!")
            return
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"**{amount}** Nachrichten wurden von **{ctx.author}** gelöscht.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def flatten(self, ctx):
        """Flattens all the previous texts in this channel into a wall of text"""

        async with ctx.channel.typing():
            lines = [m.clean_content for m in await ctx.channel.history(limit=None, oldest_first=True) if m.id != ctx.message.id]
            await self.bot.send_paginated(ctx, lines, linefmt="{} ")


def setup(bot):
    bot.add_cog(Admin(bot))
