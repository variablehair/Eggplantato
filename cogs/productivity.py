import discord
from discord.ext import commands
import sqlite3
from cogs.utils import errors
from ast import literal_eval
import re
import datetime
import aiohttp
from urllib.parse import parse_qs
from lxml import etree

# Google functions are copied from RoboDanny, accessed on April 6, 2017. https://github.com/Rapptz/RoboDanny/blob/master/cogs/buttons.py#L78

def DayParser(str_arg):
	"""Parses the day of the week from a string."""
	compiled = re.compile(r"^(?:(?P<monday>(?:m(?:on)?))|(?P<tuesday>tu(?:es?)?)|(?P<wednesday>w(?:ed)?)|"
	"(?P<thursday>th(?:u(?:rs)?)?)|(?P<friday>f(?:ri)?)|(?P<saturday>sat?)|(?P<sunday>sun?))$|^(?P<dayfull>"
	"(?:(?:mon)|(?:tues)|(?:wednes)|(?:thurs)|(?:fri)|(?:satur)|(?:sun))day)$")
	match = compiled.match(str_arg.lower())
	if match is None or not match.group(0):
		raise commands.BadArgument('Failed to parse day.')
	elif match.group("dayfull"):
		return match.group("dayfull")
	else:
		return [k for k, v in match.groupdict().items() if v][0]
		
def TimeParser(str_arg):
	"""Parses an amount of seconds from a string of *w*d*h*m*s. Max time of 1 year.
	
	Does not require knowledge of the user's current time. Returns timedelta object."""
	
	compiled = re.compile(r"^(?P<weeks>[0-9]{1,2}[Ww])?(?P<days>[0-9]{1,3}[Dd])?"
	"(?P<hours>[0-9]{1,4}[Hh])?(?P<minutes>[0-9]{1,6}[Mm])?(?P<seconds>[0-9]{1,8}[Ss])?$")
	match = compiled.match(str_arg)
	if match is None or not match.group(0):
		raise commands.BadArgument('Failed to parse time.')
	int_seconds = 0
	
	if match.group("weeks") is not None:
		int_seconds += int(match.group("weeks")) * 604800
	if match.group("days") is not None:
		int_seconds += int(match.group("days")) * 86400
	if match.group("hours") is not None:
		int_seconds += int(match.group("hours")) * 3600
	if match.group("minutes") is not None:
		int_seconds += int(match.group("minutes")) * 60
	if match.group("seconds") is not None:
		int_seconds += int(match.group("seconds"))
		
	if int_seconds < 31540000: #1 year
		return datetime.timedelta(seconds=int_seconds)
	else:
		raise commands.BadArgument('Time specified cannot exceed 1 year.')
		
