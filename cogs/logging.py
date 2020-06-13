from discord.ext import commands


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_logchannel(self, guild):
        return self.bot.dbconf_get(guild, 'logchannel')

    def set_logchannel(self, guild, logchannel):
        return self.bot.dbconf_set(guild, 'logchannel', logchannel)

    # LogChannel setzen
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, lchannelid):
        self.set_logchannel(ctx.guild.id, lchannelid)
        await ctx.channel.purge(limit=1)
        await ctx.send("Channel <#" + lchannelid + "> ist jetzt der Channel für den Log.")

    # Memberjoin
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            if member.bot:
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                await logch.send(
                    ":inbox_tray: **" + str(member) + "(" + str(member.id) + ")** ist dem Sever beigetreten.")
            else:
                pass
        except Exception:
            pass

    # Memberleave
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            if member.bot:
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                await logch.send(
                    ":outbox_tray: **" + str(member) + " (" + str(member.id) + ")** hat den Server verlassen.")
            else:
                pass
        except Exception:
            pass

    # Member wird gebannt
    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        try:
            if not member.bot:
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                await logch.send(":no_entry_sign: **" + str(member) + " (" + str(member.id) + ")** wurde gebannt.")
            else:
                pass
        except Exception:
            pass

    # Member wird entbannt
    @commands.Cog.listener()
    async def on_member_unban(self, guild, member):
        try:
            if not member.bot:
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                await logch.send(
                    ":white_check_mark: **" + str(member) + " (" + str(member.id) + ")** wurde entgebannt.")
            else:
                pass
        except Exception:
            pass

    # Nachricht löschen
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        try:
            if payload.guild_id is not None:
                ch = payload.channel_id
                guild = payload.guild_id
                msg = payload.message_id
                content = payload.cached_message.clean_content
                member = payload.cached_message.author
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                await logch.send(':recycle: **Nachricht:** "' + str(content) + '" von User: ' + str(member) + ' (' +
                                 str(member.id) + ") gelöscht.")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            guild = member.guild
            if not member.bot:
                logchannelid = self.get_logchannel(member.guild.id)
                if logchannelid is None:
                    return
                logch = self.bot.get_channel(int(logchannelid))
                if before.channel is None:
                    await logch.send(
                        ":mega: **" + str(member) + " (" + str(member.id) + ")** hat den Voice Channel **" +
                        str(after.channel) + "** betreten.")
                elif before.channel is not None and after.channel is None:
                    await logch.send(
                        ":mega: **" + str(member) + " (" + str(member.id) + ")** hat den Voice Channel **" +
                        str(before.channel) + "** verlassen.")
                elif before.channel is not None and after.channel is not None:
                    await logch.send(
                        ":mega: **" + str(member) + " (" + str(member.id) + ")** hat den Voice Channel von **" +
                        str(before.channel) + "** zu **" + str(after.channel) + "** gewechselt.")
            else:
                pass
        except Exception:
            pass


def setup(bot):
    bot.add_cog(Logging(bot))
