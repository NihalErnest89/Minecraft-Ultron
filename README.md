# Minecraft Ultron

Automated Minecraft farming and utility bot using the GameQuery mod API. This project allows you to control a Minecraft client, automate farming, and interact with the game via chat commands and scripts.

## Features
- Automated farming routines for specific players/locations
- Chat command listener (responds to in-game chat and whispers)
- Player movement and navigation (goto, home, sleep, follow)
- Inventory and block interaction (drop items, right/left click, open containers)
- Integration with the GameQuery Minecraft mod

## Requirements
- Python 3.11+
- Minecraft with the [GameQuery mod](https://github.com/YeeticusFinch/GameQuery) installed and running
- The following Python packages (see `requirements.txt`):
  - keyboard
  - requests
  - python-dotenv

## Setup
1. **Clone this repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   Create a `.env` file in the project root with the following content:
   ```env
   LOG_PATH=C:\Users\yourname\AppData\Roaming\minecraft\logs\latest.log
   ```
   Replace the path with the location of your Minecraft `latest.log` file.
4. **Ensure Minecraft is running with the GameQuery mod loaded.**

## Usage
- **Automated Farming & Chat Listener:**
  Run the main script to start the bot and listen for chat commands:
  ```bash
  python scripts.py
  ```
  The bot will:
  - Connect to the GameQuery server
  - Listen for chat commands in the Minecraft log
  - Execute farming, sleep, home, and other commands as received

- **Direct Bot Control & Testing:**
  You can also run `mc-bot.py` directly for manual testing and to use the MCBot API interactively:
  ```bash
  python mc-bot.py
  ```
  This will present a simple menu for testing bot actions.

## Configuration
- **Farms and Home Coordinates:**
  Edit the `farms` and `HOME_COORDS` dictionaries in `scripts.py` to match your world and player setup.
- **Log Path:**
  Set the `LOG_PATH` variable in your `.env` file to point to your Minecraft `latest.log`.

## Example Chat Commands
- `farm home` — Start the farming routine and return home
- `farm` - Starts farming the nearest farm
- `sleep` — Go to the nearest bed and sleep
- `go home` — Return to home coordinates
- `stop` — Stop the current action
- `follow me` — Follow the player issuing the command
- `find a <thing>` — Go to the specified thing (e.g., `find a village`)

## Notes
- This bot is designed for use with the GameQuery mod and will not work with other Minecraft mod setups.
- Make sure you are in a multiplayer world with GameQuery setup before running the bot.
