from json import dumps
from asyncio import sleep
import datetime

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
                codes_list = []
                for invite in inv_guild:
                    inv_db[invite.code] = {
                        'user': invite.inviter.id,
                        'uses': invite.uses,
                        'max': invite.max_uses
                    }
                    codes_list.append(invite.code)
                await db.execute(
                    'UPDATE guilds SET invites=$1 WHERE id=$2',
                    dumps(inv_db), guild.id
                )
                codes = await db.fetchval(
                    'SELECT invites FROM guilds WHERE id=$1',
                    guild.id
                )
                codes = eval(codes)
                keys = codes.keys()
                for key in keys:
                    if key not in codes_list:
                        codes.pop(invite.code)
                await db.execute(
                    'UPDATE guilds SET codes=$1 WHERE id=$2',
                    dumps(codes), guild.id
                )

            pending = await db.fetch('SELECT * FROM pending')
            for row in pending:
                user, guild = row[0].split('_')
                guild = self.bot.get_guild(int(guild))
                if guild:
                    user = guild.get_member(int(user))
                    if user:
                        if not user.pending:
                            await self.give_user_roles(user, row[1], row[2])
                            continue
                await db.execute(
                    'DELETE FROM pending WHERE user_guild=$1',
                    row[0]
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

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        async with self.bot.pool.acquire() as db:
            pending = await db.fetch(
                f'SELECT * FROM pending'
            )
            delete = []
            for row in pending:
                if row[0].split('_')[1] == str(guild.id):
                    delete.append(row[0])
            for deleting in delete:
                await db.execute(
                    'DELETE FROM pending WHERE user_guild=$1',
                    deleting
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.pool.acquire() as db:
            codes, invites = await db.fetchval(
                'SELECT (codes, invites) FROM guilds WHERE id=$1',
                member.guild.id
            )
            codes = eval(codes)
            invites = eval(invites)
            cur_invites = await member.guild.invites()

            for inv in cur_invites:
                if not codes.get(inv.code):
                    continue
                temp_invite = codes[inv.code]
                if temp_invite['uses'] < inv.uses:
                    if temp_invite['uses'] <= temp_invite['max'] != 0:
                        invites.pop(inv.code)
                        codes.pop(inv.code)
                        await db.execute(
                            'UPDATE guilds SET codes=$1, invites=$2 WHERE id=$3',
                            dumps(codes), dumps(invites), member.guild.id
                        )
                    else:
                        invites[inv.code]['uses'] += 1
                        await db.execute(
                            'UPDATE guilds SET invites=$1 WHERE id=$2',
                            dumps(invites), member.guild.id
                        )

                    if member.pending:
                        await db.execute(
                            'INSERT INTO pending (user_guild, roles, inviter) VALUES ($1, $2, $3)',
                            f'{member.id}_{member.guild.id}', temp_invite['role'], temp_invite['user']
                        )
                    else:
                        await self.give_user_roles(member, temp_invite['role'], temp_invite['user'])
                    return

            logs = await db.fetchval(
                'SELECT logs FROM guilds WHERE id=$1',
                member.guild.id
            )
            channel = discord.utils.get(member.guild.channels, id=logs)
            if not channel:
                return

            for inv in cur_invites:
                temp_invite = invites[inv.code]
                if temp_invite['uses'] < inv.uses:
                    temp_invite['uses'] += 1
                    await db.execute(
                        'UPDATE guilds SET invites=$1 WHERE id=$2',
                        dumps(invites), member.guild.id
                    )
                    inviter = self.bot.get_user(temp_invite['user'])
                    if not inviter:
                        inviter = await self.bot.fetch_user(temp_invite['user'])
                    embed = discord.Embed(
                        title=f'Welcome {member}!',
                        description=f'Invited by: {inviter}\n',
                        color=discord.Color.green(),
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_author(name=member, icon_url=member.avatar_url)

                    return await channel.send(embed=embed)

            embed = discord.Embed(
                title='Huh?',
                description=f'I could not figure out, how {member} joined',
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending and not after.pending:
            await self.give_user_roles(after)

    async def roles_no_perms(self, member, inviter):
        async with self.bot.pool.acquire() as db:
            logs = await db.fetchval(
                'SELECT logs FROM guilds WHERE id=$1',
                member.guild.id
            )
            channel = discord.utils.get(member.guild.channels, id=logs)
            if not channel:
                return
            inviter = self.bot.get_user(inviter)
            if not inviter:
                inviter = await self.bot.fetch_user(inviter)
            embed = discord.Embed(
                title='Uh oh',
                description=f'{member} has joined the server, who is invited by {inviter}.\n'
                            f'The issue: I was unable to give {member} one or more roles!\n'
                            f'Please make sure that i am high enough in the Role Hierarchy,\n'
                            f'since i can only give members the roles, if the member and\n'
                            f'role is under me.',
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.red()
            )
            return await channel.send(embed=embed)

    async def give_user_roles(self, member, roles=None, inviter=None):
        async with self.bot.pool.acquire() as db:
            if not roles:
                try:
                    roles, inviter = await db.fetchval(
                        f'SELECT (roles, inviter) FROM pending WHERE user_guild=$1',
                        f'{member.id}_{member.guild.id}'
                    )
                except TypeError:
                    return
                await db.execute(
                    'DELETE FROM pending WHERE user_guild=$1',
                    f'{member.id}_{member.guild.id}'
                )

            all_roles = []
            for role in roles:
                role = discord.utils.get(member.guild.roles, id=role)
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        return await self.roles_no_perms(member, inviter)
                    all_roles.append(role.mention)

            logs = await db.fetchval(
                'SELECT logs FROM guilds WHERE id=$1',
                member.guild.id
            )
            channel = discord.utils.get(member.guild.channels, id=logs)
            if not channel:
                return

            inviter = self.bot.get_user(inviter)
            if not inviter:
                inviter = await self.bot.fetch_user(inviter)
            embed = discord.Embed(
                title=f'Welcome {member}!',
                description=f'Invited by: {self.bot.get_user(inviter)}\n'
                            f'Roles received: {", ".join(all_roles) if all_roles else "None"}',
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name=member, icon_url=member.avatar_url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        async with self.bot.pool.acquire() as db:
            pending = await db.fetchval(
                f'SELECT * FROM pending WHERE user_guild=$1',
                f'{member.id}_{member.guild.id}'
            )
            if pending:
                await db.execute(
                    'DELETE FROM pending WHERE user_guild=$1',
                    f'{member.id}_{member.guild.id}'
                )

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        async with self.bot.pool.acquire() as db:
            codes = await db.fetchval(
                'SELECT invites FROM guilds WHERE id=$1',
                invite.guild.id
            )
            codes = eval(codes)
            codes[invite.code] = {
                'user': invite.inviter.id,
                'uses': invite.uses,
                'max': invite.max_uses
            }
            await db.execute(
                'UPDATE guilds SET invites=$1 WHERE id=$2',
                dumps(codes), invite.guild.id
            )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        async with self.bot.pool.acquire() as db:
            codes, invites = await db.fetchval(
                'SELECT (codes, invites) FROM guilds WHERE id=$1',
                invite.guild.id
            )
            codes = eval(codes)
            invites = eval(invites)
            if codes.get(invite.code):
                codes.pop(invite.code)
                await db.execute(
                    'UPDATE guilds SET codes=$1 WHERE id=$2',
                    dumps(codes), invite.guild.id
                )
                print('CODES YEET')
            if invites.get(invite.code):
                invites.pop(invite.code)
                await db.execute(
                    'UPDATE guilds SET invites=$1 WHERE id=$2',
                    dumps(invites), invite.guild.id
                )
                print('INVITES YEET')


def setup(bot):
    bot.add_cog(System(bot))
