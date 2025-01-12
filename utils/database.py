import discord
from discord.ext import commands
import sqlite3
import json
import os
from dotenv import load_dotenv

# List Of Database Functions

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")
armory_path = os.getenv("armory_path")
admin_roles = os.getenv("admin_roles", "").split(",")
export_path = os.getenv("userexport_path")

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
    conn.commit()
    conn.close()

#Import Store Items
def load_armory_json():

    armory_link = os.path.join(armory_path)
      
    with open(armory_link, 'r') as file:
        return json.load(file)

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
        print("The JSON file could not be found.")

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

# Add a new user to the database
def add_user(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO user_data (user_id, crowns, inventory)
        VALUES (?, ?, ?)
        """, (user_id, 0, "[]"))
        conn.commit()

# Update crowns for a user
def update_crowns(user_id, amount, name):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if the user exists
        cursor.execute("SELECT 1 FROM user_data WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result is None:
            # User doesn't exist, add them to the database
            print(f"Adding new user {name.display_name} to the database.")
            cursor.execute("""
            INSERT INTO user_data (user_id, crowns, inventory)
            VALUES (?, ?, ?)
            """, (user_id, 0, "[]"))

        # Update the crowns for the user
        print(f"Updating Crowns for user {name.display_name}. Adding {amount} Crowns.")
        cursor.execute("""
        UPDATE user_data
        SET crowns = crowns + ?
        WHERE user_id = ?
        """, (amount, user_id))

        conn.commit()
    return result

# Retrieve user data
def get_user_data(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crowns, inventory, characters FROM user_data WHERE user_id = ?", (user_id,))
        return cursor.fetchone()
      
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

# Admin Role Check
def is_admin():
    def predicate(ctx):
        return any(role.name in admin_roles for role in ctx.author.roles)
    return commands.check(predicate)

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

# TROUBLESHOOTING FUNCTION TO EXPORT USER_DATA TABLE FROM DATABASE TO JSON FILE
def export_users_to_json():
    export_folder = os.path.dirname(export_path)
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_data")
        
        # Get column names for the dictionary keys
        columns = [description[0] for description in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Convert rows to a list of dictionaries
        data = [dict(zip(columns, row)) for row in rows]

    with open(export_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

    return export_path  # Return the file name