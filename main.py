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


# Botowner für Permissions zu manchen Commands
def botowner(ctx):
    if ctx.author.id == 296323983819669514 or ctx.author.id == 137291894953607168:
        return True
    else:
        return False


# Bot herunterfahren
@bot.command()
@commands.check(botowner)
async def shutdown(ctx):
    await ctx.channel.purge(limit=1)
    await ctx.send("Bot wird heruntergefahren...")
    await _shutdown(ctx)

async def _shutdown(ctx):
    await bot.logout()

# Bot updaten
@bot.command()
@commands.check(botowner)
async def update(ctx):
    await ctx.channel.purge(limit=1)
    await ctx.send("Bot wird aktualisiert...")
    call(["git", "pull", "origin", "master"])

    await _shutdown(ctx)
    os.execv(__file__, sys.argv)

@bot.command()
async def ping(ctx):
    await ctx.channel.purge(limit=1)
    await ctx.send(f'Pong! Meine Latenz sind aktuell {round(bot.latency * 1000)} ms.')


# Modul laden
@bot.command()
@commands.check(botowner)
async def load(ctx, extension):
    await ctx.channel.purge(limit=1)
    e = extension.lower()
    bot.load_extension(f'cogs.{e}')
    await ctx.send(e + "aktiviert")
    print(e + ' aktiviert')


# Modul deaktivieren
@bot.command()
@commands.check(botowner)
async def unload(ctx, extension):
    await ctx.channel.purge(limit=1)
    e = extension.lower()
    bot.unload_extension(f'cogs.{e}')
    print(e + ' deaktiviert')
    await ctx.send(e + ' deaktiviert')


# Modul neuladen
@bot.command()
@commands.check(botowner)
async def reload(ctx, extension):
    await ctx.channel.purge(limit=1)
    e = extension.lower()
    bot.reload_extension(f'cogs.{e}')
    print(e + ' neugeladen')
    await ctx.send(e + ' neugeladen')


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
