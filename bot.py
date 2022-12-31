import time
import discord
import asyncio

from balls.db import *
from error import print_e
from discord.ext import commands

client = commands.Bot(command_prefix=".", intents=discord.Intents.all(), case_insensitive=True)
client.remove_command("help")

@client.event
async def on_ready():
    print("r")
    await client.change_presence(activity=discord.Game(name="balls", timestamps={"start": time.time()}))
    await client.load_extension("balls.main")

@client.command(name="cog")
async def _cog(ctx, action, *cog):
    if ctx.author.id in how_the_fuck_should_i_name_this_list:
        if action == "load":
            send = "loaded "
            for i in cog:
                try:
                    await client.load_extension(i)
                    # await ctx.send(f"loaded {i.split('.')[1]}")
                    send += i.split(".")[1] + (", " if cog.index(i) < len(cog) - 1 else "")
                    print(f"loaded cog {i}")
                except Exception as e:
                    print_e(e) 
        elif action == "unload":
            send = "unloaded "
            for i in cog:
                try:
                    await client.unload_extension(i)
                    # await ctx.send(f"unloaded {cog.split('.')[1]}")
                    send += i.split(".")[1] + (", " if cog.index(i) < len(cog) - 1 else "")
                    print(f"unloaded cog {i}")
                except Exception as e:
                    print_e(e)
        elif action == "reload":
            send = "reloaded "
            for i in cog:
                try:
                    await client.unload_extension(i)
                    await asyncio.sleep(0.5)
                    await client.load_extension(i)
                    send += i.split(".")[1] + (", " if cog.index(i) < len(cog) - 1 else "")
                    print(f"reloaded cog {i}")
                except Exception as e:
                    print_e(e)
        else:
            print("?")
        await ctx.send(send)

@client.command()
async def db_clear(ctx):
    if ctx.author.id in how_the_fuck_should_i_name_this_list:
        clear_db()
        await ctx.reply("cleared database")

client.run("no.")