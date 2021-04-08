import functools
import sqlite3
from typing import Optional

import discord
from discord.ext import commands

import basedbot

COLOR_NETWORK_JOIN = 0x00d100
COLOR_MESSAGE_WARN = 0xf0bb2b
COLOR_MESSAGE_CRIT = 0xed3e32

class GuildNetworkMember:
    def __init__(self, bot, db, network, data):
        self._bot = bot
        self._db = db
        self._network = network
        self._guild = self._bot.get_guild(data["gid"])
        self._admin = (data["admin"] > 0)

    def __str__(self):
        return str(self._guild)

    @property
    def network(self):
        return self._network

    @property
    def guild(self):
        return self._guild

    @property
    def admin(self):
        return self._admin

    @admin.setter
    def admin(self, value):
        self._admin = value

        with self._db.get('', scope='global') as db:
            db.execute("UPDATE network_member SET admin = ? WHERE nid = ? AND gid = ?",
                       (1 if value else 0, self.network.id, self.guild.id))


class GuildNetwork:
    def __init__(self, bot, db, data):
        self._bot = bot
        self._db = db
        self._nid = data["rowid"]
        self._name = data["name"]

        # Populate members
        with self._db.get('', scope='global') as db:
            result = db.execute("SELECT gid FROM network_member WHERE nid = ?", (self._nid,)).fetchall()
        self._members = {r[0]: self._fetch_member(r[0]) for r in result}

        self._owner = self.get_member(data["owner"])

    @property
    def id(self):
        return self._nid

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        if not isinstance(value, GuildNetworkMember):
            raise ValueError("New owner is not of type GuildNetworkMember!")

        if value.network != self:
            raise ValueError("New owner is not from same network!")

        value.admin = True
        self._owner = value

        with self._db.get('', scope='global') as db:
            db.execute("UPDATE network SET owner = ? WHERE rowid = ?", (value.guild.id, self.id))

    @property
    def members(self):
        return list(self._members.values())

    @property
    def admins(self):
        return [e for e in self.members if e.admin]

    def _fetch_member(self, gid):
        with self._db.get('', scope='global') as db:
            result = db.execute("SELECT * FROM network_member WHERE nid = ? AND gid = ?", (self._nid, gid)).fetchone()

        if result is None:
            return None

        return GuildNetworkMember(self._bot, self._db, self, result)

    def get_member(self, gid):
        if gid not in self._members:
            val = self._fetch_member(gid)

            if val is None:
                return None

            self._members[gid] = val

        return self._members[gid]

    def join(self, gid):
        with self._db.get('', scope='global') as db:
            db.execute("REPLACE INTO network_member (nid, gid, admin) VALUES (?, ?, 0)", (self._nid, gid))

        return self.get_member(gid)

    def leave(self, gid):
        with self._bot.db.get(gid) as db:
            db.execute("DELETE FROM network_invites WHERE network = ?", (self._nid,))

        with self._db.get('', scope='global') as db:
            db.execute("DELETE FROM network_member WHERE nid = ? AND gid = ?", (self._nid, gid))

        if gid in self._members:
            del self._members[gid]

        if len(self._members) == 0:
            return

        if self.owner.guild.id == gid:
            admins = self.admins
            self.owner = admins[0] if len(admins) != 0 else self.members[0]


def _check_affect_member(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, member, *args, **kwargs):
        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You don't have a high enough role to modify this member.")
            return

        if ctx.guild.me.top_role <= member.top_role:
            await ctx.send("I don't have a high enough role to modify this member.")
            return

        await func(self, ctx, member, *args, **kwargs)

    return wrapper


