import discord 
from discord.ext import commands
import asyncio
import os
import json
import sqlite3
from dotenv import load_dotenv
from utils.database import embed_builder, manage_inventory

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")


class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items_per_page = 5  # Adjust this number to fit your layout
        self.store_pages = {}  # Track store pages for each user interaction
    
    # DISPLAY STORE. !store !s
    @commands.command(name="store", aliases=["s"], help="Opens up the store for some fashionable shopping~")
    async def store(self, ctx):
        #Displays the landing page with store categories."""
        # Fetch categories from the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category_tag FROM armory_data")
            #cursor.execute("SELECT DISTINCT category_tag FROM armory_data WHERE category_tag != ?", ("Debug Item",))
            #The part after WHERE is to exclude Debug Items from the fetched list.
            categories = [row[0] for row in cursor.fetchall()]

        if not categories:
            await ctx.send("The store is currently empty.")
            return

        # Create the embed for the landing page
        embed = embed_builder(
            title="Welcome to the Grim Armory!",
            description="Here are the currently available items:\n\nPlease select a category to begin browsing.\n\n" + 
                        "\n".join(f"• {category}" for category in categories),
            footer_text="Type the category name to browse items."
        )

        # Send the embed and wait for a response
        message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300.0, check=check)
            category = response.content.strip()

            if category in categories:
                await self.show_category(ctx, category)
            else:
                await ctx.send("Invalid category. Please try again.")
        except TimeoutError:
            await ctx.send("Purchase timed out.")

    async def show_category(self, ctx, category):
        #Displays the items in the selected category with pagination.
        # Fetch items for the category
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT item_name, price, item_description FROM armory_data WHERE category_tag = ?",
                (category,)
            )
            items = cursor.fetchall()

        if not items:
            await ctx.send(f"No items found in category '{category}'.")
            return

        # Paginate the items
        pages = [items[i:i + self.items_per_page] for i in range(0, len(items), self.items_per_page)]

        # Store the pagination data
        self.store_pages[ctx.author.id] = {"category": category, "pages": pages, "current_page": 0}

        # Display the first page
        await self.show_page(ctx)

    async def show_page(self, ctx):
        #Displays the current page of items.
        user_data = self.store_pages.get(ctx.author.id)
        if not user_data:
            return

        current_page = user_data["current_page"]
        pages = user_data["pages"]
        category = user_data["category"]

        # Prepare the embed content
        items = pages[current_page]
        numbered_items = [
        f"{index + 1}. **{item[0]}** - {item[1]} Crowns\n{item[2]}"
        for index, item in enumerate(items)
        ]

        # Create the embed
        embed = embed_builder(
            title=f"{category}s",
            description="Please react with a number to select the corresponding item.\n\n" + "\n\n".join(numbered_items),
        )
        embed.set_footer(text=f"Page {current_page + 1} of {len(pages)}")

        # Send the embed
        message = await ctx.send(embed=embed)

       # Add reactions for navigation and item selection
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i in range(len(items)):  # Add only as many reactions as there are items
            await message.add_reaction(number_emojis[i])

        if len(pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

        def check(reaction, user):
            valid_emojis = number_emojis[:len(items)] + ["⬅️", "➡️"]
            return user == ctx.author and str(reaction.emoji) in valid_emojis

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=300.0, check=check)

            if str(reaction.emoji) == "⬅️" and current_page > 0:
                user_data["current_page"] -= 1
                await message.delete()
                await self.show_page(ctx)
            elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                user_data["current_page"] += 1
                await message.delete()
                await self.show_page(ctx)
            elif str(reaction.emoji) in number_emojis:
                selected_index = number_emojis.index(str(reaction.emoji))
                selected_item = items[selected_index]
            
            # Confirm the purchase
            await ctx.send(f"Are you sure you want to buy **{selected_item[0]}** for {selected_item[1]} Crowns? (y/n)")

            def confirmation_check(m):
                return m.author == ctx.author and m.content.lower() in ["y", "n"]

            confirmation = await self.bot.wait_for("message", timeout=300.0, check=confirmation_check)
            if confirmation.content.lower() == "y":
                # Call a function to handle the purchase logic
                await self.purchase_item(ctx, user, selected_item[0], selected_item[1])
            else:
                await ctx.send("Purchase canceled.")
        
            await message.clear_reactions()
        except TimeoutError:
            await ctx.send("Purchase timed out.")
            await message.clear_reactions()


    async def purchase_item(self, channel, user, item_name, price):
    
        user_id = str(user.id)

        # Check and update user crowns
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Retrieve user's crown balance
            cursor.execute("SELECT crowns FROM user_data WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            current_crowns = result[0]

            if not current_crowns or current_crowns < price:
                await channel.send(f"You don't have enough Crowns to buy {item_name}. You need {price} Crowns.")
                return

            # Deduct the Crowns and add the item to the inventory
            new_crowns = current_crowns - price

            manage_inventory(user_id, item_name, 1)
            cursor.execute("UPDATE user_data SET crowns = ? WHERE user_id = ?", (new_crowns, user_id))

            conn.commit()
        await channel.send(f"Successfully bought {item_name} for {price} Crowns! You now have {new_crowns} Crowns left.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        #Handles reaction navigation.
        if user.bot:
            return
        if user.id in self.store_pages:
            await self.show_page(reaction.message.channel)
           

async def setup(bot):
    print("Setting up Store cog...")
    await bot.add_cog(Store(bot))