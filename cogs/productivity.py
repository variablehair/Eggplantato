import discord
from discord.ext import commands
import sqlite3
from cogs.utils import errors
from ast import literal_eval

class Productivity():
	"""Tools to make your life easier (?)"""
	
	def __init__(self, bot):
		self.bot = bot
		self.todoconn = sqlite3.connect('data/todo.db')
		try:
			c = self.todoconn.cursor()
			c.execute("SELECT user FROM lists WHERE user='debug'")
		except sqlite3.OperationalError as e:
			print(str(e))
			raise errors.DatabaseError("Error loading todo database; did you run initdb?")
		finally:
			self.todoconn.close()
		
	@commands.group(pass_context=True, invoke_without_context=True)
	async def todo(self, ctx):
		"""A simple todo list. `todo add [task]` to add something, `todo` to look at your list. `todo help` for more commands"""
		if ctx.invoked_subcommand is None:
			await ctx.invoke(self._todoget)			
				
	@todo.command(name="get", alias=["list"])
	async def _todoget(self, ctx):
		"""Prints your todo list"""
		self.todoconn = sqlite3.connect('data/todo.db')
		c = self.todoconn.cursor()
		c.execute("SELECT tasks FROM lists WHERE user=?", (str(ctx.message.author.id),))
		tup_data = c.fetchone()
		if tup_data is None:
			await ctx.send("You don't have anything in your todo list! Add something with `todo add [task]`.")
		else:
			list_user_tasks = literal_eval(tup_data[0])
			str_ret = ":eggplant: Your todo list:\n"
			for i in range(len(list_user_tasks)):
				str_ret = "".join([str_ret, str(i+1), ": ", list_user_tasks[i], "\n"])
			await ctx.send(str_ret)
		self.todoconn.close()
		
	@todo.command(pass_context=True, name="add")
	async def _todoadd(self, ctx, *args):
		"""Adds a task to your list"""
		if args == []:
			await ctx.send("You must specify a task to add!")
			return
		else:
			self.todoconn = sqlite3.connect('data/todo.db')
			c = self.todoconn.cursor()
			c.execute("SELECT tasks FROM lists WHERE user=?", (str(ctx.message.author.id),))
			tup_data = c.fetchone()
			str_task = " ".join(args)
			if tup_data is None:
				c.execute("INSERT INTO lists VALUES (?,?)", (str(ctx.message.author.id), "[" + str_task + "]"))
			else:
				list_user_tasks = literal_eval(tup_data[0])
				list_user_tasks.append(str_task)
				c.execute("UPDATE lists SET tasks=? WHERE user=?", (str(list_user_tasks), str(ctx.message.author.id)))
			self.todoconn.commit()
			self.todoconn.close()
			await ctx.send("{} added successfully!".format(str_task))

	@todo.command(name="remove", alias=["delete", "rm", "del"])
	async def _todoremove(self, ctx, *args):
		"""Removes a task from your list"""
		if len(args) == 0:
			await ctx.send("You must specify the number of a task to remove.")
			return
		self.todoconn = sqlite3.connect('data/todo.db')
		c = self.todoconn.cursor()
		c.execute("SELECT tasks FROM lists WHERE user=?", (str(ctx.message.author.id),))
		tup_data = c.fetchone()
		if tup_data is None:
			await ctx.send("Your todo list is empty.")
		else:
			list_user_tasks = literal_eval(tup_data[0])
			try:
				int_taskid = int(args[0])
				if int_taskid <= 0 or int_taskid > len(list_user_tasks):
					await ctx.send("Please enter a valid index!")
				else: 
					await ctx.send("Task `{}` removed successfully.".format(list_user_tasks.pop(int_taskid - 1)))
					c.execute("UPDATE lists SET tasks=? WHERE user=?", (str(list_user_tasks), str(ctx.message.author.id)))
					self.todoconn.commit()
			except ValueError:
				str_task = " ".join(args)
				try:
					list_user_tasks.remove(str_task)
					await ctx.send("Task `{}` removed successfully.".format(str_task))
					c.execute("UPDATE lists SET tasks=? WHERE user=?", (str(list_user_tasks), str(ctx.message.author.id)))
					self.todoconn.commit()
				except ValueError:
					await ctx.send("Task `{}` not found.".format(str_task))
		self.todoconn.close()
					
def setup(bot):
	bot.add_cog(Productivity(bot))