import io
import re
from urllib import request
from urllib.parse import urlparse, quote
from aiohttp import ClientTimeout, ClientSession
import discord
from discord.ext import commands

import basedbot


def _is_url(text):
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        return False


def _memegen_escape_text(text):
    # according to https://memegen.link/#special-characters
    escapes = [
        ("_", "__"),
        ("-", "--"),
        (" ", "_"),
        ("\n", "~n"),
        ("?", "~q"),
        ("&", "~a"),
        ("%", "~p"),
        ("#", "~h"),
        ("/", "~s"),
        ("\\", "~b"),
        ("<", "~l"),
        (">", "~g"),
        ('"', "''"),
    ]

    for char, escape in escapes:
        text = text.replace(char, escape)

    return text


class MessageStore(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @basedbot.has_permissions("msg.list")
    async def msg(self, ctx):
        """Allows for saving larger chunks of text using a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute(
                "SELECT name FROM msg WHERE name NOT LIKE '-%' ORDER BY name ASC"
            ).fetchall()

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
            current_msg = db.execute(
                "SELECT name, content, allow_memegen FROM msg WHERE name = ?",
                (name.lower(),),
            ).fetchall()
            if len(current_msg) > 0:
                # only allow memegen if the current message is still an URL
                keep_memegen = current_msg[0][2] and _is_url(content)
                db.execute(
                    "UPDATE msg SET content = ?, allow_memegen = ? WHERE name = ?",
                    (content, keep_memegen, name.lower()),
                )
            else:
                db.execute(
                    "INSERT INTO msg (name, content) VALUES (?, ?)",
                    (name.lower(), content),
                )

        await ctx.message.add_reaction("\U00002705")

    @msg.command()
    @basedbot.has_permissions("msg.set")
    async def memegen(self, ctx, action, shorthand):
        """Enable or disable meme generation for a shorthand"""

        if action not in ("enable", "disable"):
            await ctx.send("Invalid action. Valid actions are `enable` and `disable`")
            return

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute(
                "SELECT name, content FROM msg WHERE name = ? OR name = ?",
                (shorthand.lower(), "-" + shorthand.lower()),
            ).fetchall()

        if len(result) <= 0:
            await ctx.send("Shorthand not found.")
            return

        shorthand_text = result[0][1]
        if not _is_url(shorthand_text):
            await ctx.send(
                "Shorthand text must be a valid URL to manage meme generation."
            )
            return

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute(
                "UPDATE msg SET allow_memegen = ? WHERE name = ? OR name = ?",
                (action == "enable", shorthand.lower(), "-" + shorthand.lower()),
            )

        await ctx.message.add_reaction("\U00002705")

    @msg.command()
    @basedbot.has_permissions("msg.caption")
    async def caption(self, ctx, shorthand, *, caption):
        """Caption a meme"""

        with self.bot.db.get(ctx.guild.id) as db:
            result = db.execute(
                """SELECT name, content, allow_memegen FROM msg
                                   WHERE allow_memegen AND (name = ? OR name = ?)""",
                (shorthand.lower(), "-" + shorthand.lower()),
            ).fetchall()

        if len(result) <= 0:
            await ctx.send(
                "Shorthand not found or captioning has not been enabled for the chosen shorthand."
            )
            return

        shorthand_url = result[0][1]
        if not _is_url(shorthand_url):
            await ctx.send(
                "Shorthand text must be a valid URL to enable meme generation."
            )
            return

        safe_caption = await commands.clean_content(
            fix_channel_mentions=True, use_nicknames=True
        ).convert(ctx, caption)
        safe_caption = _memegen_escape_text(safe_caption)
        safe_caption = quote(safe_caption, safe="")
        quoted_url = quote(shorthand_url, safe="")

        file_url = f"https://api.memegen.link/images/custom/_/{safe_caption}.gif?background={quoted_url}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
        }

        async with ctx.typing(), \
                ClientSession(timeout=ClientTimeout(30), raise_for_status=True, headers=headers) as session, \
                session.get(file_url) as resp:
            # Restrict buffer size to 32MB
            file_data = b''
            async for chunk in resp.content.iter_chunked(512 * 1024):
                file_data += chunk
                if len(file_data) > 32 * 1024 * 1024:
                    raise ValueError('File too large')

            file = discord.File(io.BytesIO(file_data), filename="meme.gif")

            await ctx.send(file=file)

    @msg.command()
    @basedbot.has_permissions("msg.delete")
    async def delete(self, ctx, name):
        """Removes a shorthand"""

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute(
                "DELETE FROM msg WHERE name = ? OR name = ?",
                (name.lower(), "-" + name.lower()),
            )

        await ctx.message.add_reaction("\U00002705")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Checks messages for a shorthand and prints the matching value"""

        if message.author.bot:
            return

        search = re.search(r"\$(\w+)", message.clean_content)
        if search is None:
            return

        key = search.group(1)

        with self.bot.db.get(message.guild.id) as db:
            result = db.execute(
                "SELECT name, content FROM msg WHERE name = ? OR name = ?",
                (key.lower(), "-" + key.lower()),
            ).fetchall()

        if len(result) == 0:
            return

        await message.channel.send(result[0][1])


async def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.perm.register("msg.list", base=True, pretty_name="List shorthands (msg)")
    bot.perm.register("msg.caption", base=True, pretty_name="Caption images (msg)")
    bot.perm.register(
        "msg.set", base="administrator", pretty_name="Create/Update shorthands (msg)"
    )
    bot.perm.register(
        "msg.delete", base="administrator", pretty_name="Delete shorthands (msg)"
    )
    await bot.add_cog(MessageStore(bot))
