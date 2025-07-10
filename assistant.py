# assistant.py
import os
import pyttsx3
import speech_recognition as sr
from openai import OpenAI
from commands import handle_command
from dotenv import load_dotenv
import platform
import webbrowser
import datetime
import pygame
import threading
import random
import time
import subprocess
import cv2
import numpy as np
import face_recognition 
import pickle
import winsound
import json
from PIL import Image
import sys
import pyautogui
import math
import sympy  # For advanced math capabilities
import serial  # For drone/car control

# Handle psutil import
try:
    import psutil # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ─── Load and verify the OpenAI API key ─────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = None
if API_KEY:
    client = OpenAI(api_key=API_KEY)

class DroneController:
    """Class to control drones or RC cars"""
    def __init__(self):
        self.connected = False
        self.serial_connection = None
        self.command_queue = []
        
    def connect(self, port='COM3', baudrate=9600):
        """Connect to the drone/car via serial"""
        try:
            self.serial_connection = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            return "Drone connected successfully, sir."
        except Exception as e:
            return f"Failed to connect to drone: {str(e)}, sir."
            
    def disconnect(self):
        """Disconnect from the drone/car"""
        if self.connected and self.serial_connection:
            self.serial_connection.close()
            self.connected = False
            return "Drone disconnected, sir."
        return "Drone is not connected, sir."
        
    def send_command(self, command):
        """Send a command to the drone/car"""
        if not self.connected:
            return "Drone is not connected, sir."
            
        try:
            if self.serial_connection is not None:
                self.serial_connection.write(command.encode())
                return f"Command '{command}' sent to drone, sir."
            else:
                return "Serial connection is not established, sir."
        except Exception as e:
            return f"Failed to send command: {str(e)}, sir."
            
    def move_forward(self, duration=1):
        return self.send_command(f"FWD{duration}")
        
    def move_backward(self, duration=1):
        return self.send_command(f"BCK{duration}")
        
    def turn_left(self, degrees=90):
        return self.send_command(f"LFT{degrees}")
        
    def turn_right(self, degrees=90):
        return self.send_command(f"RGT{degrees}")
        
    def takeoff(self):
        return self.send_command("TOFF")
        
    def land(self):
        return self.send_command("LAND")

