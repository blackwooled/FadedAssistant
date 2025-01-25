import discord
from discord.ext import commands
import sqlite3
import aiosqlite
import json
import os
from dotenv import load_dotenv

# List Of Database Functions

# Load .env file to get variables
load_dotenv()
db_path = os.getenv("db_path")
armory_path = os.getenv("armory_path")
bestiary_path = os.getenv("bestiary_path")
admin_roles = [int(role_id) for role_id in os.getenv("admin_roles", "").split(",")]
export_path = os.getenv("userexport_path")
guild_id = os.getenv("guild_id")

# SQLite Database initialization

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create the user_data table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        user_id TEXT PRIMARY KEY,
        crowns INTEGER DEFAULT 0,
        inventory TEXT DEFAULT '[]',
        characters TEXT DEFAULT '[]'
    )
    """)

    if os.path.exists(export_path):
        import_user_data()

    # Create the armory_data table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armory_data (
        item_name TEXT PRIMARY KEY,
        price INTEGER NOT NULL,
        item_description TEXT,
        category_tag TEXT,
        species_tag TEXT,
        item_icon TEXT
    )
    """)

    if os.path.exists(armory_path):
        import_armory_items()

    #Creates the bestiary table in the database if it doesn't already exist.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bestiary (
        nmy_name TEXT PRIMARY KEY,
        nmy_description TEXT,
        drop_pool TEXT DEFAULT '[]',
        element TEXT,
        special TEXT,
        hp INTEGER NOT NULL,
        attack INTEGER,
        speed INTEGER,
        rarity TEXT,
        encounter_rate REAL,
        nmy_icon TEXT
    )
    """)
    
    # Create the perks_data table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS perks_data (
        id INTEGER PRIMARY KEY,
        perk_name TEXT,
        bonus INTEGER DEFAULT 0
    )
    """)

    if os.path.exists(bestiary_path):
        import_bestiary()
    
    conn.commit()
    conn.close()

def import_armory_items():
    try: 
        # Load the items from the JSON file           
        armory_items = load_armory_json()
        
        # Open a connection to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Insert items into the store_items table
            for item_name, item_data, in armory_items.items():

                # Use INSERT OR REPLACE to ensure we don't add duplicate items
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO armory_data (item_name, price, item_description, category_tag, species_tag, item_icon)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (item_name, item_data["price"], item_data["item_description"], item_data["category_tag"], item_data["species_tag"], item_data.get("item_icon")))
                except sqlite3.Error as e:
                    print(f"Error occurred while inserting {item_name}: {e}")

            # Commit the transaction to save changes
            conn.commit()
        
        print("Items successfully added to the store!")  
    except FileNotFoundError:
        print("The inventory JSON file could not be found.")

def import_bestiary():
    try:          
        bestiary_items = load_bestiary_json()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            for nmy_name, nmy_data, in bestiary_items.items():

                # Use INSERT OR REPLACE to ensure we don't add duplicate items
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO bestiary (nmy_name, nmy_description, drop_pool, element, special, hp, attack, speed, rarity, encounter_rate, nmy_icon)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nmy_name, nmy_data["nmy_description"], nmy_data["drop_pool"], nmy_data["element"], nmy_data["special"], nmy_data["hp"], nmy_data["attack"], nmy_data["speed"], nmy_data["rarity"], nmy_data["encounter_rate"], nmy_data.get("nmy_icon"), ))
                except sqlite3.Error as e:
                    print(f"Error occurred while inserting {nmy_name}: {e}")
            
            conn.commit()
        
        print("Enemies successfully added to the bestiary!")  
    except FileNotFoundError:
        print("The bestiary JSON file could not be found.")

