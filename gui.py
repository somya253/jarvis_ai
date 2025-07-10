import tkinter as tk
import customtkinter as ctk
import threading
import speech_recognition as sr
from assistant import Assistant
import random
import math
import platform
from PIL import Image, ImageTk
import time
import cv2

# JARVIS Color Scheme
JARVIS_COLORS = {
    "dark_bg": "#0a0e17",
    "medium_bg": "#0f1729",
    "light_bg": "#1a243d",
    "accent": "#00eeff",
    "accent_dark": "#008899",
    "text": "#e6f7ff"
}

try:
    import psutil # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available. Some system monitoring features will be disabled.")

class RadarCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg=JARVIS_COLORS["dark_bg"], highlightthickness=0)
        self.width = self.winfo_reqwidth()
        self.height = self.winfo_reqheight()
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.radius = min(self.width, self.height) // 2 - 20
        self.angle = 0
        self.scan_line = None
        self.dots = []
        self.after_id = None
        self.active = False
        self.targets = []
        
        # Draw radar background
        self.draw_radar_background()
        
    def draw_radar_background(self):
        # Clear previous drawings
        self.delete("all")
        
        # Draw concentric circles
        for i in range(1, 6):
            r = self.radius * i // 5
            self.create_oval(
                self.center_x - r, self.center_y - r,
                self.center_x + r, self.center_y + r,
                outline=JARVIS_COLORS["accent_dark"],
                width=1,
                dash=(4, 4)
            )
            
        # Draw crosshairs
        self.create_line(
            self.center_x, self.center_y - self.radius,
            self.center_x, self.center_y + self.radius,
            fill=JARVIS_COLORS["accent_dark"],
            width=1
        )
        self.create_line(
            self.center_x - self.radius, self.center_y,
            self.center_x + self.radius, self.center_y,
            fill=JARVIS_COLORS["accent_dark"],
            width=1
        )
        
        # Draw angle markers
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = self.center_x + (self.radius - 10) * math.cos(rad)
            y1 = self.center_y + (self.radius - 10) * math.sin(rad)
            x2 = self.center_x + self.radius * math.cos(rad)
            y2 = self.center_y + self.radius * math.sin(rad)
            self.create_line(x1, y1, x2, y2, fill=JARVIS_COLORS["accent_dark"], width=1)
        
        # Draw radar label
        self.create_text(
            self.center_x, self.center_y + self.radius + 15,
            text="ACTIVE SCAN", 
            fill=JARVIS_COLORS["accent"],
            font=("Segoe UI", 10, "bold")
        )
    
    def start_scan(self):
        self.active = True
        self.scan()
        
    def stop_scan(self):
        self.active = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def add_target(self, angle, distance, label):
        """Add a target to the radar display"""
        self.targets.append({
            "angle": angle,
            "distance": distance,
            "label": label,
            "id": None
        })
    
    def clear_targets(self):
        """Remove all targets from the radar"""
        for target in self.targets:
            if target["id"]:
                self.delete(target["id"])
        self.targets = []
    
    def scan(self):
        if not self.active:
            return
            
        # Clear previous scan line
        if self.scan_line:
            self.delete(self.scan_line)
            
        # Calculate end point of scan line
        rad = math.radians(self.angle)
        end_x = self.center_x + self.radius * math.cos(rad)
        end_y = self.center_y + self.radius * math.sin(rad)
        
        # Draw new scan line
        self.scan_line = self.create_line(
            self.center_x, self.center_y,
            end_x, end_y,
            fill=JARVIS_COLORS["accent"],
            width=2
        )
        
        # Update targets
        for target in self.targets:
            if target["id"]:
                self.delete(target["id"])
                
            t_rad = math.radians(target["angle"])
            dist = target["distance"] * self.radius
            t_x = self.center_x + dist * math.cos(t_rad)
            t_y = self.center_y + dist * math.sin(t_rad)
            
            # Draw target
            target["id"] = self.create_oval(
                t_x - 5, t_y - 5,
                t_x + 5, t_y + 5,
                fill="#ff5555",
                outline=""
            )
            
            # Draw target label
            self.create_text(
                t_x, t_y - 15,
                text=target["label"],
                fill=JARVIS_COLORS["accent"],
                font=("Segoe UI", 8)
            )
        
        # Update angle
        self.angle = (self.angle + 3) % 360
        
        # Schedule next scan
        self.after_id = self.after(30, self.scan)

