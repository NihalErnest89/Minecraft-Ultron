#!/usr/bin/env python3
"""
Simple test client for the GameQuery Minecraft mod.
Make sure Minecraft is running with the mod loaded before running this script.
"""

import socket
import json
import time
import sys
from typing import Dict, Any, Optional
import requests

class MCBot:
    def __init__(self, host: str = "localhost", port: int = 25566):
        self.host = host
        self.port = port
    
    def send_query(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a query to the Minecraft client and return the response."""
        try:
            # Create socket connection
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                # Send query as JSON
                query_json = json.dumps(query) + "\n"
                sock.sendall(query_json.encode('utf-8'))

                # Use a buffered reader to read the full line
                with sock.makefile('r', encoding='utf-8') as f:
                    response_line = f.readline()
                    return json.loads(response_line.strip())

        except socket.timeout:
            print(f"❌ Timeout connecting to {self.host}:{self.port}")
            return None
        except ConnectionRefusedError:
            print(f"❌ Connection refused to {self.host}:{self.port}")
            print("   Make sure Minecraft is running with the GameQuery mod loaded")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        
    def send_chat_message(self, message: str):
        """Send a chat message as the player."""
        print(f"\n💬 Sending chat message: '{message}'")
        response = self.send_query({"type": "send_chat", "message": message})
        
        if response:
            result = response.get("result", {})
            if result.get("success"):
                print(f"✅ {result.get('message', 'Message sent')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        return response
    
    def drop_item_from_slot(self, slot: int):
        """Drop an item from a specific inventory slot."""
        print(f"\n🗑️ Dropping item from slot {slot}...")
        response = self.send_query({"type": "drop_item", "slot": slot})
        
        if response:
            result = response.get("result", {})
            if result.get("success"):
                print(f"✅ {result.get('message', 'Item dropped')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        return response
    
    def drop_items_by_name(self, item_name: str):
        """Drop all items matching a name."""
        print(f"\n🗑️ Dropping items matching '{item_name}'...")
        response = self.send_query({"type": "drop_item", "name": item_name})
        
        if response:
            result = response.get("result", {})
            if result.get("success"):
                print(f"✅ {result.get('message', 'Items dropped')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        return response
    
    def rotate_player(self, yaw: float = None, pitch: float = None):
        """Rotate the player to a specific direction."""
        rotation_desc = []
        if yaw is not None:
            rotation_desc.append(f"yaw: {yaw}°")
        if pitch is not None:
            rotation_desc.append(f"pitch: {pitch}°")
        
        print(f"\n🔄 Rotating player ({', '.join(rotation_desc)})...")
        
        query = {"type": "rotate"}
        if yaw is not None:
            query["yaw"] = yaw
        if pitch is not None:
            query["pitch"] = pitch
            
        response = self.send_query(query)
        
        if response:
            result = response.get("result", {})
            if result.get("success"):
                print(f"✅ {result.get('message', 'Player rotated')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        return response
    
    def look_at(self, x: float, y: float, z: float):
        response = self.send_query({ "type": "point_to_xyz", "x": x, "y": y, "z": z })
    
    def get_position(self):
        """Get position query."""
        response = self.send_query({"type": "position"})
        
        if response:
            if "error" in response:
                print(f"❌ Error: {response['error']}")
            else:
                pos = response.get("position", {})
                #print(f"✅ Player position:")
                #print(f"   Location: ({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})")
                #print(f"   Rotation: Yaw {pos.get('yaw', 0):.1f}°, Pitch {pos.get('pitch', 0):.1f}°")
                #print(f"   Health: {pos.get('health', 0):.1f}/{pos.get('maxHealth', 0):.1f}")
                #print(f"   Food: {pos.get('food', 0)}/20")
                #print(f"   Level: {pos.get('level', 0)} (Total XP: {pos.get('experience', 0)})")
                return pos.get('x', 0), pos.get('y', 0), pos.get('z', 0), pos.get('yaw', 0), pos.get('pitch', 0), pos.get('health', 0), pos.get('maxHealth', 0), pos.get('food', 0), pos.get('level', 0), pos.get('experience', 0)

    def goto(self, x: float, y: float, z: float, tolerance: float = 2):
        print(f"Going to {x} {y} {z}")
        self.look_at(x, y, z)
        self.send_chat_message(f"#goto {x} {y} {z}")
        cx = -69420
        cy = -69420
        cz = -69420
        while abs(cx-x) > tolerance or abs(cy-y) > tolerance or abs(cz-z) > tolerance:
            cx, cy, cz, yaw, pitch, health, maxHealth, food, level, experience = self.get_position()
            time.sleep(1)
    
    def right_click(self):
        response = self.send_query({"type": "right_click"})
        
        if response:
            if "error" in response:
                print(f"❌ Error: {response['error']}")
    
    def left_click(self):
        response = self.send_query({"type": "left_click"})
        
        if response:
            if "error" in response:
                print(f"❌ Error: {response['error']}")
                
    def attack(self):
        response = self.send_query({"type": "attack"})
        
        if response:
            if "error" in response:
                print(f"❌ Error: {response['error']}")
                
    def open_container(self):
        response = self.send_query({"type": "open_container"})
        
        if response:
            if "error" in response:
                print(f"❌ Error: {response['error']}")

    def cheat_utils_post(self, endpoint: str, payload: dict):
        try:
            url = f"http://localhost:5005/api/{endpoint}"
            resp = requests.post(url, json=payload)
            print(url)
            print(resp.status_code)
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"Error posting {endpoint} with {payload}:", e)
            return False

    def press_right_click(self):
        payload = {
            "mouseInputDisabled": False,
            "holdForward": False,
            "holdAttack": False,
            "holdUse": True
        }
        self.cheat_utils_post("lock-inputs", payload)

    def release_right_click(self):
        payload = {
            "mouseInputDisabled": False,
            "holdForward": False,
            "holdAttack": False,
            "holdUse": False
        }
        self.cheat_utils_post("lock-inputs", payload)

    def get_block(self, x, y, z):
        """Get information about the block at the specified coordinates."""
        response = self.send_query({"type": "get_block", "x": x, "y": y, "z": z})
        if response:
            return response
        else:
            print(f"❌ Failed to get block at ({x}, {y}, {z})")
            return None

    def get_blocks_in_range(self, range_size: int = 5):
        """Get all blocks in a cubic range around the player."""
        response = self.send_query({"type": "blocks", "range": range_size})
        if response and "blocks" in response.get("blocks", {}):
            return response["blocks"]["blocks"]
        return []

def get_iron(client: MCBot):
    client.goto(-231, 96, 32.5)
    client.goto(-229.5, 65, 32.5)
    client.goto(-223.5, 66, 32.5)
    client.look_at(-221.5, 66, 32.5)
    time.sleep(1)
    client.open_container()

if __name__ == "__main__":
    print("🎮 GameQuery Minecraft Mod Test Client")
    print("=====================================")
    
    client = MCBot()
    
    # Test connection
    print("\n🔗 Testing connection...")
    test_response = client.send_query({"type": "position"})
    if test_response is None:
        print("❌ Cannot connect to GameQuery server")
        print("   Make sure:")
        print("   1. Minecraft is running")
        print("   2. GameQuery mod is loaded")
        print("   3. You're in a world (not main menu)")
        sys.exit(1)
    
    print("✅ Connected to GameQuery server!")
    running = True
    while running:
        try:
            print("\nWhat would you like to do next?")
            print("1. Get Iron")
            print("2. Action demo (demonstrate new features)")
            print("3. Exit")
                
            choice = input("Enter choice (1-3): ").strip()
                
            if choice == "1":
                get_iron(client)
            #elif choice == "2":
            #    action_demo()
            elif choice == "3":
                print("👋 Goodbye!")
                sys.exit(0)
                break
            else:
                print("Invalid choice. Goodbye!")
                    
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")