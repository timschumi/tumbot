import re
from urllib.parse import urlparse, quote

from discord.ext import commands

import basedbot


class MessageStore(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @basedbot.has_permissions("msg.list")
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
    @basedbot.has_permissions("msg.set")
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
    @basedbot.has_permissions("msg.delete")
    async def delete(self, ctx, name):
        """Removes a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("DELETE FROM msg WHERE name = ? OR name = ?", (name.lower(), "-" + name.lower()))

        await ctx.message.add_reaction('\U00002705')

    @commands.Cog.listener()
    async def on_message(self, message):
        """ Checks messages for a shorthand and prints the matching value """

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

        text = result[0][1]

        def isUrl(url):
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except:
                return False

        rest = message.clean_content[search.end():].strip()
        if isUrl(text) and len(rest) > 0:
            rest = re.sub(r'\s+', '_', rest)
            rest = quote(rest, safe='/')
            text = f"https://api.memegen.link/images/custom/_/{rest}.gif?background={text}"

        await message.channel.send(text)


def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.perm.register('msg.list',
                      base=True,
                      pretty_name="List shorthands (msg)")
    bot.perm.register('msg.set',
                      base="administrator",
                      pretty_name="Create/Update shorthands (msg)")
    bot.perm.register('msg.delete',
                      base="administrator",
                      pretty_name="Delete shorthands (msg)")
    bot.add_cog(MessageStore(bot))
