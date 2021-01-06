import asyncio
import datetime
import json
import re
import time

import discord
from discord.ext import commands, tasks

import basedbot


def _reason_to_text(reason):
    if reason is None:
        return "No reason given."

    return reason


def _find_match(li, v):
    if v not in li:
        return None

    return li[li.index(v)]


class InviteManager(commands.Cog):

    def __init__(self, bot):
        self._bot = bot
        self._invs = dict()
        self._var_channel = self._bot.conf.var('invite.channel')
        self._var_inv_channel = self._bot.conf.var('invite.inv_channel')
        self._var_inv_count = self._bot.conf.var('invite.inv_count')
        self._var_inv_age = self._bot.conf.var('invite.inv_age')
        self._var_notify_deleted = self._bot.conf.var('invite.notify_deleted')
        self._perm_create = self._bot.perm.get('invite.create')
        self._perm_create_custom = self._bot.perm.get('invite.create_custom')
        self._perm_request = self._bot.perm.get('invite.request')

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

    async def _create_invite(self, messageable, member, channel, reason=None, allowed_by=None, options=None):
        # Set allowed_by if not set
        if allowed_by is None:
            allowed_by = member

        full_opt = {
            "max_age": self._var_inv_age.get(member.guild.id),
            "max_uses": self._var_inv_count.get(member.guild.id),
        }

        if options is not None:
            full_opt.update(options)

        invite = await channel.create_invite(reason=f"{member} ({member.id}): {_reason_to_text(reason)}",
                                             max_age=full_opt["max_age"], max_uses=full_opt["max_uses"])

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

    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        """Manages invites."""
        await ctx.send_help(ctx.command)

    @invite.command(name="create")
    @commands.bot_has_permissions(create_instant_invite=True)
    @basedbot.has_permissions("invite.create")
    async def invite_create(self, ctx, *, reason=None):
        """
        Creates a tracked invite

        The reason (if given) is stored in the audit log and invite tracker.

        With the appropriate permissions, additional options can be set using backticked JSON at the end of the reason:
         - `max_age`: How long the before the invite expires in seconds.
         - `max_uses`: How many times the invite can be used.
        """

        options = {}

        if reason is not None:
            matches = re.match(r'^(.*?)(?: *)(?:`(.*)`)?$', reason)
            if not matches:
                await ctx.send("Could not parse the reason/options.")
                return

            reason = matches.group(1)
            raw_options = matches.group(2)

            if reason == "":
                reason = None

            if raw_options is not None:
                if not self._perm_create_custom.allowed(ctx.author):
                    await ctx.send("You are not allowed to create invites with custom options.")
                    return

                try:
                    options = json.loads(raw_options)
                except json.JSONDecodeError as e:
                    await ctx.send(f"Failed to parse JSON:\n```{e}```")
                    return

        channel = self._get_inv_channel(ctx.guild, default=ctx.channel)

        if not await self._create_invite(ctx, ctx.author, channel, reason=reason, options=options):
            return

        await ctx.message.add_reaction('\U00002705')

    def _invite_requests_enabled(self, guild):
        # invite.channel set?
        if self._var_channel.get(guild.id) is None:
            return False

        # invite.inv_channel set?
        if self._var_inv_channel.get(guild.id) is None:
            return False

        return True

    @invite.command(name="request")
    @commands.bot_has_permissions(create_instant_invite=True)
    @basedbot.has_permissions("invite.request")
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

    def _get_last_invite(self, member):
        with self._bot.db.get(member.guild.id) as db:
            res = db.execute("SELECT code FROM invite_active WHERE user = ? OR allowed_by = ? ORDER BY rowid DESC LIMIT 1",
                             (member.id, member.id)).fetchall()

        if len(res) < 1:
            return None

        return res[0][0]

    @invite.command(name="close")
    @commands.bot_has_permissions(manage_channels=True)
    async def invite_close(self, ctx, code=None):
        """
        Deletes the given invite

        Uses invite codes or row IDs returned by the list command.

        If no invite is given, the last invite requested or approved is closed instead.
        """
        if code is None and ctx.guild is not None:
            code = self._get_last_invite(ctx.author)

        if code is None:
            await ctx.send("Could not find last invite.")
            return

        # Check if invite is managed by bot and is related to user
        with self._bot.db.get(ctx.guild.id) as db:
            res = db.execute("SELECT code FROM invite_active WHERE (user = ? OR allowed_by = ?) AND (code = ? OR rowid = ?)",
                             (ctx.author.id, ctx.author.id, code, code)).fetchall()

        if len(res) < 1:
            await ctx.message.add_reaction('\U0001F6AB')
            return

        try:
            invite = await self._bot.fetch_invite(code)
        except discord.errors.NotFound:
            await ctx.send("Could not find the given invite.")
            return

        await invite.delete(reason=f"Closed manually by {ctx.author} [{ctx.author.id}]")
        await ctx.message.add_reaction('\U00002705')

    @invite.command(name="list")
    async def invite_list(self, ctx):
        see_all = ctx.author.guild_permissions.manage_guild

        query = "SELECT rowid, user, reason, allowed_by FROM invite_active"
        args = ()

        if not see_all:
            query += " WHERE (user = ? OR allowed_by = ?)"
            args += (ctx.author.id, ctx.author.id)

        with self._bot.db.get(ctx.guild.id) as db:
            result = db.execute(query, args).fetchall()

        if len(result) < 1:
            await ctx.send("No active invites found.")
            return

        entries = []

        for e in result:
            entry = {
                'ID': e['rowid'],
                'User': str(ctx.guild.get_member(e['user'])),
                'Reason': _reason_to_text(e['reason']),
                'Approver': "<redacted>",
            }

            if see_all or ctx.author.id == e['allowed_by']:
                entry['Approver'] = str(ctx.guild.get_member(e['allowed_by']))

            entries.append(entry)

        await self._bot.send_table(ctx, ["ID", "User", "Reason", "Approver"], entries)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.update_invites(guild)

    def _get_invite_data(self, invite):
        data = {
            'invite': invite,
            'inviter': invite.inviter,
        }

        # Do we have that invite in the database?
        with self._bot.db.get(invite.guild.id) as db:
            result = db.execute("SELECT * FROM invite_active WHERE code = ?", (invite.code,)).fetchall()
        invite_data = result[0] if len(result) > 0 else None

        if invite_data:
            data['inviter'] = invite.guild.get_member(invite_data["user"])

        if invite_data and invite_data["reason"]:
            data['reason'] = invite_data["reason"]

        if invite_data and invite_data["allowed_by"] != invite_data["user"]:
            data['approver'] = invite.guild.get_member(invite_data["allowed_by"])

        return data

    @classmethod
    def _invite_data_to_text(cls, data):
        text = f"(Creator: **{data['inviter']}** [{data['inviter'].id}])"

        if 'reason' in data:
            text += f" (Reason: {data['reason']})"

        if 'approver' in data:
            text += f" (Approver: **{data['approver']}** [{data['approver'].id}])"

        if data['invite'].max_uses != 0:
            text += f" (Uses: {data['invite'].uses}/{data['invite'].max_uses})"

        return text

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        # Ignore bots
        if member.bot:
            return

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

        invs = [e for e in old if e not in self._invs[guild.id] or _find_match(self._invs[guild.id], e).uses != e.uses]

        if len(invs) == 0:
            await channel.send(f"I don't know how **{member}** [{member.id}] joined the server.")
            return

        if len(invs) == 1:
            invite = invs[0]

            # Invite been used, so add one to the counter
            invite.uses += 1

            data = self._get_invite_data(invite)

            embed = discord.Embed(title=f"**{member}** ({member.id}) joined the server.", color=0x0065bd)

            if invite.max_uses != 0:
                embed.add_field(name="Invite", value=f"{invite.code} ({invite.uses}/{invite.max_uses})", inline=False)
            else:
                embed.add_field(name="Invite", value=invite.code, inline=False)

            embed.add_field(name="Creator", value=f"{data['inviter'].mention} ({data['inviter'].id})", inline=False)

            if 'approver' in data:
                embed.add_field(name="Approver", value=f"{data['approver'].mention} ({data['approver'].id})", inline=False)

            if 'reason' in data:
                embed.add_field(name="Reason", value=data['reason'], inline=False)

            await channel.send(embed=embed)
            return

        text = f"I wasn't able to reliably determine how **{member}** [{member.id}] joined the server:"
        for e in invs:
            data = self._get_invite_data(e)
            text += f"\n - Invite **{e.code}** {self._invite_data_to_text(data)}."

        await channel.send(text)
        return

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.update_invites(invite.guild)

    async def _notify_invite_owner(self, invite, message):
        # Do we have that invite in the database?
        with self._bot.db.get(invite.guild.id) as db:
            result = db.execute("SELECT user FROM invite_active WHERE code = ?", (invite.code,)).fetchall()

        if len(result) == 0:
            return

        # Resolve the user
        inv_user = invite.guild.get_member(result[0][0])

        if inv_user is None:
            return

        await inv_user.send(message)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.update_invites(invite.guild)

        if self._var_notify_deleted.get(invite.guild.id) != "0":
            try:
                await self._notify_invite_owner(invite, f"Invite **{invite.code}** has been deleted.")
            except discord.errors.Forbidden:
                # If we can't send messages to the user, just ignore
                pass

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
        if not self._perm_create.allowed(member):
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
            # Mark as "denied"
            await message.clear_reaction('\U00002705')
            await message.edit(content=f"{message.content} (Denied by: **{member}**)")

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

        # Mark as "approved"
        await message.clear_reaction('\U0000274E')
        await message.edit(content=f"{message.content} (Approved by: **{member}**)")


