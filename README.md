# Discord Vouch & Giveaway Bot

A powerful Discord bot that handles Vouch submissions and Giveaways, with interactive UI, multilingual support, persistent data, and customizable features.

# Author

- # Ali Huz – Developer & Maintainer
- # GitHub: https://github.com/AliHuzain

# Features
- ✅ Vouch System – Submit ratings for products, services, or staff.
- 🎉 Giveaway System – Create and manage giveaways easily.
- 🖤 Interactive Discord UI – Buttons, Select Menus, Modals, and Embeds.
- 💾 Persistent Data – Tracks Vouches and Giveaways across restarts.
- 🌐 Multilingual Support – Arabic & English.
- 📊 Progress Bars – Track Vouch submission progress.
- 🏅 Milestones – Automatic roles for users after reaching 5 Vouches.
- 🔗 Dynamic Placeholders – UI adapts to selected language.

# How it Works

1️⃣ General Flow
- User runs /vouch or clicks 📝 Submit Vouch.
- Select language.
- Choose product/service from Select Menu.
- Pick the staff/owner/moderator.
- Rate with 1⭐–5⭐.
- Write a comment in a Modal.
- Upload proof image (Reply or Direct Upload).
- Bot sends Embed in Feedback channel with all info.
- Vouch counts update, milestone roles applied.
  
2️⃣ Views (UI Components)
- ProductSelectionView
- Select product/service.
- Dynamic placeholder depending on language.
- Auto-next to UserSelectionView.
- Shows Progress Bar: 🟩⬜⬜⬜⬜⬜.
- UserSelectionView
- Select staff/owner/moderator.
- Auto-next to RatingSelectionView.
- RatingSelectionView
- Choose 1–5 stars.
- Next: CommentInputView.
- CommentInputView & CommentModal
- Opens Modal to write comment.
- Next: ProofUploadView.
- ProofUploadView
- Instructions to upload image proof.
- Reply to bot message
- Direct upload
- Validates file type.
- Sends Embed to Feedback channel:
  
```bash Embed Example:

------------------------------
| ⭐⭐⭐⭐ | Product: Widget X |
| User: @customername_+role   |
| Comment: "Great service!"   |
| Proof: Image attached       |
------------------------------
```


### 3️⃣ Slash Commands

| Command | Description |
|---------|-------------|
| `/vouch` | Start Vouch submission |
| `/sendvouch <customer>` | Request Vouch from a specific user |
| `/creategiveaway` | Create Giveaway (Owner only) |
| `/serverinvite` | Generate permanent invite link |


  
4️⃣ Persistent Data & Tracking
  - vouch_tracking.json – Track Vouches per user.
  - giveaway_tracking.json – Track giveaways and allow resuming after restart.
  - Auto-save after every update.



5️⃣ Example Progress Bars & Buttons

Vouch Progress:
- Step 1️⃣ Language Selected ✅
- Step 2️⃣ Product Selected 🟩⬜⬜⬜⬜⬜
- Step 3️⃣ User Selected 🟩🟩⬜⬜⬜⬜
- Step 4️⃣ Rating Selected 🟩🟩🟩⬜⬜⬜
- Step 5️⃣ Comment Added 🟩🟩🟩🟩⬜⬜
- Step 6️⃣ Proof Uploaded 🟩🟩🟩🟩🟩⬜
- Step 7️⃣ Vouch Sent  🟩🟩🟩🟩🟩🟩
- Buttons (Discord Representation)
- [📝 Submit Vouch]   [🎉 Create Giveaway]   [✅ Confirm]

6️⃣ Giveaway Example
- 🎉 **Giveaway Started!**
- Prize: Nitro Classic
- Ends: 24 hours
- Hosted by: @Admin
- React with 🎉 to enter!

7️⃣ Requirements
- Python 3.10+
- discord.py (with UI Components support)
- Discord Bot Token

# Setup environment variables or .env file:

- DISCORD_TOKEN=your_token_here
- FEEDBACK_CHANNEL_ID=channel_id
- MILESTONE_5_VOUCHES_ROLE=role_id
- Persistent storage (JSON or database)
  

# 8️⃣ Install dependencies

- ```pip install discord.py```

# 9️⃣ Run the bot
- ```python bot.py```

- Use ```/vouch``` or ```/sendvouch @user``` to test the bot.

# 🔟 Notes
- It can be used with any free hosting site, Don't forget your .env file for discord token from https://discord.com/developers/applications/
- wait_for_image_upload depends on bot.wait_for('message'). Ensure bot is globally defined.
- Emojis, images, and links are preconfigured in SelectOptions.
