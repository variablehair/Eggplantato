import discord
from discord.ext import commands
import sqlite3

class Productivity():
	"""Tools to make your life easier (?)"""
	
	def __init__(self, bot):
		self.bot = bot
		
	@commands.group(pass_context=True, invoke_without_context=True)
	async def todo(self, ctx):
		"""A simple todo list. `todo add [task]` to add something, `todo` to look at your list. `todo help` for more commands"""
		if ctx.invoked_subcommand is None:
			await ctx.invoke(self._todoget)			
				
	@todo.command(name="get", alias=["list"])
	async def _todoget(self, ctx):
		"""Prints your todo list"""
		await ctx.send("gets list")
		
	@todo.command(pass_context=True, name="add")
	async def _todoadd(self, ctx, *args):
		"""Adds a task to your list"""
		if len(args) == 0:
			await ctx.send("You must specify a task to add!")
			return
		else:
			await ctx.send("adds {}".format(" ".join(args)))
			
	@todo.command(name="remove", alias=["delete", "rm", "del"])
	async def _todoremove(self, ctx, *args):
		"""Removes a task from your list"""
		if len(args) == 0:
			await ctx.send("You must specify the number of a task to remove.")
			return
		try:
			n = int(args[0])
			await ctx.send("Removing task #{}".format(n))
		except ValueError:
			await ctx.send("Removing task \"{}\"".format(" ".join(args)))
			
		
def setup(bot):
	bot.add_cog(Productivity(bot))