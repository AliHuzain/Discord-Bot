import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import json
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict
import random
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ID of your feedback channel
FEEDBACK_CHANNEL_ID = 1377545068298108958

# ID of your Giveaway channel - YOU NEED TO CREATE THIS CHANNEL
GIVEAWAY_CHANNEL_ID = 1402833507373551666  # Replace with actual giveaway channel ID

# Role IDs - YOU NEED TO CREATE THESE ROLES IN YOUR SERVER
MILESTONE_5_VOUCHES_ROLE = 1381622660861006025  # Replace with actual role ID for 5+ vouches

# Vouch tracking data
vouch_data_file = "vouch_tracking.json"
giveaway_data_file = "giveaway_data.json"


def load_vouch_data():
    try:
        with open(vouch_data_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "monthly_vouches": {},
            "total_vouches": {},
            "user_products": {},  # Track products purchased by each user
            "last_reset": datetime.now().strftime("%Y-%m")
        }


def load_giveaway_data():
    try:
        with open(giveaway_data_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "active_giveaways": {},
            "giveaway_history": []
        }


def save_giveaway_data(data):
    with open(giveaway_data_file, 'w') as f:
        json.dump(data, f, indent=2)


def save_vouch_data(data):
    with open(vouch_data_file, 'w') as f:
        json.dump(data, f, indent=2)


def create_progress_bar(current_step, total_steps, completed_color="🟢", incomplete_color="⚪"):
    """Create a visual progress bar with colored dots"""
    progress = ""
    for i in range(1, total_steps + 1):
        if i <= current_step:
            progress += completed_color
        else:
            progress += incomplete_color

    percentage = round((current_step / total_steps) * 100)
    return f"{progress} {percentage}% Complete"


def get_step_description(step, language="english"):
    """Get step descriptions in the selected language"""
    steps_en = {
        1: "🌐 Language Selection",
        2: "📚 Product Selection",
        3: "👤 User Selection",
        4: "⭐ Rating Selection",
        5: "📝 Comment Writing",
        6: "📸 Proof Upload"
    }

    steps_ar = {
        1: "🌐 اختيار اللغة",
        2: "📚 اختيار المنتج",
        3: "👤 اختيار المستخدم",
        4: "⭐ اختيار التقييم",
        5: "📝 كتابة التعليق",
        6: "📸 رفع الإثبات"
    }

    return steps_ar[step] if language == "arabic" else steps_en[step]


vouch_tracking = load_vouch_data()
giveaway_tracking = load_giveaway_data()

# Product category images for Customer of the Month announcements
PRODUCT_CATEGORY_IMAGES = {
    "valorant-points": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFd5QOQemfaEc61dMFLEkxl0fswvcqWCtaOWcvgucyXRq1dKjZsGVzgHRocq8g9cRkQFc&usqp=CAU"],

    "callofduty-cp": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6xgv_M-tH5qMOdIFwY-t_fZ3ikBk4F_z1Dg&s"],

    "overwatch-coins": [
        "https://blz-contentstack-images.akamaized.net/v3/assets/bltf408a0557f4e4998/blt5387d7cefaf9923d/6334e1997e84e17596f9c816/Coins_960x540.png"],

    "discord-nitro": [
        "https://cdn1.epicgames.com/offer/5f3c898b2a3244af99e9900e015717f8/EGS_Discord_Nitro_2560x1440_withlogo_2560x1440-944994658df3b04d0c4940be832da19e_2560x1440-944994658df3b04d0c4940be832da19e",
    ],
    "gamepass": [
        "https://www.stuff.tv/wp-content/uploads/sites/2/2023/04/Game-Pass.png",
    ]
}

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.members = True  # Enable members intent for user operations
bot = commands.Bot(command_prefix="!", intents=intents)


class GiveawayProductSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.select(
        placeholder="🎁 Choose the product category...",
        options=[
            discord.SelectOption(label="Valorant Points", value="valorant-points",
                                 emoji="<:Valorant_Points:1386806798610337864>"),
            discord.SelectOption(label="Call of Duty CP", value="callofduty-cp",
                                 emoji="<:COD_Point_BOCW2:1395768016255586376>"),
            discord.SelectOption(label="Overwatch Coins", value="overwatch-coins",
                                 emoji="<:Overwatch_Coin:1395787416509485087>"),
            discord.SelectOption(label="Discord Nitro", value="discord-nitro",
                                 emoji="<:icons8discordnitro:1395950198915727512>"),
            discord.SelectOption(label="Gamepass", value="gamepass", emoji="<:xbox:1395953046688890962>"),
            discord.SelectOption(label="Others", value="others", emoji="<:netflix:1395956599092150282>"),
            discord.SelectOption(label="Buy Accounts", value="buy-accounts"),
            discord.SelectOption(label="FIFA Coins", value="fifa-coins"),
        ]
    )
    async def product_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        product_category = select.values[0]
        
        # Show specific product options based on category
        specific_product_view = GiveawaySpecificProductView(product_category)

        embed = discord.Embed(
            title="🎁 Select Specific Product",
            description=f"**Category:** {product_category.replace('-', ' ').title()}\n\n"
                       "Please select the specific product you want to giveaway:",
            color=0xFF0000
        )

        await interaction.response.edit_message(embed=embed, view=specific_product_view)


