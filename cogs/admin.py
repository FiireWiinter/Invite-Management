import datetime
from json import dumps
from asyncio import TimeoutError

import discord
from discord.ext import commands

from utils.predicates import *


class Admin(commands.Cog):

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
                        temp = eval(temp)
                        for key in temp.keys():
                            if key == invite.code:
                                embed = discord.Embed(
                                    title='Code already setup!',
                                    description=f'{invite.code} has already been setup!\n'
                                                f'To edit it, delete the old one first.',
                                    timestamp=datetime.datetime.utcnow(),
                                    color=discord.Color.red()
                                )
                                return await ctx.send(embed=embed)
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
    async def del_invite(self, ctx, code):
        async with self.bot.pool.acquire() as db:
            codes = await db.fetchval(
                'SELECT codes FROM guilds WHERE id=$1',
                ctx.guild.id
            )
            codes = eval(codes)
            if codes.get(code):
                codes.pop(code)
                await db.execute(
                    'UPDATE guilds SET codes=$1 WHERE id=$2',
                    dumps(codes), ctx.guild.id
                )
                embed = discord.Embed(
                    title='Code Removed',
                    description=f'{code} has been removed from my system!',
                    timestamp=datetime.datetime.utcnow(),
                    color=discord.Color.green()
                )
                return await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title='Code not found!',
                    description=f'{code} is not a valid code in my system!\nDid you capitalize it correctly?',
                    timestamp=datetime.datetime.utcnow(),
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

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
                            f'User who joined, User who invited, Roles received',
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await ctx.send(embed=embed)

    @commands.command()
    @guild_only()
    @guild_admin()
    async def codes(self, ctx):
        embed = discord.Embed(
            title='WAIT!!!',
            description='Make sure that this is a private channel!\n'
                        'If you proceed in a public channel, invite codes will be leaked, with all of the '
                        'roles to assign to that role!\n__***SERIOUS DAMAGE CAN BE DEALT BY DOING THAT!***__',
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.orange()
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def reaction_check(reaction_, user_):
            return reaction_.emoji in ('✅', '❌') and user_ == ctx.author and reaction_.message.id == message.id
        try:
            _reaction, _user = await ctx.bot.wait_for('reaction_add', timeout=60, check=reaction_check)
        except TimeoutError:
            return await ctx.send('Timeout of 60 seconds reached!')

        if _reaction == '❌':
            return await ctx.send('Alright! I am not showing them.')

        async with ctx.bot.pool.acquire() as db:
            codes = await db.fetchval(
                'SELECT codes FROM guilds WHERE id=$1',
                ctx.guild.id
            )
            codes = eval(codes)
            all_codes = []
            keys = codes.keys()

            for key in keys:
                code = codes[key]
                inviter = ctx.bot.get_user(code['user'])
                if not inviter:
                    inviter = await ctx.bot.fetch_user(code['user'])
                not_found = 0
                roles = []
                for role_id in code['role']:
                    role = discord.utils.get(ctx.guild.roles, id=role_id)
                    if not role:
                        not_found += 1
                    else:
                        roles.append(role.mention)
                roles = ", ".join(roles)
                uses = code['uses']
                max_ = code['max']
                all_codes.append(
                    f'||{key}|| | {uses}/{max_ if max_ != 0 else "Infinite"} '
                    f'uses | Inviter: {inviter}{str(" | " + roles if roles != "" else "")}'
                    f'{f" | Roles not found: {not_found}" if not_found else ""}\n'
                )

        if len(all_codes) == 0:
            embed = discord.Embed(
                title='All Codes',
                description='There are no codes saved',
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        temp_msg = ""
        for code in all_codes:
            if len(temp_msg) + len(code) >= 2048:
                embed = discord.Embed(
                    title='All Codes',
                    description=temp_msg,
                    timestamp=datetime.datetime.utcnow(),
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                temp_msg = ""
            temp_msg += code
        if temp_msg != "":
            embed = discord.Embed(
                title='All Codes',
                description=temp_msg,
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
