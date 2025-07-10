# main.py
import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import utils
from gui import ChatGUI
import winsound

def main():
    # Load environment from .env
    utils.load_env()
  
    # Load saved settings (appearance mode, theme, font size)
    settings = utils.load_settings()
    
    # Force JARVIS theme settings
    settings["appearance_mode"] = "dark"
    settings["color_theme"] = "blue"
    
    ctk.set_appearance_mode(settings["appearance_mode"])
    ctk.set_default_color_theme(settings["color_theme"])
    
    # Start the GUI application
    app = ChatGUI(settings)
    
    # Play startup sound
    try:
        # System startup beep sequence
        winsound.Beep(800, 200)
        winsound.Beep(1000, 200)
        winsound.Beep(1200, 300)
    except:
        pass
    
    app.mainloop()

if __name__ == "__main__":
    main()