import datetime
from json import dumps

import discord
from discord.ext import commands

from utils.predicates import *


class Setup(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @guild_only()
    @guild_owner()
    async def prefix(self, ctx, prefix):
        if len(prefix) >= 6:
            return await ctx.send('Prefix can not be longer than 5.')
        async with self.bot.pool.acquire() as db:
            await db.execute(
                'UPDATE guilds SET prefix=$1 WHERE id=$2',
                prefix, ctx.guild.id
            )
            await ctx.send(f'Prefix changed to `{prefix}`')

    @commands.command()
    @guild_only()
    @guild_admin()
    async def add_invite(self, ctx, invite_code, roles: commands.Greedy[discord.Role]):
        for invite in await ctx.guild.invites():
            if invite.code == invite_code:
                async with self.bot.pool.acquire() as db:
                    temp = await db.fetchval(
                        'SELECT codes FROM guilds WHERE id=$1',
                        ctx.guild.id
                    )
                    if not temp:
                        temp = {}
                    else:
                        code = eval(temp)
                        for key in code.keys():
                            if key == invite_code:
                                return await ctx.send('This code has already been setup.')
                    temp[invite.code] = {
                        'user': invite.inviter.id,
                        'role': [role.id for role in roles],
                        'uses': invite.uses,
                        'max': invite.max_uses
                    }
                    await db.execute(
                        'UPDATE guilds SET codes=$1 WHERE id=$2',
                        dumps(temp), ctx.guild.id
                    )
                    embed = discord.Embed(
                        title='Invite added!',
                        description=f'I have added `{invite.code}` to my system!\n'
                                    f'They will receive following roles when joining the server:\n'
                                    f'{", ".join([role.mention for role in roles])}',
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    return await ctx.send(embed=embed)
        await ctx.send("Invite code not found!")

    @commands.command()
    @guild_only()
    @guild_admin()
    async def create_invite(self, ctx, roles: commands.Greedy[discord.Role]):
        await ctx.send('lol no')

    @commands.command()
    @guild_only()
    @guild_admin()
    async def set_log(self, ctx, channel: discord.TextChannel):
        try:
            await channel.send('This is a test message, to see if i can talk in here')
        except discord.Forbidden:
            embed = discord.Embed(
                title='Uh oh',
                description='It seems that i can\'t talk in that channel.\n'
                            'Please give me permissions to talk in there, or choose a different channel',
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            return await ctx.send(embed=embed)
        async with self.bot.pool.acquire() as db:
            await db.execute(
                'UPDATE guilds SET logs=$1 WHERE id=$2',
                channel.id, ctx.guild.id
            )
            embed = discord.Embed(
                title='Log Channel set!',
                description=f'Log Channel set to {channel.mention}.\n'
                            f'Following information will be sent there:\n'
                            f'User who joined, User who invited, Total amount of users '
                            f'invited by that user (who are still in the server)',
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Setup(bot))