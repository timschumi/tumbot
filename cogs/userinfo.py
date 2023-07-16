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
    async def userinfo(self, ctx, user: discord.User):
        """Displays the most relevant stats of a user"""

        member = None if ctx.guild is None else ctx.guild.get_member(user.id)

        userinfoembed = discord.Embed(
            colour=user.color, timestamp=ctx.message.created_at
        )

        userinfoembed.set_author(name=f"Informationen über: {user}")
        userinfoembed.set_thumbnail(url=user.avatar.url)
        userinfoembed.set_footer(
            text=f"Abgefragt von {ctx.author}", icon_url=ctx.author.avatar.url
        )

        userinfoembed.add_field(name="ID:", value=str(user.id))
        userinfoembed.add_field(name="Name:", value=str(user.display_name))

        if member is not None:
            userinfoembed.add_field(name="Status:", value=str(member.status))

        if member is not None and member.activity is not None:
            userinfoembed.add_field(name="Aktivität:", value=str(member.activity.name))

        userinfoembed.add_field(
            name="Account erstellt:",
            value=user.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"),
        )

        if member is not None:
            userinfoembed.add_field(
                name="Beigetreten:",
                value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"),
            )

        if member is not None:
            roles = list(reversed(member.roles))
            userinfoembed.add_field(
                name=f"Rollen ({len(roles)})",
                value=_join("\n", [role.mention for role in roles], 1024),
            )
            userinfoembed.add_field(
                name="Höchste Rolle:", value=str(member.top_role.mention)
            )

        userinfoembed.add_field(name="Bot?", value=str(user.bot))

        await ctx.send(embed=userinfoembed)


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(Userinfo(bot))
