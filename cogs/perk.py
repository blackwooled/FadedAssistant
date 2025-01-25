import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import asyncio
import os
import sqlite3

from dotenv import load_dotenv
from utils.database import update_crowns, is_admin#, assign_crowns_for_perks


# Load .env file to get variables
load_dotenv()
db_path = os.getenv("db_path")
guild_id = int(os.getenv("guild_id"))

class Perk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_perk_task.start()
    
    def cog_unload(self):
        self.daily_perk_task.cancel()

    @tasks.loop(hours=24)
    async def daily_perk_task(self):
        # Get the current time in CET+1 timezone
        cet = pytz.timezone("CET")
        now = datetime.now(cet)
    
        # If this is the first time running, calculate time until midnight
        if now.hour != 0 or now.minute != 0:
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_midnight = (next_midnight - now).total_seconds()
            await asyncio.sleep(seconds_until_midnight)
        
        # Run the crown assignment logic
        await self.assign_crowns_for_perks()
    
    @daily_perk_task.before_loop
    async def before_daily_perk_task(self):
        await self.bot.wait_until_ready()
    
    #assign_crowns_for_perks(self)

    async def assign_crowns_for_perks(self):
        #Assigns crowns to members based on their roles.
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Fetch all perks from the database
            cursor.execute("SELECT id, perk_name, bonus FROM perks_data")
            perks = cursor.fetchall()

            if not perks:
                print("No perks found in the database.")
                return
            
            # Get the guild object
            guild = self.bot.get_guild(guild_id)
            if not guild:
                print("Guild not found.")
                return    
            
            for member in guild.members:
                earnings = 0  # Reset for each member
                titles = []  # Collect perk titles for the member              
                
                for perk_id, perk_name, bonus in perks:
                    role = guild.get_role(perk_id)
                    if role and role in member.roles:  # Check if the member has the perk role
                        earnings += bonus
                        titles.append(perk_name)

                if earnings > 0:  # Only update crowns if the member has earned any    
                    await update_crowns(member.id, earnings, member)
                    print(f"Added {earnings} Crowns to {member.display_name} for perk(s): {', '.join(titles)}.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()  # Ensure the connection is always closed

    @commands.command(name="assigncrowns", help="Manually assigns crowns based on perks.", hidden=True)
    @is_admin()
    async def assign_crowns_command(self, ctx):
        #Command to manually invoke the crown assignment function.
        await ctx.send("Assigning crowns to members based on their perks...")
        
        try:
            await self.assign_crowns_for_perks()  # Call the crown assignment function
            await ctx.send("Crown assignment completed successfully!")
        except Exception as e:
            await ctx.send(f"An error occurred during crown assignment: {e}")

async def setup(bot):
    print("Setting up Perk cog...")
    await bot.add_cog(Perk(bot))