import os
from pathlib import Path

import discord.ext.commands

from .dbmgr import DatabaseManager
from .confmgr import ConfigManager


class DBot(discord.ext.commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        self.db = DatabaseManager(os.environ.get('DBOT_DBPATH', "db"))
        self.conf = ConfigManager(self.db)
        self._cogpaths = ['basedbot/cogs']

    async def close(self):
        await super().close()
        self.db.close()

    async def send_paginated(self, msg: discord.abc.Messageable, lines, linefmt="{}\n", textfmt="{}", maxlen=2000):
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
            delimiter += '-' * (key_length[i] + 2) + '|'

        lines = [header, delimiter]

        for row in table:
            line = "|"
            for key in keys:
                line += f" {str(row[key]).ljust(key_length[key])} |"

            lines.append(line)

        await self.send_paginated(messageable, lines, textfmt="```{}```")

    def add_cog_path(self, path):
        self._cogpaths.append(path)

    def find_cog(self, name):
        name = name.lower()

        for path in self._cogpaths:
            if os.path.isfile(f"{path}/{name}.py"):
                return f"{path.replace('/', '.')}.{name}"

        return None

    def find_all_cogs(self):
        cogs = []

        for cogpath in self._cogpaths:
            for path in Path(cogpath).glob('*.py'):
                cogs.append('.'.join(path.parent.parts + (path.stem,)))

        return cogs
