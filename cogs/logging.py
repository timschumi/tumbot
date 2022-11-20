from typing import Optional

from datetime import datetime
import discord
from discord.ext import commands


class Logging(commands.Cog):
    # pylint: disable=missing-class-docstring

    def __init__(self, bot):
        self.bot = bot
        self._var_channel = self.bot.conf.var("logging.channel")
        self._var_ignore_deleted_messages = self.bot.conf.var(
            "logging.ignore_deleted_messages"
        )
        self._var_clear_deleted_messages = self.bot.conf.var(
            "logging.clear_deleted_messages"
        )

    async def _log_stuff(self, guild, message, delete_after=None):
        logchannelid = self._var_channel.get(guild.id)
        if logchannelid is None:
            return
        logch = self.bot.get_channel(int(logchannelid))
        await logch.send(message, delete_after=delete_after)

    # Memberleave
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Logs leaving guild members"""

        await self._log_stuff(
            member.guild,
            f":outbox_tray: **{member}** ({member.id}) hat den Server verlassen.",
        )

    # Member wird gebannt
    @commands.Cog.listener()
    async def on_member_ban(self, _, member):
        """Logs banned guild members"""

        await self._log_stuff(
            member.guild, f":no_entry_sign: **{member}** ({member.id}) wurde gebannt."
        )

    # Nachricht löschen
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Logs deleted messages (if enabled)"""

        if payload.guild_id is None:
            return

        if self._var_ignore_deleted_messages.get(payload.guild_id):
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)

        if not payload.cached_message:
            await self._log_stuff(
                guild,
                f":recycle: Nachricht ({payload.message_id}) in Channel **{channel}** "
                f"({channel.id}) gelöscht, aber nicht mehr im Cache gespeichert.",
            )
            return

        message = payload.cached_message

        logchannelid = self._var_channel.get(guild.id)
        if logchannelid is None:
            return

        # Don't log if a bot's message has been deleted (unless it's from the log channel)
        if message.author.bot and str(logchannelid) != str(channel.id):
            return

        delete_after = self._var_clear_deleted_messages.get(guild.id)

        if delete_after:
            delete_after = int(delete_after)

        # Skip pretty presentation if we are deleting a log message from the log channel
        if message.author.bot and str(logchannelid) == str(channel.id):
            if (
                delete_after
                and (datetime.utcnow() - message.created_at).total_seconds()
                >= delete_after
            ):
                return

            await self._log_stuff(
                guild, message.clean_content, delete_after=delete_after
            )
        else:
            await self._log_stuff(
                guild,
                f":recycle: Nachricht ({message.id}) von "
                f"**{message.author}** ({message.author.id}) in Channel "
                f"**{channel}** ({channel.id}) gelöscht mit dem Inhalt:\n"
                f"{message.clean_content}",
                delete_after=delete_after,
            )


async def setup(bot):
    # pylint: disable=missing-function-docstring
    bot.conf.register(
        "logging.channel",
        conv=Optional[discord.TextChannel],
        description="The channel where various activities are logged.",
    )
    bot.conf.register(
        "logging.ignore_deleted_messages",
        conv=bool,
        default=False,
        description="If true, disables logging deleted messages.",
    )
    bot.conf.register(
        "logging.clear_deleted_messages",
        conv=Optional[int],
        description="The number of seconds until deleted messages are removed from the log.",
    )
    await bot.add_cog(Logging(bot))