class GuildNetworks(commands.Cog):
    def __init__(self, bot):
        self._bot = bot
        self._networks = {}

        self._var_channel = self._bot.conf.var('network.channel')

        self._perm_manage = self._bot.perm.get('network.manage')

        self._bot.loop.create_task(self._init_networks())

    async def _init_networks(self):
        await self._bot.wait_until_ready()

        with self._bot.db.get('', scope='global') as db:
            result = db.execute("SELECT rowid FROM network").fetchall()
        self._networks = {r[0]: self._fetch_network(r[0]) for r in result}

    def _create_network(self, name, gid):
        try:
            with self._bot.db.get('', scope='global') as db:
                c = db.execute("INSERT INTO network (name, owner) VALUES (?, ?)", (name, gid))
                db.execute("REPLACE INTO network_member (nid, gid, admin) VALUES (?, ?, 1)", (c.lastrowid, gid))
        except sqlite3.IntegrityError:
            return None

        return self.get_network(c.lastrowid)

    def _delete_network(self, nid):
        with self._bot.db.get('', scope='global') as db:
            db.execute("DELETE FROM network WHERE rowid = ?", (nid,))

        if nid in self._networks:
            del self._networks[nid]

    def _fetch_network(self, nid):
        with self._bot.db.get('', scope='global') as db:
            result = db.execute("SELECT rowid, * FROM network WHERE rowid = ?", (nid,)).fetchone()

        if result is None:
            return None

        return GuildNetwork(self._bot, self._bot.db, result)

    def get_network(self, nid):
        if nid not in self._networks:
            self._networks[nid] = self._fetch_network(nid)

        return self._networks[nid]

    @commands.group(invoke_without_command=True, aliases=["nw"])
    async def network(self, ctx):
        """Manages guild networks"""
        await ctx.send_help(ctx.command)

    @network.command(name="create")
    @basedbot.has_permissions("network.create")
    async def network_create(self, ctx, *, name):
        """Creates a new network"""
        if name is None or name.strip() == "":
            await ctx.send("No network name given!")
            return

        network = self._create_network(name, ctx.guild.id)

        if network is None:
            await ctx.send("Failed to create network.")
            return

        await ctx.message.add_reaction('\U00002705')
        return

    @network.command(name="invite")
    @basedbot.has_permissions("network.invite")
    async def network_invite(self, ctx, network: int, guild: int):
        """Invites a guild to a network"""

        network = self.get_network(network)

        if network is None:
            await ctx.send("Network not found!")
            return

        guild = self._bot.get_guild(guild)

        if guild is None:
            await ctx.send("Guild not found!")
            return

        nw_member = network.get_member(ctx.guild.id)

        if nw_member is None:
            await ctx.send("Network Member not found!")
            return

        if not nw_member.admin:
            await ctx.send("Only network admins can invite to the network.")
            return

        if network.get_member(guild.id) is not None:
            await ctx.send("The guild is already a member of the network.")
            return

        if self._var_channel.get(guild.id) is None:
            await ctx.send("The guild has not set up a channel for network messages.")
            return

        channel = self._bot.get_channel(int(self._var_channel.get(guild.id)))

        if channel is None:
            await ctx.send("The guild does not have a channel for network messages.")
            return

        message = await channel.send(f"Your guild has been invited to the following network: **{network.name}**. Ack?")

        # Add yes/no reactions
        await message.add_reaction('\U00002705')
        await message.add_reaction('\U0000274E')

        # Store invite in database
        with self._bot.db.get(guild.id) as db:
            db.execute("INSERT INTO network_invites (network, message, inviter) VALUES (?, ?, ?)",
                       (network.id, message.id, ctx.guild.id))

        await ctx.message.add_reaction('\U00002705')

    @network.command(name="list")
    @basedbot.has_permissions("network.list")
    async def network_list(self, ctx):
        """Lists all networks the current guild is in"""

        entries = []
        for n in self._networks.values():
            member = n.get_member(ctx.guild.id)

            if member is None:
                continue

            entries.append({
                "id": n.id,
                "name": n.name,
                "members": len(n.members) if member.admin else '?',
                "owner": str(n.owner)
            })

        if len(entries) == 0:
            await ctx.send("No networks found!")
            return

        await self._bot.send_table(ctx, ["id", "name", "members", "owner"], entries)
        return

    @network.command(name="leave")
    @basedbot.has_permissions("network.manage")
    async def network_leave(self, ctx, network: int):
        """Leaves a network"""
        network = self.get_network(network)

        if network is None:
            await ctx.send("Network could not be resolved.")
            return

        if network.get_member(ctx.guild.id) is None:
            await ctx.send("Network member could not be resolved.")
            return

        network.leave(ctx.guild.id)

        if len(network.members) == 0:
            self._delete_network(network.id)

        await ctx.message.add_reaction('\U00002705')

    def _get_neighbor_guilds(self, guild, pred=None):
        guilds = []

        for n in self._networks.values():
            # Skip networks that the guild is not a member of
            if n.get_member(guild.id) is None:
                continue

            for g in n.members:
                if g.guild in guilds:
                    continue

                if pred is not None and not pred(g):
                    continue

                guilds.append(g.guild)

        return guilds

    def _get_network_channel(self, guild):
        channel = self._var_channel.get(guild.id)

        # Channel not set?
        if channel is None:
            return None

        return guild.get_channel(int(channel))

    async def _send_network_channel(self, guild, *args, **kwargs):
        channel = self._get_network_channel(guild)

        if channel is None:
            return

        await channel.send(*args, **kwargs)

    @network.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @_check_affect_member
    async def network_ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban user and announce it to other guilds in the network"""

        await member.ban(reason=f"{ctx.author} ({ctx.author.id}): {reason if reason else 'No reason given.'}")
        await ctx.message.add_reaction('\U00002705')

        guilds = self._get_neighbor_guilds(ctx.guild, pred=lambda nwm: self._get_network_channel(nwm.guild) is not None)

        for g in guilds:
            user_in_guild = member in g.members

            embed = discord.Embed(title=f"{member} ({member.id}) has been banned from '{ctx.guild}'",
                                  color=(COLOR_MESSAGE_CRIT if user_in_guild else COLOR_MESSAGE_WARN))

            embed.set_thumbnail(url=ctx.guild.icon_url)

            if g == ctx.guild:
                embed.add_field(name="Banned by", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)

            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)

            if user_in_guild:
                embed.add_field(name="Status", value=f"The member is on this server.", inline=False)
            else:
                embed.add_field(name="Status", value=f"The member is not on this server.", inline=False)

            await self._send_network_channel(g, embed=embed)

    @network.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @_check_affect_member
    async def network_kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick user and announce it to other guilds in the network"""

        await member.kick(reason=f"{ctx.author} ({ctx.author.id}): {reason if reason else 'No reason given.'}")
        await ctx.message.add_reaction('\U00002705')

        guilds = self._get_neighbor_guilds(ctx.guild, pred=lambda nwm: self._get_network_channel(nwm.guild) is not None)

        for g in guilds:
            user_in_guild = member in g.members

            embed = discord.Embed(title=f"{member} ({member.id}) has been kicked from '{ctx.guild}'",
                                  color=(COLOR_MESSAGE_CRIT if user_in_guild else COLOR_MESSAGE_WARN))

            embed.set_thumbnail(url=ctx.guild.icon_url)

            if g == ctx.guild:
                embed.add_field(name="Kicked by", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)

            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)

            if user_in_guild:
                embed.add_field(name="Status", value=f"The member is on this server.", inline=False)
            else:
                embed.add_field(name="Status", value=f"The member is not on this server.", inline=False)

            await self._send_network_channel(g, embed=embed)

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

        if not self._perm_manage.allowed(member):
            return

        # Check if there is a pending invite in the database
        with self._bot.db.get(guild.id) as db:
            result = db.execute("SELECT * FROM network_invites WHERE message = ?",
                                (message.id,)).fetchall()

        if len(result) == 0:
            return

        entry = result[0]

        # Remove from pending invites
        with self._bot.db.get(guild.id) as db:
            db.execute("DELETE FROM network_invites WHERE message = ?", (entry["message"],))

        # Remove user reaction
        await message.remove_reaction(payload.emoji, member)

        # Invite denied?
        if payload.emoji.name == '\U0000274E':
            # Mark as "denied"
            await message.clear_reaction('\U00002705')
            return

        # Resolve network
        network = self.get_network(entry["network"])

        if network is None:
            await channel.send("Could not resolve the network.")
            return

        # Mark as "approved"
        await message.clear_reaction('\U0000274E')

        network.join(guild.id)

        inviter = self._bot.get_guild(entry["inviter"])

        # Construct the Embed
        embed = discord.Embed(title=f"**{guild}** ({guild.id}) joined the network.", color=COLOR_NETWORK_JOIN)
        embed.add_field(name="Network", value=f"{network.name} ({network.id})", inline=False)
        if inviter is not None:
            embed.add_field(name="Invited by", value=f"{inviter} ({inviter.id})", inline=False)

        for nw_member in network.members:
            g = nw_member.guild
            nw_channel = self._var_channel.get(g.id)

            if nw_channel is None:
                continue

            nw_channel = self._bot.get_channel(int(nw_channel))

            if nw_channel is None:
                continue

            await nw_channel.send(embed=embed)


def setup(bot):
    bot.conf.register('network.channel',
                      conv=Optional[discord.TextChannel],
                      description="The channel where guild network messages are logged.")
    bot.perm.register('network.invite',
                      base="administrator",
                      pretty_name="Invite guilds to a network")
    bot.perm.register('network.list',
                      base="administrator",
                      pretty_name="List networks that the guild is a member of")
    bot.perm.register('network.create',
                      base="administrator",
                      pretty_name="Create guild networks")
    bot.perm.register('network.manage',
                      base="administrator",
                      pretty_name="Basic network management (joining/leaving)")
    bot.add_cog(GuildNetworks(bot))
