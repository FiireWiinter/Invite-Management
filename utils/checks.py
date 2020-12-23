import json
from discord import TextChannel, DMChannel

with open('config.json') as f:
    owners = json.load(f)['owners']


def guild(ctx):
    return isinstance(ctx.channel, TextChannel)


def dm(ctx):
    return isinstance(ctx.channel, DMChannel)


def bot_owner(ctx):
    return ctx.author.id in owners


def guild_owner(ctx):
    if guild(ctx):
        return ctx.author == ctx.guild.owner


def guild_admin(ctx):
    if guild(ctx):
        return ctx.author.guild_permissions.administrator
