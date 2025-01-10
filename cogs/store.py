import discord 
from discord.ext import commands
import asyncio
import os
import sqlite3
from dotenv import load_dotenv
from utils.database import embed_builder

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
            cursor.execute("SELECT DISTINCT category_tag FROM armory_data WHERE category_tag != ?", ("Debug Item",))
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
            await ctx.send("You took too long to respond. Please try again.")

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

        # Create the embed
        embed = embed_builder(
            title=f"{category}s",
            description="\n".join(
                f"**{item[0]}** - {item[1]} Crowns\n{item[2]}" for item in pages[current_page]
            ),
        )
        embed.set_footer(text=f"Page {current_page + 1} of {len(pages)}")

        # Send the embed
        message = await ctx.send(embed=embed)

        # Add reactions for navigation
        if len(pages) > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=300.0, check=check)

            if str(reaction.emoji) == "⬅️" and current_page > 0:
                user_data["current_page"] -= 1
            elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                user_data["current_page"] += 1

            await message.delete()
            await self.show_page(ctx)
        except TimeoutError:
            await ctx.send("You took too long to respond. Please try again.")
            await message.clear_reactions()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        #Handles reaction navigation.
        if user.bot:
            return
        if user.id in self.store_pages:
            await self.show_page(reaction.message.channel)
    
        #embed = embed_builder(
        #title="Welcome to the Grim Armory!",
        #description=f"Here are the currently available items.\n Please select a category to begin!\n\n",
        #fields= (name='1. Consumable Items', value='Small, ready to use.'), (name= '2. Permanent Items', value= 'For the long haul.'), (name= 'my field title3', value= 'some stuff')
        #inline=True
       # footer_text="\nReact with a number to select the corresponding category."
       # )    
              
    #    message = await ctx.send(embed=embed)

        #embed = embed_builder(
        #title="Welcome to the Grim Armory!",
        #description=f"Here are the currently available {category.capitalize() if category else ''}items:\n\n",
        #footer_text="\nReact with the item number to select an item."
        #)
        #for item_name, price, item_description in items:
        #    embed.add_field(
        #        name=f"{item_name} - {price} Crowns",
        #        value=f"{item_description}" or "No description available.",
        #        inline=False
        #    )
        # Send the embed and add reactions for navigation
        #message = await ctx.send(embed=embed)

        # Add number reactions corresponding to items
    #    for i in range(min(len(armory_data), 10)):  # Discord limits to 10 reactions
    #        await message.add_reaction(f"{i + 1}\u20e3")  # Unicode for number emojis (1️⃣, 2️⃣, etc.)

        # Store data for later use
    #    self.bot.store_pages[message.id] = {"items": armory_data, "author_id": ctx.author.id}

    # Handles reactions to the store embed.
    #@commands.Cog.listener()
    #async def on_reaction_add(self, reaction, user):
                
    #    if user.bot:
    #        return

        # Check if the reaction is tied to a store page
    #    message_id = reaction.message.id
    #    if message_id not in self.bot.store_pages:
    #        return

        # Ensure only the original user can interact
    #    store_data = self.bot.store_pages[message_id]
    #    if user.id != store_data["author_id"]:
    #        await reaction.message.channel.send("You can't interact with this store menu.")
    #        return

        # Parse the selected item
    #    try:
    #        selected_index = int(reaction.emoji[0]) - 1
    #        selected_item = store_data["items"][selected_index]
    #        await self.confirm_purchase(reaction.message.channel, user, selected_item)
    #    except (IndexError, ValueError):
    #        pass  # Ignore invalid reactions

        # Remove user's reaction
    #    await reaction.remove(user)

    # Sends a confirmation message for purchasing an item.
    #async def confirm_purchase(self, channel, user, item):
    #    
    #    item_name, price, _ = item
    #    confirm_message = await channel.send(
    #        f"{user.mention}, are you sure you want to buy **{item_name}** for **{price} Crowns**? (y/n)"
    #    )

    #    def check(m):
    #        return m.author == user and m.content.lower() in ["y", "n"]

    #    try:
    #        response = await self.bot.wait_for("message", check=check, timeout=30)
    #        if response.content.lower() == "y":
    #            await self.purchase_item(channel, user, item_name, price)
    #        else:
    #            await channel.send("Purchase canceled.")
    #    except asyncio.TimeoutError:
    #        await channel.send("Purchase timed out.")
    #Processes the purchase of an item.
    #async def purchase_item(self, channel, user, item_name, price):
    
    #    user_id = str(user.id)

        # Check and update user crowns
    #    with sqlite3.connect(db_path) as conn:
    #        cursor = conn.cursor()

            # Retrieve user's crown balance
    #        cursor.execute("SELECT crowns, inventory FROM user_data WHERE user_id = ?", (user_id,))
    #        result = cursor.fetchone()

    #        current_crowns, inventory = result
    #        inventory = eval(inventory)  # Convert the string list back to a Python list

    #        if not current_crowns or current_crowns[0] < price:
    #            await channel.send(f"You don't have enough Crowns to buy {item_name}. You need {price} Crowns.")
    #            return

            # Deduct the price and add the item to the user's inventory
            #cursor.execute("UPDATE user_data SET crowns = crowns - ? WHERE user_id = ?", (price, user_id))
            #cursor.execute("SELECT inventory FROM user_data WHERE user_id = ?", (user_id,))
            #inventory = json.loads(cursor.fetchone()[0])
            #inventory.append({"item_name": item_name, "quantity": 1})
            #cursor.execute("UPDATE user_data SET inventory = ? WHERE user_id = ?", (json.dumps(inventory), user_id))
            #conn.commit()


            # Deduct the Crowns and add the item to the inventory
    #        new_crowns = current_crowns - price
    #        inventory.append(item_name)

            # Update the user's data in the database
    #        cursor.execute("""
    #        UPDATE user_data
    #        SET crowns = ?, inventory = ?
    #        WHERE user_id = ?
    #        """, (new_crowns, str(inventory), user_id))

    #        conn.commit()
    #    await channel.send(f"Successfully bought {item_name} for {price} Crowns! You now have {new_crowns} Crowns left.")


    # DISPLAY STORE. !store !s
    #@commands.command(name="store", aliases=["s"], help="Opens up the store for some fashionable shopping~")
    #async def store(self, ctx,):
    #    # Fetch store items from the database
    #    with sqlite3.connect(db_path) as conn:
    #        cursor = conn.cursor()
    #        cursor.execute("SELECT item_name, price, item_description FROM armory_data")
    #        armory_data = cursor.fetchall()

    #    if not armory_data:
    #        await ctx.send("The store is empty!")
    #        return
        
    #    embed = embed_builder(
    #    title="Welcome to the Grim Armory!",
    #    description="Here are the currently available items:\n\n",
    #    footer_text="\nUse `!buy <item>` to buy an item from the store."
    #    )
    #    for item_name, price, item_description in armory_data:
    #        embed.add_field(
    #            name=f"{item_name}: {price} Crowns",
    #            value=f"{item_description}" or "No description available.",
    #            inline=True
    #        )
    #    await ctx.send(embed=embed)


    # BUY ITEMS. !buy
    #@commands.command()
    #async def buy(self, ctx, item: str):
    #    user_id = str(ctx.author.id)

    #    with sqlite3.connect(db_path) as conn:
    #        cursor = conn.cursor()

    #        # Fetch user data (Crowns and Inventory)
    #        cursor.execute("SELECT crowns, inventory FROM user_data WHERE user_id = ?", (user_id,))
    #        result = cursor.fetchone()

    #        if result is None:
    #            await ctx.send("Your data does not exist. Please message to start!")
    #            return

    #        current_crowns, inventory = result
    #        inventory = eval(inventory)  # Convert the string list back to a Python list

            # Fetch the price of the item from the store
    #        cursor.execute("SELECT price FROM armory_data WHERE item_name = ?", (item,))
    #        store_item = cursor.fetchone()

    #        if store_item is None:
    #            await ctx.send(f"Item {item} not found in the store.")
    #            return

    #        item_cost = store_item[0]
    #        if current_crowns < item_cost:
    #            await ctx.send(f"You don't have enough Crowns to buy {item}. You need {item_cost} Crowns.")
    #            return

            # Deduct the Crowns and add the item to the inventory
    #        new_crowns = current_crowns - item_cost
    #        inventory.append(item)

    #        # Update the user's data in the database
    #        cursor.execute("""
    #        UPDATE user_data
    #        SET crowns = ?, inventory = ?
    #        WHERE user_id = ?
    #        """, (new_crowns, str(inventory), user_id))

    #        conn.commit()

    #    await ctx.send(f"Successfully bought {item} for {item_cost} Crowns! You now have {new_crowns} Crowns left.")


async def setup(bot):
    print("Setting up Store cog...")
    await bot.add_cog(Store(bot))
    #bot.store_pages = {}