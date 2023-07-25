# Eetubotti (Discord administration/fun bot in Finnish)

## Requirements
1. A discord bot with [Presence, Server members and Message content intents](https://discord.com/developers/applications/)
2. A discord server with following roles (see `DEFAULT_CONFIG`):
   - Levels (`LEVEL_5`, `LEVEL_10`, `LEVEL_20`, ...)
   - Muted (`MUTED`)
   - Active (`ACTIVE`) (given to most active users)
   - Birthday (`BIRTHDAY`) role (given when user has birthday)
   - Squad (`SQUAD`) and Homie (`ACTIVE_SQUAD`) roles (Squad for friends; Active Squad for Squad users who post something)
   - Moderator role (`MOD`)
   - Administrator role (`ADMIN`)
   - Owner role (`FULL_ADMINISTRATOR`, `OWNER`)
3. And the following channels:
   - AFK Voice channel (`AFK_VOICE_CHANNEL`)
   - General (`GENERAL`)
   - General 2 (`GENERAL2`)
   - Bot commands (`BOTCOMMANDS`)
   - Hidden channel for casino embeds (`CASINO_HIDE_CHANNEL`)
   - Media (`MEDIA`)
4. The bot added to the discord server. Make sure the bot has the highest role on the server.
5. [Python 3.11 or greater](https://www.python.org/downloads/)

## Installation
1. Create virtual environment on the project root folder
   - `python3.11 -m venv venv` (use /path/to/python3.11/python.exe instead of python3.11 if your Windows cmd/powershell doesn't find it, or [add the python3.11 executable to environment variables](https://www.educative.io/answers/how-to-add-python-to-path-variable-in-windows))
2. Activate the venv
   - `venv\Scripts\Activate.ps1` on Powershell (Windows)
   - `venv\Scripts\activate.bat` on cmd (Windows)
   - `source venv/bin/activate` on linux
3. Install the required packages:
   - `pip install -r requirements.txt`
4. Copy `DEFAULT_CONFIG` file to `CONFIG` and make the necessary changes where server, role and channel IDs are from your server, and the `TOKEN` is [the discord bot's token](https://discord.com/developers/applications/)
5. Run the application by running
   - `python main.py`

## Development (creating a new module)
1. Create a python file or a python package on `src/modules/` folder
2. Use the `src.basemodule.BaseModule` as your plugin's class's base class (look at other modules)
3. Add the new module to `src/modules/module_list.py`

## Changing texts or language
1. Edit or add values in `assets/localization.json`
