from discord.ext import commands
import discord.utils

def is_regal(message):
	return message.author.id == 122520008797454337
	
def is_owner():
	return commands.check(lambda ctx: is_regal(ctx.message))