def import_user_data():
    try:
        # Ensure the JSON file exists
        if not os.path.exists(export_path):
            print(f"Import file not found: {export_path}")
            return
        
        # Read the JSON file
        with open(export_path, "r", encoding="utf-8") as json_file:
            user_data = json.load(json_file)
        
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for user_id, data in user_data.items():
                crowns = data.get("crowns", 0)
                inventory = json.dumps(data.get("inventory", []))  # Convert list to JSON string
                characters = json.dumps(data.get("characters", []))  # Convert list to JSON string
                
                # Check if the user_id already exists
                cursor.execute("SELECT user_id FROM user_data WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                if result:
                    # Update existing user data
                    cursor.execute(
                        """
                        UPDATE user_data
                        SET crowns = ?, inventory = ?, characters = ?
                        WHERE user_id = ?
                        """,
                        (crowns, inventory, characters, user_id),
                    )
                else:
                    # Insert new user data
                    cursor.execute(
                        """
                        INSERT INTO user_data (user_id, crowns, inventory, characters)
                        VALUES (?, ?, ?, ?)
                        """,
                        (user_id, crowns, inventory, characters),
                    )
            
            conn.commit()
            print(f"User data successfully imported from {export_path}.")
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Add a new user to the database
def add_user(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO user_data (user_id, crowns, inventory)
        VALUES (?, ?, ?)
        """, (user_id, 0, "[]"))
        conn.commit()

# embed builder function
def embed_builder(title, description, color=discord.Color.dark_gold(), fields=None, thumbnail_url=None, image_url=None, footer_text=None):
    embed = discord.Embed(title=title, description=description, color=color)

    # Add fields to the embed if provided
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)
    
    # Optionally add a footer or image here if needed
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    if image_url:
        embed.set_image(url=image_url)
    
    if footer_text:
        embed.set_footer(text=footer_text)
    else:
        embed.set_footer(text="Use !help to learn more about commands.")
    return embed

def export_users_to_json():
    try:
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query to fetch all data from user_data table
            cursor.execute("SELECT user_id, crowns, inventory, characters FROM user_data")
            rows = cursor.fetchall()
            
            # Transform data into a dictionary
            user_data = {}
            for row in rows:
                user_id = row[0]
                crowns = row[1]
                inventory = json.loads(row[2]) if row[2] else []  # Convert JSON string to Python list
                characters = json.loads(row[3]) if row[3] else []  # Convert JSON string to Python list
                
                user_data[user_id] = {
                    "crowns": crowns,
                    "inventory": inventory,
                    "characters": characters,
                }
            
            # Ensure the export folder exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Write the dictionary to a JSON file
            with open(export_path, "w", encoding="utf-8") as json_file:
                json.dump(user_data, json_file, indent=4, ensure_ascii=False)
            
            print(f"User data successfully exported to {export_path}.")
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Retrieve leaderboard
def get_leaderboard():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT user_id, crowns
        FROM user_data
        ORDER BY crowns DESC
        LIMIT 10
        """)
        return cursor.fetchall()

# Retrieve user data
def get_user_data(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crowns, inventory, characters FROM user_data WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

# give_crowns
def give_crowns(giver, amount, recipient):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crowns FROM user_data WHERE user_id = ?", (str(giver),))
        giver_crowns = cursor.fetchone()
        
        if not giver_crowns or giver_crowns[0] < amount:
            return False 

        cursor.execute("UPDATE user_data SET crowns = crowns - ? WHERE user_id = ?", (amount, str(giver)))

        # Get the recipient's balance
        cursor.execute("SELECT crowns FROM user_data WHERE user_id = ?", (str(recipient),))
        recipient_balance = cursor.fetchone()
        if not recipient_balance:
            # If the recipient doesn't exist in the database, add them
            cursor.execute("INSERT INTO user_data (user_id, crowns, inventory) VALUES (?, ?, ?)", 
                           (str(recipient), amount, json.dumps([])))
        else:
            # Add crowns to the recipient
            cursor.execute("UPDATE user_data SET crowns = crowns + ? WHERE user_id = ?", (amount, str(recipient)))
        conn.commit()
        return True

# Admin Role Check
def is_admin():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True  # Allow server administrators
        user_roles = [role.id for role in ctx.author.roles]
        return any(role_id in admin_roles for role_id in user_roles)
    return commands.check(predicate)

#Import Store Items
def load_armory_json():

    armory_link = os.path.join(armory_path)
      
    with open(armory_link, 'r') as file:
        return json.load(file)
    
#Import Enemies From Bestiary
def load_bestiary_json():

    bestiary_link = os.path.join(bestiary_path)
      
    with open(bestiary_link, 'r') as file:
        return json.load(file)

#Import previous data about users  
def load_user_data():
    import_user_link = os.path.join(export_path)
      
    with open(import_user_link, 'r') as file:
        return json.load(file)

# Function To Add or Remove Items From The Inventory
def manage_inventory(user_id, item_name, quantity):
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get the user's current inventory
        cursor.execute("SELECT inventory FROM user_data WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        if result:
            inventory = json.loads(result[0])  # Parse the JSON string into a Python list
        else:
            inventory = []
        
        # Check if the item already exists in the inventory
        for item in inventory:
            if item["item_name"] == item_name:
                item["quantity"] += quantity
                # Remove the item if quantity drops to 0 or below
                if item["quantity"] <= 0:
                    inventory.remove(item)
                break
        else:
            # Add new item to the inventory if quantity is positive
            if quantity > 0:
                inventory.append({"item_name": item_name, "quantity": quantity})
        
        # Save the updated inventory back to the database
        cursor.execute("UPDATE user_data SET inventory = ? WHERE user_id = ?", (json.dumps(inventory), str(user_id)))
        conn.commit()

# Let users manage the characters tied to their account
def manage_user_characters(user_id, character_name, character_title, character_sheet_url, action):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Fetch the current characters
        cursor.execute("SELECT characters FROM user_data WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result:
            characters = json.loads(result[0])
        else:
            # If the user doesn't exist in the table, create an entry
            cursor.execute("INSERT INTO user_data (user_id) VALUES (?)", (user_id,))
            characters = []
        
        if action == "add":
            # Add the character
            new_character = {
                "name": character_name,
                "title": character_title,
                "sheet_url": character_sheet_url
            }
            characters.append(new_character)
            print(f"Added character: {new_character}")
        elif action == "remove":
            # Remove the character by name
            characters = [char for char in characters if char["name"] != character_name]
            print(f"Removed character with name: {character_name}")
        else:
            raise ValueError("Invalid action. Use 'add' or 'remove'.")
        
        # Update the characters in the database
        cursor.execute("UPDATE user_data SET characters = ? WHERE user_id = ?", (json.dumps(characters), user_id))
        conn.commit()

# Update crowns for a user
async def update_crowns(user_id, amount, name):
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.cursor()
        
        # Check if the user exists
        await cursor.execute("SELECT 1 FROM user_data WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()

        if result is None:
            # User doesn't exist, add them to the database
            print(f"Adding new user {name.display_name} to the database.")
            await cursor.execute("""
            INSERT INTO user_data (user_id, crowns, inventory)
            VALUES (?, ?, ?)
            """, (user_id, 0, "[]"))

        # Update the crowns for the user
        print(f"Updating Crowns for user {name.display_name}. Adding {amount} Crowns.")
        await cursor.execute("""
        UPDATE user_data
        SET crowns = crowns + ?
        WHERE user_id = ?
        """, (amount, user_id))

        await conn.commit()
    return result