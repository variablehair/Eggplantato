import discord
from discord.ext import commands
import random
from cogs.utils import checks

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
	except (AttributeError, ImportError) as e:
		await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
		return
	await ctx.send("{} loaded.".format(ext_name))
	
@bot.command()
@checks.is_owner()
async def unload(ctx, ext_name : str):
	"""Unloads a cog"""
	bot.unload_extension(cogs_location + ext_name)
	await ctx.send("{} unloaded.".format(ext_name))
	
@bot.command(name='reload')
@checks.is_owner()
async def _reload(ctx, ext_name : str):
	"""Reloads a cog"""
	bot.unload_extension(cogs_location + ext_name)
	try:
		bot.load_extension(cogs_location + ext_name)
	except (AttributeError, ImportError) as e:
		await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
		return
	await ctx.send("{} reloaded successfully.".format(ext_name))
	
@bot.command(name="context")
async def send_context(ctx):
	await ctx.send(ctx.message.author.id)
	await ctx.send(str(ctx.message.author))
	
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

@bot.group()
async def cool(ctx):
	"""Says if a user is cool.

	In reality this just checks if a subcommand is being invoked.
	"""
	if ctx.invoked_subcommand is None:
		await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))

@cool.command(name='bot')
async def _bot(ctx):
	"""Is the bot cool?"""
	await ctx.send('Yes, the bot is cool.')

bot.run('Mjg2Nzk3NzU2Mjg1MzIxMjE3.C6PpLw.FrSoTKaTNci_bIhJivviwTpB4Dg')
