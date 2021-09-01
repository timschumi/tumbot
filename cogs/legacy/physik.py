from discord.ext import commands


class Physik(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.id == 640285216245809183:
            return

        await member.send(
            f"Hey {member.mention}, Willkommen auf dem Physik Server! Schau am besten mal im Channel "
            "<#640285216245809186> vorbei, dort wird das wichtigste zum Server erklärt. "
            "Viel Spaß und eine exzellente Zeit!")


def setup(bot):
    bot.add_cog(Physik(bot))
