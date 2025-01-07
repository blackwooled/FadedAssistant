from discord.ext import commands
import os
import sqlite3
from dotenv import load_dotenv

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



async def setup(bot):
    print("Setting up Admin cog...")
    await bot.add_cog(Admin(bot))