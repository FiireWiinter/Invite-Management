from discord import DMChannel, Forbidden, NotFound


async def delmsg(ctx):
    if isinstance(ctx.channel, DMChannel):
        return
    else:
        try:
            await ctx.message.delete()
        except Forbidden or NotFound:
            return
