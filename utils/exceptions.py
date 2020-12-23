from discord.ext.commands import CheckFailure


class Error(CheckFailure):
    pass


class NotDM(Error):
    pass


class NotGuild(Error):
    pass


class NotBotOwner(Error):
    pass


class NotGuildOwner(Error):
    pass


class NotGuildAdmin(Error):
    pass
