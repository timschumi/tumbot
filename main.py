#!/usr/bin/env python3

import os

from discord import Intents
from basedbot import DBot


# Find server prefix
def get_prefix(bot, message):
    if message.guild is None:
        return '!'

    return bot.conf.get(message.guild.id, 'prefix')


bot = DBot(command_prefix=get_prefix, intents=Intents.all())
bot.conf.register('prefix', default='!', description="The command prefix that the bot reacts to.", conv=str)

bot.add_cog_path('cogs')
bot.add_cog_path('cogs/legacy')

bot.db.add_sql_path('sql/guild', scope='guild')

# Load all modules
for cog in bot.find_all_cogs():
    try:
        bot.load_extension(cog)
    except Exception as e:
        print(f"Exception while loading `{cog}`:")
        print(f"{type(e).__name__}: {e}")

bot.run(os.environ['DBOT_TOKEN'])
