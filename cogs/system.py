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
            old_invites = await db.fetchval(
                'SELECT codes FROM guilds WHERE id=$1',
                member.guild.id
            )
            old_invites = eval(old_invites)
            cur_invites = await member.guild.invites()

            for inv in cur_invites:
                temp_invite = old_invites[inv.code]
                if temp_invite['uses'] < inv.uses:
                    if temp_invite['uses'] <= temp_invite['max'] != 0:
                        old_invites.pop(inv.code)
                        await db.execute(
                            'UPDATE guilds SET codes=$1 WHERE id=$2',
                            dumps(old_invites), member.guild.id
                        )

                    if member.pending:
                        await db.execute(
                            'INSERT INTO pending (user_guild, roles, inviter) VALUES ($1, $2, $3)',
                            f'{member.id}_{member.guild.id}', temp_invite['role'], temp_invite['user']
                        )
                    else:
                        return await self.give_user_roles(member, temp_invite['role'], temp_invite['user'])

            logs = await db.fetchval(
                'SELECT logs FROM guilds WHERE id=$1',
                member.guild.id
            )
            channel = discord.utils.get(member.guild.channels, id=logs)
            if not channel:
                return
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

    async def give_user_roles(self, member, roles=None, inviter=None):
        async with self.bot.pool.acquire() as db:
            if not roles:
                roles, inviter = await db.fetchval(
                    f'SELECT (roles, inviter) FROM pending WHERE user_guild=$1',
                    f'{member.id}_{member.guild.id}'
                )
                await db.execute(
                    'DELETE FROM pending WHERE user_guild=$1',
                    f'{member.id}_{member.guild.id}'
                )

            all_roles = []
            for role in roles:
                role = discord.utils.get(member.guild.roles, id=role)
                if role:
                    await member.add_roles(role)
                    all_roles.append(role.mention)

            logs = await db.fetchval(
                'SELECT logs FROM guilds WHERE id=$1',
                member.guild.id
            )
            channel = discord.utils.get(member.guild.channels, id=logs)
            if not channel:
                return

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
    async def on_invite_delete(self, invite):
        async with self.bot.pool.acquire() as db:
            codes = await db.fetchval(
                'SELECT codes FROM guilds WHERE id=$1',
                invite.guild.id
            )
            codes = eval(codes)
            if codes.get(invite.code):
                codes.pop(invite.code)
                await db.execute(
                    'UPDATE guilds SET codes=$1 WHERE id=$2',
                    dumps(codes), invite.guild.id
                )
                print('YEET')


def setup(bot):
    bot.add_cog(System(bot))
