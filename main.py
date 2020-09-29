#!/usr/bin/env python3

import os

from basedbot import DBot


# Find server prefix
def get_prefix(bot, message):
    if message.guild is None:
        return '!'

    return bot.conf.get(message.guild.id, 'prefix', '!')


bot = DBot(command_prefix=get_prefix)

# Load all modules
for cog in bot.find_all_cogs():
    try:
        bot.load_extension(cog)
    except Exception as e:
        print(f"Exception while loading `{cog}`:")
        print(f"{type(e).__name__}: {e}")

bot.run(os.environ['DBOT_TOKEN'])
