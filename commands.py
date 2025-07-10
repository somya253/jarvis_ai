# commands.py
import os
import platform
import webbrowser
from datetime import datetime
import urllib.parse
import subprocess
import re
import pyautogui
import random

# Dictionary of common applications with their platform-specific commands
APP_COMMANDS = {
    "chrome": {
        "Windows": "start chrome",
        "Darwin": "open -a 'Google Chrome'",
        "Linux": "google-chrome"
    },
    "firefox": {
        "Windows": "start firefox",
        "Darwin": "open -a Firefox",
        "Linux": "firefox"
    },
    "word": {
        "Windows": "start winword",
        "Darwin": "open -a 'Microsoft Word'",
        "Linux": "libreoffice --writer"
    },
    "excel": {
        "Windows": "start excel",
        "Darwin": "open -a 'Microsoft Excel'",
        "Linux": "libreoffice --calc"
    },
    "powerpoint": {
        "Windows": "start powerpnt",
        "Darwin": "open -a 'Microsoft PowerPoint'",
        "Linux": "libreoffice --impress"
    },
    "outlook": {
        "Windows": "start outlook",
        "Darwin": "open -a 'Microsoft Outlook'",
        "Linux": "thunderbird"
    },
    "spotify": {
        "Windows": "start spotify",
        "Darwin": "open -a Spotify",
        "Linux": "spotify"
    },
    "vscode": {
        "Windows": "code",
        "Darwin": "open -a 'Visual Studio Code'",
        "Linux": "code"
    },
    "terminal": {
        "Windows": "start cmd",
        "Darwin": "open -a Terminal",
        "Linux": "gnome-terminal"
    }
}

