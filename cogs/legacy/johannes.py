from discord.ext import commands


class Johannes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def johannes(self, ctx):
        """Sends a cute Animal"""
        await ctx.send("\U0001F427")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        lower = message.content.lower()

        # Reactions
        if "johannes" in lower or "stöhr" in lower:
            await message.add_reaction('\U0001F427')
        if "lmu" in lower:
            await message.add_reaction(":lmuo:668091545878003712")


def setup(bot):
    bot.add_cog(Johannes(bot))
