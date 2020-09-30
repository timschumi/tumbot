import asyncio

from discord.ext import commands
import discord


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def reactionroles(self, ctx):
        """Manages reactionroles"""
        await ctx.send_help(ctx.command)
        return

    @reactionroles.command()
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, role: discord.Role):
        """Creates a new reactionrole"""

        if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
            await ctx.send("Target role is higher than current highest role.", delete_after=60)
            return

        info_message = await ctx.send("React to a message with an emoji to finish the setup.")

        try:
            payload = await self.bot.wait_for('raw_reaction_add', check=lambda p: p.user_id == ctx.author.id, timeout=60)
        except asyncio.TimeoutError:
            await info_message.delete()
            await ctx.send("Operation timed out. Try clicking a bit faster next time!")
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)

        with self.bot.db.get(guild.id) as db:
            db.execute("INSERT INTO reactionroles(message, emoji, role) VALUES(?, ?, ?)",
                       (message.id, str(payload.emoji), role.id))

        await message.add_reaction(payload.emoji)
        await message.remove_reaction(payload.emoji, member)

        await info_message.delete()

    @reactionroles.command()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx):
        """Deletes a reactionrole"""

        info_message = await ctx.send("React to a message with an emoji to delete a reactionrole.", delete_after=60)

        try:
            payload = await self.bot.wait_for('raw_reaction_add', check=lambda p: p.user_id == ctx.author.id, timeout=60)
        except asyncio.TimeoutError:
            await info_message.delete()
            await ctx.send("Operation timed out. Try clicking a bit faster next time!")
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)

        with self.bot.db.get(guild.id) as db:
            db.execute("DELETE FROM reactionroles WHERE message = ? AND emoji = ?",
                       (message.id, str(payload.emoji)))

        await message.remove_reaction(payload.emoji, guild.me)
        await message.remove_reaction(payload.emoji, member)
        await info_message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)

        if member == guild.me:
            return

        with self.bot.db.get(guild.id) as db:
            result = db.execute("SELECT role FROM reactionroles WHERE message = ? AND emoji = ?",
                                (message.id, str(payload.emoji))).fetchall()

        if len(result) == 0:
            return

        for entry in result:
            role = discord.utils.get(guild.roles, id=int(entry[0]))
            if role in member.roles:
                await member.remove_roles(role)
            else:
                await member.add_roles(role)

        await message.remove_reaction(payload.emoji, member)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
