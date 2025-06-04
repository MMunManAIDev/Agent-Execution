"""
AgentExecutive Main Entry Point

Dit script initialiseert en start de AgentExecutive applicatie.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime

from .config import Config
from .ui.app import AgentExecutiveApp
from .utils.logging import setup_logging

def check_dependencies():
    """
    Controleer of alle benodigde dependencies aanwezig zijn.
    Returns: (bool, str) - (success, error_message)
    """
    try:
        import openai
        import selenium
        from PIL import Image
        from webdriver_manager.chrome import ChromeDriverManager
        return True, None
    except ImportError as e:
        return False, f"Missing dependency: {str(e)}"

def check_environment():
    """
    Controleer of alle benodigde environment variabelen zijn ingesteld.
    Returns: (bool, str) - (success, error_message)
    """
    if not Config.OPENAI_API_KEY:
        return False, "OPENAI_API_KEY environment variable is not set"
    return True, None

def create_directories():
    """
    Maak benodigde directories aan als ze nog niet bestaan.
    """
    os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(Config.LOG_DIR, exist_ok=True)

def initialize_logging():
    """
    Initialiseer logging met timestamp in filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(Config.LOG_DIR, f"agent_executive_{timestamp}.log")
    setup_logging(log_file)

def main():
    """
    Hoofdfunctie die de applicatie start.
    """
    try:
        # Check dependencies
        deps_ok, deps_error = check_dependencies()
        if not deps_ok:
            messagebox.showerror("Dependency Error", deps_error)
            return 1

        # Check environment
        env_ok, env_error = check_environment()
        if not env_ok:
            messagebox.showerror("Environment Error", env_error)
            return 1

        # Setup directories en logging
        create_directories()
        initialize_logging()

        # Log startup
        logging.info("Starting AgentExecutive application")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Operating system: {sys.platform}")

        # Initialiseer Tkinter
        root = tk.Tk()
        root.title(f"AgentExecutive v{Config.VERSION}")
        root.geometry(Config.WINDOW_SIZE)

        # Start de applicatie
        app = AgentExecutiveApp(root)
        logging.info("Application initialized successfully")

        # Start main loop
        root.mainloop()
        
        logging.info("Application closed normally")
        return 0

    except Exception as e:
        logging.exception("Unexpected error during startup")
        messagebox.showerror(
            "Startup Error",
            f"An unexpected error occurred:\n{str(e)}\n\nCheck the logs for details."
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())