class GiveawaySpecificProductView(discord.ui.View):
    def __init__(self, product_category):
        super().__init__(timeout=300)
        self.product_category = product_category
        
        # Define specific products for each category
        product_options = {
            "valorant-points": [
                discord.SelectOption(label="5350 VP", value="5350-vp"),
                discord.SelectOption(label="11,000 VP", value="11,000-vp"),
                discord.SelectOption(label="16,350 VP", value="16,350-vp"),
                discord.SelectOption(label="22,000 VP", value="22,000-vp"),
            ],
            "callofduty-cp": [
                discord.SelectOption(label="2,400 CP", value="2,400-cp"),
                discord.SelectOption(label="5,000 CP", value="5,000-cp"),
                discord.SelectOption(label="9,500 CP", value="9,500-cp"),
                discord.SelectOption(label="13,000 CP", value="13,000-cp"),
            ],
            "overwatch-coins": [
                discord.SelectOption(label="2,200 Coins", value="2,200-coins"),
                discord.SelectOption(label="4,500 Coins", value="2000-coins"),
                discord.SelectOption(label="6,900 Coins", value="6,900-coins"),
                discord.SelectOption(label="11,800 Coins", value="11,800-coins"),

            ],
            "discord-nitro": [
                discord.SelectOption(label="1 Month Nitro", value="1-month-nitro"),
                discord.SelectOption(label="12 Months Nitro", value="12-Months-nitro"),
            ],
            "gamepass": [
                discord.SelectOption(label="3 Months Gamepass", value="Ultimate 3 months"),
            ],
            "others": [
                discord.SelectOption(label="Netflix 1 Month", value="netflix-1m"),
                discord.SelectOption(label="Spotify Premium", value="spotify-premium"),
                discord.SelectOption(label="Amazon Prime", value="amazon-prime"),
                discord.SelectOption(label="Custom Prize", value="custom-prize"),
            ],
            "fifa-coins": [
                discord.SelectOption(label="100K Coins", value="100k-coins"),
                discord.SelectOption(label="500K Coins", value="500k-coins"),
                discord.SelectOption(label="1M Coins", value="1m-coins"),
            ]
        }
        
        options = product_options.get(product_category, [discord.SelectOption(label="Default Prize", value="default")])
        
        self.specific_select = discord.ui.Select(
            placeholder="🎁 Choose specific product...",
            options=options
        )
        self.specific_select.callback = self.specific_product_callback
        self.add_item(self.specific_select)
    
    async def specific_product_callback(self, interaction: discord.Interaction):
        specific_product = self.specific_select.values[0]
        
        # Auto-generate title and description based on product
        def generate_giveaway_content(category, specific):
            titles = {
                "valorant-points": f" {specific.upper().replace('-', ' ')} GIVEAWAY!🎁",
                "callofduty-cp": f" {specific.upper().replace('-', ' ')} GIVEAWAY!🎁",
                "overwatch-coins": f" {specific.upper().replace('-', ' ')} GIVEAWAY!🎁",
                "discord-nitro": f" {specific.upper().replace('-', ' ')} GIVEAWAY!🎁",
                "gamepass": f" {specific.upper().replace('-', ' ')} GIVEAWAY! 🎁",
                "others": f" {specific.upper().replace('-', ' ')} GIVEAWAY! 🎁",
                "buy-accounts": f" {specific.upper().replace('-', ' ')} GIVEAWAY! 🎁",
                "fifa-coins": f" {specific.upper().replace('-', ' ')} GIVEAWAY! 🎁"
            }
            
            descriptions = {
                "valorant-points": f"🎉 We're giving away {specific.replace('-', ' ')}!\n\n Enter now for your chance to win Valorant Points !",
                "callofduty-cp": f"🎉 We're giving away {specific.replace('-', ' ')} !\n\n Enter now for your chance to win Call of Duty Points and unlock epic content!",
                "overwatch-coins": f"🎉 We're giving away {specific.replace('-', ' ')} !\n\n Enter now for your chance to win Overwatch Coins and get amazing skins!",
                "discord-nitro": f"🎉 We're giving away {specific.replace('-', ' ')} !\n\n Enter now for your chance to win Discord Nitro and enjoy premium features!",
                "gamepass": f"🎉 We're giving away {specific.replace('-', ' ')} !\n\n Enter now for your chance to win Xbox Game Pass and play hundreds of games!",
                "others": f"🎉 We're giving away {specific.replace('-', ' ')} !\n\n Enter now for your chance to win this amazing prize!",
                "buy-accounts": f"🎉 We're giving away a {specific.replace('-', ' ')} !\n\n Enter now for your chance to win a premium account!",
                "fifa-coins": f"🎉 We're giving away {specific.replace('-', ' ')}!\n\n Enter now for your chance to win FIFA Coins and build your ultimate team!"
            }
            
            return titles.get(category, f"🎁 FREE {specific.upper()} GIVEAWAY! 🎁"), descriptions.get(category, f"Win {specific} for free!")
        
        title, description = generate_giveaway_content(self.product_category, specific_product)
        
        giveaway_data = {
            "title": title,
            "description": description,
            "product": f"{self.product_category}:{specific_product}"
        }
        
        duration_view = GiveawayDurationSelectionView(giveaway_data)

        embed = discord.Embed(
            title="🎁 Select Giveaway Duration",
            description=f"**Title:** {title}\n"
                       f"**Description:** {description[:100]}...\n\n"
                       "Please select how long the giveaway should run:",
            color=0xFF0000
        )

        await interaction.response.edit_message(embed=embed, view=duration_view)


class GiveawayDurationSelectionView(discord.ui.View):
    def __init__(self, giveaway_data):
        super().__init__(timeout=300)
        self.giveaway_data = giveaway_data

    @discord.ui.select(
        placeholder="⏰ Choose duration...",
        options=[
            discord.SelectOption(label="1 Hour", value="1", emoji="⏰"),
            discord.SelectOption(label="3 Hours", value="3", emoji="⏰"),
            discord.SelectOption(label="6 Hours", value="6", emoji="⏰"),
            discord.SelectOption(label="12 Hours", value="12", emoji="⏰"),
            discord.SelectOption(label="16 Hours", value="16", emoji="⏰"),
            discord.SelectOption(label="24 Hours", value="24", emoji="⏰"),
        ]
    )
    async def duration_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.giveaway_data["duration"] = int(select.values[0])
        
        confirm_view = GiveawayConfirmationView(self.giveaway_data)

        embed = discord.Embed(
            title="🎁 Confirm Giveaway Details",
            description=f"**Title:** {self.giveaway_data['title']}\n"
                       f"**Description:** {self.giveaway_data['description'][:100]}...\n"
                       f"**Product:** {self.giveaway_data['product']}\n"
                       f"**Duration:** {self.giveaway_data['duration']} hours\n\n"
                       "Click **Post Giveaway** to publish it to the giveaway channel!",
            color=0xFF0000
        )

        await interaction.response.edit_message(embed=embed, view=confirm_view)


class GiveawayConfirmationView(discord.ui.View):
    def __init__(self, giveaway_data):
        super().__init__(timeout=300)
        self.giveaway_data = giveaway_data

    @discord.ui.button(label="🎉 Post Giveaway", style=discord.ButtonStyle.green)
    async def post_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_giveaway(interaction, self.giveaway_data)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Giveaway Cancelled",
            description="The giveaway creation has been cancelled.",
            color=0xFF0000
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def create_giveaway(interaction: discord.Interaction, giveaway_data):
    """Create and post a giveaway"""
    giveaway_channel = bot.get_channel(GIVEAWAY_CHANNEL_ID)
    
    if not giveaway_channel:
        await interaction.response.send_message("❌ Giveaway channel not found!", ephemeral=True)
        return

    # Calculate end time
    end_time = datetime.now() + timedelta(hours=giveaway_data['duration'])
    
    # Create giveaway embed with countdown timeline
    duration_hours = giveaway_data['duration']
    
    # Create visual timeline
    timeline_emoji = "🟩" * min(duration_hours, 12)  # Show up to 12 blocks
    if duration_hours > 12:
        timeline_emoji += f" (+{duration_hours - 12}h more)"
    
    # Get specific product with emoji and channel link
    def get_product_display(product_string):
        category, specific = product_string.split(':')
        
        # Define specific product emojis and displays
        product_displays = {
            # Valorant Points
            "valorant-points:5350-vp": "<:Valorant_Points:1386806798610337864> 5350 VP",
            "valorant-points:11,000-vp": "<:Valorant_Points:1386806798610337864> 11,000 VP", 
            "valorant-points:16,350-vp": "<:Valorant_Points:1386806798610337864> 16,350 VP",
            "valorant-points:22,000-vp": "<:Valorant_Points:1386806798610337864> 22,000 VP",
            
            # Call of Duty CP
            "callofduty-cp:2,400-cp": "<:COD_Point_BOCW2:1395768016255586376>> 2,400 CP",
            "callofduty-cp:5,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 5,000 CP",
            "callofduty-cp:9,500-cp": "<:COD_Point_BOCW2:1395768016255586376> 9,500 CP",
            "callofduty-cp:13,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 13,000 CP",
            
            # Overwatch Coins
            "overwatch-coins:2,200-coins": "<:Overwatch_Coin:1395787416509485087> 2,200 Coins",
            "overwatch-coins:2000-coins": "<:Overwatch_Coin:1395787416509485087> 4,500 Coins",
            "overwatch-coins:6,900-coins": "<:Overwatch_Coin:1395787416509485087> 6,900 Coins",
            "overwatch-coins:11,800-coins": "<:Overwatch_Coin:1395787416509485087> 11,800 Coins",
            
            # Discord Nitro
            "discord-nitro:1-month-nitro": "<:discordnitro:1395949499704283166> 1 Month Nitro",
            "discord-nitro:12-Months-nitro": "<:discordnitro:1395949499704283166> 12 Months Nitro",
            
            # Gamepass
            "gamepass:Ultimate 3 months": "<:xbox:1395953046688890962> 3 Months Gamepass Ultimate",
            
            # Others
            "others:netflix-1m": "<:netflix:1395956599092150282> Netflix 1 Month",
            "others:spotify-premium": "<:spotify:1395958371244314795> Spotify Premium",
            "others:custom-prize": "🎁 Custom Prize",
            
            # FIFA Coins
            "fifa-coins:100k-coins": "<:100KCoins:YOUR_EMOJI_ID> 100K FIFA Coins",
            "fifa-coins:500k-coins": "<:500KCoins:YOUR_EMOJI_ID> 500K FIFA Coins", 
            "fifa-coins:1m-coins": "<:1MCoins:YOUR_EMOJI_ID> 1M FIFA Coins",
        }
        
        # Get channel links
        channel_links = {
            "valorant-points": "<#1377608623525728366>",
            "callofduty-cp": "<#1386423140464201909>",
            "overwatch-coins": "<#1395764822255210506>",
            "discord-nitro": "<#1395949111412392068>",
            "gamepass": "<#1395765771161960489>",
            "others": "<#1395956006734925897>",
            "buy-accounts": "<#1396249701866541107>",
            "fifa-coins": "<#1386423375169064990>"
        }
        
        product_display = product_displays.get(product_string, specific.replace('-', ' ').title())
        channel_link = channel_links.get(category, "")
        
        if channel_link:
            return f"{product_display} {channel_link}"
        else:
            return product_display
    
    product_link = get_product_display(giveaway_data['product'])
    
    embed = discord.Embed(
        title=f"🎉 {giveaway_data['title']} 🎉",
        description=f"**{giveaway_data['description']}**\n\n"
                   f"🎁 **Prize:** {product_link}\n -"
                   f"⏰ **Ends:** <t:{int(end_time.timestamp())}:R> (<t:{int(end_time.timestamp())}:f>)\n"
                   f"🎪 **Duration:** {duration_hours} hours\n"
                   f"📊 **Timeline:** {timeline_emoji}\n\n"
                   f"**How to enter:**\n"
                   f"🔸 React with ANY emoji to join the giveaway!\n"
                   f"🔸 Winners will be selected randomly\n"
                   f"🔸 **BONUS:** Invite friends !\n"
                   f"🔸 Good luck everyone! 🍀",
        color=0xFF00001396249701866541107
    )
    
    embed.set_image(url="https://cdn.discordapp.com/attachments/1367317832093667483/1402853905599168543/standard.gif?ex=68956d02&is=68941b82&hm=75d2999e17ad6a4c60a4b81e01ac7ac381c82ae7307d91867b7f49043b7d351e&")
    embed.set_footer(text="Developed by: RxxD")
    embed.timestamp = datetime.now()

    # Post giveaway
    try:
        giveaway_message = await giveaway_channel.send(f"🎊 **NEW GIVEAWAY!** @everyone 🎊", embed=embed)
        await giveaway_message.add_reaction("🎉")
        
        # Store giveaway data
        global giveaway_tracking
        giveaway_id = str(giveaway_message.id)
        giveaway_tracking["active_giveaways"][giveaway_id] = {
            "message_id": giveaway_message.id,
            "channel_id": giveaway_channel.id,
            "title": giveaway_data['title'],
            "description": giveaway_data['description'],
            "product": giveaway_data['product'],
            "creator_id": interaction.user.id,
            "start_time": datetime.now().isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hours": giveaway_data['duration'],
            "winners": []
        }
        save_giveaway_data(giveaway_tracking)
        
        # Schedule winner selection
        asyncio.create_task(schedule_giveaway_end(giveaway_id, giveaway_data['duration']))
        
        # Confirm to admin
        success_embed = discord.Embed(
            title="✅ Giveaway Posted!",
            description=f"Your giveaway **{giveaway_data['title']}** has been posted successfully!\n\n"
                       f"📍 Posted in: {giveaway_channel.mention}\n"
                       f"⏰ Will end in: {giveaway_data['duration']} hours\n"
                       f"🎁 Prize: {giveaway_data['product'].replace('-', ' ').title()}",
            color=0xFF0000
        )
        await interaction.response.edit_message(embed=success_embed, view=None)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating giveaway: {str(e)}", ephemeral=True)


