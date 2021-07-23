import json
import discord
from discord.ext import commands
import urllib.request as u


class IsEven(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def isEven(self, ctx, number):
        if not number.isnumeric():
            await ctx.send("Error! This is not a number!")
        number = int(number)
        response = u.urlopen(f"https://api.isevenapi.xyz/api/iseven/{number}")
        json_response = json.loads(response.read())
        if "error" in json_response:
            if json_response["error"] == "Invalid number.":
                await ctx.send("This number is not a valid number according to tha API but according to Python :eyes:")
            elif json_response["error"] == "Number out of range. Upgrade to isEven API Premium or Enterprise.":
                await ctx.send("I am not on premium :(")
        else:
            emb = discord.Embed(
                title=f"Is Even for Number {number}",
                description=(
                    f"Number {number} is even!" if json_response["iseven"] else f"Number {number} is not even!"),
                colour=0x13b038 if json_response["iseven"] else 0xa83232
            )

            emb.add_field(name="Advertisement", value=json_response["ad"])
            emb.set_footer(text="Build using isEven API https://isevenapi.xyz/")

            await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(IsEven(bot))
