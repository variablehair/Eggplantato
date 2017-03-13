import discord
from discord.ext import commands
import random

description = '''Eggplantato is Eggplantato. Desu desu.'''
bot = commands.Bot(command_prefix=';', description=description)

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')

@bot.command()
async def _8ball(name="8ball", aliases=["regalball", "8?", "8"]):
	"""a very special 8ball for those who need a little positivity in their lives"""
	self.ballxd = open("data/balls.txt").readlines()
	if query.endswith("?") and query != "?" or random() >= 0.17:
		await self.bot.say(":eggplant: |  " + choice(self.ballxd)[:-1] + "  | :potato:")
	else:
		await self.bot.say(":eggplant: |  You can't even format a question correctly, huh. I wish I could say I was surprised, but...you know what, I'll just pretend to be surprised. Hey, don't forget to add a question mark to the end of your question! I know that you're normally capable of it and that you just had an off day today. Yep. Definitely. Didn't sleep well, probably. Don't worry, I'll be here waiting for you to fix it. However long it takes you. It's not like I have anything better to do, and I mean, you definitely don't. | :potato:")

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
	"""Chooses between multiple choices."""
	await bot.say(random.choice(choices))

@bot.command()
async def repeat(times : int, content='repeating...'):
	"""Repeats a message multiple times."""
	for i in range(times):
		await bot.say(content)

@bot.command()
async def joined(member : discord.Member):
	"""Says when a member joined."""
	await bot.say('{0.name} joined in {0.joined_at}'.format(member))

@bot.group(pass_context=True)
async def cool(ctx):
	"""Says if a user is cool.

	In reality this just checks if a subcommand is being invoked.
	"""
	if ctx.invoked_subcommand is None:
		await bot.say('No, {0.subcommand_passed} is not cool'.format(ctx))

@cool.command(name='bot')
async def _bot():
	"""Is the bot cool?"""
	await bot.say('Yes, the bot is cool.')

bot.run('Mjg2Nzk3NzU2Mjg1MzIxMjE3.C6PpLw.FrSoTKaTNci_bIhJivviwTpB4Dg')
