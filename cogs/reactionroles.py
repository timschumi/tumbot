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

        self.active[ctx.author.id] = role.id
        await ctx.send("React to a message with an emoji to finish the setup.", delete_after=60)

    @rr.command()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx):
        """Deletes a reactionrole"""

        self.active[ctx.author.id] = None
        await ctx.send("React to a message with an emoji to delete a reactionrole.", delete_after=60)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        print("Added reaction: {} {}".format(reaction, user))
        guild = reaction.message.guild

        if user.id in self.active:
            print("User in list")
            if self.active[user.id] is None:
                with self.bot.db.get(guild.id) as db:
                    db.execute("DELETE FROM reactionroles WHERE message = ? AND emoji = ?",
                               (reaction.message.id, reaction.emoji))
                await reaction.remove(guild.me)
            else:
                with self.bot.db.get(guild.id) as db:
                    db.execute("INSERT INTO reactionroles(message, emoji, role) VALUES(?, ?, ?)",
                               (reaction.message.id, reaction.emoji, self.active[user.id]))
                await reaction.message.add_reaction(reaction)

            await reaction.remove(user)
            self.active.pop(user.id)
            return

        with self.bot.db.get(guild.id) as db:
            result = db.execute("SELECT role FROM reactionroles WHERE message = ? AND emoji = ?",
                                (reaction.message.id, reaction.emoji)).fetchall()

        if len(result) == 0:
            return

        member = guild.get_member(user.id)

        for entry in result:
            role = discord.utils.get(guild.roles, id=entry[0])
            await member.add_roles(role)

        await reaction.remove(user)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
