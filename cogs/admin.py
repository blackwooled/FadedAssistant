from discord.ext import commands
import os
import sqlite3
import discord
from dotenv import load_dotenv
from utils.database import manage_inventory, is_admin, embed_builder, export_users_to_json

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")
export_path = os.getenv("userexport_path")


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    
    @commands.group(name="admin", invoke_without_command=True, hidden=True)
    @is_admin()
    async def admin_group(self, ctx):      
        # Get the Admin cog
        admin_cog = self.bot.get_cog("Admin")
        if not admin_cog:
            await ctx.send("Admin cog not found.")
            return

        embed = embed_builder(
        title="Admin Commands",
        description="Welcome to the admin section. Here are the available admin commands:",
        )
        
        for command in admin_cog.get_commands():
            embed.add_field(
                    name=f"!{command.name}",
                    value=command.help or "No description available.",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    # ADD OR REMOVE ITEMS
    @admin_group.command(name="items", help="Add or remove items from user inventories. Syntax: !admin items <user> <item_name> <+-quantity>")
    async def manage_items(self, ctx, member: commands.MemberConverter, item_name: str, quantity: int):
        manage_inventory(member.id, item_name, quantity)
        if quantity>0:
            await ctx.send(f"{quantity} {item_name} has been added to {member.display_name}'s inventory.")
        else:
            await ctx.send(f"{-quantity} {item_name} has been removed from {member.display_name}'s inventory.")
    
    @admin_group.command(name="print", help="Prints current user database to json. Used for backing up data and updating the bot.")
    async def export_users(self, ctx):
        #Export the user_data table to a JSON file.
        try:
            export_users_to_json()  # Call the function to export data
            await ctx.send(file=discord.File(export_path))
            await ctx.send(f"User data exported successfully to `{export_path}`.")      
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @admin_group.command(name="money", help = "Adds or removes Crowns from user balance. Syntax: !admin money <user> <+-amount>")
    async def manage_money(self, ctx, member: commands.MemberConverter, amount: int):
       
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user exists in the database
                cursor.execute("SELECT crowns FROM user_data WHERE user_id = ?", (str(member.id),))
                result = cursor.fetchone()

                if result:
                    current_crowns = result[0]

                    if current_crowns + amount < 0:
                        print(f"{member.display_name} does not have enough on balance to remove {abs(amount)} Crowns.")
                        await ctx.send(f"{member.display_name} does not have enough on balance to remove {abs(amount)} Crowns.")
                        return

                    # Update the user's Crown balance
                    print(f"Updating Crowns for user {member.display_name}. Adding {(amount)} Crowns.")
                    cursor.execute("UPDATE user_data SET crowns = crowns + ? WHERE user_id = ?",(amount, str(member.id)),)
                    new_balance = result[0] + amount
                    conn.commit()
                else:    
                    await ctx.send(f"{member.display_name} does not have a profile in the database.")
                    return
                
            operation1 = "added" if amount > 0 else "removed"
            operation2 = "to" if amount > 0 else "from"
            await ctx.send(f"Successfully {operation1} {abs(amount)} Crowns {operation2} {member.mention}'s account. They now have {new_balance} Crowns.")
        except sqlite3.Error as e:
            await ctx.send(f"Failed to manage Crowns due to a database error: {e}")


    
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



async def setup(bot):
    print("Setting up Admin cog...")
    await bot.add_cog(Admin(bot))