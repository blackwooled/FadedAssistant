from discord.ext import commands
import os
import sqlite3
from dotenv import load_dotenv

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")


class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # DISPLAY STORE. !store
    @commands.command(name="store")
    async def store(self, ctx):
        # Fetch store items from the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_name, price FROM armory_data")
            armory_data = cursor.fetchall()

        if not armory_data:
            await ctx.send("The store is empty!")
            return

        store_message = "Welcome to the Grim Armory! Here are the currently available items:\n\n"
        for item_name, price in armory_data:
            store_message += f"{item_name}: {price} Crowns\n"

        store_message += "\nUse `!buy <item>` to buy an item from the store."
        await ctx.send(store_message)


    # BUY ITEMS. !buy
    @commands.command()
    async def buy(self, ctx, item: str):
        user_id = str(ctx.author.id)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Fetch user data (Crowns and Inventory)
            cursor.execute("SELECT crowns, inventory FROM user_data WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if result is None:
                await ctx.send("Your data does not exist. Please message to start!")
                return

            current_crowns, inventory = result
            inventory = eval(inventory)  # Convert the string list back to a Python list

            # Fetch the price of the item from the store
            cursor.execute("SELECT price FROM armory_data WHERE item_name = ?", (item,))
            store_item = cursor.fetchone()

            if store_item is None:
                await ctx.send(f"Item {item} not found in the store.")
                return

            item_cost = store_item[0]
            if current_crowns < item_cost:
                await ctx.send(f"You don't have enough Crowns to buy {item}. You need {item_cost} Crowns.")
                return

            # Deduct the Crowns and add the item to the inventory
            new_crowns = current_crowns - item_cost
            inventory.append(item)

            # Update the user's data in the database
            cursor.execute("""
            UPDATE user_data
            SET crowns = ?, inventory = ?
            WHERE user_id = ?
            """, (new_crowns, str(inventory), user_id))

            conn.commit()

        await ctx.send(f"Successfully bought {item} for {item_cost} Crowns! You now have {new_crowns} Crowns left.")


async def setup(bot):
    print("Setting up Store cog...")
    await bot.add_cog(Store(bot))