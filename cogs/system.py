from json import dumps
from asyncio import sleep

import discord
from discord.ext import commands


class System(commands.Cog):

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
        await sleep(5)
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


def setup(bot):
    bot.add_cog(System(bot))
