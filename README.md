# Pedguin_Zomboid_High_Scores_Bot
## Developed by Peter Mann (Pedguin) and Anthony Castillo (ComradeWolf)

A personalized discord bot made using the discord 2.6.4 library alongside the mcrcon 0.7.0 library for direct interactions with the Project Zomboid server and the paramiko 4.0.0 library for communicating with the host of the server. Includes custom slash prefixed commands, logging, and files for inputting your own authentication information.

### QuickStart:
1. Install requirements.txt using pipreqs (pip install -r requirements.txt)
2. Launch bot.py
3. Fill out the newly created settings_connection.json and settings_discord.json with your appropriate information.
4. Relaunch bot.py
5. You should now be able to interact with the bot in chat channels. Try the '!help' command.

## Todo:
- Fix skill level up pings.
- Fix bot not updating player skill levels (possibly related to the former issue).
- Fix bot not recognizing player names with spaces in them.
- Implement a restart at midnight feature.