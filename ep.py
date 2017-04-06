import discord
from discord.ext import commands
import random
from cogs.utils import checks, errors
import sqlite3
import os.path
from defaults import ep_token

description = '''Desu.'''
bot = commands.Bot(command_prefix='hey ep ', description=description)
cogs_location = "cogs."

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	
@bot.command()
@checks.is_owner()
async def load(ctx, ext_name : str):
	"""Loads a cog"""
	try:
		bot.load_extension(cogs_location + ext_name)
	except errors.DatabaseError as e:
		await ctx.send(str(e))
	except (AttributeError, ImportError) as e:
		await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
		return
	if ctx.invoked_with != "reload":
		await ctx.send("{} loaded.".format(ext_name))
	
@bot.command()
@checks.is_owner()
async def unload(ctx, ext_name : str):
	"""Unloads a cog"""
	bot.unload_extension(cogs_location + ext_name)
	if ctx.invoked_with != "reload":
		await ctx.send("{} unloaded.".format(ext_name))
	
@bot.command(name='reload')
@checks.is_owner()
async def _reload(ctx, ext_name : str):
	"""Reloads a cog"""
	await ctx.invoke(unload, ext_name)
	await ctx.invoke(load, ext_name)
	await ctx.send("{} reloaded.".format(ext_name))
		
@bot.command()
@checks.is_owner()
async def add(ctx, left: int, right: int):
	"""Adds two numbers together."""
	await ctx.send(left + right)

@bot.command()
@checks.is_owner()
async def initdb(ctx):
	"""Initialize all database objects for the bot. #TODO: make the function take subcommands so only certain cogs are initialized rather than all of them."""
	#create todo list
	if os.path.exists("data/todo.db"):
		await ctx.send('Todo database already exists at \"data/todo.db\"!')
	else:
		conn = sqlite3.connect('data/todo.db')
		c = conn.cursor()
		c.execute("CREATE TABLE lists (user TEXT, tasks TEXT)")
		c.execute("INSERT INTO lists VALUES ('debug', '[]')")
		conn.commit()
		conn.close()
		await ctx.send('Todo database created successfully.')

bot.run(ep_token)
