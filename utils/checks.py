
from discord.ext import commands
from discord.ext.commands import has_role, MissingRole

# Check for admin or moderator roles
def admin_or_moderator():
    def predicate(ctx):
        if any(role.name in ["unstoppable force", "esteemed guest"] for role in ctx.author.roles):
            return True
        raise MissingRole("You do not have the required clearance to use this command.")
    return commands.check(predicate)