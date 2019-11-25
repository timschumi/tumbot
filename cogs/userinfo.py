import discord
from discord.ext import commands


class Userinfo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member):
        roles = [role for role in member.roles]

        userinfoembed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at)

        userinfoembed.set_author(name=f'Informationen über: {member}')
        userinfoembed.set_thumbnail(url=member.avatar_url)
        userinfoembed.set_footer(text=f'{ctx.author} abgefragt von', icon_url=ctx.author.avatar_url)

        userinfoembed.add_field(name='ID:', value=str(member.id))
        userinfoembed.add_field(name='Name:', value=str(member.display_name))

        userinfoembed.add_field(name='Status:', value=str(member.status))
        userinfoembed.add_field(name='Aktivität:', value=str(member.activity.name))

        userinfoembed.add_field(name='Account erstellt:',
                                value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
        userinfoembed.add_field(name='Beigetreten:', value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))

        userinfoembed.add_field(name=f'Rollen ({len(roles)})', value='  '.join([role.mention for role in roles]))
        userinfoembed.add_field(name='Höchste Rolle:', value=str(member.top_role.mention))

        userinfoembed.add_field(name='Bot?', value=str(member.bot))

        await ctx.send(embed=userinfoembed)

    @userinfo.error
    async def userinfo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            errorcu01embed = discord.Embed(title="Error #CU01",
                                           description="Fehlende NutzerID! Syntax: userinfo <userid>", color=0xff0000)
            await ctx.send(embed=errorcu01embed)


def setup(bot):
    bot.add_cog(Userinfo(bot))
