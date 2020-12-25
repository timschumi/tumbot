import functools
import typing

import discord
from discord.ext import commands


def check_perm_exists(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, name, *args):
        if name not in self.bot.perm.registered_permissions:
            await ctx.send(f"Permission **{name}** does not exist.")
            return

        await func(self, ctx, name, *args)

    return wrapper


def _id_to_string(guild, id):
    if id == guild.id:
        return "@everyone"

    role = guild.get_role(id)

    if role is not None:
        return f"@{role.name}"

    member = guild.get_member(id)

    if member is not None:
        return f"{member}"

    return f"@{id}"


def _perm_to_string(perm, guild):
    roleids = [role.id for role in reversed(guild.roles)]
    string = f"{perm.pretty_name}:"

    defs = perm.definitions(guild)

    # List user permissions
    for id, state in defs.items():
        if id in roleids:
            continue

        string += f"\n - {'Granted' if state else 'Denied'} for {_id_to_string(guild, id)}"

    # List role permissions (in order)
    for id in roleids:
        if id not in defs:
            continue

        string += f"\n - {'Granted' if defs[id] else 'Denied'} for {_id_to_string(guild, id)}"

    if perm.base is not None:
        string += f"\n - Fallback: {perm.base} (if none of the above rules match)"

    return string


class DBotPerm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def perm(self, ctx):
        """Manages the bot-specific permissions"""

        await ctx.send_help(ctx.command)
        return

    @perm.command(name="list")
    @commands.has_permissions(administrator=True)
    async def perm_list(self, ctx):
        """Lists all available permissions"""

        entries = []

        for permname in sorted(self.bot.perm.registered_permissions):
            perm = self.bot.perm.get(permname)
            entries.append({'name': perm.name, 'description': perm.pretty_name})

        if len(entries) == 0:
            await ctx.send("There aren't any registered permissions.")
            return

        await self.bot.send_table(ctx, ["name", "description"], entries)

    @perm.command(name="get")
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_get(self, ctx, name):
        """Retrieves information about a permission"""

        perm = self.bot.perm.get(name)
        await ctx.send(f"```{_perm_to_string(perm, ctx.guild)}```")

    @perm.command(name="grant")
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_grant(self, ctx, permission, target: typing.Union[discord.Role, discord.Member]):
        """Grants a permission to a user or role"""

        perm = self.bot.perm.get(permission)
        perm.grant(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="deny")
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_deny(self, ctx, permission, target: typing.Union[discord.Role, discord.Member]):
        """Denies a permission to a user or role"""

        perm = self.bot.perm.get(permission)
        perm.deny(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="default")
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_default(self, ctx, permission, target: typing.Union[discord.Role, discord.Member]):
        """Resets a permission to default for a user or role"""

        perm = self.bot.perm.get(permission)
        perm.default(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')


def setup(bot):
    bot.add_cog(DBotPerm(bot))
