from discord.ext import commands
import re

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, query):
        matches = re.match(r'`(.*)`', query)
        if not matches:
            await ctx.send("Couldn't filter out the query that should be executed.")
            return

        query = matches.group(1)
        with self.bot.db.get(ctx.guild.id) as db:
            result = [dict(row) for row in db.execute(query).fetchall()]

        if len(result) < 1:
            return

        keys = result[0].keys()
        key_length = {}

        for row in result:
            for key in keys:
                if not key in key_length:
                    key_length[key] = len(str(key))

                key_length[key] = max(key_length[key], len(str(row[key])))

        text = "|"

        for i in keys:
            text += " {} |".format(str(i).ljust(key_length[i]))

        text += "\n" + '-' * len(text)

        for row in result:
            newtext = "\n|"
            for key in keys:
                newtext += " {} |".format(str(row[key]).ljust(key_length[key]))

            if len(text) + len(newtext) >= 2000:
                await ctx.send("```{}```".format(text))
                text = ""

            text += newtext

        await ctx.send("```{}```".format(text))

def setup(bot):
    bot.add_cog(Admin(bot))
