import functools
import logging
import typing

import discord
from discord.ext import commands


def _check_perm_exists(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, name, *args):
        if name not in self.bot.perm.registered_permission_names:
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


def _state_to_string(state):
    return 'Granted' if state else 'Denied'


def _sorted_defs(perm, guild):
    roleids = [role.id for role in reversed(guild.roles)]
    defs = perm.definitions(guild)
    sorted_defs = {}

    for discord_id, state in defs.items():
        # Skip role permissions on the first run
        if discord_id in roleids:
            continue

        sorted_defs[discord_id] = state

    # List remaining role permissions
    for discord_id in roleids:
        if discord_id not in defs:
            continue

        sorted_defs[discord_id] = defs[discord_id]

    return sorted_defs


def _perm_to_string(perm, guild):
    string = f"{perm.pretty_name}:"

    defs = _sorted_defs(perm, guild)

    for discord_id, state in defs.items():
        string += f"\n - {_state_to_string(state)} for {_id_to_string(guild, discord_id)}"

    if isinstance(perm.base, str):
        string += f"\n - Fallback permission: '{perm.base}'"
    else:
        string += f"\n - {'Granted' if perm.base is True else 'Denied'} by default"

    string += " (if none of the above rules match)"

    return string


class RoleConverterExt(commands.RoleConverter):
    # pylint: disable=too-few-public-methods
    """ Extends the RoleConverter to handle the 'everyone' role """

    async def convert(self, ctx, argument):
        # pylint: disable=missing-function-docstring
        if argument == 'everyone':
            return ctx.guild.get_role(ctx.guild.id)

        return await super().convert(ctx, argument)


class DBotPerm(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # pylint: disable=missing-function-docstring
        self.bot.loop.create_task(self._cleanup_invalid_entries())

    @commands.group(aliases=["pm", "permission", "permissions"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def perm(self, ctx):
        """ Bot permission management """

        await ctx.send_help(ctx.command)
        return

    @perm.command(name="list")
    @commands.has_permissions(administrator=True)
    async def perm_list(self, ctx):
        """ Lists all available permissions """

        entries = []

        for perm in sorted(self.bot.perm.registered_permissions, key=lambda p: p.name):
            entries.append({'name': perm.name, 'description': perm.pretty_name})

        if len(entries) == 0:
            await ctx.send("There aren't any registered permissions.")
            return

        await self.bot.send_table(ctx, ["name", "description"], entries)

    @perm.command(name="get", aliases=["show"])
    @commands.has_permissions(administrator=True)
    @_check_perm_exists
    async def perm_get(self, ctx, name):
        """ Retrieves information about a permission """

        perm = self.bot.perm.get(name)
        await ctx.send(f"```{_perm_to_string(perm, ctx.guild)}```")

    @perm.command(name="grant", aliases=["allow"])
    @commands.has_permissions(administrator=True)
    @_check_perm_exists
    async def perm_grant(self, ctx, permission,
                         target: typing.Union[RoleConverterExt, discord.Member]):
        """ Grants a permission to a user or role """

        perm = self.bot.perm.get(permission)
        perm.grant(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="deny", aliases=["disallow"])
    @commands.has_permissions(administrator=True)
    @_check_perm_exists
    async def perm_deny(self, ctx, permission,
                        target: typing.Union[RoleConverterExt, discord.Member]):
        """ Denies a permission to a user or role """

        perm = self.bot.perm.get(permission)
        perm.deny(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @perm.command(name="default", aliases=["reset"])
    @commands.has_permissions(administrator=True)
    @_check_perm_exists
    async def perm_default(self, ctx, permission,
                           target: typing.Union[RoleConverterExt, discord.Member]):
        """ Resets a permission to default for a user or role """

        perm = self.bot.perm.get(permission)
        perm.default(ctx.guild, target.id)

        await ctx.message.add_reaction('\U00002705')

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """ Removes dead permission entries when a user leaves """

        for perm in self.bot.perm.registered_permissions:
            perm.default(member.guild, member.id)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """ Removes dead permission entries when a role is deleted """

        for perm in self.bot.perm.registered_permissions:
            perm.default(role.guild, role.id)

    async def _cleanup_invalid_entries(self):
        """ Performs a sanity check of the database entries when the bot is ready """

        await self.bot.wait_until_ready()

        for perm in self.bot.perm.registered_permissions:
            for guild in self.bot.guilds:
                for entry in perm.definitions(guild):
                    # ID is a valid member?
                    if guild.get_member(entry):
                        continue

                    # ID is a valid role?
                    if guild.get_role(entry):
                        continue

                    logging.info("ID %s not found as member or role in guild %s, reset.", entry, guild)
                    perm.default(guild, entry)


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(DBotPerm(bot))
