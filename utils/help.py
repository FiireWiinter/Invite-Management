import json
import sys

import discord
from discord.ext import commands

from utils.prefix import prefix
import utils.formatters as formatters

with open('config.json') as f:
    data = json.load(f)
    owners = data['owners']
    version = data['version']


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='The holy help command')
    async def help(self, ctx, cmd=None):
        author = ctx.author
        owner = await self.bot.fetch_user(owners[0])

        if cmd is None:
            embed = discord.Embed(
                title=f'Type {await prefix(ctx)}help <command> for more info on a command!',
                color=discord.Color.green()
            )

            embed.set_author(name=author.display_name, icon_url=author.avatar_url)
            embed.set_footer(text=f'A bot created with ♥ by {owner} ・ '
                                  f'Uptime: {formatters.uptime(ctx)}. Version {version}')

            cogs_list = []
            for cog in self.bot.cogs:
                cog_ = self.bot.get_cog(cog)
                cog_len = len(cog_.get_commands())
                cogs_list.append((cog, cog_len))

            cogs_list.sort(key=lambda tup: tup[1], reverse=True)
            client_cogs = [entry[0] for entry in cogs_list]

            for cog in client_cogs:
                final_cmds = []
                cog = self.bot.get_cog(cog)
                cog_cmds = cog.get_commands()
                for cmd in cog_cmds:
                    if not cmd.hidden:
                        final_cmds.append(cmd)

                cmds = []
                for cmd in final_cmds:
                    cmd = f'{cmd.name}: {cmd.description if cmd.description != "" else "No Description found!"}'
                    cmds.append(cmd)

                if len(cmds) == 0:
                    continue
                else:
                    embed.add_field(
                        name=f'{cog.__class__.__name__} [{len(cmds)}]',
                        value='```yaml\n' + '\n'.join(cmds) + '\n```',
                        inline=False
                    )

            embed.add_field(
                name="Links",
                value="[Invite me with required Permissions)](https://discord.com/oauth2/authorize?client_id="
                      "802514124415172618&permissions=268520544&scope=bot) [Invite me with Admin Permissions)]("
                      "https://discord.com/api/oauth2/authorize?client_id=802514124415172618&permissions=8&scope=bot)"
                      "[GitHub Repo](https://github.com/FiireWiinter/Invite-Management)",
                inline=False
            )

            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                try:
                    await author.send(embed=embed)
                except discord.Forbidden:
                    pass

        else:
            command = self.bot.get_command(cmd)
            try:
                help_embed = await formatters.help_formatter(ctx, command)
                await ctx.send(embed=help_embed)
            except AttributeError:
                await ctx.send(f'That is not a valid command! '
                               f'Please do `{await prefix(ctx)}help` for a list of valid commands!')

    @commands.command(description='Some bot statistics')
    async def stats(self, ctx):
        embed = discord.Embed(
            title='Stats',
            color=discord.Color.green()
        )
        embed.add_field(
            name='Version',
            value='Python: `{0.major}.{0.minor}.{0.micro}`\n'
                  'discord.py: `{1}`'.format(sys.version_info, discord.__version__),
            inline=True
        )
        stats = f'Servers: {len(self.bot.guilds)}\nUsers: {len(self.bot.users)}'
        embed.add_field(name='Statistics', value=stats, inline=True)
        t_owners = [await self.bot.fetch_user(i) for i in owners]
        f_owners = []
        for user in t_owners:
            f_owners.append(f'{user.name}#{user.discriminator}')
        embed.add_field(name='Owners', value="\n".join(f_owners), inline=True)
        embed.add_field(name='Uptime', value=formatters.uptime(ctx), inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
