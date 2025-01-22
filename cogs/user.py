from discord import Message
from discord.ext import commands
import os
import json
import re
from dotenv import load_dotenv
from utils.database import get_user_data, get_leaderboard, give_crowns, embed_builder, manage_user_characters

# Load .env file to get user_data.db path
load_dotenv()
db_path = os.getenv("db_path")

# Regex for URL validation
url_pattern = re.compile(
    r'^(https?:\/\/)?'  # http:// or https://
    r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # Domain
    #r'(:[0-9]{1,5})?'  # Optional port
    #r'(\/\S*)?$'  # Path
)

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #BALANCE. !balance
    @commands.command(name="balance", help="Shows your current Crowns balance.")
    async def balance(self, ctx):
        user_id = str(ctx.author.id)
        user_data = get_user_data(user_id)
        if user_data:
            crowns, inventory, characters = user_data
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

        crowns, inventory, characters = result
        # vv debugging line to print inventory into console logs
        #print(inventory)
        inventory = json.loads(inventory)  # Convert the string list back to a Python list
        characters = json.loads(characters)

        if inventory:
            inventory_list = "\n".join([f"{item['item_name']} [x{item['quantity']}]" for item in inventory])
        else:
            inventory_list = "No items."
        
        if characters:
            characters_list = "\n".join([f"[{char['name']} - {char['title']}]({char['sheet_url']})" for char in characters])
        else:
            characters_list = "No characters."
        
        user = await self.bot.fetch_user(int(user_id))
        avatar_url = user.avatar.url
        fields = {
        "Inventory": str(inventory_list),
        "Characters": str(characters_list)
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

        crowns, inventory, characters = result
        inventory = json.loads(inventory)  # Convert the string list back to a Python list

        if inventory:
            inventory_list = "\n".join([f"{item['item_name']} [x{item['quantity']}]" for item in inventory])
            await ctx.send(f"Your inventory:\n{inventory_list}")
        else:
            await ctx.send("Your inventory is empty.")

    # Add or remove characters from user profile. !character, !c
    @commands.command(name="character", aliases=["c"], help="Add or remove characters from your profile.\n Syntax: !character add <name> <title> <URL> || !character remove <name>")
    async def manage_character(self, ctx, action, name, title=None, sheet_url=None):
        
        #Add or remove characters from the user's character list.
        #Usage:
        #- Add: !character add "Character Name" "Title" "http://sheet.url"
        #- Remove: !character remove "Character Name"
        
        user_id = str(ctx.author.id)
        
        try:
            if action == "add":
                if not (name and title and sheet_url):
                    await ctx.send("You need to provide a name, a title, and a link to the character sheet in order to add a character.\n The correct syntax is as follows: **!character add <name> <title> <URL>**.")
                    await self.add_character_help(ctx)
                    return
                
                manage_user_characters(user_id, name, title, sheet_url, action="add")
                await ctx.send(f"Character '{name}' added successfully!")
            
            elif action == "remove":
                if not name:
                    await ctx.send("Please provide the name of the character to remove.\n The correct syntax is as follows: **!character remove <name>**.")
                    return
                
                manage_user_characters(user_id, name, None, None, action="remove")
                await ctx.send(f"Character '{name}' removed successfully!")
            
            else:
                await ctx.send("Invalid action. Use 'add' or 'remove'.")
                await self.add_character_help(ctx)
        
        except Exception as e:
            await print(f"An error occurred: {e}")
            await ctx.send(f"An error occurred! Better poke an admin.")

    # help function for character adding (on user's request)
    async def add_character_help(self, ctx):
        # Guides the user through adding a character interactively.
        
        def check_author(message: Message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            # Step 1: Ask if the user needs help
            await ctx.send("I can offer you guidance. Would you like some help? [y/n]")
            help_response = await self.bot.wait_for("message", check=check_author, timeout=60)

            if help_response.content.lower() not in ["y", "yes"]:
                await ctx.send("No problemo! Please retry the command when you're ready or poke a mod if you'd prefer a human to help c:")
                return
            
            # Step 2: Ask for character name
            await ctx.send("Please type the name of your character:")
            name_response = await self.bot.wait_for("message", check=check_author, timeout=60)
            if not name_response.content.strip():
                await ctx.send("Character name cannot be empty. Please try again.")
                return
            char_name = name_response.content

            # Step 3: Ask for character title
            await ctx.send("Awesome! Please type the title of your character:")
            title_response = await self.bot.wait_for("message", check=check_author, timeout=60)
            char_title = title_response.content

            # Step 4: Ask for character sheet URL
            await ctx.send("Great! One last thing: please give me the link to your character sheet:")
            url_response = await self.bot.wait_for("message", check=check_author, timeout=60)
            sheet_url = url_response.content

            # Validate URL format
            #if not sheet_url.startswith("http://") and not sheet_url.startswith("https://"):
            #    await ctx.send("That doesn't look like a valid URL. Please try again.")
            #    return
            if not re.match(url_pattern, sheet_url):
                await ctx.send("The URL provided is invalid. Please try again.")
                return

            user_id = str(ctx.author.id)
            manage_user_characters(user_id, char_name, char_title, sheet_url, action="add")
            await ctx.send(f"Character **{char_name}** has been added successfully!")
                    
        except TimeoutError:
            await ctx.send("You took too long to respond! Please try the command again.")
        except Exception as e:
            await print(f"An error occurred: {e}")
            await ctx.send(f"An error occurred! Better poke an admin.")

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
            if not command.hidden and command.cog_name != "Admin":  # Skip commands marked as hidden
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