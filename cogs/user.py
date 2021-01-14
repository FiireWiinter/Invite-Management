import discord
from discord.ext import commands

from utils.predicates import guild_only


class User(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @guild_only()
    async def invites(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        async with self.bot.pool.acquire() as db:
            user = await db.fetchval(
                'SELECT users FROM guilds WHERE ID=$1', member.id
            )
            # not coded to the end


def setup(bot):
    bot.add_cog(User(bot))
