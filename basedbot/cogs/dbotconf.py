import functools

from discord.ext import commands

from basedbot import ConfigAccessLevel
from basedbot.converter import InvalidConversionException


def _is_admin(member):
    return member.guild_permissions.administrator


def _is_owner(member):
    return member.guild.owner == member


def _has_access_to_var(member, var):
    if var.access == ConfigAccessLevel.INTERNAL:
        return False

    if _is_admin(member) and var.access == ConfigAccessLevel.ADMIN:
        return True

    if _is_owner(member) and var.access == ConfigAccessLevel.OWNER:
        return True

    return False


async def _var_value_to_string(ctx, var):
    try:
        return await var.show(ctx)
    except InvalidConversionException:
        return "<conversion error>"


async def _var_to_string(ctx, var):
    string = f"{var.name} = {await _var_value_to_string(ctx, var)}"
    string += f" ({var.conv.name()}, def. {await var.conv.show(ctx, var.default)})"

    if var.description is not None:
        string += f"\n - {var.description}"

    return string


def _check_var_exists(func):
    @functools.wraps(func)
    async def wrapper(self, ctx, name, *args):
        if name not in self.bot.conf.registered_variables:
            await ctx.send(f"Variable **{name}** does not exist.")
            return

        await func(self, ctx, name, *args)

    return wrapper


def _check_var_access(func):
    @functools.wraps(func)
    @_check_var_exists
    async def wrapper(self, ctx, name, *args):
        var = self.bot.conf.var(name)

        if not _has_access_to_var(ctx.author, var):
            await ctx.send(f"You don't have access to the variable **{name}**.")
            return

        await func(self, ctx, name, *args)

    return wrapper


class DBotConf(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def conf(self, ctx):
        """Bot configuration variable management"""

        await ctx.send_help(ctx.command)
        return

    @conf.command(name="list")
    @commands.has_permissions(administrator=True)
    async def conf_list(self, ctx):
        """Lists all available configuration variables"""

        entries = []

        for varname in sorted(self.bot.conf.registered_variables):
            var = self.bot.conf.var(varname)

            # Skip if we don't have access
            if not _has_access_to_var(ctx.author, var):
                continue

            entry = {"name": var.name, "value": await _var_value_to_string(ctx, var)}

            entries.append(entry)

        if len(entries) == 0:
            await ctx.send("You don't have access to any variables.")
            return

        await self.bot.send_table(ctx, ["name", "value"], entries)

    @conf.command(name="get")
    @commands.has_permissions(administrator=True)
    @_check_var_exists
    async def conf_get(self, ctx, name):
        """Retrieves a single configuration variable"""

        var = self.bot.conf.var(name)
        await ctx.send(f"```{await _var_to_string(ctx, var)}```")

    @conf.command(name="set")
    @commands.has_permissions(administrator=True)
    @_check_var_access
    async def conf_set(self, ctx, name, value):
        """Sets the value of a specific configuration variable"""

        var = self.bot.conf.var(name)

        try:
            await var.cset(ctx, value)
        except InvalidConversionException as e:
            await ctx.send(f"```{e}```")
            return

        await ctx.message.add_reaction("\U00002705")

    @conf.command(name="unset")
    @commands.has_permissions(administrator=True)
    @_check_var_access
    async def conf_unset(self, ctx, name):
        """Resets a configuration variable to its default"""

        var = self.bot.conf.var(name)
        var.unset(ctx.guild.id)

        await ctx.message.add_reaction("\U00002705")


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(DBotConf(bot))
