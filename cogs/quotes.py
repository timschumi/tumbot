from discord.ext import commands


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, search=""):
        """Displays one random quote"""

        search = "%" + search + "%"

        with self.bot.db.get(ctx.guild.id) as db:
            quote = db.execute("SELECT content FROM quotes WHERE LOWER(content) LIKE ? ORDER BY RANDOM() LIMIT 1",
                               (search,)).fetchall()

        if len(quote) == 0:
            await ctx.send("No quotes found!")
            return

        await ctx.send(quote[0][0])

    @quote.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, content):
        """Adds a quote"""

        content = await commands.clean_content(fix_channel_mentions=True).convert(ctx, content)

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO quotes (content) VALUES (?)", (content,))

        await ctx.message.add_reaction('\U00002705')

    @quote.command()
    @commands.has_permissions(manage_channels=True)
    async def list(self, ctx, search=""):
        """Lists all the quotes"""

        search = f"%{search}%"

        with self.bot.db.get(ctx.guild.id) as db:
            quotes = db.execute("SELECT content FROM quotes WHERE LOWER(content) LIKE ? ORDER BY content",
                                (search,)).fetchall()

        if len(quotes) == 0:
            await ctx.send("No quotes found.")
            return

        text = ""
        for quote in quotes:
            line = f"{quote[0]}\n\n"
            # [single lines can not ever be > 1994 chars]

            # -6: Account for code block
            if len(text) + len(line) >= 2000 - 6:
                await ctx.send(text)
                text = ""
            text += line
        if len(text) > 0:
            await ctx.send(text)

    @quote.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, search):
        """Removes a quote"""

        search = "%" + search + "%"

        with self.bot.db.get(ctx.guild.id) as db:
            resulting_ids = db.execute("SELECT rowid FROM quotes WHERE LOWER(content) LIKE ? ORDER BY content",
                                       (search,)).fetchall()

        if len(resulting_ids) > 1:
            await ctx.send("Only one quote at a time can be removed, to prevent admin-abuse.")
            return
        if len(resulting_ids) == 0:
            await ctx.send("No quotes could be found. What does not exist cant be deleted. \U0001F427")
            return

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("DELETE FROM quotes WHERE rowid = (?)", (resulting_ids[0][0],))

        await ctx.message.add_reaction('\U00002705')


def setup(bot):
    bot.add_cog(Quotes(bot))
