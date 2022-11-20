import discord
from discord.ext import commands


def _join(delimiter, values, maxlen):
    joined = ""

    for value in values:
        string = (delimiter if len(joined) > 0 else "") + str(value)

        if len(joined) + len(string) > maxlen:
            return joined

        joined += string

    return joined


class Userinfo(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["userinfos", "whois"])
    async def userinfo(self, ctx, member: discord.Member):
        """Displays the most relevant stats of a user"""

        roles = list(reversed(member.roles))

        userinfoembed = discord.Embed(
            colour=member.color, timestamp=ctx.message.created_at
        )

        userinfoembed.set_author(name=f"Informationen über: {member}")
        userinfoembed.set_thumbnail(url=member.avatar.url)
        userinfoembed.set_footer(
            text=f"Abgefragt von {ctx.author}", icon_url=ctx.author.avatar.url
        )

        userinfoembed.add_field(name="ID:", value=str(member.id))
        userinfoembed.add_field(name="Name:", value=str(member.display_name))

        userinfoembed.add_field(name="Status:", value=str(member.status))

        if member.activity is not None:
            userinfoembed.add_field(name="Aktivität:", value=str(member.activity.name))

        userinfoembed.add_field(
            name="Account erstellt:",
            value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"),
        )
        userinfoembed.add_field(
            name="Beigetreten:",
            value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"),
        )

        userinfoembed.add_field(
            name=f"Rollen ({len(roles)})",
            value=_join("\n", [role.mention for role in roles], 1024),
        )
        userinfoembed.add_field(
            name="Höchste Rolle:", value=str(member.top_role.mention)
        )

        userinfoembed.add_field(name="Bot?", value=str(member.bot))

        await ctx.send(embed=userinfoembed)


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(Userinfo(bot))