class ExpiredInvitesTracker(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        self._exp_times = {}

        self._bot.loop.create_task(self._init_invites())

    @classmethod
    def _calc_exp_time(cls, invite):
        exp_time = invite.created_at + datetime.timedelta(seconds=invite.max_age)
        return time.mktime(exp_time.timetuple())

    async def _init_invites(self):
        await self._bot.wait_until_ready()

        for g in self._bot.guilds:
            if not g.me.guild_permissions.manage_guild:
                continue

            for i in await g.invites():
                await self.on_invite_create(i)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        # Don't track if the invite doesn't expire
        if invite.max_age == 0:
            return

        self._exp_times[invite] = self._calc_exp_time(invite)

        # Restart loop in case new invite has a smaller max_age
        if self.check_invites.is_running():
            self.check_invites.restart()
        else:
            self.check_invites.start()

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        # Don't do anything if the invite wasn't tracked
        if invite not in self._exp_times:
            return

        del self._exp_times[invite]

        if len(self._exp_times) == 0 and self.check_invites.is_running():
            self.check_invites.cancel()

    @tasks.loop()
    async def check_invites(self):
        # Stop if no invites are left
        if len(self._exp_times) == 0:
            self.check_invites.cancel()

        # Get next invite that expires
        invite = min(self._exp_times, key=self._exp_times.get)
        exp_time = self._exp_times[invite]

        # Sleep until then
        await asyncio.sleep(exp_time - time.mktime(datetime.datetime.utcnow().timetuple()))

        # Send out the event
        self._bot.dispatch('invite_delete', invite)


def setup(bot):
    bot.conf.register('invite.channel',
                      description="The channel where invite tracking is logged.")
    bot.conf.register('invite.inv_channel',
                      description="The channel where invites will point to (None = current).")
    bot.conf.register('invite.inv_count',
                      default="1",
                      description="The amount of people that can be invited (0 = infinite).")
    bot.conf.register('invite.inv_age',
                      default="0",
                      description="The lifetime of an invite in seconds (0 = infinite).")
    bot.conf.register('invite.notify_deleted',
                      default="0",
                      description="If not 0, messages the invite owner if an invite gets deleted.")
    bot.perm.register('invite.create',
                      base="create_instant_invite",
                      pretty_name="Create invites")
    bot.perm.register('invite.create_custom',
                      base="create_instant_invite",
                      pretty_name="Create invites with custom settings")
    bot.perm.register('invite.request',
                      base=False,
                      pretty_name="Request invites")

    bot.add_cog(InviteManager(bot))
    bot.add_cog(ExpiredInvitesTracker(bot))
