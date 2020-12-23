import asyncio
import datetime
import json
import logging
import os
import time

import asyncpg
import discord
from discord.ext import commands

from utils import predicates, utils

with open("config.json") as f:
    cfg = json.load(f)
token = cfg["dev_token"]
owners = cfg["owners"]
db_login = cfg["db"]

activity_message = cfg["activity"]["message"]
activity_status = cfg["activity"]["status"]
if activity_status == "online":
    activity_status = discord.Status.online
elif activity_status == "idle":
    activity_status = discord.Status.idle
elif activity_status == "dnd":
    activity_status = discord.Status.dnd
else:
    activity_status = discord.Status.online

loop = asyncio.get_event_loop()


async def get_prefix(_client, message):
    if isinstance(message.channel, discord.DMChannel):
        prefix = "im!"
    else:
        async with _client.pool.acquire() as db:
            prefix = await db.fetchval(
                "SELECT prefix FROM guilds WHERE id=$1",
                message.guild.id
            )
    return prefix


class Bot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=get_prefix,
            intents=discord.Intents.all()
        )
        self.start_time = kwargs.pop("start_time")
        self.pool = kwargs.pop("pool")
        logging.basicConfig(
            format=f'%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )
        self.log = logging.getLogger("bot")
        self.log.setLevel(logging.INFO)
        self.discord_log = logging.getLogger("discord")
        self.discord_log.setLevel(logging.WARNING)

    async def on_connect(self):
        self.log.info("Connected to Discord")
        await self.change_presence(
            activity=discord.Activity(
                name="Starting Up",
                type=discord.ActivityType.playing
            ),
            status=discord.Status.dnd
        )

        # Add/Remove all Guilds that changed while bot was offline
        async with self.pool.acquire() as db:
            temp = await db.fetch(
                "SELECT id FROM guilds"
            )
            old_guilds = []
            for i in temp:
                old_guilds.append(i[0])
            old_guilds.sort()
            temp = self.guilds
            current_guilds = []
            for i in temp:
                current_guilds.append(i.id)
            current_guilds.sort()
            if old_guilds != current_guilds:
                changed = list(set(old_guilds) ^ set(current_guilds))
                for guild in changed:
                    if guild in old_guilds:
                        await db.execute(
                            "DELETE FROM guilds WHERE id=$1",
                            guild
                        )
                    else:
                        await db.execute(
                            f"INSERT INTO guilds (ID, prefix) VALUES ($1, $2)",
                            guild, "im!",
                        )

    async def on_ready(self):
        self.log.info("Bot is online.")
        self.log.info(f"Guild count: {len(client.guilds)}")
        await self.change_presence(
            activity=discord.Game(
                activity_message
            ),
            status=activity_status
        )


async def run():
    pool = await asyncpg.create_pool(**db_login)
    bot = Bot(
        pool=pool,
        start_time=datetime.datetime.utcnow()
    )
    bot.log.info("Connected to PostgreSQL Database")
    return bot


async def stop():
    await client.pool.close()
    await client.logout()


client = loop.run_until_complete(run())
client.remove_command('help')


@client.before_invoke
async def wait_before_commands(_ctx):
    await client.wait_until_ready()


# Ignore any other bot
@client.event
async def on_message(message):
    author = message.author
    channel = message.channel

    if author.bot:
        return
    try:
        if message.mentions[0] == client.user:
            embed = discord.Embed(
                title=(
                    f"My prefix is `{await get_prefix(client, message)}`! \n"
                    f"Type `{await get_prefix(client, message)}help` for more commands!"
                ),
                color=discord.Color.green()
            )
            msg = await channel.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
    except (IndexError, discord.NotFound, discord.Forbidden):
        pass

    await client.process_commands(message)


@client.event
async def on_guild_join(guild):
    async with client.pool.acquire() as db:
        await db.execute(
            f"INSERT INTO guilds (ID, prefix) VALUES ($1, $2)",
            guild.id, "im!"
        )


@client.event
async def on_guild_remove(guild):
    async with client.pool.acquire() as db:
        await db.execute(
            "DELETE FROM guilds WHERE id=$1",
            guild.id
        )


# Shutdown the bot
@client.command()
@predicates.bot_owner()
async def shutdown(ctx):
    await utils.delmsg(ctx)
    await ctx.send("Shutting down...")
    await client.change_presence(
        activity=discord.Activity(
            name="Shutting Down!",
            type=discord.ActivityType.playing
        ),
        status=discord.Status.dnd
    )
    await stop()


# Ping command
@client.command()
async def ping(ctx):
    embed = discord.Embed(
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow(),
        title="Ping!",
    )
    before = time.monotonic()
    msg = await ctx.send(embed=embed)
    _ping = (time.monotonic() - before) * 1000
    embed.title = f"Ping! {int(_ping)}"
    await msg.edit(embed=embed)


# Reload command
@client.command(aliases=['rl'], description='Reload a cog.')
@predicates.bot_owner()
async def reload(ctx, extension):
    await utils.delmsg(ctx)
    try:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Cog ``{extension}`` reloaded.')
        ctx.bot.log.info(f'Cog {extension} reloaded')
    except commands.ExtensionNotLoaded:
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Cog ``{extension}`` reloaded.')
        ctx.bot.log.info(f'Cog {extension} reloaded')


# Unload Cog
@client.command(description='Unload a cog.')
@predicates.bot_owner()
async def unload(ctx, extension):
    await utils.delmsg(ctx)
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Cog ``{extension}`` unloaded.')
    ctx.bot.log.info(f'Cog {extension} unloaded')


# Load cog
@client.command(description='Load a cog.')
@predicates.bot_owner()
async def load(ctx, extension):
    await utils.delmsg(ctx)
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Cog ``{extension}`` loaded.')
    ctx.bot.log.info(f'Cog {extension} loaded.')


# Cog loader
for file in os.listdir('./cogs'):
    if file.endswith('.py'):
        if file.startswith("_"):
            continue
        else:
            client.load_extension(f'cogs.{file[:-3]}')

for file in os.listdir('./utils'):
    if file.endswith('.py'):
        if file.startswith('_'):
            continue
        else:
            try:
                client.load_extension(f'utils.{file[:-3]}')
            except commands.NoEntryPointError:
                pass


if __name__ == "__main__":
    try:
        client.log.info("Establishing Connection to Discord")
        loop.run_until_complete(client.start(token))
    except KeyboardInterrupt:
        loop.run_until_complete(stop())
    finally:
        loop.close()
