#!/usr/bin/env python3
"""
Minecraft Ultron - Automated farming script using GameQuery mod API
Uses the MCBot class for reliable communication with Minecraft
"""

import time
import math
import sys
import os
import keyboard
import importlib.util
from dotenv import load_dotenv
import ast

# Import MCBot class from the mc-bot.py file
spec = importlib.util.spec_from_file_location("mc_bot", "mc-bot.py")
mc_bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc_bot)
MCBot = mc_bot.MCBot

# --- Configuration ---

load_dotenv()
LOG_PATH = os.environ["LOG_PATH"] # path to your latest.log
BOT_NAME = os.environ.get("BOT_NAME", "IronManForever")

FARMS_FILE = "farms.txt"
WAYPOINTS_FILE = "waypoints.txt"

def load_farms():
    farms = {}
    if os.path.exists(FARMS_FILE):
        with open(FARMS_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    name, coords = line.strip().split('=', 1)
                    farms[name] = ast.literal_eval(coords)
    return farms

def save_farm(player, coords):
    farms = load_farms()
    farms[player] = coords
    with open(FARMS_FILE, 'w') as f:
        for name, c in farms.items():
            f.write(f"{name}={list(c)}\n")

farms = load_farms()

def load_waypoints():
    waypoints = {}
    if os.path.exists(WAYPOINTS_FILE):
        with open(WAYPOINTS_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    name, coords = line.strip().split('=', 1)
                    coords = tuple(map(float, coords.strip().split()))
                    waypoints[name] = coords
    return waypoints

def save_waypoint(name, coords):
    waypoints = load_waypoints()
    waypoints[name] = coords
    with open(WAYPOINTS_FILE, 'w') as f:
        for n, c in waypoints.items():
            f.write(f"{n}={' '.join(map(str, c))}\n")

waypoints = load_waypoints()

HOME_COORDS = (-4188, 59, 4259)

# --- Utilities ---

def tail_log_and_wait_for(targets, timeout=60):
    """Monitor log file for specific messages."""
    print(f"🕵️ Waiting for any of {targets} in logs...")
    start = time.time()
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        f.seek(0, os.SEEK_END)  # Go to end of log
        while time.time() - start < timeout:
            if keyboard.is_pressed('esc'):
                print("❌ ESC pressed — exiting.")
                exit()

            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue

            lower_line = line.lower()
            for target in targets:
                if target.lower() in lower_line:
                    print(f"✅ Found in log: {line.strip()}")
                    return target
    print(f"❌ Timeout: none of {targets} found.")
    return None

def wait_for_farm_completion(client: MCBot, timeout: int = 300):
    """Wait for farming to complete by monitoring log file."""
    print("🌾 Monitoring farming progress via log file...")
    
    # Wait for either "Farm failed" or "goal reached" in the logs
    result = tail_log_and_wait_for(["Farm failed", "goal reached"], timeout=timeout)
    
    if result is None:
        print(f"❌ Timeout: Farming did not complete within {timeout} seconds")
        return False
    elif "Farm failed" in result:
        print("❌ Farming failed!")
        return False
    else:
        print("✅ Farming completed successfully!")
        return True

def wait_for_arrival(client, tolerance=0.2, stable_required=1, check_interval=1.0, max_wait=60):
    """
    Wait until the player stops moving (position is stable) for a number of checks.
    Returns True if arrived, False if timeout.
    """
    stable_count = 0
    last_pos = None
    start_time = time.time()
    while stable_count < stable_required:
        pos = client.get_position()
        if last_pos is not None:
            dist = ((pos[0] - last_pos[0]) ** 2 + (pos[1] - last_pos[1]) ** 2 + (pos[2] - last_pos[2]) ** 2) ** 0.5
            if dist < tolerance:
                stable_count += 1
            else:
                stable_count = 0
        last_pos = pos
        if time.time() - start_time > max_wait:
            print("❌ Timeout waiting for arrival.")
            return False
        time.sleep(check_interval)
    return True

def get_new_chat_lines(last_pos):
    """Read new chat lines from the log file since last_pos. Returns (lines, new_pos)."""
    lines = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        f.seek(last_pos)
        while True:
            line = f.readline()
            if not line:
                break
            # Only process player chat messages (customize this filter as needed)
            if "]: <" in line:
                lines.append(line.strip())
        new_pos = f.tell()
    return lines, new_pos

# --- Main Logic ---

def farm_command(client: MCBot, player: str = None):
    if player not in farms:
        print(f"⚠️ Player '{player}' not found in farm dictionary.")
        return False

    fx, fy, fz = farms[player]
    hx, hy, hz = HOME_COORDS

    print(f"🚜 Starting farm routine for {player}...")

    # Step 1: Go to farm
    print(f"🚶 Walking to farm at ({fx}, {fy}, {fz})...")
    client.goto(fx, fy, fz, tolerance=2)

    # Step 2: Enable farming settings
    print("⚙️ Enabling farming settings...")
    client.send_chat_message("#settings allowBreak true")
    time.sleep(0.5)
    client.send_chat_message("#settings allowPlace true")
    time.sleep(0.5)

    # Step 3: Start farming
    print("🌾 Starting farming...")
    client.send_chat_message("#farm")
    
    # Wait for farming to complete
    farming_success = wait_for_farm_completion(client)
    
    # Step 4: Disable settings
    print("⚙️ Disabling farming settings...")
    client.send_chat_message("#settings allowBreak false")
    time.sleep(0.5)
    client.send_chat_message("#settings allowPlace false")
    time.sleep(0.5)

    # Step 5: Go to farm coords again, then to chest
    print(f"🔄 Returning to farm at ({fx}, {fy}, {fz}) to deposit items...")
    client.goto(fx, fy, fz, tolerance=2)
    print("📦 Going to chest...")
    client.send_chat_message("#goto chest")
    print("⏳ Waiting for arrival at chest...")
    wait_for_arrival(client, tolerance=0.2, stable_required=2)

    # Step 6: Return home (always return home regardless of farming success)
    print(f"🏠 Returning home to ({hx}, {hy}, {hz})...")
    client.goto(hx, hy, hz, tolerance=2)

    if farming_success:
        print(f"✅ Farming complete for {player}!")
        return True
    else:
        print(f"❌ Farming failed for {player}, but returned home safely.")
        return False

def sleep_command(client: MCBot, bed_type: str = "white_bed"):
    print(f"🛏️ Going to nearest {bed_type.replace('_', ' ')} with Baritone...")
    client.send_chat_message(f"#goto {bed_type}")

    # Wait for arrival by checking position stability
    print("⏳ Waiting for arrival at bed...")
    arrived = wait_for_arrival(client, tolerance=0.2, stable_required=2)
    if not arrived:
        print("Failed to arrive at bed in time.")
        return False

    # Try to find and interact with the bed, but don't crash if it fails
    try:
        print("🔎 Searching for bed to look at and use...")
        x0, y0, z0, *_ = client.get_position()
        if x0 is None:  # Check if position call failed
            print("⚠️ Could not get current position, skipping bed interaction")
            return True
            
        blocks = client.get_blocks_in_range(3)  # Reduced range to prevent overload
        if not blocks:  # Check if block scanning failed
            print("⚠️ Could not scan for blocks, trying simple bed use")
            client.use_bed()
            return True
            
        min_dist = 1000
        bed_coords = None
        for block in blocks:
            if block.get('type', '').lower() == f'block{{minecraft:{bed_type}}}':
                x, y, z = block.get('x', 0), block.get('y', 0), block.get('z', 0)
                dist = ((x - x0) ** 2 + (y - y0) ** 2 + (z - z0) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    bed_coords = (x, y, z)
        if bed_coords:
            client.send_chat_message("Zzzz")
            print(f"👀 Looking at {bed_type.replace('_', ' ')} at {bed_coords}")
            client.look_at(*bed_coords)
            time.sleep(0.5)
            print("Using bed")
            client.use_bed(bed_coords[0], bed_coords[1], bed_coords[2])
        else:
            print(f"⚠️ No {bed_type.replace('_', ' ')} found nearby, trying simple bed use")
            client.use_bed()
    except Exception as e:
        print(f"⚠️ Error during bed interaction: {e}")
        print("Trying simple bed use as fallback...")
        try:
            client.use_bed()
        except Exception as e2:
            print(f"❌ Fallback bed use also failed: {e2}")

    return True

def home_command(client: MCBot):
    hx, hy, hz = HOME_COORDS
    print(f"🏠 Going home to ({hx}, {hy}, {hz})...")
    client.goto(hx, hy, hz, tolerance=2)
    print("⏳ Waiting for arrival at home...")
    arrived = wait_for_arrival(client, tolerance=0.2, stable_required=3)
    if arrived:
        print("✅ Arrived at home!")
        return True
    else:
        print("❌ Failed to arrive at home in time.")
        return False

def crops_home_command(client: MCBot, player: str = None):
    if player not in farms:
        print(f"⚠️ Player '{player}' not found in farm dictionary.")
        return False

    fx, fy, fz = farms[player]
    hx, hy, hz = HOME_COORDS

    print(f"🌾 Starting crops home routine for {player}...")

    # Step 1: Go to farm
    print(f"🚶 Walking to farm at ({fx}, {fy}, {fz})...")
    client.goto(fx, fy, fz, tolerance=2)

    # Step 2: Go to chest
    print("📦 Going to chest...")
    client.send_chat_message("#goto chest")
    print("⏳ Waiting for arrival at chest...")
    wait_for_arrival(client, tolerance=0.2, stable_required=2)

    # Step 3: Return home
    print(f"🏠 Returning home to ({hx}, {hy}, {hz})...")
    client.goto(hx, hy, hz, tolerance=2)

    print(f"✅ Crops home complete for {player}!")
    return True

def send_cmd(client: MCBot, cmd: str, player: str = None):
    """Send a command using the MCBot API."""
    if cmd.lower() == "farm":
        return farm_command(client, player)
    elif cmd.lower().startswith("sleep"):
        parts = cmd.split()
        bed_type = parts[1] if len(parts) > 1 else "white_bed"
        return sleep_command(client, bed_type)
    elif cmd.lower() == "home":
        return home_command(client)
    elif cmd.lower() == "crops home":
        return crops_home_command(client, player)
    elif cmd.lower().startswith("go to "):
        arg = cmd[6:].strip()
        # Try to interpret as coordinates first
        coords = None
        try:
            coords = tuple(map(float, arg.split()))
        except Exception:
            coords = None
        if coords and len(coords) == 3:
            print(f"🚶 Going to coordinates {coords}...")
            client.goto(*coords, tolerance=2)
            print(f"✅ Arrived at {coords}!")
            return True
        else:
            global waypoints
            waypoints = load_waypoints()
            print(f"🔎 Available waypoints: {list(waypoints.keys())}")
            if arg in waypoints:
                coords = waypoints[arg]
                print(f"🚶 Going to waypoint '{arg}' at {coords}...")
                client.send_chat_message(f"#goto {coords[0]} {coords[1]} {coords[2]}")
                print(f"✅ Sent #goto for waypoint '{arg}'!")
                return True
            else:
                print(f"❌ No such waypoint or invalid coordinates: {arg}")
                return False
    else:
        print(f"💬 Sending command: {cmd}")
        client.send_chat_message(cmd)
        return True

def get_player_status(client: MCBot):
    """Get and display current player status."""
    try:
        x, y, z, yaw, pitch, health, max_health, food, level, experience = client.get_position()
        print(f"\n📊 Player Status:")
        print(f"   Location: ({x:.1f}, {y:.1f}, {z:.1f})")
        print(f"   Rotation: Yaw {yaw:.1f}°, Pitch {pitch:.1f}°")
        print(f"   Health: {health:.1f}/{max_health:.1f}")
        print(f"   Food: {food}/20")
        print(f"   Level: {level} (Total XP: {experience})")
        return True
    except Exception as e:
        print(f"❌ Error getting player status: {e}")
        return False

# --- Entry Point ---

def main():
    global waypoints
    print("🎮 Minecraft Ultron - GameQuery Edition")
    print("=====================================")

    client = MCBot()

    # Test connection
    print("\n🔗 Testing connection to GameQuery server...")
    test_response = client.send_query({"type": "position"})
    if test_response is None:
        print("❌ Cannot connect to GameQuery server")
        return

    print("✅ Connected to GameQuery server!")
    get_player_status(client)

    # Get initial file size
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        f.seek(0, os.SEEK_END)
        last_pos = f.tell()

    print("\n🕵️ Listening for chat commands in Minecraft...")
    while True:
        lines = []
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            f.seek(last_pos)
            while True:
                line = f.readline()
                if not line:
                    break
                lines.append(line.strip())
            last_pos = f.tell()
        for line in lines:
            print(f"LOG: {line}")
            user = None
            msg = None
            # Public chat: [CHAT] <User> command
            if "[CHAT] <" in line:
                try:
                    user_and_msg = line.split("[CHAT] <", 1)[1]
                    user, msg = user_and_msg.split(">", 1)
                    user = user.strip()
                    msg = msg.strip()
                    if user == BOT_NAME:
                        continue  # Ignore messages sent by the bot itself
                    print(f"📝 Detected chat from {user}: {msg}")
                except Exception as e:
                    print(f"Failed to parse chat line: {line} ({e})")
                    continue
            # Whisper: [CHAT] User whispers to you: command
            elif "[CHAT]" in line and "whispers to you:" in line:
                try:
                    after_chat = line.split("[CHAT]", 1)[1].strip()
                    user, msg = after_chat.split("whispers to you:", 1)
                    user = user.strip()
                    msg = msg.strip()
                    if user == BOT_NAME:
                        continue  # Ignore messages sent by the bot itself
                    print(f"📝 Detected whisper from {user}: {msg}")
                except Exception as e:
                    print(f"Failed to parse whisper line: {line} ({e})")
                    continue
            else:
                continue

            # Check for farm set command
            if msg and msg.lower().startswith("my farm is at"):
                try:
                    coords = msg.lower().replace("my farm is at", "").strip().split()
                    if len(coords) == 3:
                        coords = tuple(map(float, coords))
                        save_farm(user, coords)
                        global farms
                        farms = load_farms()
                        print(f"✅ Set farm for {user} to {coords}")
                        client.send_chat_message(f"Your farm is at {coords}")
                        continue
                except Exception as e:
                    print(f"❌ Failed to set farm for {user}: {e}")
                    continue

            # Now handle commands as before
            if msg is None or user is None:
                continue
            if msg.strip() == "farm":
                client.send_chat_message("#farm")
            elif msg.strip().startswith("farm home"):
                send_cmd(client, "farm", user)
            elif msg.strip().startswith("crops home"):
                send_cmd(client, "crops home", user)
            elif msg.startswith("sleep"):
                send_cmd(client, msg, user)
            elif msg.startswith("go to "):
                send_cmd(client, msg, user)
            elif msg.startswith("go home"):
                send_cmd(client, "home", user)
            elif msg.startswith("stop"):
                client.send_chat_message("#stop")
                client.send_chat_message(f"#allowBreak false")
            elif msg.startswith("follow me"):
                client.send_chat_message(f"#follow player {user}")
                client.send_chat_message(f"Ok komrad")
                # Wait a moment for the follow command to process
                time.sleep(2)
                
                # Check if follow failed by looking for error in recent log entries
                with open(LOG_PATH, 'r', encoding='utf-8') as f:
                    f.seek(0, os.SEEK_END)
                    f.seek(max(0, f.tell() - 1000))  # Check last 1000 characters
                    recent_log = f.read()
                    
                    if "No valid entities in range!" in recent_log:
                        print(f"⚠️ Follow failed for {user}, trying to find player location...")
                        
                        # Get player coordinates and go there
                        coords = client.get_player_coords(user)
                        if coords:
                            x, y, z = coords
                            print(f"📍 Found {user} at ({x}, {y}, {z}), going there...")
                            client.send_chat_message(f"#goto {x} {y} {z}")
                        else:
                            print(f"❌ Could not find player {user} in the world")
                    else:
                        print(f"✅ Following {user}")
            elif msg.startswith("find a "):
                thing = msg[len("find a "):].strip()
                if thing:
                    client.send_chat_message(f"#goto {thing}")
            elif msg.startswith("mine "):
                block = msg[len("mine "):].strip()
                if block:
                    client.send_chat_message(f"#allowBreak true")
                    print(f"⛏️ Mining {block}...")
                    client.send_chat_message(f"#mine {block}")
                    client.send_chat_message(f"Mining {block} away (till you say stop)!")
            elif msg.startswith("set "):
                parts = msg.split()
                if len(parts) == 5 and parts[2].replace('.', '', 1).replace('-', '', 1).isdigit():
                    name = parts[1]
                    try:
                        coords = tuple(map(float, parts[2:5]))
                        save_waypoint(name, coords)
                        global waypoints
                        waypoints = load_waypoints()
                        print(f"✅ Set waypoint '{name}' to {coords}")
                        client.send_chat_message(f"'{name}' is set to {coords}")
                    except Exception as e:
                        print(f"❌ Failed to set waypoint: {e}")
                else:
                    print("❌ Usage: set <name> <x> <y> <z>")
            elif msg.startswith("go to "):
                arg = msg[len("go to "):].strip()
                # Try to interpret as coordinates first
                coords = None
                try:
                    coords = tuple(map(float, arg.split()))
                except Exception:
                    coords = None
                if coords and len(coords) == 3:
                    print(f"🚶 Going to coordinates {coords}...")
                    client.goto(*coords, tolerance=2)
                    print(f"✅ Arrived at {coords}!")
                else:
                    # Always reload waypoints in case they were updated
                    waypoints = load_waypoints()
                    print(f"🔎 Available waypoints: {list(waypoints.keys())}")
                    if arg in waypoints:
                        coords = waypoints[arg]
                        print(f"🚶 Going to waypoint '{arg}' at {coords}...")
                        client.send_chat_message(f"#goto {coords[0]} {coords[1]} {coords[2]}")
                        print(f"✅ Sent #goto for waypoint '{arg}'!")
                    else:
                        print(f"❌ No such waypoint or invalid coordinates: {arg}")
            # Add more commands as needed
        time.sleep(2)

if __name__ == "__main__":
    main()
