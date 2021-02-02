from discord.ext import commands
import statcord
import dbl
import json

with open("config.json") as f:
    cfg = json.load(f)
    dev = cfg["dev_mode"]


class Postings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not dev:
            self.api = statcord.Client(self.bot, cfg["statcord"])
            self.api.start_loop()
            # dbl.DBLClient(self.bot, cfg["top.gg"], autopost=True)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if not dev:
            self.api.command_run(ctx)


def setup(bot):
    bot.add_cog(Postings(bot))
