import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.database import init_db, add_user, update_crowns

# Load .env file to get variables
load_dotenv()
token = os.getenv("token")
prefix = os.getenv("prefix")

# Set up the bot's prefix and intents, disable default help command
bot = commands.Bot(command_prefix=prefix, help_command=None, intents=discord.Intents.all())

# Event that runs when the bot starts
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    init_db()  # Initialize the database when the bot starts

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

# Track Crowns when a user sends a message
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    user_id = str(message.author.id)
    # Get name for more legible logs
    name = message.author

    # Calculate Crowns based on message length
    Gains = round(len(message.content)/10)
    # Update user Crowns
    await update_crowns(user_id, Gains, name)
    await bot.process_commands(message)  # Ensure commands still work

# Run the bot with token
bot.run(token)

