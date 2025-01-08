import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
from utils.database import get_user_data, get_leaderboard, give_crowns, embed_builder

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #BALANCE. !balance
    @commands.command(name="balance", help="Shows your current Crowns balance.")
    async def balance(self, ctx):
        user_id = str(ctx.author.id)
        user_data = get_user_data(user_id)
        if user_data:
            crowns, inventory = user_data
            await ctx.send(f"Hello {ctx.author.display_name}! You have {crowns} Crowns.")
        else:
            await ctx.send("You don't have any funds yet. Start chatting to earn Crowns!")

    #GIVE MONEY TO OTHER USER. !give
    @commands.command(name="give", help="Gift Crowns to another user.\nSyntax: !give <amount> @user")
    async def give(self, ctx, amount: int, member: commands.MemberConverter):
            
            if amount <= 0:
                await ctx.send("You cannot give a negative amount.")
                return
            
            sender_id = ctx.author.id
            recipient_id = member.id

            if sender_id == recipient_id:
                await ctx.send("You cannot give Crowns to yourself.")
                return
    
            success = give_crowns(sender_id, amount, recipient_id)

            if success:
                await ctx.send(f"{ctx.author.mention} gave {amount} Crowns to {member.mention}!")
            else:
                await ctx.send("You do not have enough Crowns for this transaction or the user does not exist in my database.")


    # DISPLAY PROFILE. !profile !p
    @commands.command(name="profile", aliases=["p"], help="Displays your profile.")
    async def profile(self, ctx):
        user_id = str(ctx.author.id)

        result = get_user_data(user_id)

        if result is None:
            await ctx.send(f"Your data does not exist. Please message to start!")
            return

        crowns, inventory = result
        inventory = json.loads(inventory)  # Convert the string list back to a Python list

        if inventory:
            inventory_list = "\n".join([f"{item['item_name']} [x{item['quantity']}]" for item in inventory])
        else:
            inventory_list = "No items."
        
        user = await self.bot.fetch_user(int(user_id))
        avatar_url = user.avatar.url
        fields = {
        "Inventory": str(inventory_list)
        }
        
        embed = embed_builder(
        title=f"{user.display_name}'s Profile",
        description=f"{user.display_name}'s bank has {crowns} Crowns.",
        fields=fields,
        thumbnail_url=avatar_url
        )
        await ctx.send(embed=embed)

    # DISPLAY INVENTORY. !inventory
    @commands.command(name="inventory", aliases=["i"], help="Shows what you've collected in your inventory so far.")
    async def inventory(self, ctx):
        user_id = str(ctx.author.id)
        
        result = get_user_data(user_id)

        if result is None:
            await ctx.send(f"Your data does not exist. Please message to start!")
            return

        crowns, inventory = result
        inventory = json.loads(inventory)  # Convert the string list back to a Python list

        if inventory:
            inventory_list = "\n".join([f"{item['item_name']} [x{item['quantity']}]: {'itemdescription'}" for item in inventory])
            await ctx.send(f"Your inventory:\n{inventory_list}")
        else:
            await ctx.send("Your inventory is empty.")


    #LEADERBOARD. !leaderboard
    @commands.command(name="leaderboard", aliases=["l"], help="Displays the top 10 leaderboard.")
    async def leaderboard(self, ctx):
        leaderboard_data = get_leaderboard()
        leaderboard_message = "🏆 **Leaderboard** 🏆\n"
        for rank, (user_id, crowns) in enumerate(leaderboard_data, start=1):
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_message += f"{rank}. {user.display_name}: {crowns} Crowns\n"

        await ctx.send(leaderboard_message)

    #HELP. !help
    @commands.command(name="help", aliases=["h"], hidden=True)
    async def help(self, ctx):
        
        embed = embed_builder(
        title="Bot Commands",
        description="Here is a list of commands you can use with this bot:",
        )
        for command in self.bot.commands:
            if not command.hidden:  # Skip commands marked as hidden
                aliases = f" or !{'or !'.join(command.aliases)}" if command.aliases else ""
                embed.add_field(
                    name=f"!{command.name}{aliases}",
                    value=command.help or "No description available.",
                    inline=False
                )
        await ctx.send(embed=embed)

async def setup(bot):
    print("Setting up User cog...")
    await bot.add_cog(User(bot))