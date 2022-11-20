import asyncio
import functools

from discord.ext import commands
import discord


async def _decode_raw_reaction(bot, payload: discord.RawReactionActionEvent):
    # Fetch all the information
    guild = bot.get_guild(payload.guild_id)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = guild.get_member(payload.user_id)

    # Construct reaction
    reaction = discord.Reaction(
        message=message, data={"me": member == guild.me}, emoji=payload.emoji
    )

    return reaction, member


def _decode_reaction(func):
    @functools.wraps(func)
    async def wrapper(self, payload: discord.RawReactionActionEvent):
        # Ignore private messages
        if payload.guild_id is None:
            return

        # Ignore own reactions
        if payload.user_id == self.bot.user.id:
            return

        reaction, member = await _decode_raw_reaction(self.bot, payload)
        return await func(self, reaction, member)

    return wrapper


async def _wait_for_user_reaction(bot, user, timeout=60):
    payload = await bot.wait_for(
        "raw_reaction_add", check=lambda p: p.user_id == user.id, timeout=timeout
    )
    return await _decode_raw_reaction(bot, payload)


class ReactionRoles(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def reactionroles(self, ctx):
        """Manages reactionroles"""
        await ctx.send_help(ctx.command)
        return

    @reactionroles.command(aliases=["append"])
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, role: discord.Role):
        """Creates a new reactionrole"""

        if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
            await ctx.send(
                "Target role is higher than current highest role.", delete_after=60
            )
            return

        if ctx.guild.me.top_role <= role:
            await ctx.send(
                "Target role is higher than the bots current highest role.",
                delete_after=60,
            )
            return
        info_message = await ctx.send(
            "React to a message with an emoji to finish the setup."
        )

        try:
            reaction, member = await _wait_for_user_reaction(
                self.bot, ctx.author, timeout=60
            )
        finally:
            await info_message.delete()

        message = reaction.message
        guild = message.guild

        with self.bot.db.get(guild.id) as db:
            result = db.execute(
                "SELECT * FROM reactionroles WHERE message == ? AND emoji == ? AND role = ?",
                (message.id, str(reaction.emoji), role.id),
            ).fetchall()
            if len(result) > 0:
                await ctx.send(
                    "Hey you already added that emoji to that message and that Role!"
                )
                return
            db.execute(
                "INSERT INTO reactionroles(message, emoji, role) VALUES(?, ?, ?)",
                (message.id, str(reaction.emoji), role.id),
            )

        await message.add_reaction(reaction.emoji)
        await reaction.remove(member)

    @reactionroles.command(aliases=["remove"])
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx):
        """Deletes a reactionrole"""

        info_message = await ctx.send(
            "React to a message with an emoji to delete a reactionrole."
        )

        try:
            reaction, member = await _wait_for_user_reaction(
                self.bot, ctx.author, timeout=60
            )
        finally:
            await info_message.delete()

        message = reaction.message
        guild = message.guild

        with self.bot.db.get(guild.id) as db:
            db.execute(
                "DELETE FROM reactionroles WHERE message = ? AND emoji = ?",
                (message.id, str(reaction.emoji)),
            )

        await reaction.remove(guild.me)
        await reaction.remove(member)

    @commands.Cog.listener(name="on_raw_reaction_add")
    @_decode_reaction
    async def on_reaction_add(self, reaction, member):
        """Listens for new reactions and distributes the matching roles"""

        if reaction.me:
            return

        message = reaction.message
        guild = message.guild

        with self.bot.db.get(guild.id) as db:
            result = db.execute(
                "SELECT DISTINCT role FROM reactionroles WHERE message = ? AND emoji = ?",
                (message.id, str(reaction.emoji)),
            ).fetchall()

        if len(result) == 0:
            return

        for entry in result:
            role = discord.utils.get(guild.roles, id=int(entry[0]))
            if role in member.roles:
                await member.remove_roles(role)
            else:
                await member.add_roles(role)

        await reaction.remove(member)

    @add.error
    @delete.error
    async def handle_error(self, ctx, error):
        """Prints a nice message when the user is too slow"""

        original = getattr(error, "original", error)

        if isinstance(original, asyncio.TimeoutError):
            await ctx.send("Operation timed out. Try clicking a bit faster next time!")
            return

        # Defer to common error handler
        errhandler = self.bot.get_cog("ErrorHandler")

        if errhandler is not None:
            await errhandler.on_command_error(ctx, error, force=True)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Remove reaction roles on messages that no longer exist"""

        if not payload.guild_id:
            return

        with self.bot.db.get(payload.guild_id) as db:
            db.execute(
                "DELETE FROM reactionroles WHERE message = ?", (payload.message_id,)
            )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Remove reaction roles on roles that no longer exist"""

        with self.bot.db.get(role.guild.id) as db:
            db.execute("DELETE FROM reactionroles WHERE role = ?", (role.id,))


async def setup(bot):
    # pylint: disable=missing-function-docstring
    await bot.add_cog(ReactionRoles(bot))