def handle_command(text):
    """Detect and handle custom commands in user input."""
    if text is None:
        return None
    ltext = text.lower()

    # Time query
    if "time" in ltext:
        now = datetime.now().strftime("%I:%M %p")
        return f"Sir, the current time is {now}."

    # Date query
    if "date" in ltext:
        today = datetime.now().strftime("%B %d, %Y")
        return f"Today's date is {today}, sir."

    # Open Notepad (Windows only)
    if "notepad" in ltext:
        if platform.system() == "Windows":
            os.system("notepad")
            return "Opening Notepad, sir."
        else:
            return "Notepad is only available on Windows systems, sir."

    # Open Calculator
    if "calculator" in ltext or "calc" in ltext:
        if platform.system() == "Windows":
            os.system("calc")
            return "Opening Calculator, sir."
        elif platform.system() == "Darwin":  # macOS
            os.system("open -a Calculator")
            return "Opening Calculator, sir."
        else:
            return "Calculator is not supported on this OS, sir."

    # Web search (triggered by "search <query>")
    if ltext.startswith("search "):
        query = ltext.split("search ", 1)[1]
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        webbrowser.open(url)
        return f"Searching for '{query}' on the web, sir."

    # System commands
    if "system info" in ltext:
        uname = platform.uname()
        return (
            f"System Information:\n"
            f"System: {uname.system}\n"
            f"Node Name: {uname.node}\n"
            f"Release: {uname.release}\n"
            f"Version: {uname.version}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {uname.processor}"
        )
    
    if "open browser" in ltext:
        webbrowser.open("https://www.google.com")
        return "Opening web browser, sir."
    
    if "shutdown" in ltext and "system" in ltext:
        return "System shutdown command received. Confirm with 'shutdown confirm'."
    
    if "shutdown confirm" in ltext:
        if platform.system() == "Windows":
            os.system("shutdown /s /t 1")
        else:
            os.system("shutdown -h now")
        return "Shutting down system..."
    
    # JARVIS-specific commands
    if "jarvis" in ltext and ("thank" in ltext or "thanks" in ltext):
        return "You're welcome, sir. Always at your service."
    
    if "jarvis" in ltext and ("good" in ltext and "morning" in ltext):
        return "Good morning, sir. How may I assist you today?"
        
    if "jarvis" in ltext and ("good" in ltext and "night" in ltext):
        return "Good night, sir. Do you require any assistance before I enter standby mode?"

    # Open any application
    if "open " in ltext:
        # Extract application name
        app_name = ltext.split("open ", 1)[1].strip()
        
        # Check if it's a known application
        if app_name in APP_COMMANDS:
            cmd = APP_COMMANDS[app_name].get(platform.system())
            if cmd:
                os.system(cmd)
                return f"Opening {app_name}, sir."
            else:
                return f"Sorry sir, {app_name} is not supported on this platform."
        
        # Try to open as a general application
        try:
            if platform.system() == "Windows":
                os.system(f"start {app_name}")
            elif platform.system() == "Darwin":
                os.system(f"open -a '{app_name}'")
            else:  # Linux
                os.system(f"{app_name} &")
            return f"Opening {app_name}, sir."
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"

    # Music commands
    if "play music" in ltext or "start music" in ltext:
        query = ltext.split("music", 1)[1].strip() if "music" in ltext else ""
        return "play_music:" + query
        
    if "pause music" in ltext:
        return "pause_music"
        
    if "resume music" in ltext or "continue music" in ltext:
        return "resume_music"
        
    if "stop music" in ltext:
        return "stop_music"
        
    # Alarm commands
    if "set alarm" in ltext:
        # Extract time (HH:MM format)
        match = re.search(r'(\d{1,2}:\d{2})', text)
        if match:
            time_str = match.group(1)
            return "set_alarm:" + time_str
        else:
            return "Please specify time in HH:MM format, sir."
        
    # Fun commands
    if "flip a coin" in ltext:
        return "flip_coin"
        
    if "roll a dice" in ltext or "roll dice" in ltext:
        return "roll_dice"
        
    # Camera command
    if "open camera" in ltext:
        return open_camera()
        
    # ===== CINEMATIC COMMANDS =====
    if "activate hologram" in ltext:
        return "activate_hologram"
        
    if "deactivate hologram" in ltext:
        return "deactivate_hologram"
        
    if "security mode" in ltext and "activate" in ltext:
        return "activate_security_mode"
        
    if "security mode" in ltext and ("deactivate" in ltext or "stand down" in ltext):
        return "deactivate_security_mode"
        
    if "send email" in ltext:
        # Simplified parsing
        parts = ltext.split("send email")[1].split(" to ")
        if len(parts) > 1:
            recipient = parts[1].split(" subject ")[0].strip()
            subject = parts[1].split(" subject ")[1].split(" body ")[0].strip()
            body = parts[1].split(" body ")[1].strip()
            return f"send_email:{recipient}|{subject}|{body}"
        return "Please specify recipient, subject and body, sir."
        
    if "weather" in ltext:
        return "get_weather"
        
    if "news" in ltext:
        return "get_news"
        
    if "analyze" in ltext:
        return "analyze_object"
        
    if "activate defense" in ltext or "activate weapons" in ltext:
        return "activate_defense_systems"
        
    if "jarvis" in ltext and "status" in ltext:
        return "Running all systems at peak efficiency, sir. All protocols nominal."
        
    if "initiate protocol" in ltext:
        protocols = [
            "House Party Protocol",
            "Clean Slate Protocol",
            "Iron Legion Protocol",
            "Veronica Protocol"
        ]
        return f"Initiating {random.choice(protocols)}, sir."
        
    # Screen capture command
    if "take screenshot" in ltext:
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.png")
            return "Screenshot captured and saved, sir."
        except Exception as e:
            return f"Failed to capture screenshot: {str(e)}"
            
    # Lock computer command
    if "lock system" in ltext:
        try:
            if platform.system() == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Darwin":
                os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")
            else:  # Linux
                os.system("gnome-screensaver-command -l")
            return "System locked, sir."
        except Exception as e:
            return f"Failed to lock system: {str(e)}"

    # Face recognition commands
    if "who is this" in ltext or "recognize face" in ltext:
        return "recognize_face"
        
    if "remember this face" in ltext:
        name = ltext.split("as", 1)[1].strip() if "as" in ltext else "User"
        return f"register_face:{name}"
        
    # Screen control commands
    if "dim screen" in ltext or "lower brightness" in ltext:
        return "dim_screen"
        
    if "brighten screen" in ltext or "increase brightness" in ltext:
        return "brighten_screen"
        
    if "reset brightness" in ltext:
        return "reset_brightness"
        
    # System health commands
    if "system health" in ltext or "system status" in ltext:
        return "system_health"
        
    # Entertainment commands
    if "tell me a joke" in ltext:
        return "tell_joke"
        
    if "flip a switch" in ltext:
        return "flip_switch"
        
    if "play game" in ltext:
        game_name = ltext.split("game", 1)[1].strip() if "game" in ltext else ""
        return f"play_game:{game_name}"
        
    if "system scan" in ltext:
        return "system_scan"
        
    # Camera surveillance command
    if "surveillance mode" in ltext:
        if "activate" in ltext:
            return "activate_surveillance"
        elif "deactivate" in ltext:
            return "deactivate_surveillance"
            
    # Math commands
    if "calculate" in ltext or "what is" in ltext and ("+" in text or "-" in text or "*" in text or "/" in text or "math" in ltext):
        # Extract expression
        expression = ltext.split("calculate", 1)[1].strip() if "calculate" in ltext else ltext.split("what is", 1)[1].strip()
        return f"calculate:{expression}"
        
    # Drone control commands
    if "drone" in ltext or "car" in ltext:
        if "connect" in ltext:
            return "connect_drone"
        elif "disconnect" in ltext:
            return "disconnect_drone"
        elif "take off" in ltext:
            return "takeoff_drone"
        elif "land" in ltext:
            return "land_drone"
        elif "move forward" in ltext:
            return "move_drone:forward"
        elif "move backward" in ltext:
            return "move_drone:backward"
        elif "turn left" in ltext:
            return "move_drone:left"
        elif "turn right" in ltext:
            return "move_drone:right"
            
    return None

def open_camera():
    """Open camera application"""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("start microsoft.windows.camera:")
            return "Opening camera, sir."
        elif system == "Darwin":  # macOS
            os.system("open /System/Applications/Photo Booth.app")
            return "Opening camera, sir."
        elif system == "Linux":
            os.system("cheese &")
            return "Opening camera, sir."
        else:
            return "Camera not supported on this OS, sir."
    except Exception as e:
        return f"Failed to open camera: {str(e)}"