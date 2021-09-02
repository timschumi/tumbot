import random

import discord
from discord.ext import commands


def _randomstring(file):
    with open(f"strings/{file}.txt", encoding="utf-8") as f:
        return random.choice(f.read().splitlines())


def _excellentstring():
    return f"{_randomstring('exzellenz_trivial')} ist {random.choice(('trivial', 'sehr exzellent'))}."


class Randomstuff(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['exzellent', 'excellence'])
    async def exzellenz(self, ctx):
        """Shows you some excellent fact"""
        await ctx.send(random.choice((_randomstring("exzellenz_extra"), _excellentstring())))

    @commands.command(aliases=["penguinfact"])
    async def pinguinfakt(self, ctx):
        """Displays cool penguin facts"""
        await ctx.send(_randomstring("pinguinfakten"))

    @commands.command(aliases=['source', 'sauce'])
    async def repo(self, ctx):
        """Displays the repo link"""
        await ctx.send("<https://github.com/timschumi/tumbot>")

    @commands.command(aliases=['gettumbot'])
    async def botinvite(self, ctx):
        """Displays the invite link for the bot"""
        await ctx.send(f"https://discord.com/oauth2/authorize?&client_id={self.bot.user.id}&scope=bot&permissions=8")

    @commands.command(aliases=["mf"])
    async def metafrage(self, ctx):
        """Displays the meta-question-text"""

        metafrageembed = discord.Embed(
            title="Metafrage",
            description='Eine Metafrage ist eine Frage über eine Frage, wie beispielsweise "Darf ich etwas fragen?" '
                        'oder "Kennt sich jemand mit Computern aus?". In der Regel wird der Begriff Metafrage aber '
                        'verallgemeinert und damit alle Fragen bezeichnet, die keine direkte Frage zum Problem des '
                        'Hilfesuchenden sind. Der Hilfesuchende fragt also zunächst allgemein, ob jemand helfen kann. '
                        '[...] Meistens werden Metafragen ignoriert oder der Fragende wird rüde darauf hingewiesen, '
                        'dass ihm niemand bei seinem Problem helfen könne, ohne dies zu kennen. [...]'
                        '\n\n **Beispiele** \n Kennt sich jemand mit Streams aus? \n Kann mir jemand bei Gad helfen? \n'
                        'Darf ich euch was fragen? \n Kannst du mal herkommen?\n')
        metafrageembed.set_footer(text="Quelle: http://metafrage.de/")
        metafrageembed.set_thumbnail(
            url="https://cdn.pixabay.com/photo/2015/10/31/12/00/question-1015308_960_720.jpg")
        await ctx.send(embed=metafrageembed)


def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.add_cog(Randomstuff(bot))
