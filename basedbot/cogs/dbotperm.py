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


def _id_to_string(guild, discord_id):
    if discord_id == guild.id:
        return "@everyone"

    role = guild.get_role(discord_id)

    if role is not None:
        return f"@{role.name}"

    member = guild.get_member(discord_id)

    if member is not None:
        return f"{member}"

    return f"@{discord_id}"


def _perm_to_string(perm, guild):
    roleids = [role.id for role in reversed(guild.roles)]
    string = f"{perm.pretty_name}:"

    defs = perm.definitions(guild)

    # List user permissions
    for discord_id, state in defs.items():
        if discord_id in roleids:
            continue

        string += f"\n - {'Granted' if state else 'Denied'} for {_id_to_string(guild, discord_id)}"

    # List role permissions (in order)
    for discord_id in roleids:
        if discord_id not in defs:
            continue

        string += f"\n - {'Granted' if defs[discord_id] else 'Denied'} for {_id_to_string(guild, discord_id)}"

    if isinstance(perm.base, str):
        string += f"\n - Fallback permission: '{perm.base}'"
    else:
        string += f"\n - {'Granted' if perm.base is True else 'Denied'} by default"

    string += " (if none of the above rules match)"

    return string


class RoleConverterExt(commands.RoleConverter):
    # pylint: disable=too-few-public-methods
    async def convert(self, ctx, argument):
        if argument == 'everyone':
            return ctx.guild.get_role(ctx.guild.id)

        return await super().convert(ctx, argument)


class DBotPerm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["pm", "permission", "permissions"], invoke_without_command=True)
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

    @perm.command(name="get", aliases=["show"])
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_get(self, ctx, name):
        """Retrieves information about a permission"""

        perm = self.bot.perm.get(name)
        await ctx.send(f"```{_perm_to_string(perm, ctx.guild)}```")

    @perm.command(name="grant", aliases=["allow"])
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_grant(self, ctx, permission,
                         target: typing.Union[RoleConverterExt, discord.Member]):
        """Grants a permission to a user or role"""

        perm = self.bot.perm.get(permission)
        perm.grant(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="deny", aliases=["disallow"])
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_deny(self, ctx, permission,
                        target: typing.Union[RoleConverterExt, discord.Member]):
        """Denies a permission to a user or role"""

        perm = self.bot.perm.get(permission)
        perm.deny(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="default", aliases=["reset"])
    @commands.has_permissions(administrator=True)
    @check_perm_exists
    async def perm_default(self, ctx, permission,
                           target: typing.Union[RoleConverterExt, discord.Member]):
        """Resets a permission to default for a user or role"""

        perm = self.bot.perm.get(permission)
        perm.default(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')


def setup(bot):
    bot.add_cog(DBotPerm(bot))
