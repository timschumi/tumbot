from discord.ext import commands
import discord


class Johannes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if "johannes" in message.content.lower() or "stöhr" in message.content.lower():
            await message.add_reaction('\U0001F427')
        elif "eidi" in message.content.lower() and ("cheat" in message.content.lower() or
                                                    "sheet" in message.content.lower()):
            await message.channel.send("Ja wir dürfen in der Eidi-Klausur ein Cheat-Sheet verwenden. "
                                       "Dieses ist ein doppelseitig handbeschriebenes Din-A4-Blatt!")
        elif "lmu" in message.content.lower():
            await message.add_reaction(":lmuo:668091545878003712")


def setup(bot):
    bot.add_cog(Johannes(bot))
