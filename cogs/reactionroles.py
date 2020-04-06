from discord.ext import commands
import discord


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = {}

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rr(self, ctx):
        """Manages reactionroles"""
        pass

    @rr.command()
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx, role: discord.Role):
        """Creates a new reactionrole"""

        # Fallback if role can't be mentioned: Search by name
        if not isinstance(role, discord.Role):
            role = discord.utils.get(ctx.guild.roles, name=role)

        if role is None:
            await ctx.send("Could not resolve role.", delete_after=60)
            return

        if ctx.author.top_role <= role:
            await ctx.send("Target role is higher than current highest role.", delete_after=60)
            return

        self.active[ctx.author.id] = role.id
        await ctx.send("React to a message with an emoji to finish the setup.", delete_after=60)

    @rr.command()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx):
        """Deletes a reactionrole"""

        self.active[ctx.author.id] = None
        await ctx.send("React to a message with an emoji to delete a reactionrole.", delete_after=60)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = guild.get_member(payload.user_id)

        if member == guild.me:
            return

        if member.id in self.active:
            if self.active[member.id] is None:
                with self.bot.db.get(guild.id) as db:
                    db.execute("DELETE FROM reactionroles WHERE message = ? AND emoji = ?",
                               (message.id, str(payload.emoji)))
                await message.remove_reaction(payload.emoji, guild.me)
            else:
                with self.bot.db.get(guild.id) as db:
                    db.execute("INSERT INTO reactionroles(message, emoji, role) VALUES(?, ?, ?)",
                               (message.id, str(payload.emoji), self.active[member.id]))
                await message.add_reaction(payload.emoji)

            await message.remove_reaction(payload.emoji, member)
            self.active.pop(member.id)
            return

        with self.bot.db.get(guild.id) as db:
            result = db.execute("SELECT role FROM reactionroles WHERE message = ? AND emoji = ?",
                                (message.id, str(payload.emoji))).fetchall()

        if len(result) == 0:
            return

        for entry in result:
            role = discord.utils.get(guild.roles, id=int(entry[0]))
            await member.add_roles(role)

        await message.remove_reaction(payload.emoji, member)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
