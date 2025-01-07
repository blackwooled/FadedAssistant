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

# SQLite Database initialization

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create the user_data table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_data (
        user_id TEXT PRIMARY KEY,
        crowns INTEGER DEFAULT 0,
        inventory TEXT DEFAULT '[]'
    )
    """)

    # Create the armory_data table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armory_data (
        item_name TEXT PRIMARY KEY,
        price INTEGER NOT NULL
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
            for item_name, item_data in armory_items.items():
                price = item_data["price"]

                # Use INSERT OR REPLACE to ensure we don't add duplicate items
                cursor.execute("""
                INSERT OR REPLACE INTO armory_data (item_name, price)
                VALUES (?, ?)
                """, (item_name, price))

            # Commit the transaction to save changes
            conn.commit()
        
        print("Items successfully added to the store!")

    except sqlite3.Error as e:
        print(f"Error occurred while inserting items: {e}")

    except FileNotFoundError:
        print("The JSON file could not be found.")

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
        cursor.execute("SELECT crowns, inventory FROM user_data WHERE user_id = ?", (user_id,))
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

# ADMIN ONLY COMMANDS **********************************************************************************

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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all user data
    cursor.execute("SELECT * FROM user_data")
    rows = cursor.fetchall()

    # Convert the data into a dictionary format
    data = {}
    for row in rows:
        user_id, crowns, inventory = row
        data[user_id] = {
            "Crowns": crowns,
            "Inventory": inventory
        }

    # Write the data to a JSON file with indenting
    with open("user_data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

    conn.close()
    print("Data exported to 'user_data.json'.")