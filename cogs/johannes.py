from discord.ext import commands


class Johannes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sendchannel = 711702521793740852

    def cheatsheet(self, subject):
        return f"Ja wir dürfen in der {subject}-Klausur ein Cheat-Sheet verwenden. Dieses ist ein doppelseitig " \
               f"handbeschriebenes Din-A4-Blatt!"

    @commands.command()
    async def johannes(self, ctx):
        await ctx.send("\U0001F427")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        lower = message.content.lower()

        if message.guild is None and not message.author.bot:
            channel = self.bot.get_channel(self.sendchannel)
            content = f'**{message.author} ({message.author.id})** sagt: "{message.content}"'
            if len(message.content) < 1800:
                await channel.send(content)
            else:
                await channel.send(content[0:1800])
                await channel.send(content[1801])
            return

        if (message.channel.id == self.sendchannel) and message.content[0:18].isnumeric():
            await message.add_reaction("✅")
            dmchannel = self.bot.get_user(int(message.content[0:18]))
            if dmchannel.dm_channel is None:
                await dmchannel.create_dm()
            await dmchannel.dm_channel.send(message.content[19:])
            return

        # Reactions
        if "johannes" in lower or "stöhr" in lower:
            await message.add_reaction('\U0001F427')
        if "lmu" in lower:
            await message.add_reaction(":lmuo:668091545878003712")
        # Messages
        if "gad" in lower and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("GAD"))
        elif "eist" in lower and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("EIST"))
        elif "linalg" in lower and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("LINALG"))
        elif ("dwt" in lower or "wahrscheinlichkeitstheorie" in lower) and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("DWT"))
        elif "theo" in lower and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("THEO"))
        elif ("grnvs" in lower or "rechnernetz" in lower) and ("cheat" in lower or "sheet" in lower):
            await message.channel.send(self.cheatsheet("GRNVS"))


def setup(bot):
    bot.add_cog(Johannes(bot))