class SystemMonitor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=JARVIS_COLORS["medium_bg"], corner_radius=10)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="SYSTEM STATUS",
            font=("Segoe UI", 12, "bold"),
            text_color=JARVIS_COLORS["accent"]
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # System info
        self.os_label = ctk.CTkLabel(
            self, 
            text=f"OS: {platform.system()} {platform.release()}",
            font=("Segoe UI", 10),
            text_color=JARVIS_COLORS["text"]
        )
        self.os_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        self.cpu_label = ctk.CTkLabel(
            self, 
            text="CPU: Checking...",
            font=("Segoe UI", 10),
            text_color=JARVIS_COLORS["text"]
        )
        self.cpu_label.grid(row=2, column=0, padx=10, pady=2, sticky="w")
        
        self.ram_label = ctk.CTkLabel(
            self, 
            text="RAM: Checking...",
            font=("Segoe UI", 10),
            text_color=JARVIS_COLORS["text"]
        )
        self.ram_label.grid(row=3, column=0, padx=10, pady=2, sticky="w")
        
        self.disk_label = ctk.CTkLabel(
            self, 
            text="Disk: Checking...",
            font=("Segoe UI", 10),
            text_color=JARVIS_COLORS["text"]
        )
        self.disk_label.grid(row=4, column=0, padx=10, pady=2, sticky="w")
        
        self.net_label = ctk.CTkLabel(
            self, 
            text="Network: Checking...",
            font=("Segoe UI", 10),
            text_color=JARVIS_COLORS["text"]
        )
        self.net_label.grid(row=5, column=0, padx=10, pady=2, sticky="w")
        
        # Start monitoring if psutil is available
        if PSUTIL_AVAILABLE:
            self.update_monitor()
        else:
            self.title_label.configure(text="SYSTEM STATUS (psutil not installed)")
            self.cpu_label.configure(text="CPU: Install psutil for monitoring")
            self.ram_label.configure(text="RAM: Install psutil for monitoring")
            self.disk_label.configure(text="Disk: Install psutil for monitoring")
            self.net_label.configure(text="Network: Install psutil for monitoring")
    
    def update_monitor(self):
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.cpu_label.configure(text=f"CPU: {cpu_percent}%")
            
            # RAM usage
            ram = psutil.virtual_memory()
            ram_total = round(ram.total / (1024 ** 3), 1)
            ram_used = round(ram.used / (1024 ** 3), 1)
            ram_percent = ram.percent
            self.ram_label.configure(text=f"RAM: {ram_percent}% ({ram_used}/{ram_total} GB)")
            
            # Disk usage (primary disk)
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.disk_label.configure(text=f"Disk: {disk_percent}%")
            
            # Network usage
            net = psutil.net_io_counters()
            down = round(net.bytes_recv / 1024, 1)
            up = round(net.bytes_sent / 1024, 1)
            self.net_label.configure(text=f"Network: Down {down} KB/s | Up {up} KB/s")
        except Exception as e:
            print(f"System monitoring error: {e}")
            
        # Update every 2 seconds
        self.after(2000, self.update_monitor)

class SurveillanceViewer(ctk.CTkFrame):
    def __init__(self, master, assistant, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=JARVIS_COLORS["dark_bg"])
        self.assistant = assistant
        self.active = False
        self.camera_label = ctk.CTkLabel(self, text="")
        self.camera_label.pack(padx=10, pady=10)
        
    def start_surveillance(self):
        self.active = True
        self.update_camera()
        
    def stop_surveillance(self):
        self.active = False
        
    def update_camera(self):
        if not self.active:
            return
            
        # Capture camera frame
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Convert to PIL format
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame)
            
            # Resize for display
            width, height = 320, 240
            pil_img = pil_img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to Tkinter format
            tk_img = ImageTk.PhotoImage(image=pil_img)
            
            # Update label
            self.camera_label.configure(image=tk_img)
            self._camera_img = tk_img  # Keep a reference to avoid garbage collection
            
        # Schedule next update
        self.after(1000, self.update_camera)

