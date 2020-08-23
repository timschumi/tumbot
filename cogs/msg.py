from discord.ext import commands
import discord
import re


class MessageStore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
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
        metafrageembed.set_thumbnail(url="https://cdn.pixabay.com/photo/2015/10/31/12/00/question-1015308_960_720.jpg")
        await ctx.send(embed=metafrageembed)

    @commands.group(invoke_without_command=True)
    async def msg(self, ctx):
        """Allows for saving larger chunks of text using a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute("SELECT name FROM msg WHERE name NOT LIKE '-%' ORDER BY name ASC").fetchall()

        if len(result) <= 0:
            await ctx.send("No shorthands available.")
            return

        text = ""

        for row in result:
            text += f"`{row[0]}`\n"

        await ctx.send(f"Available shorthands:\n{text}")

    @msg.command()
    @commands.has_permissions(manage_channels=True)
    async def set(self, ctx, name, *, content):
        """Assigns content to a shorthand"""

        content = await commands.clean_content().convert(ctx, content)

        with self.bot.db.get(ctx.guild.id) as db:
            if len(db.execute("SELECT name, content FROM msg WHERE name = ?", (name.lower(),)).fetchall()) > 0:
                db.execute("UPDATE msg SET content = ? WHERE name = ?", (content, name.lower()))
            else:
                db.execute("INSERT INTO msg (name, content) VALUES (?, ?)", (name.lower(), content))

        await ctx.message.add_reaction('\U00002705')

    @msg.command()
    @commands.has_permissions(manage_channels=True)
    async def delete(self, ctx, name):
        """Removes a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("DELETE FROM msg WHERE name = ? OR name = ?", (name.lower(), "-" + name.lower()))

        await ctx.message.add_reaction('\U00002705')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        search = re.search(r'\$(\w+)', message.clean_content)
        if search is None:
            return

        key = search.group(1)

        with self.bot.db.get(message.guild.id) as db:
            result = db.execute("SELECT name, content FROM msg WHERE name = ? OR name = ?",
                                (key.lower(), "-" + key.lower())).fetchall()

        if len(result) == 0:
            return

        await message.channel.send(result[0][1])


def setup(bot):
    bot.add_cog(MessageStore(bot))
