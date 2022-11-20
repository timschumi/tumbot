import asyncio
import logging
import os
from pathlib import Path

import discord.ext.commands

from .dbmgr import DatabaseManager
from .confmgr import ConfigManager
from .permmgr import PermissionManager


class DBot(discord.ext.commands.Bot):
    """Bot extension for the basedbot framework"""

    def __init__(self, **options):
        if "command_prefix" not in options:
            options["command_prefix"] = DBot.fetch_prefix

        super().__init__(**options)
        self.db = DatabaseManager(os.environ.get("DBOT_DBPATH", "db"))
        self.conf = ConfigManager(self.db)
        self.perm = PermissionManager(self.db)
        self._cogpaths = ["basedbot/cogs"]
        self.conf.register(
            "prefix",
            default="!",
            conv=str,
            description="The command prefix that the bot reacts to.",
        )
        self._var_prefix = self.conf.var("prefix")

    async def close(self):
        """Shuts down the bot"""

        await super().close()
        self.db.close()

    async def send_paginated(
        self,
        msg: discord.abc.Messageable,
        lines,
        linefmt="{}\n",
        textfmt="{}",
        maxlen=2000,
    ):
        """Sends the given list of strings in chunks, up to a maximum message length"""

        linefmt_len = len(linefmt.format(""))
        textfmt_len = len(textfmt.format(""))

        text = ""

        for line in lines:
            if len(text) + textfmt_len + len(line) + linefmt_len >= maxlen:
                await msg.send(textfmt.format(text))
                text = ""

            text += linefmt.format(line)

        if len(text) > 0:
            await msg.send(textfmt.format(text))

        return

    async def send_table(self, messageable: discord.abc.Messageable, keys, table):
        """Sends an ASCII-table with the given keys and contents"""

        key_length = {}

        for row in table:
            for key in keys:
                if key not in key_length:
                    key_length[key] = len(str(key))

                key_length[key] = max(key_length[key], len(str(row[key])))

        header = "|"
        delimiter = "|"

        for i in keys:
            header += f" {str(i).ljust(key_length[i])} |"
            delimiter += "-" * (key_length[i] + 2) + "|"

        lines = [header, delimiter]

        for row in table:
            line = "|"
            for key in keys:
                line += f" {str(row[key]).ljust(key_length[key])} |"

            lines.append(line)

        await self.send_paginated(messageable, lines, textfmt="```{}```")

    def add_cog_path(self, path):
        """Adds a new entry to the list of cog search paths"""

        self._cogpaths.append(path)

    def find_cog(self, name):
        """Finds a cog with the given name in the search path"""

        name = name.lower()

        for path in self._cogpaths:
            if os.path.isfile(f"{path}/{name}.py"):
                return f"{path.replace('/', '.')}.{name}"

        return None

    def find_all_cogs(self):
        """Lists all the cogs present in the search path"""

        cogs = []

        for cogpath in self._cogpaths:
            for path in Path(cogpath).glob("*.py"):
                cogs.append(".".join(path.parent.parts + (path.stem,)))

        return cogs

    def fetch_prefix(self, message):
        """Find the set prefix for a server"""

        if message.guild is None:
            return "!"

        return self._var_prefix.get(message.guild.id)

    async def wait_until_ready(self) -> None:
        """Waits until the client's internal cache is all ready."""

        await super().wait_until_ready()

        # Wait until the bot has received member data from all guilds.
        while True:
            for g in self.guilds:
                if not g.me:
                    break
            else:
                break

            logging.info("Found guild %s with uninitialized bot data, waiting...", g)
            await asyncio.sleep(1)
