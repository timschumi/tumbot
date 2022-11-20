import ast
import re
import sqlite3
import traceback

from discord.ext import commands


def _insert_returns(body):
    # insert return statement if the last statement is an expression
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        _insert_returns(body[-1].body)
        _insert_returns(body[-1].orelse)

    # for with blocks we insert returns into the body
    if isinstance(body[-1], (ast.With, ast.AsyncWith)):
        _insert_returns(body[-1].body)


class DBotAdmin(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, query):
        """Executes an SQL-query"""

        # Set default scope
        if ctx.guild is not None:
            scope = "guild"
        else:
            scope = "user"

        matches = re.match(r"`(.*)`(?: (\w+)(?:/(\d+))?)?", query)
        if not matches:
            await ctx.send("Couldn't filter out the query that should be executed.")
            return

        if matches.group(2) is not None:
            scope = matches.group(2)

        if matches.group(3) is None:
            if scope == "guild":
                dbid = ctx.guild.id
            else:
                dbid = ctx.author.id
        else:
            dbid = matches.group(3)

        query = matches.group(1)
        async with ctx.typing():
            try:
                with self.bot.db.get(dbid, scope) as db:
                    result = [dict(row) for row in db.execute(query).fetchall()]
            except sqlite3.OperationalError as e:
                await ctx.send(f"```{e}```")
                return

        if len(result) < 1:
            await ctx.message.add_reaction("\U00002705")
            return

        await self.bot.send_table(ctx, result[0].keys(), result)

    @commands.command()
    @commands.is_owner()
    async def eval(self, ctx, *, cmd):
        """Runs a Python command or script"""

        # Remove surrounding code block and parse it
        cmd = cmd.strip("` ")
        try:
            parsed_cmd = ast.parse(cmd)
        except SyntaxError:
            await ctx.send(
                f"Exception while parsing command:\n```{traceback.format_exc()}```"
            )
            return

        # Create a fake function stub and parse it
        parsed_fn = ast.parse("async def _eval(): pass")

        # Correct line numbers
        for node in parsed_cmd.body:
            ast.increment_lineno(node)

        # Add returns for convenience
        _insert_returns(parsed_cmd.body)

        # Insert our code into the fake function
        parsed_fn.body[0].body = parsed_cmd.body

        # Define our execution environment
        env = {
            "ctx": ctx,
        }

        # Compile our function for execution and load it
        exec(
            compile(parsed_fn, filename="<ast>", mode="exec"), env
        )  # pylint: disable=exec-used

        async with ctx.typing():
            try:
                output = await eval("_eval()", env)  # pylint: disable=eval-used
            except Exception:  # pylint: disable=broad-except
                await ctx.send(
                    f"Exception while running command:\n```{traceback.format_exc()}```"
                )
                return

        # Nothing returned? If so, show that the command actually ran.
        if output is None:
            await ctx.message.add_reaction("\U00002705")
            return

        await ctx.send(f"```{output}```")
        return

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog):
        """Loads a previously not loaded Cog"""

        name = self.bot.find_cog(cog)

        if name is None:
            await ctx.send(f"Cog `{cog}` could not be found.")
            return

        await self.bot.load_extension(name)
        await ctx.message.add_reaction("\U00002705")

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog):
        """Unloads a previously loaded Cog"""

        name = self.bot.find_cog(cog)

        if name is None:
            await ctx.send(f"Cog `{cog}` could not be found.")
            return

        await self.bot.unload_extension(name)
        await ctx.message.add_reaction("\U00002705")

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, cog):
        """Unloads and reloads a previously loaded Cog"""

        name = self.bot.find_cog(cog)

        if name is None:
            await ctx.send(f"Cog `{cog}` could not be found.")
            return

        await self.bot.reload_extension(name)
        await ctx.message.add_reaction("\U00002705")


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(DBotAdmin(bot))
