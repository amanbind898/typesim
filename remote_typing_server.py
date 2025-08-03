import os
import asyncio
import websockets
from pynput.keyboard import Controller, Key
import time

keyboard = Controller()
pressed_keys = set()
text_history = []

# Map command keys to pynput Key objects
KEY_MAP = {
    "ENTER": Key.enter,
    "TAB": Key.tab,
    "SPACE": Key.space,
    "BACKSPACE": Key.backspace,
    "SHIFT": Key.shift,
    "CTRL": Key.ctrl,
    "ALT": Key.alt,
    "ESC": Key.esc,
    "UP": Key.up,
    "DOWN": Key.down,
    "LEFT": Key.left,
    "RIGHT": Key.right,
    "CMD": Key.cmd,      # Windows/Command key
    "WIN": Key.cmd,
    "DELETE": Key.delete,
    "CLEAR": None,  # Special command
}

def get_key_object(key_str):
    key_str = key_str.upper()
    return KEY_MAP.get(key_str, key_str.lower())  # fallback to character

def log_history(item):
    if len(text_history) > 50:  # store last 50 commands/texts only
        text_history.pop(0)
    text_history.append(item)

def handle_key_command(cmd_type, key):
    key_obj = get_key_object(key)
    if key_obj is None and key == "CLEAR":
        # Clear action handled in message loop
        return
    if cmd_type == "DOWN":
        keyboard.press(key_obj)
        pressed_keys.add(key)
    elif cmd_type == "UP":
        keyboard.release(key_obj)
        pressed_keys.discard(key)
    elif cmd_type == "PRESS":
        keyboard.press(key_obj)
        keyboard.release(key_obj)

async def type_text(websocket):
    print("✅ Client connected.")
    try:
        async for message in websocket:
            print(f"📥 Received: {message}")
            log_history(message)
            if message.startswith("__TEXT__"):
                text = message.replace("__TEXT__", "")
                for char in text:
                    keyboard.type(char)
                    time.sleep(0.00)  # slight delay per char
            elif message.startswith("__CMD__"):
                command = message.replace("__CMD__", "").upper()
                if command == "CLEAR":
                    for _ in range(100):
                        keyboard.press(Key.backspace)
                        keyboard.release(Key.backspace)
                        time.sleep(0.005)
                else:
                    handle_key_command("PRESS", command)
            elif message.startswith("__DOWN__"):
                handle_key_command("DOWN", message.replace("__DOWN__", "").upper())
            elif message.startswith("__UP__"):
                handle_key_command("UP", message.replace("__UP__", "").upper())
            elif message.startswith("__PRESS__"):
                handle_key_command("PRESS", message.replace("__PRESS__", "").upper())
            elif message.startswith("__HISTORY__LAST"):
                history_str = "\n".join(text_history[-10:])
                await websocket.send(f"__HISTORY__REPLY__{history_str}")
    except websockets.ConnectionClosed:
        print("❌ Client disconnected.")

async def main():
    # Render provides $PORT — must default for local dev
    PORT = int(os.environ.get('PORT', 8765))
    async with websockets.serve(type_text, "0.0.0.0", PORT):
        print(f"🚀 Server running at ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
