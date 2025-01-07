import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.database import init_db, add_user, update_crowns, add_item_to_inventory, import_armory_items

# Load the .env file to get the token and prefix for the bot
load_dotenv()
token = os.getenv("token")
prefix = os.getenv("prefix")

# Set up the bot's prefix and intents
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())

# BOT EVENTS ***************************************************

# Event that runs when the bot starts
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    init_db()  # Initialize the database when the bot starts
    import_armory_items()  #Import Shop Items when the bot starts

    # Automatically load cogs from the "cogs" folder
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load cog {cog_name}: {e}")
                

# Adds new users to the database
@bot.event
async def on_member_join(member):
    user_id = str(member.id)
    add_user(user_id)
    print(f"Added {member.name} to the database.")
    #export_users_to_json()

# Track Crowns when a user sends a message
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    user_id = str(message.author.id)
    # Calculate Crowns based on message length
    Gains = round(len(message.content)/10)
    # Update user Crowns
    update_crowns(user_id, Gains)
    #Below Function Exports user_data table content to user_data.json. Disable if redundant or inconvenient.
    #export_users_to_json()
    await bot.process_commands(message)  # Ensure commands still work


#!!!!! COMMANDS RESTRICTED TO ADMIN ROLES ****************************************************************

#ADD ITEM
@bot.command()
@commands.has_any_role("unstoppable force", "esteemed guest")
async def give_item(ctx, member: commands.MemberConverter, item_name: str, quantity: int, *, description: str):
    add_item_to_inventory(member.id, item_name, quantity, description)
    await ctx.send(f"{quantity}x {item_name} has been added to {member.name}'s inventory.")






# 1/1/25 LEAVING THIS BIT AS A WIP. THIS AND THE FUNCTION MODIFY_CROWNS ARE STILL WORK IN PROGRESS. BACKUP #3


#@bot.group()
#@commands.has_any_role("unstoppable force", "esteemed guest")  # Check role spelling and update accordingly
#async def admin(ctx):
#    if ctx.invoked_subcommand is None:
#        await ctx.send("Welcome to the admin section. Use `!admin c_add` or `!admin c_remove`.")

# Subcommand to add Crowns
#@admin.command()
#async def add(ctx, member: commands.MemberConverter, amount: int):
#    if amount < 0:
#        await ctx.send("You cannot add a negative amount of Crowns.")
#        return
        
#    member = await commands.MemberConverter().convert(ctx, user.id)
    
#    updated_crowns = modify_crowns(member.id, amount)
#    if updated_crowns is not None:
#        await ctx.send(f"{amount} Crowns have been added to {member.name}. They now have {updated_crowns} Crowns.")
#    else:
#        await ctx.send(f"{member.name} does not exist in the database.")

# Subcommand to remove Crowns
#@admin.command()
#async def remove(ctx, member: commands.MemberConverter, amount: int):
#    if amount < 0:
#        await ctx.send("You cannot remove a negative amount of Crowns.")
#        return

#    updated_crowns = modify_crowns(member.id, -amount)
#    if updated_crowns is not None:
#        await ctx.send(f"{amount} Crowns have been removed from {member.name}. They now have {updated_crowns} Crowns.")
#    else:
#        await ctx.send(f"{member.name} does not exist in the database.")

# Error handling for admin command group
#@admin.error
#async def admin_error(ctx, error):
#    if isinstance(error, commands.MissingAnyRole):
#        await ctx.send("You do not have access to the admin section.")
#    elif isinstance(error, commands.MissingRequiredArgument):
#        await ctx.send("Please specify the required arguments.")
#    elif isinstance(error, commands.BadArgument):
#        await ctx.send("Invalid input. Make sure to mention a valid user and a number.")

# Error handling for subcommands
#@add.error
#@remove.error
#async def subcommand_error(ctx, error):
#    if isinstance(error, commands.MissingRequiredArgument):
#        await ctx.send("Please specify a user and an amount.")
#    elif isinstance(error, commands.BadArgument):
#        await ctx.send("Invalid input. Make sure to mention a valid user and a number.")



# Run the bot with token
bot.run(token)

