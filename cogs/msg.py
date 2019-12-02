from discord.ext import commands
import discord
import re


class MessageStore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def msg(self, ctx):
        """Allows for saving larger chunks of text using a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute("SELECT name, content FROM msg ORDER BY name ASC").fetchall()

        name_len = 0
        value_len = 0

        for row in result:
            name_len = max(name_len, len(str(row[0])))
            value_len = max(value_len, len(str(row[1])))

        text = ""

        for row in result:
            text += "| {} | {} |\n".format(str(row[0]).ljust(name_len), str(row[1]).ljust(value_len))

        await ctx.send("Available shorthands:\n```{}```".format(text))


    @msg.command()
    @commands.has_permissions(manage_channels=True)
    async def set(self, ctx, name, *, content):
        """Assigns content to a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            if len(db.execute("SELECT name, content FROM msg WHERE name = ?", (name.lower(),)).fetchall()) > 0:
                db.execute("UPDATE msg SET content = ? WHERE name = ?", (content, name.lower()))
            else:
                db.execute("INSERT INTO msg (name, content) VALUES (?, ?)", (name.lower(), content))

        await ctx.message.add_reaction('\U00002705')

    @commands.Cog.listener()
    async def on_message(self, message):
        search = re.search(r'#(\w+)', message.clean_content)
        if search is None:
            return

        key = search.group(1)

        with self.bot.db.get(message.guild.id) as db:
            result = db.execute("SELECT name, content FROM msg WHERE name = ?", (key.lower(),)).fetchall()

        if len(result) == 0:
            return

        await message.channel.send(result[0][1])


def setup(bot):
    bot.add_cog(MessageStore(bot))
