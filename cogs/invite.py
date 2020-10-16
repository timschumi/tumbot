import discord
from discord.ext import commands


class InviteManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.invites = dict()
        self._var_channel = self.bot.conf.register('invite.channel',
                                                   description="The channel where invite tracking is logged.")

        self.bot.loop.create_task(self.init_invites())

    async def init_invites(self):
        await self.bot.wait_until_ready()

        for g in self.bot.guilds:
            await self.update_invites(g)

    async def update_invites(self, guild):
        self.invites[guild.id] = await guild.invites()

    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        """Manages invites."""

        await ctx.send_help(ctx.command)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.update_invites(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        old = self.invites[guild.id]
        self.invites[guild.id] = await guild.invites()

        channel = self._var_channel.get(guild.id)

        if channel is None:
            return

        channel = self.bot.get_channel(int(channel))
        if channel is None:
            return

        for i, v in enumerate(old):
            if v not in self.invites[guild.id]:
                invite = v
                break

            if v.uses != self.invites[guild.id][i].uses:
                invite = v
                break
        else:
            await channel.send("Konnte Invite nicht tracken!")
            return

        text = f"**{member}** ({member.id}) wurde von **{invite.inviter}** ({invite.inviter.id}) eingeladen."

        text += f" (Invite: {invite.code})"

        # Invite has been used, so add one to the counter
        invite.uses += 1

        if invite.max_uses != 0:
            text += f" ({invite.uses}/{invite.max_uses})"

        await channel.send(text)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.update_invites(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.update_invites(invite.guild)


def setup(bot):
    bot.add_cog(InviteManager(bot))
