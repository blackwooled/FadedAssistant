import sqlite3
import json
import os

# List Of Database Functions

#Finding user_data.db in data folder
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "..", "data", "user_data.db")

# SQLite Database initialization

def init_db():
    print(f"Database path: {db_path}")  # Debugging line
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
def update_crowns(user_id, amount):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if the user exists
        cursor.execute("SELECT 1 FROM user_data WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result is None:
            # User doesn't exist, add them to the database
            print(f"Adding new user {user_id} to the database.")
            cursor.execute("""
            INSERT INTO user_data (user_id, crowns, inventory)
            VALUES (?, ?, ?)
            """, (user_id, 0, "[]"))

        # Update the crowns for the user
        print(f"Updating crowns for user {user_id}. Adding {amount} crowns.")
        cursor.execute("""
        UPDATE user_data
        SET crowns = crowns + ?
        WHERE user_id = ?
        """, (amount, user_id))

        conn.commit()

# Retrieve user data
def get_user_data(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crowns, inventory FROM user_data WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

# Add or Remove Crowns from a user (!!Admin Only!!)
def modify_crowns(user_id, amount):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crowns FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        if result:
            current_crowns = result[0]
            remaining_crowns = max(0, current_crowns + amount)
            cursor.execute("UPDATE users SET crowns = ? WHERE user_id = ?", (remaining_crowns, str(user_id)))
            conn.commit()
            return remaining_crowns
        else:
            return None

# Function To View Inventory
def view_inventory(user_id):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        if result:
            inventory = json.loads(result[0])
            return inventory
        else:
            return []

# Function To Remove Items From The Inventory (!!Admin Only!!)
def remove_item_from_inventory(user_id, item_name, quantity):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get the user's current inventory
        cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        if result:
            inventory = json.loads(result[0])
        else:
            inventory = []
        
        # Update or remove the item
        updated_inventory = []
        for item in inventory:
            if item["item_name"] == item_name:
                if item["quantity"] > quantity:
                    item["quantity"] -= quantity
                    updated_inventory.append(item)
                elif item["quantity"] == quantity:
                    continue  # Remove the item entirely
            else:
                updated_inventory.append(item)
        
        # Save the updated inventory back to the database
        cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (json.dumps(updated_inventory), str(user_id)))
        conn.commit()

# Add Item To Inventory (!!Admin Only!!)
def add_item_to_inventory(user_id, item_name, quantity, description):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get the user's current inventory
        cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        if result:
            inventory = json.loads(result[0])
        else:
            inventory = []
        
        # Check if the item already exists in the inventory
        for item in inventory:
            if item["item_name"] == item_name:
                item["quantity"] += quantity
                break
        else:
            # Add new item to the inventory
            inventory.append({"item_name": item_name, "quantity": quantity, "description": description})
        
        # Save the updated inventory back to the database
        cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (json.dumps(inventory), str(user_id)))
        conn.commit()

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
    

#Import Store Items
def load_armory_json():
    # Get the absolute path to the 'data' folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    armory_path = os.path.join(base_dir, "..", "data", "armory_items.json")
    
    # Connect to the database file
    armory_connection = sqlite3.connect(armory_path)
      
    with open(armory_connection, 'r') as file:
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