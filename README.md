# Eetubotti (Discord administration/fun bot in Finnish)

## Requirements
1. A discord bot with [Presence, Server members and Message content intents](https://discord.com/developers/applications/)
2. A discord server with following roles (see `src/constants.py`):
   - Levels (`LEVEL_5`, `LEVEL_10`, `LEVEL_20`, ...)
   - Muted (`MUTED`)
   - Active (`ACTIVE`) (given to most active users)
   - Birthday (`BIRTHDAY`) role (given when user has birthday)
   - Squad (`SQUAD`) and Homie (`HOMIE`) roles (Squad for friends; Homie for Squad users who post something)
   - Moderator role (`MOD`)
   - Administrator role (`ADMIN`)
   - Owner role (`WHITENAME`, `JUSU`)
3. And the following channels:
   - AFK Voice channel (`AFK_CHANNEL`)
   - General (`YLEINEN`)
   - General 2 (`YLEINEN2`)
   - Bot commands (`BOTTIKOMENNOT`)
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
4. Create `.env` file on the project folder root, and add a line
   - `TOKEN={token}` where {token} is [the discord bot's token](https://discord.com/developers/applications/)
5. Make necessary changes to `src/constants.py` where server, role and channel IDs are from your server
6. Run the application by running
   - `python main.py`

## Development (creating a new module)
1. Create a python file or a python package on `src/modules/` folder
2. Use the `src.basemodule.BaseModule` as your plugin's class's base class (look at other modules)
3. Add the new module to `src/modules/module_list.py`

## Changing texts or language
1. Edit or add values in `assets/localization.json`
