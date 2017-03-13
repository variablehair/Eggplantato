import discord
from discord.ext import commands
import random

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='hey ep ', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command(name="8ball", aliases=["regalball", "8?", "8"])
async def _8ball(ctx, *, query : str):
	"""a very special 8ball for those who need a little positivity in their lives"""
	replies = open("data/balls.txt").readlines()
	if query.endswith("?") and query != "?" or random() >= 0.17:
		await ctx.send(":eggplant: |  " + random.choice(replies)[:-1] + "  | :potato:")
	else:
		await ctx.send(":eggplant: |  You can't even format a question correctly, huh. I wish I could say I was surprised, but...you know what, I'll just pretend to be surprised. Hey, don't forget to add a question mark to the end of your question! I know that you're normally capable of it and that you just had an off day today. Yep. Definitely. Didn't sleep well, probably. Don't worry, I'll be here waiting for you to fix it. However long it takes you. It's not like I have anything better to do, and I mean, you definitely don't. | :potato:")
	
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
