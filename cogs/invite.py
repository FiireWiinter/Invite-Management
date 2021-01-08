from json import dumps

import discord
from discord.ext import commands

from utils.predicates import guild_only


class Invite(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.pool.acquire() as db:
            for guild in self.bot.guilds:
                inv_guild = await guild.invites()
                inv_db = {}
                for invite in inv_guild:
                    inv_db[invite.code] = {
                        'user': invite.inviter.id,
                        'uses': invite.uses,
                        'max': invite.max_uses
                    }
                await db.execute(
                    'UPDATE guilds SET invites=$1 WHERE id=$2',
                    dumps(inv_db), guild.id
                )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        async with self.bot.pool.acquire() as db:
            inv_db = {}
            for invite in await guild.invites():
                inv_db[invite.code] = {
                    'user': invite.inviter.id,
                    'uses': invite.uses,
                    'max': invite.max_uses
                }
            await db.execute(
                'UPDATE guilds SET invites=$1 WHERE id=$2',
                dumps(inv_db), guild.id
            )

    @commands.command()
    @guild_only()
    async def invites(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with self.bot.pool.acquire() as db:
            user = await db.fetchval(
                'SELECT users FROM guilds WHERE ID=$1', member.id
            )
            print(user)


def setup(bot):
    bot.add_cog(Invite(bot))
