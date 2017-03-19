from discord.ext import commands
from .utils import checks
import asyncio
import traceback
import discord
import inspect
import textwrap
from contextlib import redirect_stdout
import io

class Admin:
	"""Basically everything here is shamelessly stolen from R. Danny (https://github.com/Rapptz/RoboDanny)"""
	def __init__(self, bot):
		self.bot = bot
		self._last_result = None
		self.sessions = set()

	def cleanup_code(self, content):
		"""Automatically removes code blocks from the code."""
		# remove ```py\n```
		if content.startswith('```') and content.endswith('```'):
			return '\n'.join(content.split('\n')[1:-1])

		# remove `foo`
		return content.strip('` \n')

	def get_syntax_error(self, e):
		if e.text is None:
			return '```py\n{0.__class__.__name__}: {0}\n```'.format(e)
		return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

	@commands.command(pass_context=True, hidden=True, name='eval')
	@checks.is_owner()
	async def _eval(self, ctx, *, body: str):
		env = {
			'bot': self.bot,
			'ctx': ctx,
			'channel': ctx.message.channel,
			'author': ctx.message.author,
			'server': ctx.message.guild,
			'message': ctx.message,
			'_': self._last_result
		}

		env.update(globals())

		body = self.cleanup_code(body)
		stdout = io.StringIO()
		to_compile = 'async def func():\n%s' % textwrap.indent(body, '  ')

		try:
			exec(to_compile, env)
		except SyntaxError as e:
			return await ctx.send(self.get_syntax_error(e))

		func = env['func']
		try:
			with redirect_stdout(stdout):
				ret = await func()
		except Exception as e:
			value = stdout.getvalue()
			await ctx.send('```py\n{}{}\n```'.format(value, traceback.format_exc()))
		else:
			value = stdout.getvalue()
			try:
				await self.bot.add_reaction(ctx.message, '\u2705')
			except:
				pass

			if ret is None:
				if value:
					await ctx.send('```py\n%s\n```' % value)
			else:
				self._last_result = ret
				await ctx.send('```py\n%s%s\n```' % (value, ret))
				
def setup(bot):
	bot.add_cog(Admin(bot))