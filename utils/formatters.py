import datetime
import discord
import math

from utils.prefix import prefix


# Date String Formatter
def date_string(time, unit):
    time = int(time)
    if time == 1:
        if unit == 'second':
            return f'1 {unit}'
        else:
            return f'1 {unit},'
    elif time == 0:
        return ''
    else:
        if unit == 'second':
            return f'{time} {unit}s'
        return f'{time} {unit}s,'


# Uptime formatter
def uptime(ctx):
    elapsedTime = datetime.datetime.utcnow() - ctx.bot.start_time
    days = divmod(elapsedTime.total_seconds(), 86400)
    hours = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)
    seconds = divmod(minutes[1], 1)

    dt = date_string(days[0], 'day')
    ht = date_string(hours[0], 'hour')
    mt = date_string(minutes[0], 'minute')
    st = date_string(seconds[0], 'second')

    times_before = [dt, ht, mt, st]
    times_after = []

    for time_unit in times_before:
        if time_unit == '':
            continue
        else:
            times_after.append(time_unit)

    if len(times_after) == 1:
        return times_after[0]
    else:
        beginning = ' '.join(times_after[:-1])
        end = f' and {times_after[-1]}'

        return f'{beginning}{end}'


# Help formatter
async def help_formatter(ctx, cmd):
    embed = discord.Embed(
        title=f'Help | {cmd.name}',
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )

    params = [
        key if str(value).count('=None') == 0
        else f'(Optional: {key})' for key, value in cmd.clean_params.items()
    ]
    if len(params) > 0:
        embed.add_field(
            name='Usage',
            value=f'```{await prefix(ctx)}{cmd} <{"> <".join(params)}>```',
            inline=False
        )
    else:
        embed.add_field(
            name='Usage',
            value=f'```{await prefix(ctx)}{cmd}```',
            inline=False
        )
    embed.add_field(
        name='Description',
        value=f'```\n{cmd.description if cmd.description != "" else "No Description Found!"}\n```'
    )

    return embed


# Cooldown formatter
def cooldown_formatter(cooldown):
    cooldown = round(cooldown)
    days = math.floor(cooldown / 86400)
    hours = math.floor(cooldown / 3600) - (days * 24)
    minutes = math.floor(cooldown / 60) - (hours * 60) - (days * 24 * 60)
    seconds = cooldown - (minutes * 60) - (hours * 3600) - (days * 86400)
    dt = date_string(days, 'day')
    ht = date_string(hours, 'hour')
    mt = date_string(minutes, 'minute')
    st = date_string(seconds, 'second')

    times_before = [dt, ht, mt, st]
    times_after = []

    for time_unit in times_before:
        if time_unit == '':
            continue
        else:
            times_after.append(time_unit)

    if len(times_after) == 1:
        return times_after[0]
    else:
        beginning = ' '.join(times_after[:-1])
        end = f' and {times_after[-1]}'

        return f'{beginning}{end}'


def error_formatter(ctx, error, notify=True):
    embed = discord.Embed(
        title='God damn it Karen!',
        description=f'A error has occurred in the {ctx.command} command!\n'
                    f'{"The Devs have been notified!" if notify else ""}',
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(
        name='Error in command',
        value=f'> ```py\n> {error}\n> ```'
    )

    return embed
