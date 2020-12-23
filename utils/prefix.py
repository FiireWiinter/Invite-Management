from discord import DMChannel


async def prefix(ctx):
    if isinstance(ctx.channel, DMChannel):
        return 'im!'
    else:
        async with ctx.bot.pool.acquire() as db:
            prefix_ = await db.fetchval(
                "SELECT prefix FROM guilds WHERE ID=$1",
                ctx.guild.id
            )
            return prefix_
