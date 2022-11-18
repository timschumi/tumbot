import discord
from discord.ext import commands


class Physik(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """ Shows a custom join message for physicists """

        if not member.guild.id == 640285216245809183:
            return

        try:
            await member.send(
                f"Hey {member.mention}, Willkommen auf dem Physik Server! Schau am besten mal im Channel "
                "<#640285216245809186> vorbei, dort wird das wichtigste zum Server erklärt. "
                "Viel Spaß und eine exzellente Zeit!")
        except discord.errors.Forbidden:
            pass


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(Physik(bot))
