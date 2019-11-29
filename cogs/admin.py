from discord.ext import commands
import discord
import re

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sql(self, ctx, *, query):
        if not self.bot.botowner(ctx):
            return

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
            text += "\n|"
            for key in keys:
                text += " {} |".format(str(row[key]).ljust(key_length[key]))

        await ctx.send("```{}```".format(text))

def setup(bot):
    bot.add_cog(Admin(bot))
