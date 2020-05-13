from discord.ext import commands


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, search=""):
        """Lists one quote that use an optional query"""

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
        """adds a quote"""

        content = await commands.clean_content(fix_channel_mentions=True).convert(ctx, content)

        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO quotes (content) VALUES (?)", (content,))

        await ctx.message.add_reaction('\U00002705')

    @quote.command()
    @commands.has_permissions(manage_channels=True)
    async def list(self, ctx, search=""):
        """Lists all quotes that use an optional query"""

        # if else for performance reasons, as SQLite does not perform query optimisation
        if len(search) > 0:
            search = "%" + search + "%"

            with self.bot.db.get(ctx.guild.id) as db:
                quotes = db.execute("SELECT content FROM quotes WHERE LOWER(content) LIKE ? ORDER BY content",
                                    (search,)).fetchall()
        else:
            with self.bot.db.get(ctx.guild.id) as db:
                quotes = db.execute("SELECT content FROM quotes ORDER BY content",
                                    (search,)).fetchall()

        if len(quotes) == 0:
            await ctx.send("No quotes found.")
            return

        text = ""
        for quote in quotes:
            line = "{}\n".format(quote[0])
            # lines can never be >= 2000-6, due to being inputted by the user in discord as well using the same
            # message length mechanism

            # -6: Account for code block
            if len(text) + len(line) >= 2000 - 6:
                await ctx.send("```{}```".format(text))
                text = ""
            text += line
        if len(text) > 0:
            await ctx.send("```{}```".format(text))


def setup(bot):
    bot.add_cog(Quotes(bot))