class ChatGUI(ctk.CTk):
    def __init__(self, settings):
        super().__init__()
        self.title("J.A.R.V.I.S.")
        self.geometry("1100x750")
        self.settings = settings
        
        # Set window transparency
        self.attributes("-alpha", 0.95)  # 95% opacity
        
        # Customize appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=JARVIS_COLORS["dark_bg"])
        
        # Initialize assistant
        self.assistant = Assistant(gui=self)
        self.recognizer = sr.Recognizer()

        # Futuristic font
        self.font = ctk.CTkFont(family="Segoe UI", 
                               size=self.settings.get("font_size", 16),
                               weight="bold")
        
        # Voice visualization
        self.voice_visualization = []
        self.listening = False
        
        # Security alert state
        self.security_alert_active = False
        
        # Surveillance system
        self.surveillance_mode = False
        self.surveillance_viewer = None
        
        # Build UI
        self._build_title_bar()
        self._build_main_frame()
        
        # Start radar scan
        self.radar.start_scan()
        
        # Add targets to radar
        self._add_radar_targets()
        
        # Make window draggable
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.on_move)
        
    def _add_radar_targets(self):
        # Add some targets to the radar
        self.radar.add_target(30, 0.7, "AI Core")
        self.radar.add_target(120, 0.4, "Security")
        self.radar.add_target(200, 0.6, "Database")
        self.radar.add_target(300, 0.3, "Network")
        
    def _build_title_bar(self):
        # Add title bar
        self.title_bar = tk.Frame(self, bg=JARVIS_COLORS["medium_bg"])
        self.title_bar.pack(fill="x", pady=0, padx=0)
        
        # Title text
        tk.Label(self.title_bar, text="J.A.R.V.I.S. - VOICE ASSISTANT", 
                bg=JARVIS_COLORS["medium_bg"], fg=JARVIS_COLORS["accent"],
                font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        
        # Close button
        close_btn = tk.Button(self.title_bar, text="✕", 
                            command=self.destroy, bd=0, 
                            bg=JARVIS_COLORS["medium_bg"], 
                            fg=JARVIS_COLORS["text"], 
                            activebackground="#ff5555",
                            font=("Arial", 12))
        close_btn.pack(side="right", padx=5)
        
        # Minimize button
        min_btn = tk.Button(self.title_bar, text="—", 
                          command=self.iconify, bd=0,
                          bg=JARVIS_COLORS["medium_bg"], 
                          fg=JARVIS_COLORS["text"], 
                          activebackground=JARVIS_COLORS["light_bg"],
                          font=("Arial", 12))
        min_btn.pack(side="right", padx=5)
        
    def _build_main_frame(self):
        # Main container frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - System info
        left_frame = ctk.CTkFrame(main_frame, width=350, 
                                 fg_color="transparent")
        left_frame.pack(side="left", fill="both", padx=(0, 10), pady=5)
        left_frame.pack_propagate(False)
        
        # Radar display
        radar_frame = ctk.CTkFrame(left_frame, fg_color=JARVIS_COLORS["medium_bg"],
                                 corner_radius=10)
        radar_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Radar title
        ctk.CTkLabel(radar_frame, text="ACTIVE SCAN", 
                    font=("Segoe UI", 14, "bold"),
                    text_color=JARVIS_COLORS["accent"]).pack(pady=10)
        
        # Radar canvas
        self.radar = RadarCanvas(radar_frame, width=320, height=320)
        self.radar.pack(pady=10)
        
        # System monitor
        self.sys_monitor = SystemMonitor(left_frame)
        self.sys_monitor.pack(fill="both", expand=True)
        
        # Add surveillance panel
        self.surveillance_viewer = SurveillanceViewer(left_frame, self.assistant)
        self.surveillance_viewer.pack(fill="both", expand=True, pady=10)
        
        # Right panel - Chat interface
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, pady=5)
        
        # Hologram display frame
        self.hologram_frame = ctk.CTkFrame(right_frame, 
                                         fg_color=JARVIS_COLORS["dark_bg"],
                                         corner_radius=10)
        self.hologram_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Hologram label
        self.hologram_label = tk.Label(self.hologram_frame, 
                                     bg=JARVIS_COLORS["dark_bg"])
        self.hologram_label.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Build chat components below hologram
        self._build_chat_frame(right_frame)
        self._build_input_frame(right_frame)
        self._build_settings_bar(right_frame)
    
    def update_hologram(self, image):
        """Update holographic display with new image"""
        # Resize image
        width, height = 400, 300
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to Tkinter format
        tk_img = ImageTk.PhotoImage(image=image)
        
        # Update label
        self.hologram_label.configure(image=tk_img)
        self._hologram_img = tk_img  # Keep a reference to avoid garbage collection

    def security_alert(self):
        """Visual security alert effect"""
        self.security_alert_active = True
        self._flash_security_alert()

    def _flash_security_alert(self):
        """Create flashing security alert effect"""
        if not self.security_alert_active:
            return
            
        current_bg = self.hologram_label.cget("bg")
        new_bg = "#ff5555" if current_bg == JARVIS_COLORS["dark_bg"] else JARVIS_COLORS["dark_bg"]
        self.hologram_label.configure(bg=new_bg)
        self.after(200, self._flash_security_alert)

    def stop_security_alert(self):
        """Stop security alert flashing"""
        self.security_alert_active = False
        self.hologram_label.configure(bg=JARVIS_COLORS["dark_bg"])
    
    def _build_settings_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(5, 0))
        
        # Quick commands
        commands_frame = ctk.CTkFrame(bar, fg_color="transparent")
        commands_frame.pack(side="left", padx=5)
        
        commands = [
            ("System Info", self.show_system_info),
            ("Open Browser", lambda: self.assistant.open_browser()),
            ("Clean RAM", self.clean_ram),
            ("Shutdown", self.shutdown_system)
        ]
        
        for text, cmd in commands:
            btn = ctk.CTkButton(
                commands_frame, 
                text=text,
                width=100,
                height=30,
                fg_color=JARVIS_COLORS["accent_dark"],
                hover_color=JARVIS_COLORS["accent"],
                corner_radius=5,
                font=("Segoe UI", 10),
                command=cmd
            )
            btn.pack(side="left", padx=5)
        
        # Music controls
        music_frame = ctk.CTkFrame(bar, fg_color="transparent")
        music_frame.pack(side="left", padx=10)
        
        music_commands = [
            ("⏮", self.previous_track),
            ("▶", self.play_music),
            ("⏸", self.pause_music),
            ("⏹", self.stop_music),
            ("⏭", self.next_track)
        ]
        
        for text, cmd in music_commands:
            btn = ctk.CTkButton(
                music_frame, 
                text=text,
                width=30,
                height=30,
                fg_color=JARVIS_COLORS["accent_dark"],
                hover_color=JARVIS_COLORS["accent"],
                corner_radius=15,
                font=("Segoe UI", 14),
                command=cmd
            )
            btn.pack(side="left", padx=2)
            
        # Security controls
        security_frame = ctk.CTkFrame(bar, fg_color="transparent")
        security_frame.pack(side="left", padx=10)
        
        security_commands = [
            ("🔒", self.activate_security),
            ("🔓", self.deactivate_security),
            ("👁️", self.toggle_surveillance)
        ]
        
        for text, cmd in security_commands:
            btn = ctk.CTkButton(
                security_frame, 
                text=text,
                width=30,
                height=30,
                fg_color=JARVIS_COLORS["accent_dark"],
                hover_color=JARVIS_COLORS["accent"],
                corner_radius=15,
                font=("Segoe UI", 14),
                command=cmd
            )
            btn.pack(side="left", padx=2)
        
        # Mic toggle button with JARVIS style
        self.mic_btn = ctk.CTkButton(
            bar, text="", width=40, height=40,
            fg_color=JARVIS_COLORS["accent_dark"] if not self.assistant.mic_enabled else JARVIS_COLORS["accent"],
            hover_color=JARVIS_COLORS["accent"],
            command=self.toggle_mic
        )
        self.mic_btn.pack(side="right", padx=10)
        
        # Add mic icon
        self.mic_label = tk.Label(self.mic_btn, text="●", 
                                bg=self.mic_btn.cget("fg_color"),
                                fg=JARVIS_COLORS["text"],
                                font=("Arial", 16))
        self.mic_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Add sound wave visualization
        self.visualization_frame = ctk.CTkFrame(bar, fg_color="transparent")
        self.visualization_frame.pack(side="right", padx=10)
        
        # Create bars for visualization
        for i in range(8):
            bar = ctk.CTkFrame(self.visualization_frame, width=3, height=10,
                             fg_color=JARVIS_COLORS["accent_dark"])
            bar.grid(row=0, column=i, padx=1)
            self.voice_visualization.append(bar)
        
    def _build_chat_frame(self, parent):
        # Create glass effect chat area
        self.chat_frame = ctk.CTkFrame(
            parent, 
            fg_color=JARVIS_COLORS["light_bg"],
            bg_color=JARVIS_COLORS["dark_bg"],
            corner_radius=15
        )
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add chat textbox
        self.chatbox = ctk.CTkTextbox(
            self.chat_frame, 
            wrap="word", 
            font=self.font,
            fg_color="transparent",
            text_color=JARVIS_COLORS["text"],
            border_width=0
        )
        self.chatbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.chatbox.insert("0.0", "J.A.R.V.I.S.: Systems online. How can I assist you today?\n")
        self.chatbox.configure(state="disabled")
        
        # Configure text tags
        self.chatbox.tag_config("jarvis", foreground=JARVIS_COLORS["accent"])
        self.chatbox.tag_config("user", foreground="#ffffff")
        self.chatbox.tag_config("system", foreground="#ffaa00")
        
    def _build_input_frame(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        # Create JARVIS-style input with glow effect
        self.entry = ctk.CTkEntry(
            frame, 
            placeholder_text="Speak or type your command...",
            font=self.font,
            fg_color=JARVIS_COLORS["medium_bg"],
            border_color=JARVIS_COLORS["accent_dark"],
            text_color=JARVIS_COLORS["text"],
            corner_radius=10,
            placeholder_text_color=JARVIS_COLORS["accent_dark"]
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.entry.bind("<Return>", lambda e: self.on_send())
        
        # Voice button with animation
        self.voice_btn = ctk.CTkButton(
            frame, 
            text="", 
            width=50,
            height=50,
            fg_color=JARVIS_COLORS["accent_dark"],
            hover_color=JARVIS_COLORS["accent"],
            corner_radius=25,
            command=self.on_voice
        )
        self.voice_btn.pack(side="left", padx=(0,5))
        
        # Add mic icon to voice button
        self.voice_icon = tk.Label(
            self.voice_btn, 
            text="●",  # Using circle as recording indicator
            font=("Arial", 24),
            fg=JARVIS_COLORS["accent"],
            bg=self.voice_btn.cget("fg_color")
        )
        self.voice_icon.place(relx=0.5, rely=0.5, anchor="center")
        
        # Send button
        self.send_btn = ctk.CTkButton(
            frame, 
            text="SEND", 
            width=80,
            height=50,
            fg_color=JARVIS_COLORS["accent_dark"],
            hover_color=JARVIS_COLORS["accent"],
            corner_radius=10,
            font=self.font,
            command=self.on_send
        )
        self.send_btn.pack(side="left")
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def stop_move(self, event):
        self.x = None
        self.y = None
        
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
    
    def toggle_mic(self):
        new_state = self.assistant.toggle_mic()
        # Update button color
        fg_color = JARVIS_COLORS["accent_dark"] if not new_state else JARVIS_COLORS["accent"]
        self.mic_btn.configure(fg_color=fg_color)
        self.mic_label.configure(bg=fg_color)
        
    def on_send(self, text=None):
        msg = text if text is not None else self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0,"end")
        self._append(f"You: {msg}\n", "user")
        threading.Thread(target=self._get_response, args=(msg,)).start()
    
    def on_voice(self):
        if not self.assistant.mic_enabled:
            self._append("Microphone is disabled. Enable it first.\n", "system")
            return
            
        # Start visualization animation
        self.listening = True
        self._animate_voice()
        threading.Thread(target=self._voice_thread).start()
    
    def _animate_voice(self):
        if not self.listening:
            return
            
        # Animate voice bars
        for bar in self.voice_visualization:
            height = random.randint(2, 20)
            bar.configure(height=height)
        
        # Continue animation
        self.after(100, self._animate_voice)
    
    def _voice_thread(self):
        # Change button to indicate recording
        self.voice_icon.configure(text="●", fg="#ff0000")
        
        # Get voice input
        text = self.assistant.listen()
        
        # Reset button
        self.voice_icon.configure(text="●", fg=JARVIS_COLORS["accent"])
        self.listening = False
        
        if text:
            self.on_send(text)
        else:
            self._append("Could not understand audio.\n", "system")
    
    def _get_response(self, message):
        resp = self.assistant.process_input(message)
        self._append(f"J.A.R.V.I.S.: {resp}\n\n", "jarvis")
        # Speak the response
        threading.Thread(target=self.assistant.speak, args=(resp,)).start()
    
    def _append(self, text, tag=None):
        self.chatbox.configure(state="normal")
        if tag:
            self.chatbox.insert("end", text, tag)
        else:
            self.chatbox.insert("end", text)
        self.chatbox.configure(state="disabled")
        self.chatbox.see("end")
    
    # Music control methods
    def play_music(self):
        threading.Thread(target=self._execute_command, args=("play_music:",)).start()
        
    def pause_music(self):
        threading.Thread(target=self._execute_command, args=("pause_music",)).start()
        
    def stop_music(self):
        threading.Thread(target=self._execute_command, args=("stop_music",)).start()
        
    def next_track(self):
        threading.Thread(target=self._execute_command, args=("next_track",)).start()
        
    def previous_track(self):
        threading.Thread(target=self._execute_command, args=("previous_track",)).start()
        
    # Security control methods
    def activate_security(self):
        threading.Thread(target=self._execute_command, args=("activate_security_mode",)).start()
        
    def deactivate_security(self):
        threading.Thread(target=self._execute_command, args=("deactivate_security_mode",)).start()
        
    def toggle_surveillance(self):
        if not self.surveillance_mode:
            self.surveillance_mode = True
            self.surveillance_viewer.start_surveillance() # type: ignore
            self._append("Surveillance mode activated, sir.\n", "system")
        else:
            self.surveillance_mode = False
            self.surveillance_viewer.stop_surveillance() # type: ignore
            self._append("Surveillance mode deactivated, sir.\n", "system")
        
    def _execute_command(self, command):
        resp = self.assistant.process_input(command)
        self._append(f"J.A.R.V.I.S.: {resp}\n\n", "jarvis")
        self.assistant.speak(resp)
    
    # System commands
    def show_system_info(self):
        uname = platform.uname()
        info = (
            f"System: {uname.system}\n"
            f"Node Name: {uname.node}\n"
            f"Release: {uname.release}\n"
            f"Version: {uname.version}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {uname.processor}"
        )
        self._append(f"J.A.R.V.I.S.: System Information:\n{info}\n\n", "jarvis")
    
    def clean_ram(self):
        # This is just a simulation - real RAM cleaning requires OS-specific methods
        self._append("J.A.R.V.I.S.: Optimizing system memory...\n", "jarvis")
        self.after(2000, lambda: self._append("J.A.R.V.I.S.: Memory optimization complete. Performance improved.\n\n", "jarvis"))
    
    def shutdown_system(self):
        self._append("J.A.R.V.I.S.: Shutting down system in 5 seconds...\n", "jarvis")
        self.after(5000, self.destroy)