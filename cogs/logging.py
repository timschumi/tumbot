from discord.ext import commands


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_logchannel(self, guild):
        return self.bot.conf.get(guild, 'logchannel')

    def set_logchannel(self, guild, logchannel):
        return self.bot.conf.set(guild, 'logchannel', logchannel)

    async def log_stuff(self, guild, message):
        logchannelid = self.get_logchannel(guild.id)
        if logchannelid is None:
            return
        logch = self.bot.get_channel(int(logchannelid))
        await logch.send(message)

    # LogChannel setzen
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, lchannelid):
        self.set_logchannel(ctx.guild.id, lchannelid)
        await ctx.channel.purge(limit=1)
        await ctx.send("Channel <#" + lchannelid + "> ist jetzt der Channel für den Log.")

    # Memberleave
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_stuff(member.guild, f":outbox_tray: **{member}** ({member.id}) hat den Server verlassen.")

    # Member wird gebannt
    @commands.Cog.listener()
    async def on_member_ban(self, _, member):
        await self.log_stuff(member.guild, f":no_entry_sign: **{member}** ({member.id}) wurde gebannt.")

    # Nachricht löschen
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = channel.get_message(payload.message_id)

        logchannelid = self.get_logchannel(guild.id)
        if logchannelid is None:
            return

        # Don't log if a bot's message has been deleted (unless it's from the log channel)
        if message.author.bot and str(logchannelid) != str(channel.id):
            return

        # Skip pretty presentation if we are deleting a log message from the log channel
        if message.author.bot and str(logchannelid) == str(channel.id):
            await self.log_stuff(guild, message.clean_content)
        else:
            await self.log_stuff(guild, f":recycle: Nachricht ({message.id}) von **{message.author}** ({message.author.id}) in Channel **{channel}** ({channel.id}) "
                f"gelöscht mit dem Inhalt:\n{message.clean_content}")


def setup(bot):
    bot.add_cog(Logging(bot))
