from discord.ext import commands
import discord


class Johannes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if "johannes" not in message.content.lower() and "stöhr" not in message.content.lower():
            return

        await message.add_reaction('\U0001F427')

def setup(bot):
    bot.add_cog(Johannes(bot))
