import discord
from discord.ext import commands
import random
from cogs.utils import checks, errors
import sqlite3
import os.path

description = '''Desu.'''
bot = commands.Bot(command_prefix='hey ep ', description=description)

#specifies the folder that contains the cogs
cogs_location = "cogs."

#specifies cogs to be loaded by default


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
	ctx.invoke(unload, ctx, ext_name)
	ctx.invoke(load, ctx, ext_name)
	await ctx.send("{} reloaded.".format(ext_name))
		
@bot.command()
async def add(ctx, left: int, right: int):
	"""Adds two numbers together."""
	await ctx.send(left + right)

@bot.command()
async def roll(ctx, dice: str):
	"""Rolls a dice in NdN format."""
	try:
		rolls, limit = map(int, dice.split('d'))
	except Exception:
		await ctx.send('Format has to be in NdN!')
		return

	result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
	await ctx.send(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
	"""Chooses between multiple choices."""
	await ctx.send(random.choice(choices))

@bot.command()
async def repeat(ctx, times: int, content='repeating...'):
	"""Repeats a message multiple times."""
	for i in range(times):
		await ctx.send(content)

@bot.command()
async def joined(ctx, member: discord.Member):
	"""Says when a member joined."""
	await ctx.send('{0.name} joined in {0.joined_at}'.format(member))

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

bot.run('Mjg2Nzk3NzU2Mjg1MzIxMjE3.C6PpLw.FrSoTKaTNci_bIhJivviwTpB4Dg')
