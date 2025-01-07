from discord.ext import commands
import os
import json
from dotenv import load_dotenv
from utils.database import view_inventory, get_user_data, get_leaderboard

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #BALANCE. !balance
    @commands.command()
    async def balance(self, ctx):
        user_id = str(ctx.author.id)
        user_data = get_user_data(user_id)
        if user_data:
            crowns, inventory = user_data
            await ctx.send(f"{ctx.author.display_name}, you have {crowns} Crowns.")
        else:
            await ctx.send("You don't have any funds yet. Start chatting to earn Crowns!")


    # DISPLAY PROFILE. !profile
    @commands.command()
    async def profile(self, ctx):
        user_id = str(ctx.author.id)

        #command get_user_data does exactly this, need to change this

        # Fetch user data from the database
        
        result = get_user_data(user_id)

        if result is None:
            await ctx.send(f"Your data does not exist. Please message to start!")
            return

        crowns, inventory = result
        inventory = json.loads(inventory)  # Convert the string list back to a Python list

        # Display user's data
        inventory_list = ", ".join(inventory) if inventory else "No items"
        user = await self.bot.fetch_user(int(user_id))
        await ctx.send(f"{user.display_name}'s Profile:\nCrowns: {crowns}\nInventory: {inventory_list}")


    # DISPLAY INVENTORY. !inventory
    @commands.command()
    async def inventory(self, ctx):
        user_id = ctx.author.id
        inventory = view_inventory(user_id)
        if inventory:
            inventory_list = "\n".join([f"{item['item_name']} (x{item['quantity']}): {item['description']}" for item in inventory])
            await ctx.send(f"Your inventory:\n{inventory_list}")
        else:
            await ctx.send("Your inventory is empty.")


    #LEADERBOARD. !leaderboard
    @commands.command()
    async def leaderboard(self, ctx):
        leaderboard_data = get_leaderboard()
        leaderboard_message = "🏆 **Leaderboard** 🏆\n"
        for rank, (user_id, crowns) in enumerate(leaderboard_data, start=1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_message += f"{rank}. {user.display_name}: {crowns} Crowns\n"

        await ctx.send(leaderboard_message)

async def setup(bot):
    print("Setting up User cog...")
    await bot.add_cog(User(bot))