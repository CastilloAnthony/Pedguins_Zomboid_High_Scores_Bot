# Pedguin_Zomboid_High_Scores_Bot
## Developed by Peter Mann (Pedguin) and Anthony Castillo (ComradeWolf)

A personalized discord bot made using the discord 2.6.4 library alongside the mcrcon 0.7.0 library for direct interactions with the Project Zomboid server and the paramiko 4.0.0 library for communicating with the host of the server. Includes custom slash prefixed commands, logging, and files for inputting your own authentication information.

### QuickStart:
1. Install requirements.txt using pipreqs (pip install -r requirements.txt)
2. Launch bot.py
3. Fill out the newly created settings_connection.json and settings_discord.json with your appropriate information.
4. Relaunch bot.py
5. You should now be able to interact with the bot in discord channels. Try the '/command'

#### Todo:
- Modify !sync to be /sync an ephermal
- Fix connection error with rcon pz server that appears after running for a while (Pending Completeion)
- Fix connection error with sftp server that appears after running for a while (Pending Completeion)
- Remove old/unused code and comments
- Move poll_players to a separate thread
- Move commands to a Cog class
- Move bot to a Bot class
- Implement a truncate pz_perk_log.json feature
- Remove anomalous player data (ongoing as they appear)
- Twitch bot to say deaths in twitch chat (very low priority)