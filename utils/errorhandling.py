import traceback
import datetime

import discord
from discord.ext import commands

from utils.formatters import cooldown_formatter, help_formatter, error_formatter
from utils.exceptions import *


class ErrorHandling(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NSFWChannelRequired):
                embed = discord.Embed(
                    title='You are horny!',
                    description='This command can only be used in NSFW Channels!',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)
            elif isinstance(error, NotDM):
                embed = discord.Embed(
                    title='Don\'t be publicly about this!',
                    description='This command can not be used in a Server!',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)
            elif isinstance(error, NotGuild):
                embed = discord.Embed(
                    title='Don\'t be sneaky!',
                    description='This command can not be used in Direct Messages!',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)
            elif isinstance(error, NotBotOwner):
                embed = discord.Embed(
                    title='OwO, what\'s this???',
                    description='This command is a owner only command, and can not be executed by ANYONE else!\n'
                                'Don\'t you try to use it again, because it won\'t work.'
                                'Or else the owner might hurt you! ||jk jk||',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)
            elif isinstance(error, NotGuildOwner):
                embed = discord.Embed(
                    title='Oi mate!',
                    description='This command can only be used by the Server Owner!',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)
            elif isinstance(error, NotGuildAdmin):
                embed = discord.Embed(
                    title='Oi mate!',
                    description='This command can only be used by Server Admins!',
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.utcnow()
                )
                await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            cooldown = cooldown_formatter(error.retry_after)
            embed = discord.Embed(
                title='Cooldown',
                description=f'Please wait {cooldown} until you can use the {ctx.command} command again.',
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(embed=await help_formatter(ctx, ctx.command))
            elif isinstance(error, commands.BadArgument):
                await ctx.send(embed=error_formatter(ctx, error, False))
            elif isinstance(error, commands.BadUnionArgument):
                await ctx.send(embed=error_formatter(ctx, error, False))
            elif isinstance(error, commands.ArgumentParsingError):
                await ctx.send(embed=error_formatter(ctx, error, False))

        else:
            await ctx.send(embed=error_formatter(ctx, f'{type(error).__name__}: {error}'))
            error = traceback.format_exception(type(error), error, error.__traceback__)
            ctx.bot.log.ERROR(f'Occurred in {ctx.guild}, in {ctx.channel} by user {ctx.author}\n{"-" * 15}')
            ctx.bot.log.ERROR(f'Ignoring exception in command {ctx.command}:')
            ctx.bot.log.ERROR(error)


def setup(bot):
    bot.add_cog(ErrorHandling(bot))
