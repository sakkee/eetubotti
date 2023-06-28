# Eetubotti (Discord administration/fun bot in Finnish)

## Installation
1. [Download Python 3.11 or greater](https://www.python.org/downloads/)
2. Create virtual environment on the project root folder
- `python3.11 -m venv venv` (use /path/to/python3.11/python.exe instead of python3.11 if your Windows cmd/powershell doesn't find it, or [add the python3.11 executable to environment variables](https://www.educative.io/answers/how-to-add-python-to-path-variable-in-windows))
3. Activate the venv
- `venv\Scripts\Activate.ps1` on Powershell (Windows)
- `venv\Scripts\activate.bat` on cmd (Windows)
- `source venv/Scripts/activate` on linux
4. Install the required packages:
- `pip install -r requirements.txt`
5. Create `.env` file on the project folder root, and add a line
- `TOKEN={token}` where {token} is [the discord bot's token](https://discord.com/developers/applications/)
6. Make necessary changes to `src/constants.py` where server, role and channel IDs are from your server
7. Run the application by running
- `python main.py`

## Development (creating a new module)
1. Create a python file or a python package on `src/modules/` folder
2. Use the `src.modules.module.Module` as `Plugin`-named class's base class (look at other modules)
3. Add the new module to `src/modules/module_list.py`

## Changing texts or language
1. Edit or add values in `src/localizations.py`
