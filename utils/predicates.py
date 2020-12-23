from discord.ext.commands import check

import utils.checks as checks
from utils.exceptions import *


def guild_only():
    async def predicate(ctx):
        if checks.guild(ctx):
            return True
        else:
            raise NotGuild()
    return check(predicate)


def dm_only():
    async def predicate(ctx):
        if checks.dm(ctx):
            return True
        else:
            raise NotDM()
    return check(predicate)


def bot_owner():
    async def predicate(ctx):
        if checks.bot_owner(ctx):
            return True
        else:
            raise NotBotOwner()
    return check(predicate)


def guild_owner():
    async def predicate(ctx):
        if checks.guild_owner(ctx):
            return True
        else:
            raise NotGuildOwner()
    return check(predicate)


def guild_admin():
    async def predicate(ctx):
        if checks.guild_admin(ctx):
            return True
        else:
            raise NotGuildAdmin()
    return check(predicate)