def AmPmParser(str_arg):
	"""Parses a 4 digit time literal from user input with optional AM or PM"""
	compiled = re.compile(r"(?P<timelit>^[0-9]{1,4})(?P<am>[Aa][Mm]?$)?(?P<pm>[Pp][Mm]?$)?")
	match = compiled.match(str_arg)
	if match is None or not match.group(0):
		raise commands.BadArgument('Failed to parse time.')
	
	int_timelit = int(match.group("timelit"))
	# check if <=12 with ampm (e.g. 12am), if >24 when it's a 2 char input, or >2399
	if int_timelit > 2399 or (len(match.group("timelit")) <= 2 and int_timelit > 24) \
		or (int_timelit > 12 and (match.group("pm") or match.group("am"))):
			raise commands.BadArgument('Time argument too long.')		
	
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
			
	@commands.command(pass_context=True, aliases=[""])
	async def settime(self, ctx, str_usertime):
		"""Set your time zone. You can tell me your UTC offset (`-8` or `+350`) **or** the most recent multiple of 30 \
		minutes (e.g. if it is currently `1:54PM`, you use `settime 1330` or `settime 130pm`)"""
		pass #todo: this
			
	@commands.command(pass_context=True, aliases=["remind", "timer"])
	async def remindme(self, ctx, str_left : str, str_right: str=''):
		if str_right:
			# do stuff
			await ctx.send("2 args")
		else:
			try:
				await ctx.send(DayParser(str_left))
			except commands.BadArgument:
				await ctx.send("Your day is not formatted correctly!"
				" You can use shorthand `(m or TU or wEd)` or the full name of the day `(sunday)`")
		
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
				c.execute("INSERT INTO lists VALUES (?,?)", (str(ctx.message.author.id), "[\'" + str_task + "\']"))
			else:
				list_user_tasks = literal_eval(tup_data[0])
				list_user_tasks.append(str_task)
				c.execute("UPDATE lists SET tasks=? WHERE user=?", (str(list_user_tasks), str(ctx.message.author.id)))
			self.todoconn.commit()
			self.todoconn.close()
			await ctx.send("{} added successfully!".format(str_task))

	@todo.command(name="remove", aliases=["delete", "rm", "del"])
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
	
	def parse_google_card(self, node):
		if node is None:
			return None

		e = discord.Embed(colour=0x738bd7)

		# check if it's a calculator card:
		calculator = node.find(".//table/tr/td/span[@class='nobr']/h2[@class='r']")
		if calculator is not None:
			e.title = 'Calculator'
			e.description = ''.join(calculator.itertext())
			return e

		parent = node.getparent()

		# check for unit conversion card
		unit = parent.find(".//ol//div[@class='_Tsb']")
		if unit is not None:
			e.title = 'Unit Conversion'
			e.description = ''.join(''.join(n.itertext()) for n in unit)
			return e

		# check for currency conversion card
		currency = parent.find(".//ol/table[@class='std _tLi']/tr/td/h2")
		if currency is not None:
			e.title = 'Currency Conversion'
			e.description = ''.join(currency.itertext())
			return e

		# check for release date card
		release = parent.find(".//div[@id='_vBb']")
		if release is not None:
			try:
				e.description = ''.join(release[0].itertext()).strip()
				e.title = ''.join(release[1].itertext()).strip()
				return e
			except:
				return None

		# check for definition card
		words = parent.find(".//ol/div[@class='g']/div/h3[@class='r']/div")
		if words is not None:
			try:
				definition_info = words.getparent().getparent()[1] # yikes
			except:
				pass
			else:
				try:
					# inside is a <div> with two <span>
					# the first is the actual word, the second is the pronunciation
					e.title = words[0].text
					e.description = words[1].text
				except:
					return None

				# inside the table there's the actual definitions
				# they're separated as noun/verb/adjective with a list
				# of definitions
				for row in definition_info:
					if len(row.attrib) != 0:
						# definitions are empty <tr>
						# if there is something in the <tr> then we're done
						# with the definitions
						break

					try:
						data = row[0]
						lexical_category = data[0].text
						body = []
						for index, definition in enumerate(data[1], 1):
							body.append('%s. %s' % (index, definition.text))

						e.add_field(name=lexical_category, value='\n'.join(body), inline=False)
					except:
						continue

				return e

		# check for "time in" card
		time_in = parent.find(".//ol//div[@class='_Tsb _HOb _Qeb']")
		if time_in is not None:
			try:
				time_place = ''.join(time_in.find("span[@class='_HOb _Qeb']").itertext()).strip()
				the_time = ''.join(time_in.find("div[@class='_rkc _Peb']").itertext()).strip()
				the_date = ''.join(time_in.find("div[@class='_HOb _Qeb']").itertext()).strip()
			except:
				return None
			else:
				e.title = time_place
				e.description = '%s\n%s' % (the_time, the_date)
				return e

		# check for weather card
		# this one is the most complicated of the group lol
		# everything is under a <div class="e"> which has a
		# <h3>{{ weather for place }}</h3>
		# string, the rest is fucking table fuckery.
		weather = parent.find(".//ol//div[@class='e']")
		if weather is None:
			return None

		location = weather.find('h3')
		if location is None:
			return None

		e.title = ''.join(location.itertext())

		table = weather.find('table')
		if table is None:
			return None

		# This is gonna be a bit fucky.
		# So the part we care about is on the second data
		# column of the first tr
		try:
			tr = table[0]
			img = tr[0].find('img')
			category = img.get('alt')
			image = 'https:' + img.get('src')
			temperature = tr[1].xpath("./span[@class='wob_t']//text()")[0]
		except:
			return None # RIP
		else:
			e.set_thumbnail(url=image)
			e.description = '*%s*' % category
			e.add_field(name='Temperature', value=temperature)

		# On the 4th column it tells us our wind speeds
		try:
			wind = ''.join(table[3].itertext()).replace('Wind: ', '')
		except:
			return None
		else:
			e.add_field(name='Wind', value=wind)

		# On the 5th column it tells us our humidity
		try:
			humidity = ''.join(table[4][0].itertext()).replace('Humidity: ', '')
		except:
			return None
		else:
			e.add_field(name='Humidity', value=humidity)

		return e

	async def get_google_entries(self, query):
		params = {
			'q': query,
			'safe': 'on'
		}
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'
		}

		# list of URLs
		entries = []

		# the result of a google card, an embed
		card = None

		async with aiohttp.get('https://www.google.com/search', params=params, headers=headers) as resp:
			if resp.status != 200:
				raise RuntimeError('Google somehow failed to respond.')

			root = etree.fromstring(await resp.text(), etree.HTMLParser())

			# with open('google.html', 'w', encoding='utf-8') as f:
			#     f.write(etree.tostring(root, pretty_print=True).decode('utf-8'))

			"""
			Tree looks like this.. sort of..
			<div class="g">
				...
				<h3>
					<a href="/url?q=<url>" ...>title</a>
				</h3>
				...
				<span class="st">
					<span class="f">date here</span>
					summary here, can contain <em>tag</em>
				</span>
			</div>
			"""

			card_node = root.find(".//div[@id='topstuff']")
			card = self.parse_google_card(card_node)

			search_nodes = root.findall(".//div[@class='g']")
			for node in search_nodes:
				url_node = node.find('.//h3/a')
				if url_node is None:
					continue

				url = url_node.attrib['href']
				if not url.startswith('/url?'):
					continue

				url = parse_qs(url[5:])['q'][0] # get the URL from ?q query string

				# if I ever cared about the description, this is how
				entries.append(url)

				# short = node.find(".//span[@class='st']")
				# if short is None:
				#     entries.append((url, ''))
				# else:
				#     text = ''.join(short.itertext())
				#     entries.append((url, text.replace('...', '')))

		return card, entries

	@commands.command(aliases=['google'], pass_context=True)
	async def g(self, ctx, *, query):
		"""Searches google and gives you top result."""
		try:
			card, entries = await self.get_google_entries(query)
		except RuntimeError as e:
			await ctx.send(str(e))
		else:
			if card:
				value = '\n'.join(entries[:3])
				if value:
					card.add_field(name='Search Results', value=value, inline=False)
				return await ctx.send(embed=card)

			if len(entries) == 0:
				return await ctx.send('No results found... sorry.')

			next_two = entries[1:3]
			first_entry = entries[0]
			if first_entry[-1] == ')':
				first_entry = first_entry[:-1] + '%29'

			if next_two:
				formatted = '\n'.join(map(lambda x: '<%s>' % x, next_two))
				msg = '{}\n\n**See also:**\n{}'.format(first_entry, formatted)
			else:
				msg = first_entry

			await ctx.send(msg)
					
def setup(bot):
	bot.add_cog(Productivity(bot))