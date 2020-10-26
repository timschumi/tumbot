import discord
from discord.ext import commands


def _reason_to_text(reason):
    if reason is None:
        return "No reason given."

    return reason


class InviteManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.invites = dict()
        self._var_channel = self.bot.conf.register('invite.channel',
                                                   description="The channel where invite tracking is logged.")
        self._var_perm_backend = self.bot.conf.register('invite.perm_backend',
                                                        default="permission",
                                                        description="The control mechanism for who gets to create invites [permission/role].")
        self._var_perm_role = self.bot.conf.register('invite.perm_role',
                                                     description="The role that is allowed to create invites.")
        self._var_inv_channel = self.bot.conf.register('invite.inv_channel',
                                                       description="The channel where invites will point to (None = current).")
        self._var_inv_count = self.bot.conf.register('invite.inv_count',
                                                     default="1",
                                                     description="The amount of people that can be invited (0 = infinite).")
        self._var_inv_age = self.bot.conf.register('invite.inv_age',
                                                   default="0",
                                                   description="The lifetime of an invite in seconds (0 = infinite).")

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

    def _get_inv_channel(self, ctx):
        # Get stored channel
        channel = int(self._var_inv_channel.get(ctx.guild.id))
        if channel is not None:
            # Try to resolve
            channel = ctx.guild.get_channel(channel)

        # Can't resolve or not set
        if channel is None:
            channel = ctx.channel

        return channel

    def _can_user_invite(self, ctx):
        backend = self._var_perm_backend.get(ctx.guild.id)

        if backend == "role":
            role = self._var_perm_role.get(ctx.guild.id)

            if role is None:
                return False

            role = ctx.guild.get_role(int(role))

            return role in ctx.author.roles

        # Fallback for "permission" and everything else
        return ctx.author.guild_permissions.create_instant_invite

    @invite.command(name="create")
    @commands.bot_has_permissions(create_instant_invite=True)
    async def invite_create(self, ctx, *, reason=None):
        if not self._can_user_invite(ctx):
            await ctx.message.add_reaction('\U0001F6AB')
            return

        channel = self._get_inv_channel(ctx)

        invite = await channel.create_invite(reason=f"{ctx.author} ({ctx.author.id}): {_reason_to_text(reason)}",
                                             max_age=self._var_inv_age.get(ctx.guild.id),
                                             max_uses=self._var_inv_count.get(ctx.guild.id))

        try:
            await ctx.author.send(f"Invite: <{invite.url}>, reason: {_reason_to_text(reason)}")
        except discord.errors.Forbidden:
            await ctx.send("Could not message you the invite link. Do you have messages from server members enabled?")
            await invite.delete(reason="Could not message the invite link.")
            return

        # Store invite in database
        with self.bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO invite_active (code, user, reason) VALUES (?, ?, ?)", (invite.code, ctx.author.id, reason))

        await ctx.message.add_reaction('\U00002705')

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

        inviter = invite.inviter

        # Do we have that invite in the database?
        result = self.bot.db.get(guild.id).execute("SELECT * FROM invite_active WHERE code = ?", (invite.code,)).fetchall()
        invite_data = result[0] if len(result) > 0 else None

        if invite_data:
            inviter = guild.get_member(invite_data["user"])

        text = f"**{member}** ({member.id}) wurde von **{inviter}** ({inviter.id}) eingeladen."

        if invite_data and invite_data["reason"]:
            text += f" (Reason: {invite_data['reason']})"

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

        # TODO: Clean up expired invites
        with self.bot.db.get(invite.guild.id) as db:
            db.execute("DELETE FROM invite_active WHERE code = ?", (invite.code,))


def setup(bot):
    bot.add_cog(InviteManager(bot))
