import discord
from discord.ext import commands
import random

class Happy():
	def __init__(self, bot):
		self.bot = bot
		
	@commands.command()
	async def happy(self, ctx):
		await ctx.send("Fuck you uwu")
		
	@commands.command(name="8ball", aliases=["8?", "8"])
	async def _8ball(self, ctx, *, query : str):
		"""a very special 8ball for those who need a little positivity in their lives"""
		replies = open("data/happy/balls.txt").readlines()
		if query.endswith("?") and query != "?" or random.random() >= 0.17:
			await ctx.send(":eggplant: |  " + random.choice(replies)[:-1] + "  | :potato:")
		else:
			await ctx.send(":eggplant: |  You can't even format a question correctly, huh. I wish I could say I was surprised, but...you know what, I'll just pretend to be surprised. Hey, don't forget to add a question mark to the end of your question! I know that you're normally capable of it and that you just had an off day today. Yep. Definitely. Didn't sleep well, probably. Don't worry, I'll be here waiting for you to fix it. However long it takes you. It's not like I have anything better to do, and I mean, you definitely don't. | :potato:")
		
def setup(bot):
	bot.add_cog(Happy(bot))