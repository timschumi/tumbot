#!/usr/bin/env python3.7

import os
import discord
import logging
from subprocess import call
from bot import Bot
from dbmgr import DbMgr
from discord.ext import commands

db = DbMgr()


# Finde den Prefix eines Servers
def get_prefix(bot, message):
    if message.guild is None:
        return '!'

    return bot.dbconf_get(message.guild.id, 'prefix', '!')


bot = Bot(db, command_prefix=get_prefix)


# Bot herunterfahren
@bot.command()
@commands.is_owner()
async def shutdown(ctx):
    await ctx.message.add_reaction('\U00002705')
    await bot.logout()


# Bot updaten
@bot.command()
@commands.is_owner()
async def update(ctx):
    if call(["git", "pull", "origin", "master"]) == 0:
        await ctx.message.add_reaction('\U00002705')
    else:
        await ctx.message.add_reaction('\U0001F525')


@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Meine Latenz sind aktuell {round(bot.latency * 1000)} ms.')


# Modul laden
@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    e = extension.lower()
    bot.load_extension(f'cogs.{e}')
    await ctx.message.add_reaction('\U00002705')
    print(e + ' aktiviert')


# Modul deaktivieren
@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    e = extension.lower()
    bot.unload_extension(f'cogs.{e}')
    print(e + ' deaktiviert')
    await ctx.message.add_reaction('\U00002705')


# Modul neuladen
@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    e = extension.lower()
    bot.reload_extension(f'cogs.{e}')
    print(e + ' neugeladen')
    await ctx.message.add_reaction('\U00002705')


# Beim start alle module laden die nicht mit test starten
for filename in os.listdir('./cogs'):
    if filename.endswith(".py"):
        if filename.startswith('test'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception:
                print(F'{filename}' + ' ist fehlerhaft')
        else:
            if filename.endswith('.py'):
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(filename[:-3] + ' aktiviert')
            elif filename.endswith('__pycache__'):
                print('Py-Cache gefunden')
            else:
                print(F'{filename}' + ' ist fehlerhaft')
    else:
        pass

bot.run(os.environ['TUMBOT_TOKEN'])
