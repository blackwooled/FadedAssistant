from discord.ext import commands
import os
import sqlite3

#Finding user_data.db in data folder
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "..", "data", "user_data.db")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



async def setup(bot):
    print("Setting up Admin cog...")
    await bot.add_cog(Admin(bot))