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

    async def send_table(self, messageable: discord.abc.Messageable, keys, table, maxlen=2000):
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

        text = header + "\n" + delimiter

        for row in table:
            line = "\n|"
            for key in keys:
                line += f" {str(row[key]).ljust(key_length[key])} |"

            # -6: Account for code block
            if len(text) + len(line) >= maxlen - 6:
                await messageable.send(f"```{text}```")
                text = ""

            text += line

        await messageable.send(f"```{text}```")

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
