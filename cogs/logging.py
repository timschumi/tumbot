from discord.ext import commands

from basedbot import ConfigAccessLevel


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._var_channel = self.bot.conf.register('logging.channel', access=ConfigAccessLevel.ADMIN)

    async def log_stuff(self, guild, message):
        logchannelid = self._var_channel.get(guild.id)
        if logchannelid is None:
            return
        logch = self.bot.get_channel(int(logchannelid))
        await logch.send(message)

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

        if not payload.cached_message:
            await self.log_stuff(guild, f":recycle: Nachricht ({payload.message_id}) in Channel **{channel}** "
                                        f"({channel.id}) gelöscht, aber nicht mehr im Cache gespeichert.")
            return

        message = payload.cached_message

        logchannelid = self._var_channel.get(guild.id)
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