class FaceRecognition:
    def __init__(self):
        self.known_faces = {}
        self.face_data_file = "face_data.dat"
        self.load_face_data()
        
    def load_face_data(self):
        if os.path.exists(self.face_data_file):
            try:
                with open(self.face_data_file, 'rb') as f:
                    self.known_faces = pickle.load(f)
            except:
                self.known_faces = {}
    
    def save_face_data(self):
        with open(self.face_data_file, 'wb') as f:
            pickle.dump(self.known_faces, f)
    
    def recognize_face(self):
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            return "Camera not available, sir."
        
        # Capture single frame
        ret, frame = video_capture.read()
        
        if not ret:
            video_capture.release()
            return "Could not capture image, sir."
        
        # Find all face locations and encodings
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        if not face_encodings:
            video_capture.release()
            return "No faces detected, sir."
        
        recognized_names = []
        
        for face_encoding in face_encodings:
            # Compare with known faces
            for name, known_encoding in self.known_faces.items():
                match = face_recognition.compare_faces([known_encoding], face_encoding)
                if match[0]:
                    recognized_names.append(name)
                    break
        
        video_capture.release()
        
        if recognized_names:
            return f"I see {', '.join(recognized_names)}, sir."
        return "I see an unknown person, sir."
    
    def register_face(self, name):
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            return "Camera not available, sir."
        
        # Capture single frame
        ret, frame = video_capture.read()
        
        if not ret:
            video_capture.release()
            return "Could not capture image, sir."
        
        # Find face encodings
        face_encodings = face_recognition.face_encodings(frame)
        
        if not face_encodings:
            video_capture.release()
            return "No faces detected, sir."
        
        # Save first face found
        self.known_faces[name] = face_encodings[0]
        self.save_face_data()
        
        video_capture.release()
        return f"Face registered for {name}, sir."

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playlist = []
        self.current_index = 0
        self.playing = False
        self.paused = False
        self.load_default_playlist()
        
    def load_default_playlist(self):
        """Load music from default directories"""
        # Check common music directories
        possible_dirs = [
            os.path.join(os.path.expanduser("~"), "Music"),
            os.path.join(os.path.expanduser("~"), "Documents", "Music"),
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "/music",
            "/sdcard/Music"  # For Android devices
        ]
        
        for music_dir in possible_dirs:
            if os.path.exists(music_dir):
                for file in os.listdir(music_dir):
                    if file.endswith((".mp3", ".wav", ".ogg", ".flac")):
                        self.playlist.append(os.path.join(music_dir, file))
                
                # Stop after finding the first directory with music
                if self.playlist:
                    break
    
    def play_music(self, query=""):
        if not self.playlist:
            return "No music found in your music directories, sir."
            
        if self.paused:
            return self.resume_music()
            
        if query:
            # Try to find matching track
            matches = [i for i, path in enumerate(self.playlist) 
                      if query.lower() in os.path.basename(path).lower()]
            if matches:
                self.current_index = matches[0]
        
        if not self.playing:
            self.playing = True
            threading.Thread(target=self._play_current).start()
            track_name = os.path.basename(self.playlist[self.current_index])
            return f"Playing {track_name}, sir."
        return "Music is already playing, sir."
        
    def _play_current(self):
        try:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and self.playing:
                time.sleep(1)
        except Exception as e:
            print(f"Music playback error: {e}")
    
    def pause_music(self):
        if self.playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            return "Music paused, sir."
        return "No music is currently playing, sir."
        
    def resume_music(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            return "Resuming music, sir."
        return "Music is not paused, sir."
        
    def stop_music(self):
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False
            self.paused = False
            return "Music stopped, sir."
        return "No music is currently playing, sir."
        
    def next_track(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            if self.playing:
                self.stop_music()
                self.play_music()
            return f"Playing next track: {os.path.basename(self.playlist[self.current_index])}, sir."
        return "No music available, sir."
        
    def previous_track(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            if self.playing:
                self.stop_music()
                self.play_music()
            return f"Playing previous track: {os.path.basename(self.playlist[self.current_index])}, sir."
        return "No music available, sir."

class Assistant:
    """
    Core assistant logic: TTS, STT, custom commands, GPT fallback, and mic toggle.
    """
    def __init__(self, gui=None):
        # Text‑to‑Speech engine
        self.engine = pyttsx3.init()
        rate = self.engine.getProperty("rate")
        self.engine.setProperty("rate", rate - 20)
        
        # Try to set a deeper voice
        try:
            voices = self.engine.getProperty('voices')
            # Prefer male voice if available
            for voice in voices:
                if "male" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            # If no male voice, use first available
            if not self.engine.getProperty('voice'):
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"Voice setting error: {e}")

        # Speech recognizer
        self.recognizer = sr.Recognizer()

        # Mic toggle flag
        self.mic_enabled = True
        
        # Music player
        self.music_player = MusicPlayer()
        
        # Alarm tracking
        self.active_alarms = []
        
        # GUI reference
        self.gui = gui
        
        # Security mode
        self.security_mode = False
        self.security_thread = None
        
        # Cinematic responses
        self.responses = {
            "greeting_morning": [
                "Good morning, sir. Systems are fully operational. How may I assist?",
                "Rise and shine, sir. All systems nominal. What's on the agenda today?"
            ],
            "greeting_evening": [
                "Good evening, sir. How may I be of service?",
                "Evening, sir. All systems green. What do you require?"
            ],
            "acknowledgement": [
                "Certainly, sir.",
                "Right away, sir.",
                "Processing your request, sir.",
                "Executing now, sir."
            ],
            "confirmation": [
                "Task completed, sir.",
                "Operation successful, sir.",
                "Request fulfilled, sir."
            ],
            "security_alert": [
                "Security alert! Potential threat detected!",
                "Warning! Unauthorized access attempt!",
                "Threat assessment initiated!"
            ]
        }
        
        # Face recognition system
        self.face_recognition = FaceRecognition()
        
        # Screen control
        self.original_brightness = self.get_display_brightness()
        
        # Hologram state
        self.hologram_active = False
        self.hologram_thread = None
        
        # Drone controller
        self.drone_controller = DroneController()

    from typing import Optional

    def cinematic_speak(self, text: str, category: Optional[str] = None):
        """Speak with cinematic flair and visual effects"""
        # Select random cinematic response if category provided
        if category and category in self.responses:
            text = random.choice(self.responses[category])
        
        # Add subtle sound effect before speaking
        try:
            winsound.Beep(800, 100)  # System engage sound
        except:
            pass
        
        # Speak with enhanced effects
        self.speak(text)
        
        # Add subtle sound effect after speaking
        try:
            winsound.Beep(600, 100)  # System disengage sound
        except:
            pass

    def toggle_mic(self) -> bool:
        """
        Toggle the microphone on/off.
        Returns the new state (True=on, False=off).
        """
        self.mic_enabled = not self.mic_enabled
        return self.mic_enabled

    def speak(self, text: str):
        """Speak the given text out loud with JARVIS-like processing effect."""
        print(f"J.A.R.V.I.S.: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, timeout: int = 5) -> str:
        """
        Listen to the microphone and return recognized text.
        If mic is disabled or recognition fails, returns an empty string.
        """
        if not self.mic_enabled:
            return ""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, phrase_time_limit=timeout)
                return self.recognizer.recognize_google(audio) # type: ignore
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return ""
        except Exception as e:
            print(f"Microphone error: {e}")
            return ""

    def solve_math_problem(self, problem):
        """Solve mathematical problems using sympy"""
        try:
            # Try to parse and solve the expression
            expr = sympy.sympify(problem)
            result = sympy.N(expr)
            return f"The solution is {result}, sir."
        except:
            # Handle more complex equations
            try:
                if '=' in problem:
                    # Solve equations
                    equation = problem.split('=')[0] + '-(' + problem.split('=')[1] + ')'
                    x = sympy.Symbol('x')
                    result = sympy.solve(equation, x)
                    return f"The solution is {result}, sir."
                else:
                    # Evaluate expression
                    result = eval(problem, {"__builtins__": None}, 
                                {k: v for k, v in math.__dict__.items() if not k.startswith('__')})
                    return f"The result is {result}, sir."
            except Exception as e:
                return f"Could not solve the problem: {str(e)}, sir."

    def process_input(self, text: str) -> str:
        """
        Handle a user message: run custom commands first;
        otherwise, query OpenAI and return its response.
        """
        text = text.strip()
        if not text:
            return "I didn't catch that, sir."
            
        ltext = text.lower()
        
        # Handle greetings with cinematic responses
        if any(greeting in ltext for greeting in ["good morning", "morning jarvis"]):
            return random.choice(self.responses["greeting_morning"])
        
        if any(greeting in ltext for greeting in ["good evening", "evening jarvis"]):
            return random.choice(self.responses["greeting_evening"])

        # 1) Custom commands
        cmd_resp = handle_command(text)
        if cmd_resp is not None:
            # Handle special commands that need processing
            if cmd_resp.startswith("play_music:"):
                query = cmd_resp.split(":", 1)[1]
                return random.choice(self.responses["acknowledgement"]) + " " + self.play_music(query)
            elif cmd_resp.startswith("set_alarm:"):
                time_str = cmd_resp.split(":", 1)[1]
                return random.choice(self.responses["acknowledgement"]) + " " + self.set_alarm(time_str)
            elif cmd_resp == "pause_music":
                return self.pause_music()
            elif cmd_resp == "resume_music":
                return self.resume_music()
            elif cmd_resp == "stop_music":
                return self.stop_music()
            elif cmd_resp == "flip_coin":
                return self.flip_coin()
            elif cmd_resp == "roll_dice":
                return self.roll_dice()
            elif cmd_resp == "next_track":
                return self.next_track()
            elif cmd_resp == "previous_track":
                return self.previous_track()
            elif cmd_resp == "activate_hologram":
                return self.activate_hologram()
            elif cmd_resp == "deactivate_hologram":
                return self.deactivate_hologram()
            elif cmd_resp == "activate_security_mode":
                return self.activate_security_mode()
            elif cmd_resp == "deactivate_security_mode":
                return self.deactivate_security_mode()
            elif cmd_resp == "get_weather":
                return self.get_weather()
            elif cmd_resp == "get_news":
                return self.get_news()
            elif cmd_resp == "analyze_object":
                return self.analyze_object()
            elif cmd_resp == "activate_defense_systems":
                return self.activate_defense_systems()
            elif cmd_resp.startswith("send_email:"):
                parts = cmd_resp.split(":", 1)[1].split("|")
                if len(parts) == 3:
                    return self.send_email(parts[0], parts[1], parts[2])
            elif cmd_resp == "recognize_face":
                return self.face_recognition.recognize_face()
            elif cmd_resp.startswith("register_face:"):
                name = cmd_resp.split(":", 1)[1]
                return self.face_recognition.register_face(name)
            elif cmd_resp == "dim_screen":
                return self.set_display_brightness(30)
            elif cmd_resp == "brighten_screen":
                return self.set_display_brightness(80)
            elif cmd_resp == "reset_brightness":
                return self.reset_display_brightness()
            elif cmd_resp == "system_health":
                return self.system_health_check()
            elif cmd_resp == "tell_joke":
                return self.tell_joke()
            elif cmd_resp == "flip_switch":
                return self.flip_switch()
            elif cmd_resp.startswith("play_game:"):
                game_name = cmd_resp.split(":", 1)[1]
                return self.play_game(game_name)
            elif cmd_resp == "system_scan":
                return self.system_scan()
            elif cmd_resp == "activate_surveillance":
                return "Surveillance mode activated through GUI, sir."
            elif cmd_resp == "deactivate_surveillance":
                return "Surveillance mode deactivated through GUI, sir."
            elif cmd_resp.startswith("calculate:"):
                problem = cmd_resp.split(":", 1)[1]
                return self.solve_math_problem(problem)
            elif cmd_resp == "connect_drone":
                return self.drone_controller.connect()
            elif cmd_resp == "disconnect_drone":
                return self.drone_controller.disconnect()
            elif cmd_resp == "takeoff_drone":
                return self.drone_controller.takeoff()
            elif cmd_resp == "land_drone":
                return self.drone_controller.land()
            elif cmd_resp.startswith("move_drone:"):
                direction = cmd_resp.split(":", 1)[1]
                if direction == "forward":
                    return self.drone_controller.move_forward()
                elif direction == "backward":
                    return self.drone_controller.move_backward()
                elif direction == "left":
                    return self.drone_controller.turn_left()
                elif direction == "right":
                    return self.drone_controller.turn_right()
            else:
                return cmd_resp

        # 2) Fallback to GPT if API key is available
        if client:
            try:
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": text}]
                )
                content = resp.choices[0].message.content
                return content.strip() if content is not None else "No response received from OpenAI."
            except Exception as e:
                print(f"[OpenAI Error] {e}")
                return "Apologies, sir. I'm having trouble reaching the main systems."
        else:
            return "I'm currently operating in offline mode. For advanced queries, please provide an OpenAI API key."

    # Music control methods
    def play_music(self, query=""):
        return self.music_player.play_music(query)
        
    def pause_music(self):
        return self.music_player.pause_music()
        
    def resume_music(self):
        return self.music_player.resume_music()
        
    def stop_music(self):
        return self.music_player.stop_music()
        
    def next_track(self):
        return self.music_player.next_track()
        
    def previous_track(self):
        return self.music_player.previous_track()

    # Alarm system
    def set_alarm(self, time_str):
        """Set an alarm at specified time"""
        try:
            # Parse time (handle both HH:MM and HH:MM AM/PM)
            try:
                alarm_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                alarm_time = datetime.datetime.strptime(time_str, "%I:%M %p").time()
                
            now = datetime.datetime.now().time()
            
            if alarm_time < now:
                return "Please set a time in the future, sir."
                
            # Create alarm datetime
            alarm_datetime = datetime.datetime.combine(datetime.datetime.today(), alarm_time)
            if alarm_datetime < datetime.datetime.now():
                alarm_datetime += datetime.timedelta(days=1)
                
            # Add to active alarms
            alarm_id = str(alarm_datetime.timestamp())
            self.active_alarms.append(alarm_id)
            
            threading.Thread(target=self._run_alarm, args=(alarm_datetime, alarm_id)).start()
            return f"Alarm set for {alarm_datetime.strftime('%I:%M %p')}, sir."
        except ValueError:
            return "Please specify time in HH:MM format, sir."

    def _run_alarm(self, alarm_datetime, alarm_id):
        """Background thread for alarm"""
        while datetime.datetime.now() < alarm_datetime and alarm_id in self.active_alarms:
            time.sleep(30)
            
        if alarm_id in self.active_alarms:
            self.speak("Alarm! Time is up, sir.")
            # Play alarm sound
            try:
                for _ in range(5):
                    winsound.Beep(1000, 500)
                    time.sleep(1)
            except:
                pass
            
            # Remove alarm after triggering
            if alarm_id in self.active_alarms:
                self.active_alarms.remove(alarm_id)

    def cancel_alarm(self):
        """Cancel all active alarms"""
        if self.active_alarms:
            self.active_alarms = []
            return "All alarms canceled, sir."
        return "No active alarms to cancel, sir."

    # Fun utilities
    def flip_coin(self):
        """Flip a virtual coin"""
        result = random.choice(["Heads", "Tails"])
        return f"It's {result}, sir."

    def roll_dice(self):
        """Roll virtual dice"""
        return f"You rolled a {random.randint(1, 6)}, sir."

    # System commands
    def open_browser(self):
        """Open the default web browser"""
        try:
            webbrowser.open("https://www.google.com")
            return "Opening web browser, sir."
        except Exception as e:
            return f"Failed to open browser: {str(e)}"

    def get_system_info(self):
        """Get detailed system information"""
        uname = platform.uname()
        info = (
            f"System: {uname.system}\n"
            f"Node Name: {uname.node}\n"
            f"Release: {uname.release}\n"
            f"Version: {uname.version}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {uname.processor}"
        )
        return info
        
    # ===== CINEMATIC FEATURES =====
    def activate_hologram(self):
        """Activate holographic display"""
        if not self.hologram_active:
            self.hologram_active = True
            self.hologram_thread = threading.Thread(target=self._display_hologram)
            self.hologram_thread.daemon = True
            self.hologram_thread.start()
            return "Holographic display activated, sir."
        return "Hologram is already active, sir."

    def deactivate_hologram(self):
        """Deactivate holographic display"""
        if self.hologram_active:
            self.hologram_active = False
            return "Holographic display deactivated, sir."
        return "Hologram is not active, sir."

    def _display_hologram(self):
        """Simulate holographic display"""
        # Create blue holographic effect
        while self.hologram_active and self.gui:
            # Generate dynamic holographic pattern
            width, height = 800, 600
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create grid pattern
            for i in range(0, width, 50):
                cv2.line(image, (i, 0), (i, height), (0, 150, 255), 1)
            for i in range(0, height, 50):
                cv2.line(image, (0, i), (width, i), (0, 150, 255), 1)
                
            # Add floating elements
            cv2.putText(image, "J.A.R.V.I.S. HOLO INTERFACE", (50, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
            
            # Draw scanning effect
            scan_y = int(time.time() * 50) % height
            cv2.line(image, (0, scan_y), (width, scan_y), (0, 255, 255), 3)
            
            # Convert to PIL format
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(image)
            
            # Update GUI
            self.gui.update_hologram(pil_img)
                
            time.sleep(0.1)

    def activate_security_mode(self):
        """Activate advanced security monitoring"""
        if not self.security_mode:
            self.security_mode = True
            self.security_thread = threading.Thread(target=self._security_scan)
            self.security_thread.daemon = True
            self.security_thread.start()
            self.activate_hologram()
            return "Security mode activated. All systems monitoring for threats, sir."
        return "Security mode is already active, sir."

    def deactivate_security_mode(self):
        """Deactivate security monitoring"""
        if self.security_mode:
            self.security_mode = False
            self.deactivate_hologram()
            return "Security mode deactivated, sir."
        return "Security mode is not active, sir."

    def _security_scan(self):
        """Simulate security scanning"""
        while self.security_mode:
            # Simulate occasional security alerts
            if random.random() < 0.05:  # 5% chance of alert
                alert = random.choice(self.responses["security_alert"])
                self.cinematic_speak(alert)
                
                # Visual alert in GUI
                if self.gui:
                    self.gui.security_alert()
                    
                # Simulate threat neutralization
                time.sleep(2)
                self.cinematic_speak("Threat neutralized. Systems secure.", "confirmation")
                
            time.sleep(1)

    # Screen brightness control
    def get_display_brightness(self):
        """Get current display brightness"""
        try:
            if platform.system() == "Windows":
                import wmi
                c = wmi.WMI(namespace='wmi')
                brightness = c.WmiMonitorBrightness()[0].CurrentBrightness
                return brightness
            elif platform.system() == "Darwin":
                result = subprocess.run(["brightness", "-l"], capture_output=True, text=True)
                output = result.stdout
                brightness = float(output.split("brightness ")[1].split("\n")[0])
                return int(brightness * 100)
        except:
            return 80  # Default
        
    def set_display_brightness(self, level):
        """Set display brightness (0-100)"""
        try:
            if platform.system() == "Windows":
                import wmi
                c = wmi.WMI(namespace='wmi')
                method = c.WmiMonitorBrightnessMethods()[0]
                method.WmiSetBrightness(level, 0)
                return f"Screen brightness set to {level}%, sir."
            elif platform.system() == "Darwin":
                brightness = level / 100
                subprocess.run(["brightness", str(brightness)])
                return f"Screen brightness set to {level}%, sir."
            else:
                return "Brightness control not supported on this OS, sir."
        except Exception as e:
            return f"Failed to adjust brightness: {str(e)}"
            
    def reset_display_brightness(self):
        """Reset brightness to original level"""
        return self.set_display_brightness(self.original_brightness)

    # New features
    def system_health_check(self):
        """Check system health and report issues"""
        alerts = []
        
        if PSUTIL_AVAILABLE:
            # CPU check
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 90:
                alerts.append(f"High CPU usage: {cpu_usage}%")
            
            # Memory check
            mem = psutil.virtual_memory()
            if mem.percent > 90:
                alerts.append(f"High memory usage: {mem.percent}%")
            
            # Disk check
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                alerts.append(f"Low disk space: {disk.percent}% used")
        
        if alerts:
            return "System alerts: " + "; ".join(alerts) + ", sir."
        return "All systems operating within normal parameters, sir."
    
    def tell_joke(self):
        """Tell a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What did one ocean say to the other ocean? Nothing, they just waved!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a fake noodle? An impasta!",
            "Why couldn't the bicycle stand up by itself? It was two tired!"
        ]
        return random.choice(jokes)
    
    def flip_switch(self):
        """Simulate a switch flipping with sound effect"""
        try:
            winsound.Beep(800, 100)
            return "Switch flipped, sir."
        except:
            return "Task completed, sir."
    
    def play_game(self, game_name):
        """Play simple games"""
        game_name = game_name.lower()
        
        if "rock" in game_name or "paper" in game_name or "scissors" in game_name:
            choices = ["rock", "paper", "scissors"]
            user_choice = None
            
            # Detect user choice
            for choice in choices:
                if choice in game_name:
                    user_choice = choice
                    break
            
            if not user_choice:
                return "Please choose rock, paper, or scissors, sir."
            
            ai_choice = random.choice(choices)
            
            # Determine winner
            if user_choice == ai_choice:
                result = "It's a tie!"
            elif (user_choice == "rock" and ai_choice == "scissors") or \
                 (user_choice == "paper" and ai_choice == "rock") or \
                 (user_choice == "scissors" and ai_choice == "paper"):
                result = "You win!"
            else:
                result = "I win!"
            
            return f"You chose {user_choice}, I chose {ai_choice}. {result}"
        
        return "I don't know that game, sir. Try 'rock paper scissors'."
    
    def system_scan(self):
        """Simulate a full system scan"""
        scan_steps = [
            "Initiating full system scan",
            "Checking processor integrity",
            "Verifying memory modules",
            "Analyzing storage systems",
            "Testing network interfaces",
            "Scanning security protocols"
        ]
        
        result = random.choice([
            "Scan complete. All systems optimal.",
            "Scan complete. Minor issues detected. No action required.",
            "Scan complete. Security protocols reinforced."
        ])
        
        return " ".join(scan_steps) + ". " + result

    def get_weather(self):
        """Get current weather information"""
        try:
            # Simulate weather report
            weather_conditions = [
                "sunny", "cloudy", "rainy", "stormy", "snowy"
            ]
            temperatures = [
                "mild 22°C", "warm 28°C", "cool 18°C", "cold 5°C", "freezing -2°C"
            ]
            
            return (f"Current weather: "
                    f"{random.choice(weather_conditions)} with "
                    f"temperatures around {random.choice(temperatures)}, sir.")
        except:
            return "Weather service unavailable, sir."

    def get_news(self):
        """Get top news headlines"""
        try:
            # Simulate news retrieval
            headlines = [
                "Stark Industries announces breakthrough in clean energy technology",
                "Avengers assemble for humanitarian mission",
                "SI stock reaches all-time high",
                "Government approves new arc reactor regulations",
                "Pepper Potts named Businessperson of the Year"
            ]
            return "Top headlines today: " + "; ".join(random.sample(headlines, 3)) + ", sir."
        except:
            return "News service unavailable, sir."

    def analyze_object(self):
        """Simulate object analysis like in the movies"""
        analysis = [
            "Composition: Titanium alloy with carbon fiber reinforcement",
            "Structural integrity: 98.7%",
            "Energy signature: Low-level gamma radiation detected",
            "Recommendation: Handle with care",
            "Threat level: Minimal"
        ]
        return "Analysis complete, sir: " + "; ".join(analysis)

    def activate_defense_systems(self):
        """Simulate defense system activation"""
        sequence = [
            "Energy shields: ONLINE",
            "Repulsor arrays: CHARGED",
            "Targeting systems: CALIBRATED",
            "Defense protocols: ENGAGED"
        ]
        return "Defense systems activated, sir: " + " | ".join(sequence)

    def send_email(self, to_address, subject, body):
        """Send an email (dummy implementation)"""
        # You can implement actual email sending here using smtplib if needed.
        # For now, just simulate success.
        return f"Email sent to {to_address} with subject '{subject}', sir."