async def schedule_giveaway_end(giveaway_id: str, duration_hours: int):
    """Schedule the end of a giveaway"""
    await asyncio.sleep(duration_hours * 3600)  # Convert hours to seconds
    await end_giveaway(giveaway_id)


async def end_giveaway(giveaway_id: str):
    """End a giveaway and select winner"""
    global giveaway_tracking
    
    if giveaway_id not in giveaway_tracking["active_giveaways"]:
        return
        
    giveaway_data = giveaway_tracking["active_giveaways"][giveaway_id]
    
    try:
        channel = bot.get_channel(giveaway_data["channel_id"])
        if not channel:
            return
            
        message = await channel.fetch_message(giveaway_data["message_id"])
        if not message:
            return
            
        # Get users who reacted with ANY emoji
        participants = []
        total_reactions = 0
        
        for reaction in message.reactions:
            total_reactions += reaction.count
            async for user in reaction.users():
                if not user.bot and user not in participants:  # Exclude bots and avoid duplicates
                    participants.append(user)
                
        if not participants:
            # Get specific product with emoji and channel link
            def get_product_display_no_participants(product_string):
                category, specific = product_string.split(':')
                
                # Define specific product emojis and displays
                product_displays = {
                    # Valorant Points
                    "valorant-points:5350-vp": "<:Valorant_Points:1386806798610337864> 5350 VP",
                    "valorant-points:11,000-vp": "<:Valorant_Points:1386806798610337864> 11,000 VP", 
                    "valorant-points:16,350-vp": "<:Valorant_Points:1386806798610337864> 16,350 VP",
                    "valorant-points:22,000-vp": "<:Valorant_Points:1386806798610337864> 22,000 VP",
                    
                    # Call of Duty CP
                    "callofduty-cp:2,400-cp": "<:COD_Point_BOCW2:1395768016255586376> 2,400 CP",
                    "callofduty-cp:5,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 5,000 CP",
                    "callofduty-cp:9,500-cp": "<:COD_Point_BOCW2:1395768016255586376> 9,500 CP",
                    "callofduty-cp:13,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 13,000 CP",
                    
                    # Overwatch Coins
                    "overwatch-coins:2,200-coins": "<:Overwatch_Coin:1395787416509485087> 2,200 Coins",
                    "overwatch-coins:2000-coins": "<:Overwatch_Coin:1395787416509485087> 4,500 Coins",
                    "overwatch-coins:6,900-coins": "<:Overwatch_Coin:1395787416509485087> 6,900 Coins",
                    "overwatch-coins:11,800-coins": "<:Overwatch_Coin:1395787416509485087> 11,800 Coins",
                    
                    # Discord Nitro
                    "discord-nitro:1-month-nitro": "<:discordnitro:1395949499704283166> 1 Month Nitro",
                    "discord-nitro:12-Months-nitro": "<:discordnitro:1395949499704283166> 12 Months Nitro",
                    
                    # Gamepass
                    "gamepass:Ultimate 3 months": "<:xbox:1395953046688890962> 3 Months Gamepass Ultimate",
                    
                    # Others
                    "others:netflix-1m": "<:netflix:1395956599092150282> Netflix 1 Month",
                    "others:spotify-premium": "<:spotify:1395958371244314795> Spotify Premium",
                    "others:custom-prize": "🎁 Custom Prize",
                    
                    # FIFA Coins
                    "fifa-coins:100k-coins": "<:100KCoins:YOUR_EMOJI_ID> 100K FIFA Coins",
                    "fifa-coins:500k-coins": "<:500KCoins:YOUR_EMOJI_ID> 500K FIFA Coins", 
                    "fifa-coins:1m-coins": "<:1MCoins:YOUR_EMOJI_ID> 1M FIFA Coins",
                }
                
                # Get channel links
                channel_links = {
                    "valorant-points": "<#1377608623525728366>",
                    "callofduty-cp": "<#1386423140464201909>",
                    "overwatch-coins": "<#1395764822255210506>",
                    "discord-nitro": "<#1395949111412392068>",
                    "gamepass": "<#1395765771161960489>",
                    "others": "<#1395956006734925897>",
                    "buy-accounts": "<#1396249701866541107>",
                    "fifa-coins": "<#1386423375169064990>"
                }
                
                product_display = product_displays.get(product_string, specific.replace('-', ' ').title())
                channel_link = channel_links.get(category, "")
                
                if channel_link:
                    return f"{product_display} {channel_link}"
                else:
                    return product_display
            
            product_link = get_product_display_no_participants(giveaway_data['product'])
            
            # No participants
            embed = discord.Embed(
                title="😢 Giveaway Ended - No Participants",
                description=f"**{giveaway_data['title']}** has ended with no participants.\n\n"
                           f"🎁 **Prize:** {product_link}\n"
                           f"📅 **Ended:** <t:{int(datetime.now().timestamp())}:R>",
                color=0xFF0000
            )
            await channel.send(embed=embed)
        else:
            # Select random winner from participants
            winner = random.choice(participants)
            
            # Get specific product with emoji and channel link
            def get_product_display_end(product_string):
                category, specific = product_string.split(':')
                
                # Define specific product emojis and displays
                product_displays = {
                    # Valorant Points
                    "valorant-points:5350-vp": "<:Valorant_Points:1386806798610337864> 5350 VP",
                    "valorant-points:11,000-vp": "<:Valorant_Points:1386806798610337864> 11,000 VP", 
                    "valorant-points:16,350-vp": "<:Valorant_Points:1386806798610337864> 16,350 VP",
                    "valorant-points:22,000-vp": "<:Valorant_Points:1386806798610337864> 22,000 VP",
                    
                    # Call of Duty CP
                    "callofduty-cp:2,400-cp": "<:COD_Point_BOCW2:1395768016255586376> 2,400 CP",
                    "callofduty-cp:5,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 5,000 CP",
                    "callofduty-cp:9,500-cp": "<:COD_Point_BOCW2:1395768016255586376> 9,500 CP",
                    "callofduty-cp:13,000-cp": "<:COD_Point_BOCW2:1395768016255586376> 13,000 CP",
                    
                    # Overwatch Coins
                    "overwatch-coins:2,200-coins": "<:Overwatch_Coin:1395787416509485087> 2,200 Coins",
                    "overwatch-coins:2000-coins": "<:Overwatch_Coin:1395787416509485087> 4,500 Coins",
                    "overwatch-coins:6,900-coins": "<:Overwatch_Coin:1395787416509485087> 6,900 Coins",
                    "overwatch-coins:11,800-coins": "<:Overwatch_Coin:1395787416509485087> 11,800 Coins",
                    
                    # Discord Nitro
                    "discord-nitro:1-month-nitro": "<:discordnitro:1395949499704283166> 1 Month Nitro",
                    "discord-nitro:12-Months-nitro": "<:discordnitro:1395949499704283166> 12 Months Nitro",
                    
                    # Gamepass
                    "gamepass:Ultimate 3 months": "<:xbox:1395953046688890962> 3 Months Gamepass Ultimate",
                    
                    # Others
                    "others:netflix-1m": "<:netflix:1395956599092150282> Netflix 1 Month",
                    "others:spotify-premium": "<:spotify:1395958371244314795> Spotify Premium",
                    "others:custom-prize": "🎁 Custom Prize",
                    
                    # FIFA Coins
                    "fifa-coins:100k-coins": "<:100KCoins:YOUR_EMOJI_ID> 100K FIFA Coins",
                    "fifa-coins:500k-coins": "<:500KCoins:YOUR_EMOJI_ID> 500K FIFA Coins", 
                    "fifa-coins:1m-coins": "<:1MCoins:YOUR_EMOJI_ID> 1M FIFA Coins",
                }
                
                # Get channel links
                channel_links = {
                    "valorant-points": "<#1377608623525728366>",
                    "callofduty-cp": "<#1386423140464201909>",
                    "overwatch-coins": "<#1395764822255210506>",
                    "discord-nitro": "<#1395949111412392068>",
                    "gamepass": "<#1395765771161960489>",
                    "others": "<#1395956006734925897>",
                    "buy-accounts": "<#1396249701866541107>",  # No channel
                    "fifa-coins": "<#1386423375169064990>"  # No channel
                }
                
                product_display = product_displays.get(product_string, specific.replace('-', ' ').title())
                channel_link = channel_links.get(category, "")
                
                if channel_link:
                    return f"{product_display} {channel_link}"
                else:
                    return product_display
            
            product_link = get_product_display_end(giveaway_data['product'])
            
            # Winner announcement
            embed = discord.Embed(
                title="🎊 GIVEAWAY WINNER! 🎊",
                description=f"**{giveaway_data['title']}** has ended!\n\n"
                           f"🏆 **Winner:** {winner.mention}\n"
                           f"🎁 **Prize:** {product_link}\n"
                           f"👥 **Participants:** {len(participants)}\n"
                           f"📅 **Ended:** <t:{int(datetime.now().timestamp())}:R>\n\n"
                           f"🎉 Congratulations {winner.display_name}! 🎉\n"
                           f"Please open a ticket in <#1377633537506672690> to claim your prize!",
                color=0xFF0000
            )
            embed.set_thumbnail(url=winner.avatar.url if winner.avatar else None)
            embed.set_footer(text="Developed by: RxxD")
            
            await channel.send(f"🎊 Congratulations {winner.mention}! 🎊", embed=embed)
            
            # Update giveaway data
            giveaway_data["winners"] = [winner.id]
            giveaway_data["participants"] = len(participants)
        
        # Move to history
        giveaway_tracking["giveaway_history"].append(giveaway_data)
        del giveaway_tracking["active_giveaways"][giveaway_id]
        save_giveaway_data(giveaway_tracking)
        
    except Exception as e:
        print(f"Error ending giveaway {giveaway_id}: {e}")


class LanguageSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="🌐 Select your language / اختر اللغة",
        options=[
            discord.SelectOption(label="English", value="english", emoji="🇺🇸"),
            discord.SelectOption(label="العربية", value="arabic", emoji="🇸🇦"),
        ]
    )
    async def language_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        vouch_data = {
            'language': select.values[0],
            'submitter': interaction.user
        }

        product_view = ProductSelectionView(vouch_data)

        current_step = 2
        total_steps = 6
        progress_bar = create_progress_bar(current_step, total_steps, "🟩", "⬜")

        if select.values[0] == "arabic":
            embed = discord.Embed(
                title="✅ تم اختيار اللغة!",
                description=f"**اللغة المختارة:** العربية\n\n"
                            f"**📊 التقدم:** {progress_bar}\n\n"
                            "📚 **الخطوة 2: اختر المنتج**\n"
                            "يرجى اختيار المنتج/الخدمة التي تريد تقييمها:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=product_view, content=None)
        else:
            embed = discord.Embed(
                title="✅ Language Selected!",
                description=f"**Selected:** English\n\n"
                            f"**📊 Progress:** {progress_bar}\n\n"
                            "📚 **Step 2: Select Product**\n"
                            "Please select the product/service you're vouching for:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=product_view, content=None)


class ProductSelectionView(discord.ui.View):
    def __init__(self, vouch_data):
        super().__init__(timeout=None)
        self.vouch_data = vouch_data

        # Set placeholder based on language
        if vouch_data['language'] == "arabic":
            placeholder = "📚 اختر منتجك أو خدمتك..."
        else:
            placeholder = "📚 Choose your product/service..."

        # Update the select placeholder after initialization
        self.product_select.placeholder = placeholder

    @discord.ui.select(
        placeholder="temp",  # Will be set in __init__
        options=[
            discord.SelectOption(label="Valorant Points", value="valorant-points",
                                 emoji="<:Valorant_Points:1386806798610337864> "),
            discord.SelectOption(label="Call of Duty CP", value="callofduty-cp",
                                 emoji="<:COD_Point_BOCW2:1395768016255586376> "),
            discord.SelectOption(label="Overwatch Coins", value="overwatch-coins",
                                 emoji="<:Overwatch_Coin:1395787416509485087>"),
            discord.SelectOption(label="Discord Nitro", value="discord-nitro",
                                 emoji="<:icons8discordnitro:1395950198915727512>"),
            discord.SelectOption(label="Gamepass", value="gamepass", emoji="<:xbox:1395953046688890962> "),
            discord.SelectOption(label="Others", value="others", emoji="<:netflix:1395956599092150282>"),
            discord.SelectOption(label="Buy Accounts", value="buy-accounts"),
            discord.SelectOption(label="FIFA Coins", value="fifa-coins"),
        ]
    )
    async def product_select(self, interaction: discord.Interaction, select: discord.ui.Select):

        self.vouch_data['product'] = select.values[0]

        user_view = UserSelectionView(self.vouch_data)

        current_step = 3
        total_steps = 6
        progress_bar = create_progress_bar(current_step, total_steps, "🟩", "⬜")

        if self.vouch_data['language'] == "arabic":
            embed = discord.Embed(
                title="✅ تم اختيار المنتج!",
                description=f"**المنتج المختار:** {select.values[0]}\n\n"
                            f"**📊 التقدم:** {progress_bar}\n\n"
                            "👤 **الخطوة 3: اختر المستخدم**\n"
                            "اختر المستخدم الذي أكمل طلبك:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=user_view, content=None)
        else:
            embed = discord.Embed(
                title="✅ Product Selected!",
                description=f"**Selected:** {select.values[0]}\n\n"
                            f"**📊 Progress:** {progress_bar}\n\n"
                            "👤 **Step 3: Select User**\n"
                            "Choose the user who completed your order:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=user_view, content=None)


class UserSelectionView(discord.ui.View):
    def __init__(self, vouch_data):
        super().__init__(timeout=None)
        self.vouch_data = vouch_data

        # Set placeholder based on language
        if vouch_data['language'] == "arabic":
            placeholder = "👤 اختر المستخدم..."
        else:
            placeholder = "👤 Choose the user..."

        # Update the select placeholder after initialization
        self.user_select.placeholder = placeholder

    @discord.ui.select(
        placeholder="temp",  # Will be set in __init__
        options=[
            discord.SelectOption(label="Owner", value="owner", emoji="<:Radiant:1378395701808992286>"),
            discord.SelectOption(label="Moderator", value="moderator", emoji="<:manager:1402163552994984019>"),
        ]
    )
    async def user_select(self, interaction: discord.Interaction, select: discord.ui.Select):

        self.vouch_data['vouched_user'] = select.values[0]

        rating_view = RatingSelectionView(self.vouch_data)

        current_step = 4
        total_steps = 6
        progress_bar = create_progress_bar(current_step, total_steps, "🟩", "⬜")

        if self.vouch_data['language'] == "arabic":
            embed = discord.Embed(
                title="✅ تم اختيار المنتج والمستخدم!",
                description=f"**المنتج:** {self.vouch_data['product']}\n"
                            f"**المستخدم:** {select.values[0]}\n\n"
                            f"**📊 التقدم:** {progress_bar}\n\n"
                            "⭐ **الخطوة 4: قيم تجربتك**\n"
                            "اختر تقييمك بالنجوم:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=rating_view, content=None)
        else:
            embed = discord.Embed(
                title="✅ Product & User Selected!",
                description=f"**Product:** {self.vouch_data['product']}\n"
                            f"**User:** {select.values[0]}\n\n"
                            f"**📊 Progress:** {progress_bar}\n\n"
                            "⭐ **Step 4: Rate Your Experience**\n"
                            "Choose your star rating:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=rating_view, content=None)


class RatingSelectionView(discord.ui.View):
    def __init__(self, vouch_data):
        super().__init__(timeout=None)
        self.vouch_data = vouch_data

        # Set placeholder based on language
        if vouch_data['language'] == "arabic":
            placeholder = "⭐ اختر تقييمك..."
        else:
            placeholder = "⭐ Choose your rating..."

        # Update the select placeholder after initialization
        self.rating_select.placeholder = placeholder

    @discord.ui.select(
        placeholder="temp",  # Will be set in __init__
        options=[
            discord.SelectOption(label="⭐", value="1"),
            discord.SelectOption(label="⭐⭐", value="2"),
            discord.SelectOption(label="⭐⭐⭐", value="3"),
            discord.SelectOption(label="⭐⭐⭐⭐", value="4"),
            discord.SelectOption(label="⭐⭐⭐⭐⭐", value="5"),
        ]
    )
    async def rating_select(self, interaction: discord.Interaction, select: discord.ui.Select):

        self.vouch_data['rating'] = select.values[0]

        comment_view = CommentInputView(self.vouch_data)

        star_count = int(select.values[0])
        stars_display = "⭐" * star_count

        current_step = 5
        total_steps = 6
        progress_bar = create_progress_bar(current_step, total_steps, "🟩", "⬜")

        if self.vouch_data['language'] == "arabic":
            embed = discord.Embed(
                title="✅ تم اختيار المنتج والمستخدم والتقييم!",
                description=f"**المنتج:** {self.vouch_data['product']}\n"
                            f"**المستخدم:** {self.vouch_data['vouched_user']}\n"
                            f"**التقييم:** {stars_display}\n\n"
                            f"**📊 التقدم:** {progress_bar}\n\n"
                            "📝 **الخطوة 5: اكتب تعليقك**\n"
                            "انقر على الزر أدناه لكتابة تقييمك:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=comment_view, content=None)
        else:
            embed = discord.Embed(
                title="✅ Product, User & Rating Selected!",
                description=f"**Product:** {self.vouch_data['product']}\n"
                            f"**User:** {self.vouch_data['vouched_user']}\n"
                            f"**Rating:** {stars_display}\n\n"
                            f"**📊 Progress:** {progress_bar}\n\n"
                            "📝 **Step 5: Write Your Comment**\n"
                            "Click the button below to write your feedback:",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=comment_view, content=None)


class CommentModal(discord.ui.Modal):
    def __init__(self, vouch_data):
        self.vouch_data = vouch_data

        if vouch_data['language'] == "arabic":
            super().__init__(title="اكتب تقييمك")
            self.feedback = discord.ui.TextInput(
                label="التعليقات",
                style=discord.TextStyle.paragraph,
                placeholder="أخبرنا عن تجربتك، هل كانت الخدمة سريعة؟ هل تنصح بنا؟",
                required=True,
                max_length=4000
            )
        else:
            super().__init__(title="Write Your Feedback")
            self.feedback = discord.ui.TextInput(
                label="Comments",
                style=discord.TextStyle.paragraph,
                placeholder="Tell us about your experience, was the service fast? Would you recommend us?",
                required=True,
                max_length=4000
            )

        self.add_item(self.feedback)

    async def on_submit(self, interaction: discord.Interaction):
        self.vouch_data['feedback'] = self.feedback.value

        proof_view = ProofUploadView(self.vouch_data)

        star_count = int(self.vouch_data['rating'])
        stars_display = "⭐" * star_count

        current_step = 6
        total_steps = 6
        progress_bar = create_progress_bar(current_step, total_steps, "🟩", "⬜")

        if self.vouch_data['language'] == "arabic":
            embed = discord.Embed(
                title="✅ تم جمع جميع التفاصيل!",
                description=f"**المنتج:** {self.vouch_data['product']}\n"
                            f"**المستخدم:** {self.vouch_data['vouched_user']}\n"
                            f"**التقييم:** {stars_display}\n"
                            f"**التعليق:** {self.vouch_data['feedback'][:100]}{'...' if len(self.vouch_data['feedback']) > 100 else ''}\n\n"
                            f"**📊 التقدم:** {progress_bar}\n\n"
                            "📸 **الخطوة الأخيرة: ارفع الإثبات**\n"
                            "يرجى النقر على الزر أدناه وإرفاق صورة كإثبات للمعاملة.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=proof_view, content=None)
        else:
            embed = discord.Embed(
                title="✅ All Details Collected!",
                description=f"**Product:** {self.vouch_data['product']}\n"
                            f"**User:** {self.vouch_data['vouched_user']}\n"
                            f"**Rating:** {stars_display}\n"
                            f"**Comment:** {self.vouch_data['feedback'][:100]}{'...' if len(self.vouch_data['feedback']) > 100 else ''}\n\n"
                            f"**📊 Progress:** {progress_bar}\n\n"
                            "📸 **Final Step: Upload Proof**\n"
                            "Please click the button below and attach an image as proof of your transaction.",
                color=0xFF0000
            )
            await interaction.response.edit_message(embed=embed, view=proof_view, content=None)


class CommentInputView(discord.ui.View):
    def __init__(self, vouch_data):
        super().__init__(timeout=None)
        self.vouch_data = vouch_data

        # Set button label based on language
        if vouch_data['language'] == "arabic":
            button_label = "📝 اكتب تعليق"
        else:
            button_label = "📝 Write Comment"

        # Update the button label after initialization
        self.write_comment.label = button_label

    @discord.ui.button(label="temp", style=discord.ButtonStyle.primary)
    async def write_comment(self, interaction: discord.Interaction, button: discord.ui.Button):

        modal = CommentModal(self.vouch_data)
        await interaction.response.send_modal(modal)


class ProofUploadView(discord.ui.View):
    def __init__(self, vouch_data):
        super().__init__(timeout=None)
        self.vouch_data = vouch_data

        # Set button label based on language
        if vouch_data['language'] == "arabic":
            button_label = "📎 ارفع الإثبات"
        else:
            button_label = "📎 Upload Proof"

        # Update the button label after initialization
        self.upload_proof.label = button_label

    @discord.ui.button(label="temp", style=discord.ButtonStyle.primary, emoji="📸")
    async def upload_proof(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vouch_data['language'] == "arabic":
            embed = discord.Embed(
                title="📸 ارفع صورة الإثبات",
                description="**لديك طريقتان لرفع الصورة:**\n\n"
                            "🎯 **الطريقة 1: اضغط REPLY على هذه الرسالة**\n"
                            "🔸 اضغط على زر **'الرد'** على هذه الرسالة\n"
                            "🔸 ارفق الصورة\n"
                            "🔸 اضغط إرسال\n\n"
                            "🎯 **الطريقة 2: أرسل الصورة مباشرة**\n"
                            "🔸 أرسل الصورة في هذه القناة مباشرة\n"
                            "🔸 اضغط إرسال\n\n"
                            "📱 **للهاتف:**\n"
                            "🔸 اضغط على أيقونة **'+'** أو **'📷'** في الدردشة\n"
                            "🔸 اختر **'الكاميرا'** أو **'المعرض'**\n"
                            "🔸 التقط/اختر صورة الإثبات\n"
                            "🔸 اضغط إرسال\n\n"
                            "💻 **للكمبيوتر:**\n"
                            "🔸 اسحب الصورة إلى نافذة الدردشة\n"
                            "🔸 أو اضغط **'+'** لإرفاق الصورة\n"
                            "🔸 اضغط إرسال\n\n"
                            "⏰ **المهلة:** 10 دقائق",
                color=0xFF0000
            )

            embed.add_field(
                name="📸 ارسل صورة الإثبات",
                value="",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="📸 Upload Your Proof Image",
                description="**You have TWO ways to upload your image:**\n\n"
                            "🎯 **Method 1: Click REPLY on this message**\n"
                            "🔸 Click the **'Reply'** button on this message\n"
                            "🔸 Attach your image\n"
                            "🔸 Hit send\n\n"
                            "🎯 **Method 2: Send image directly**\n"
                            "🔸 Send the image directly in this channel\n"
                            "🔸 Hit send\n\n"
                            "📱 **For Mobile:**\n"
                            "🔸 Tap the **'+'** or **'📷'** icon in chat\n"
                            "🔸 Choose **'Camera'** or **'Photo Library'**\n"
                            "🔸 Take/select your proof image\n"
                            "🔸 Hit send\n\n"
                            "💻 **For Desktop:**\n"
                            "🔸 Drag image into the chat window\n"
                            "🔸 Or click **'+'** to attach image\n"
                            "🔸 Hit send\n\n"
                            "⏰ **Time Limit:** 10 minutes",
                color=0xFF0000
            )
            embed.add_field(
                name="📸 Send your proof image",
                value="",
                inline=False
            )

        embed.set_image(
            url="https://cdn.discordapp.com/attachments/1378390312300318843/1402611673407160371/RXXDbotGif-ezgif.com-video-to-gif-converter.gif?ex=68948b6a&is=689339ea&hm=8164becac1370fb8c431b99e4ee63d775e6297468860a0633879a76c4f67692e&")
        embed.set_footer(text="Developed by: RxxD")

        # Send the instruction message
        instruction_msg = await interaction.response.send_message(embed=embed, ephemeral=False)

        # Get the message object for reply detection
        instruction_message = await interaction.original_response()

        print(f"[DEBUG] Instruction message sent, ID: {instruction_message.id}")
        print(f"[DEBUG] Listening for messages from user {interaction.user.id} in channel {interaction.channel.id}")

        # Start waiting for user's image upload
        await self.wait_for_image_upload(interaction, instruction_message)

    async def wait_for_image_upload(self, interaction: discord.Interaction, instruction_message):
        try:
            # Wait for any image from the user in this channel
            image_file = await self.wait_for_message(interaction, instruction_message)

            if image_file:
                await self.submit_vouch_with_proof(interaction, image_file)

                # Send success message
                if self.vouch_data['language'] == "arabic":
                    success_embed = discord.Embed(
                        title="🎉 تم بنجاح! 🎉",
                        description=f"{self.vouch_data['submitter'].mention}\n"
                                    "**تم إرسال تقييمك بنجاح! شكراً لك! 💕**\n\n"
                                    "✨ تقييمك يعني الكثير لنا!\n"
                                    "🌟 شكراً لاختيارك RxxD SHOP!\n",
                        color=0xFF0000
                    )
                    success_embed.set_image(
                        url="https://cdn.discordapp.com/attachments/1378390312300318843/1402614694757273620/cat-kiss.gif?ex=68948e3a&is=68933cba&hm=d83c045e0e82599f3d1878e8019fae6f42dcf98644d20136d66d4db3970ede0e&")
                    success_embed.set_footer(text="💋من RxxD")
                    await interaction.followup.send(embed=success_embed, ephemeral=False)
                else:
                    success_embed = discord.Embed(
                        title="🎉 SUCCESS! 🎉",
                        description=f"{self.vouch_data['submitter'].mention}\n"
                                    "**Your vouch has been submitted successfully! Thank you! 💕**\n\n"
                                    "✨ Your feedback is important to us!\n"
                                    "🌟 Thank you for choosing RxxD SHOP!\n",
                        color=0xFF0000
                    )
                    success_embed.set_image(
                        url="https://cdn.discordapp.com/attachments/1378390312300318843/1402614694757273620/cat-kiss.gif?ex=68948e3a&is=68933cba&hm=d83c045e0e82599f3d1878e8019fae6f42dcf98644d20136d66d4db3970ede0e&")
                    success_embed.set_footer(text="💋 from RxxD")
                    await interaction.followup.send(embed=success_embed, ephemeral=False)
                return

        except asyncio.TimeoutError:
            pass

        # Timeout occurred
        if self.vouch_data['language'] == "arabic":
            timeout_embed = discord.Embed(
                title="⏰ انتهت المهلة الزمنية",
                description="**لم يتم العثور على صورة صالحة!**\n\n"
                            "يرجى التأكد من:\n"
                            "• الرد على رسالة التعليمات مع صورة\n"
                            "• أو إرسال صورة مباشرة في القناة\n"
                            "• إرفاق ملف صورة صالح\n"
                            "• الإرسال خلال 10 دقائق\n\n"
                            "انقر على الزر مرة أخرى للمحاولة مجدداً.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=timeout_embed, ephemeral=False)
        else:
            timeout_embed = discord.Embed(
                title="⏰ Time Expired",
                description="**No valid image found!**\n\n"
                            "Please make sure to:\n"
                            "• Reply to instruction message with image\n"
                            "• Or send image directly in this channel\n"
                            "• Attach a valid image file\n"
                            "• Send within 10 minutes\n\n"
                            "Click the button again to try again.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=timeout_embed, ephemeral=False)

    async def wait_for_message(self, interaction: discord.Interaction, instruction_message):
        """Wait for user's message with image attachment (direct send or reply)"""
        import asyncio

        def check(message):
            print(f"[DEBUG] Checking message from {message.author} in {message.channel}")
            print(f"[DEBUG] Expected user: {interaction.user}, Expected channel: {interaction.channel}")

            # Must be from the same user
            if message.author != interaction.user:
                print(f"[DEBUG] Wrong user: {message.author} != {interaction.user}")
                return False

            # Must be in the same channel  
            if message.channel != interaction.channel:
                print(f"[DEBUG] Wrong channel: {message.channel} != {interaction.channel}")
                return False

            # Must have attachments
            if not message.attachments:
                print("[DEBUG] No attachments found")
                return False

            print(f"[DEBUG] Found {len(message.attachments)} attachments")

            # Must have at least one image attachment
            image_attachments = [att for att in message.attachments if att.content_type and att.content_type.startswith('image/')]
            if not image_attachments:
                print("[DEBUG] No image attachments found")
                print(f"[DEBUG] Attachment types: {[att.content_type for att in message.attachments]}")
                return False

            print(f"[DEBUG] Found {len(image_attachments)} image attachments")
            return True

        try:
            print(f"[DEBUG] Starting to wait for message from {interaction.user.display_name} (ID: {interaction.user.id}) in channel {interaction.channel.name} (ID: {interaction.channel.id})")
            msg = await bot.wait_for('message', check=check, timeout=600)
            print(f"[DEBUG] Found message with {len(msg.attachments)} attachments")

            # Get the first image attachment
            image_attachments = [att for att in msg.attachments if att.content_type and att.content_type.startswith('image/')]
            if not image_attachments:
                print("[DEBUG] No valid image attachments found")
                return None

            image_attachment = image_attachments[0]
            print(f"[DEBUG] Using image attachment: {image_attachment.filename}")

            # Download image data BEFORE deleting the message
            try:
                image_data = await image_attachment.read()
                print(f"[DEBUG] Successfully downloaded image data: {len(image_data)} bytes")

                # Create a new attachment object with the downloaded data
                image_file = discord.File(
                    fp=BytesIO(image_data),
                    filename=image_attachment.filename
                )

                # Clean up the user's message AFTER downloading
                try:
                    await msg.delete()
                    print("[DEBUG] Successfully deleted user's message")
                except discord.NotFound:
                    print("[DEBUG] Message already deleted")
                except discord.Forbidden:
                    print("[DEBUG] No permission to delete message")

                return image_file
            except Exception as e:
                print(f"[DEBUG] Error downloading image data: {e}")
                return None
        except asyncio.TimeoutError:
            print("[DEBUG] Timeout waiting for image upload")
            return None
        except Exception as e:
            print(f"[DEBUG] Error in wait_for_message: {e}")
            return None



    async def submit_vouch_with_proof(self, interaction, image_file):
        feedback_channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
        if not feedback_channel:
            await interaction.followup.send("❌ Feedback channel not found.", ephemeral=False)
            return

        try:
            star_count = int(self.vouch_data['rating'])
            stars = "⭐" * star_count
        except:
            stars = "N/A"

        # Image file is already prepared with downloaded data
        # Just update the filename to include 'proof_' prefix
        original_filename = image_file.filename
        image_file.filename = f"proof_{original_filename}"

        # Map staff roles to their IDs for mentions
        staff_mentions = {
            "owner": "<@&1377574452203884605>",
            "moderator": "<@&1377586242132381736>",
        }

        # Map products to their channel links with emojis
        product_channels = {
            "valorant-points": "<:Valorant_Points:1386806798610337864> <#1377608623525728366>",
            "callofduty-cp": "<:COD_Point_BOCW2:1395768016255586376> <#1386423140464201909>",
            "overwatch-coins": "<:Overwatch_Coin:1395787416509485087> <#1395764822255210506>",
            "discord-nitro": "<:icons8discordnitro:1395950198915727512> <#1395949111412392068>",
            "gamepass": "<:xbox:1395953046688890962> <#1395765771161960489>",
            "others": "<:netflix:1395956599092150282> <#1395956006734925897>",
            "buy-accounts": "👤 Buy Accounts",  # No channel provided
            "fifa-coins": "⚽ FIFA Coins"  # No channel provided
        }

        staff_mention = staff_mentions.get(self.vouch_data['vouched_user'], self.vouch_data['vouched_user'])
        product_link = product_channels.get(self.vouch_data['product'], self.vouch_data['product'])

        embed = discord.Embed(
            title="💬 New Vouch",
            color=0xFF0000
        )

        # Set customer's banner as embed image (top)
        if self.vouch_data['submitter'].banner:
            embed.set_image(url=self.vouch_data['submitter'].banner.url)

        # Set customer's avatar and display name as author
        embed.set_author(
            name=f"Vouch by {self.vouch_data['submitter'].display_name}",
            icon_url=self.vouch_data['submitter'].avatar.url if self.vouch_data['submitter'].avatar else None
        )

        embed.add_field(name="🧾 Customer", value=self.vouch_data['submitter'].mention, inline=True)
        embed.add_field(name="📚 Product", value=product_link, inline=True)
        embed.add_field(name="⭐ Rating", value=f"{stars} ({self.vouch_data['rating']}/5)", inline=True)
        embed.add_field(name="👨‍💼 Staff Member", value=staff_mention, inline=True)
        embed.add_field(name="🗓️ Date", value=f"<t:{int(interaction.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="", value="", inline=True)  # Empty field for spacing

        # Enhanced feedback formatting
        feedback_preview = self.vouch_data['feedback'][:200] + "..." if len(self.vouch_data['feedback']) > 200 else \
            self.vouch_data['feedback']
        formatted_feedback = f"```yaml\n{feedback_preview}\n```"
        embed.add_field(name="📝 Customer Feedback", value=formatted_feedback, inline=False)

        # Set author as customer name with their avatar
        embed.set_author(
            name=f"{self.vouch_data['submitter'].display_name}",
            icon_url=self.vouch_data['submitter'].avatar.url if self.vouch_data['submitter'].avatar else None
        )

        # Clean footer with just developer credit
        embed.set_footer(text="Developed by: RxxD")
        embed.timestamp = interaction.created_at

        # Set proof image as thumbnail if no banner, otherwise add as separate field
        if not self.vouch_data['submitter'].banner:
            embed.set_image(url=f"attachment://{image_file.filename}")
        else:
            embed.set_thumbnail(url=f"attachment://{image_file.filename}")

        # Send the vouch message
        vouch_message = await feedback_channel.send(embed=embed, file=image_file)

        # Add reaction voting
        reactions = ["👍", "✅", "❤️"]
        for reaction in reactions:
            try:
                await vouch_message.add_reaction(reaction)
            except:
                pass

        # Create a thread reply with simple thank you message
        try:
            thread = await vouch_message.create_thread(
                name=f"Thanks {self.vouch_data['submitter'].display_name}!"
            )

            await thread.send("thank you 💗")
        except:
            pass

        # Update vouch tracking
        await update_vouch_count(self.vouch_data['submitter'].id, interaction.guild, self.vouch_data['product'])





@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
        
        
        # Resume active giveaways on restart
        global giveaway_tracking
        current_time = datetime.now()
        for giveaway_id, giveaway_data in list(giveaway_tracking["active_giveaways"].items()):
            end_time = datetime.fromisoformat(giveaway_data["end_time"])
            if current_time >= end_time:
                # Giveaway should have ended, end it now
                await end_giveaway(giveaway_id)
            else:
                # Schedule remaining time
                remaining_seconds = (end_time - current_time).total_seconds()
                if remaining_seconds > 0:
                    asyncio.create_task(schedule_giveaway_end_seconds(giveaway_id, remaining_seconds))
        
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print(f"✅ Logged in as {bot.user}")


async def schedule_giveaway_end_seconds(giveaway_id: str, seconds: float):
    """Schedule the end of a giveaway with specific seconds"""
    await asyncio.sleep(seconds)
    await end_giveaway(giveaway_id)


async def update_vouch_count(user_id: int, guild, product: str = None):
    """Update vouch count and check for milestone rewards"""
    global vouch_tracking
    user_id_str = str(user_id)

    # Update counts
    vouch_tracking["monthly_vouches"][user_id_str] = vouch_tracking["monthly_vouches"].get(user_id_str, 0) + 1
    vouch_tracking["total_vouches"][user_id_str] = vouch_tracking["total_vouches"].get(user_id_str, 0) + 1

    # Track user's product purchases
    if product:
        if user_id_str not in vouch_tracking["user_products"]:
            vouch_tracking["user_products"][user_id_str] = {}
        vouch_tracking["user_products"][user_id_str][product] = vouch_tracking["user_products"][user_id_str].get(
            product, 0) + 1

    total_count = vouch_tracking["total_vouches"][user_id_str]

    # Check for milestone rewards
    if total_count == 5:
        try:
            role = guild.get_role(MILESTONE_5_VOUCHES_ROLE)
            user = guild.get_member(user_id)
            if user and role:
                await user.add_roles(role, reason="5 Vouches Milestone Achieved!")

                channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
                if channel:
                    embed = discord.Embed(
                        title="🎖️ Milestone Achieved!",
                        description=f"🎉 {user.mention} has reached **5 vouches** and earned a special role!",
                        color=0xFF0000
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            print(f"Error awarding milestone role: {e}")

    save_vouch_data(vouch_tracking)


class VouchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Submit Vouch", style=discord.ButtonStyle.green)
    async def vouch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        language_view = LanguageSelectionView()

        embed = discord.Embed(
            title="🌐 Welcome to the Vouch System!",
            description="🌐 **Step 1: Select Language / الخطوة 1: اختر اللغة**\n\n"
                        "Please select your preferred language:\n"
                        "يرجى اختيار اللغة المفضلة لديك:",
            color=0xFF0000
        )
        embed.set_footer(text="Developed by: RxxD")

        await interaction.response.send_message(embed=embed, view=language_view, ephemeral=False)


@bot.tree.command(name="vouch", description="Submit a vouch via form")
async def vouch(interaction: discord.Interaction):
    language_view = LanguageSelectionView()

    embed = discord.Embed(
        title="🌐 Welcome to the Vouch System!",
        description="🌐 **Step 1: Select Language / الخطوة 1: اختر اللغة**\n\n"
                    "Please select your preferred language:\n"
                    "يرجى اختيار اللغة المفضلة لديك:",
        color=0xFF0000
    )
    embed.set_footer(text="Developed by: RxxD")

    await interaction.response.send_message(embed=embed, view=language_view, ephemeral=False)


@bot.tree.command(name="sendvouch", description="Send vouch request to a customer")
async def sendvouch(interaction: discord.Interaction, customer: discord.Member):
    embed = discord.Embed(
        title="🌟 Vouch Request / طلب تقييم",
        description=f"Hi {customer.mention}! You've been asked to submit a vouch.\n\nPlease click the button below to share your experience.",
        color=0xFF0000
    )
    embed.set_thumbnail(
        url="https://pouch.jumpshare.com/preview/oky3WC_tm0XahN3In8OYtac_KZszaiEYJ8BhsSmMG6BxrdsBS43-hWs4ybJyh6mxh_MUOcAssdOj7lSmtJ2pBu7nK7VYHo4fwHe9iBnI-RY")
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1367317832093667483/1394696445680025600/standard_1.gif?ex=68921dc8&is=6890cc48&hm=f3db0567b263407be6e52f82b5b5f5473dfcf65bd5be54dbf7124fdb1c65335b&")
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url)

    view = VouchView()

    # Send directly in the server channel only
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="creategiveaway", description="Create a new giveaway (Owner Only)")
async def create_giveaway_command(interaction: discord.Interaction):
    # Check if user is the server owner
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Only the server owner can use this command!", ephemeral=True)
        return
    
    product_view = GiveawayProductSelectionView()
    
    embed = discord.Embed(
        title="🎁 Create New Giveaway",
        description="Please select the product category you want to giveaway:",
        color=0xFF0000
    )
    
    await interaction.response.send_message(embed=embed, view=product_view, ephemeral=True)


@bot.tree.command(name="serverinvite", description="Get a shareable server invite link")
async def server_invite(interaction: discord.Interaction):
    try:
        # Create an invite that never expires and has unlimited uses
        invite = await interaction.channel.create_invite(
            max_age=0,  # Never expires
            max_uses=0,  # Unlimited uses
            unique=False,  # Don't create multiple invites to same channel
            reason="Server invite for giveaway sharing"
        )
        
        embed = discord.Embed(
            title="🎉 Share Our Amazing Server! 🎉",
            description=f"**Invite your friends to join the fun!**\n\n"
                       f"🎁 **Why join {interaction.guild.name}?**\n"
                       f"🔸 Regular FREE giveaways\n"
                       f"🔸 Gaming services & premium accounts\n"
                       f"🔸 Friendly community\n"
                       f"🔸 Fast delivery & trusted sellers\n\n"
                       f"**Share this link:** {invite.url}\n\n"
                       f"*The more people join, the bigger our giveaways get!* 🚀",
            color=0xFF0000
        )
        embed.set_footer(text="Help us grow and win bigger prizes!")
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Error creating invite: {str(e)}", ephemeral=True)


@bot.tree.command(name="listgiveaways", description="List active and recent giveaways (Owner Only)")
async def list_giveaways(interaction: discord.Interaction):
    # Check if user is the server owner
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Only the server owner can use this command!", ephemeral=True)
        return
    
    global giveaway_tracking
    
    embed = discord.Embed(
        title="🎁 Giveaway Status",
        color=0xFF0000
    )
    
    # Active giveaways
    if giveaway_tracking["active_giveaways"]:
        active_text = ""
        for giveaway_id, data in giveaway_tracking["active_giveaways"].items():
            end_time = datetime.fromisoformat(data["end_time"])
            active_text += f"**{data['title']}**\n"
            active_text += f"🎁 {data['product'].replace('-', ' ').title()}\n"
            active_text += f"⏰ Ends: <t:{int(end_time.timestamp())}:R>\n\n"
        
        embed.add_field(name="🟢 Active Giveaways", value=active_text[:1024], inline=False)
    else:
        embed.add_field(name="🟢 Active Giveaways", value="No active giveaways", inline=False)
    
    # Recent giveaways (last 5)
    recent_giveaways = sorted(giveaway_tracking["giveaway_history"], 
                            key=lambda x: x["start_time"], reverse=True)[:5]
    
    if recent_giveaways:
        recent_text = ""
        for data in recent_giveaways:
            start_time = datetime.fromisoformat(data["start_time"])
            winner_count = len(data.get("winners", []))
            recent_text += f"**{data['title']}**\n"
            recent_text += f"🎁 {data['product'].replace('-', ' ').title()}\n"
            recent_text += f"🏆 Winners: {winner_count}\n"
            recent_text += f"📅 <t:{int(start_time.timestamp())}:d>\n\n"
        
        embed.add_field(name="📜 Recent Giveaways", value=recent_text[:1024], inline=False)
    else:
        embed.add_field(name="📜 Recent Giveaways", value="No recent giveaways", inline=False)
    
    embed.set_footer(text="Developed by: RxxD")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="endgiveaway", description="Manually end a giveaway (Owner Only)")
@app_commands.describe(message_id="The message ID of the giveaway to end")
async def end_giveaway_manual(interaction: discord.Interaction, message_id: str):
    # Check if user is the server owner
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Only the server owner can use this command!", ephemeral=True)
        return
    
    global giveaway_tracking
    
    if message_id not in giveaway_tracking["active_giveaways"]:
        await interaction.response.send_message("❌ No active giveaway found with that message ID!", ephemeral=True)
        return
    
    try:
        await end_giveaway(message_id)
        await interaction.response.send_message("✅ Giveaway ended successfully!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error ending giveaway: {str(e)}", ephemeral=True)


bot.run(TOKEN)