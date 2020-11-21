import discord
from discord.ext import commands


def _reason_to_text(reason):
    if reason is None:
        return "No reason given."

    return reason


class InviteManager(commands.Cog):

    def __init__(self, bot):
        self._bot = bot
        self._invs = dict()
        self._var_channel = self._bot.conf.var('invite.channel')
        self._var_perm_backend = self._bot.conf.var('invite.perm_backend')
        self._var_perm_role = self._bot.conf.var('invite.perm_role')
        self._var_inv_channel = self._bot.conf.var('invite.inv_channel')
        self._var_inv_count = self._bot.conf.var('invite.inv_count')
        self._var_inv_age = self._bot.conf.var('invite.inv_age')
        self._var_allow_requests = self._bot.conf.var('invite.allow_requests')

        self._bot.loop.create_task(self.init_invites())

    async def init_invites(self):
        await self._bot.wait_until_ready()

        for g in self._bot.guilds:
            await self.update_invites(g)

    async def update_invites(self, guild):
        # Don't do anything if we don't have necessary permissions
        if not guild.me.guild_permissions.manage_guild:
            return

        self._invs[guild.id] = await guild.invites()

    def _get_inv_channel(self, guild, default=None):
        # Get stored channel
        channel = self._var_inv_channel.get(guild.id)
        if channel is not None:
            # Try to resolve
            channel = guild.get_channel(int(channel))

        # Can't resolve or not set
        if channel is None:
            return default

        return channel

    def _can_user_invite(self, member):
        backend = self._var_perm_backend.get(member.guild.id)

        if backend == "role":
            role = self._var_perm_role.get(member.guild.id)

            if role is None:
                return False

            role = member.guild.get_role(int(role))

            return role in member.roles

        # Fallback for "permission" and everything else
        return member.guild_permissions.create_instant_invite

    async def _create_invite(self, messageable, member, channel, reason=None, allowed_by=None):
        # Set allowed_by if not set
        if allowed_by is None:
            allowed_by = member

        invite = await channel.create_invite(reason=f"{member} ({member.id}): {_reason_to_text(reason)}",
                                             max_age=self._var_inv_age.get(member.guild.id),
                                             max_uses=self._var_inv_count.get(member.guild.id))

        try:
            await member.send(f"Invite: <{invite.url}>, reason: {_reason_to_text(reason)}")
        except discord.errors.Forbidden:
            await messageable.send(
                "Could not message you the invite link. Do you have messages from server members enabled?")
            await invite.delete(reason="Could not message the invite link.")
            return False

        # Store invite in database
        with self._bot.db.get(member.guild.id) as db:
            db.execute("INSERT INTO invite_active (code, user, reason, allowed_by) VALUES (?, ?, ?, ?)",
                       (invite.code, member.id, reason, allowed_by.id))

        return True

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban user and announce it to other servers"""

        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You don't have a high enough role to ban this member.")
            return

        if ctx.guild.me.top_role <= member.top_role:
            await ctx.send("I don't have a high enough role to ban this member.")
            return

        await member.ban(reason=f"{ctx.author} ({ctx.author.id}): {_reason_to_text(reason)}")
        await ctx.send(f"User **{member}** has been banned by **{ctx.author}** (reason: {_reason_to_text(reason)}).")

        for g in self._bot.guilds:
            channel = self._var_channel.get(g.id)

            # Channel not set?
            if channel is None:
                continue

            channel = g.get_channel(int(channel))

            # Could not resolve channel?
            if channel is None:
                continue

            user_on_server = member in g.members

            await channel.send(
                (":red_circle:" if user_on_server else ":yellow_circle:") +
                f" {member} ({member.id}) has been banned on {ctx.guild} (reason: {_reason_to_text(reason)}). " +
                ("The member is on this server." if user_on_server else "The member is not on this server.")
            )

    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        """Manages invites."""
        await ctx.send_help(ctx.command)

    @invite.command(name="create")
    @commands.bot_has_permissions(create_instant_invite=True)
    async def invite_create(self, ctx, *, reason=None):
        if not self._can_user_invite(ctx.author):
            await ctx.message.add_reaction('\U0001F6AB')
            return

        channel = self._get_inv_channel(ctx.guild, default=ctx.channel)

        if not await self._create_invite(ctx, ctx.author, channel, reason=reason):
            return

        await ctx.message.add_reaction('\U00002705')

    def _invite_requests_enabled(self, guild):
        # Setting enabled (i.e. not 0)?
        if self._var_allow_requests.get(guild.id) == "0":
            return False

        # invite.channel set?
        if self._var_channel.get(guild.id) is None:
            return False

        # invite.inv_channel set?
        if self._var_inv_channel.get(guild.id) is None:
            return False

        return True

    @invite.command(name="request")
    @commands.bot_has_permissions(create_instant_invite=True)
    async def invite_request(self, ctx, *, reason=None):
        # Do we have invite requesting enabled?
        if not self._invite_requests_enabled(ctx.guild):
            await ctx.send("Sorry, invite requests are not enabled on this server.")
            return

        try:
            await ctx.author.send(f"Your request has been submitted. You will get an invite link once it has been approved.")
        except discord.errors.Forbidden:
            await ctx.send("Could send a private message. Do you have messages from server members enabled?")
            return False

        channel = self._var_channel.get(ctx.guild.id)

        if channel is None:
            return

        channel = self._bot.get_channel(int(channel))
        if channel is None:
            return

        message = await channel.send(f"**{ctx.author}** ({ctx.author.id}) requested an invite. Reason: \"{_reason_to_text(reason)}\"")

        # Add yes/no reactions
        await message.add_reaction('\U00002705')
        await message.add_reaction('\U0000274E')

        # Store request in database
        with self._bot.db.get(ctx.guild.id) as db:
            db.execute("INSERT INTO invite_requests (message, user, reason) VALUES (?, ?, ?)",
                       (message.id, ctx.author.id, reason))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.update_invites(guild)

    def _invite_info_to_text(self, invite):
        inviter = invite.inviter

        # Do we have that invite in the database?
        with self._bot.db.get(invite.guild.id) as db:
            result = db.execute("SELECT * FROM invite_active WHERE code = ?", (invite.code,)).fetchall()
        invite_data = result[0] if len(result) > 0 else None

        if invite_data:
            inviter = invite.guild.get_member(invite_data["user"])

        text = f"(Creator: **{inviter}** [{inviter.id}])"

        if invite_data and invite_data["reason"]:
            text += f" (Reason: {invite_data['reason']})"

        if invite_data and invite_data["allowed_by"] != invite_data["user"]:
            allowed_by = invite.guild.get_member(invite_data["allowed_by"])
            text += f" (Approver: **{allowed_by}** [{allowed_by.id}])"

        if invite.max_uses != 0:
            text += f" (Uses: {invite.uses}/{invite.max_uses})"

        return text

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        # Don't do anything if we don't have necessary permissions
        if not guild.me.guild_permissions.manage_guild:
            return

        old = self._invs[guild.id]
        self._invs[guild.id] = await guild.invites()

        channel = self._var_channel.get(guild.id)

        if channel is None:
            return

        channel = self._bot.get_channel(int(channel))
        if channel is None:
            return

        for i, v in enumerate(old):
            if v not in self._invs[guild.id]:
                invite = v
                break

            if v.uses != self._invs[guild.id][i].uses:
                invite = v
                break
        else:
            await channel.send("Konnte Invite nicht tracken!")
            return

        # Invite has been used, so add one to the counter
        invite.uses += 1

        await channel.send(f"**{member}** [{member.id}] joined the server via invite ({invite.code})."
                           f" {self._invite_info_to_text(invite)}")

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.update_invites(invite.guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.update_invites(invite.guild)

        # TODO: Clean up expired invites
        with self._bot.db.get(invite.guild.id) as db:
            db.execute("DELETE FROM invite_active WHERE code = ?", (invite.code,))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Ignore private messages
        if payload.guild_id is None:
            return

        # Ignore own reactions
        if payload.user_id == self._bot.user.id:
            return

        # Check if its a yes/no reaction
        if payload.emoji.name != '\U00002705' and payload.emoji.name != '\U0000274E':
            return

        guild = self._bot.get_guild(payload.guild_id)
        channel = self._bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)

        # Check if the user can invite
        if not self._can_user_invite(member):
            return

        # Check if there is a pending request in the database
        with self._bot.db.get(guild.id) as db:
            result = db.execute("SELECT rowid, user, reason FROM invite_requests WHERE message = ?",
                                (message.id,)).fetchall()

        if len(result) == 0:
            return

        entry = result[0]

        # Remove invite from pending requests
        with self._bot.db.get(guild.id) as db:
            db.execute("DELETE FROM invite_requests WHERE rowid = ?", (entry["rowid"],))

        # Resolve the user
        inv_user = guild.get_member(entry["user"])

        # Remove user reaction
        await message.remove_reaction(payload.emoji, member)

        # Invite denied?
        if payload.emoji.name == '\U0000274E':
            # Remove the "allow" reaction
            await message.clear_reaction('\U00002705')

            try:
                await inv_user.send("Your request has been denied.")
            except discord.errors.Forbidden:
                await channel.send("Could not notify the user.")
            return

        inv_channel = self._get_inv_channel(guild)

        if inv_channel is None:
            await channel.send("Could not resolve channel for invite.")
            return

        if not await self._create_invite(channel, inv_user, inv_channel, reason=entry["reason"], allowed_by=member):
            return

        # Remove the "denied" reaction
        await message.clear_reaction('\U0000274E')


def setup(bot):
    bot.conf.register('invite.channel',
                      description="The channel where invite tracking is logged.")
    bot.conf.register('invite.perm_backend',
                      default="permission",
                      description="The control mechanism for who gets to create invites [permission/role].")
    bot.conf.register('invite.perm_role',
                      description="The role that is allowed to create invites.")
    bot.conf.register('invite.inv_channel',
                      description="The channel where invites will point to (None = current).")
    bot.conf.register('invite.inv_count',
                      default="1",
                      description="The amount of people that can be invited (0 = infinite).")
    bot.conf.register('invite.inv_age',
                      default="0",
                      description="The lifetime of an invite in seconds (0 = infinite).")
    bot.conf.register('invite.allow_requests',
                      default="0",
                      description="If not 0, allows users to request invites (requires [invite.channel] and [invite.inv_channel] to be set).")

    bot.add_cog(InviteManager(bot))
