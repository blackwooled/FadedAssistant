import discord 
from discord.ext import commands
from discord.ui import Select, View
import os
import sqlite3
from dotenv import load_dotenv
from utils.database import embed_builder, manage_inventory

# Load .env file to get variables
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
        #Displays the landing page with store categories.

        store_user = ctx.author.id

        # Fetch categories from the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            #cursor.execute("SELECT DISTINCT category_tag FROM armory_data")
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
                        "\n".join(f"• {category}" for category in categories + ["Catalogue"]),
            footer_text="Please select a category to browse from the dropdown menu below."
        )

        # Send the embed and wait for a response
        message = await ctx.send(embed=embed)
        
        
        # Create the dropdown (select menu) dynamically
        options = [discord.SelectOption(label=category) for category in categories]
        options.append(discord.SelectOption(label="Catalogue"))
        # Create the select menu (without using a class)
        select = Select(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options
        )
        # Define the callback function for the select menu
        async def category_select_callback(interaction: discord.Interaction):
            # Check if the user interacting is the same as the one who invoked the store command
            if interaction.user.id != store_user:
                await interaction.response.send_message("You did not open the store. Please interact with the correct message.", ephemeral=True)
                return
            
            selected_category = interaction.data['values'][0]
            # Check if "Catalogue" was selected
            if selected_category == "Catalogue":
                # Call the storecatalogue command
                await interaction.response.send_message("Loading the catalogue...", ephemeral=True)
                await self.storecatalogue(ctx)  # Replace with the correct function call if needed
            else:
                # If another category is selected, handle it normally
                await interaction.response.send_message(f"You selected the category: **{selected_category}**")
                await self.show_category(ctx, selected_category)
            

        # Assign the callback function to the select menu
        select.callback = category_select_callback

        # Create the view and add the select menu to it
        view = View(timeout=300.0)
        view.add_item(select)

        # Send the message with the dropdown menu
        await ctx.send("Please select a category from the dropdown below to begin browsing:", view=view)

        # Wait for the View's timeout
        timed_out = await view.wait()
        if timed_out:
            await ctx.send("Purchase timed out. Please start again.")
        

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
        # Add a back-to-main-store emoji
        await message.add_reaction("🔙")

        def check(reaction, user):
            valid_emojis = number_emojis[:len(items)] + ["⬅️", "➡️", "🔙"]
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
            elif str(reaction.emoji) == "🔙":
                # Return to the main store front
                await message.delete()
                await self.store(ctx)  # Call the main store function
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

    
    # CATALOGUE OF ALPHABETICALLY ORGANISED ITEMS
    @commands.command(name="catalogue", help="Showcases a catalogue of all items available for purchase listed in alphabetical order.")
    async def storecatalogue(self, ctx):
        # Step 1: Query the database for items
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT item_name, price, item_description, category_tag, species_tag FROM armory_data ORDER BY item_name"
            )
            items = cursor.fetchall()

        if not items:
            await ctx.send("The catalogue is empty!")
            return

        # Paginate the items
        pages = [items[i:i + self.items_per_page] for i in range(0, len(items), self.items_per_page)]

        category = "Catalogue"
        # Store the pagination data
        self.store_pages[ctx.author.id] = {"category": category, "pages": pages, "current_page": 0}

        # Display the first page
        await self.show_page(ctx)

    # SELL ITEM. !sell
    #@commands.command(name="sell", help="Allows you to cash in the hard-earned fruits of your laborious questing.")
    #async def sell_item     

async def setup(bot):
    print("Setting up Store cog...")
    await bot.add_cog(Store(bot))