"""
AgentExecutive Custom Widgets Module
"""

import asyncio
import json
import os
import threading
import logging
import tkinter as tk

from tkinter import ttk, scrolledtext
from typing import Callable, Optional
from datetime import datetime
from PIL import Image, ImageTk
from typing import Callable, Optional, Dict, Any  # Add Dict, Any
from concurrent.futures import ThreadPoolExecutor
from src.handlers.web_handler import WebPageHandler

from .constants import (
    UI_COLORS,
    WIDGET_STYLES,
    UI_CONFIG
)

class UrlBar(ttk.Frame):
    """URL invoer balk met navigatie controls"""
    
    def __init__(self, parent, web_handler: WebPageHandler):
        super().__init__(parent)
        self.web_handler = web_handler
        self.logger = logging.getLogger(__name__)

        # UI Elements
        self.back_btn = ttk.Button(self, text="←", width=3, command=self.on_back, style="AgentExecutive.TButton")
        self.back_btn.pack(side="left", padx=(5, 0))

        self.forward_btn = ttk.Button(self, text="→", width=3, command=self.on_forward, style="AgentExecutive.TButton")
        self.forward_btn.pack(side="left", padx=(2, 5))

        self.refresh_btn = ttk.Button(self, text="⟳", width=3, command=self.on_refresh, style="AgentExecutive.TButton")
        self.refresh_btn.pack(side="left", padx=(0, 5))

        self.entry = ttk.Entry(self)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        self.go_btn = ttk.Button(self, text="Go", command=self.load_page_async, style="AgentExecutive.TButton")
        self.go_btn.pack(side="left", padx=5)

    def get_url(self) -> str:
        """Retrieve the URL from the entry field."""
        try:
            if self.entry.winfo_exists():
                return self.entry.get().strip()
            else:
                self.logger.warning("Attempted to get URL, but the entry widget no longer exists")
                return ""
        except tk.TclError:
            self.logger.warning("Failed to get URL, as the entry widget no longer exists")
            return ""

    def set_url(self, url: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, url)

    def load_page_async(self):
        """Handles loading the page asynchronously."""
        url = self.get_url()

        # Disable the Go button and show loading text
        self.logger.info(f"Attempting to load URL: {url}")
        self.go_btn.config(text="Loading...", state="disabled")
        self.logger.info("Go button disabled and loading started")

        # Run async load_page using asyncio.create_task()
        asyncio.create_task(self.load_page(url))

    async def load_page(self, url: str):
        """Load the specified page using the web handler asynchronously."""
        try:
            if not url:
                self.logger.warning("No URL to load.")
                return

            self.logger.info(f"Attempting to load page: {url}")

            if not hasattr(self.web_handler, 'load_page'):
                self.logger.error("Web handler does not have 'load_page' method. Check initialization.")
                return

            # Properly await the load_page method
            success = await self.web_handler.load_page(url)
            if success:
                self.logger.info(f"Page loaded successfully: {url}")
            else:
                self.logger.warning(f"Page failed to load: {url}")

        except Exception as e:
            self.logger.error(f"Failed to load page: {str(e)}")
        finally:
            # Ensure button is reset only if it still exists
            if self.go_btn.winfo_exists() and self.go_btn.winfo_ismapped():
                self.reset_go_button()
            else:
                self.logger.warning("Go button does not exist, skipping reset.")

        except Exception as e:
            self.logger.error(f"Failed to load page: {str(e)}")
        finally:
            # Ensure button is reset only if it still exists
            try:
                if self.go_btn.winfo_exists() and self.go_btn.winfo_ismapped():
                    self.reset_go_button()
                else:
                    self.logger.warning("Go button does not exist, skipping reset.")
            except tk.TclError:
                self.logger.warning("Failed to reset Go button; widget might have been destroyed.")


    def reset_go_button(self):
        """Reset the 'Go' button to its original state."""
        try:
            if self.go_btn.winfo_exists() and self.go_btn.winfo_ismapped():
                self.logger.info("Resetting Go button")
                self.go_btn.config(text="Go", state="normal")
            else:
                self.logger.warning("Attempted to reset Go button, but it no longer exists or is not mapped.")
        except tk.TclError:
            self.logger.warning("Failed to reset Go button due to TclError; widget might have been destroyed.")

    def on_back(self):
        pass

    def on_forward(self):
        pass

    def on_refresh(self):
        if self.get_url():
            self.load_page_async()    

class SnapshotViewer(ttk.LabelFrame):
    """Widget voor het tonen van pagina snapshots"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Page Snapshot")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup de snapshot viewer UI"""
        # Image label
        self.image_label = ttk.Label(self)
        self.image_label.pack(padx=5, pady=5)
        
        # Placeholder text
        self.set_placeholder()
        
    def set_placeholder(self):
        """Toon placeholder tekst"""
        self.image_label.config(
            text="No snapshot available",
            image=""
        )
        
    def update_image(self, image_path: str):
        """Update het snapshot beeld"""
        try:
            if not os.path.exists(image_path):
                self.set_placeholder()
                return
                
            # Load en resize image
            image = Image.open(image_path)
            image = image.resize(UI_CONFIG['SNAPSHOT_SIZE'], Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
        except Exception as e:
            self.set_placeholder()
            raise ValueError(f"Failed to load image: {str(e)}")

class ActionPanel(ttk.LabelFrame):
    """Panel voor het tonen en uitvoeren van acties"""
    
    def __init__(self, parent, on_execute: Callable):
        super().__init__(parent, text="Action Control")
        self.on_execute = on_execute
        self.current_action = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup het action panel"""
        # Action description
        desc_frame = ttk.Frame(self)
        desc_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(desc_frame, text="Action:").pack(side="left")
        
        self.action_label = ttk.Label(desc_frame, text="No action pending")
        self.action_label.pack(side="left", padx=5)
        
        # Action details
        self.details_text = scrolledtext.ScrolledText(
            self, height=5, wrap=tk.WORD
        )
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Execute button
        self.execute_btn = ttk.Button(
            self, text="Execute Action",
            command=self.execute_action,
            state="disabled"
        )
        self.execute_btn.pack(pady=5)
        
    def set_action(self, action: Dict[str, Any]):
        if action.get('type') == 'ERROR':
            self.action_label.config(
                text="Error",
                foreground=UI_COLORS['error']
            )
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', action.get('message', 'Unknown error'))
            self.execute_btn.config(state="disabled")
        else:
            # Update action label
            self.action_label.config(
                text=action.get('type', 'Unknown'),
                foreground=UI_COLORS['info']
            )
            
            # Update details
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', json.dumps(action, indent=2))
            
            # Enable execute button
            self.execute_btn.config(state="normal")
            
    def get_action(self) -> Optional[Dict[str, Any]]:
        """
        Krijg de huidige actie.
        
        Returns:
            De huidige actie of None
        """
        return self.current_action
        
    def execute_action(self):
        """Voer de huidige actie uit"""
        if self.current_action and self.on_execute:
            self.execute_btn.config(state="disabled")
            self.on_execute()

class LogViewer(scrolledtext.ScrolledText):
    """Widget voor het tonen van logs"""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            wrap=tk.WORD,
            width=50,
            height=10
        )
        self.setup_tags()
        
    def setup_tags(self):
        """Setup text tags voor formatting"""
        self.tag_config('timestamp', foreground=UI_COLORS['info'])
        self.tag_config('error', foreground=UI_COLORS['error'])
        self.tag_config('success', foreground=UI_COLORS['success'])
        self.tag_config('warning', foreground=UI_COLORS['warning'])
        
    def append_log(self, message: str, level: str = "info"):
        """
        Voeg een log entry toe.
        
        Args:
            message: Het log bericht
            level: Log level voor kleuring
        """
        # Enable editing
        self.config(state="normal")
        
        # Voeg timestamp toe
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.insert("end", f"[{timestamp}] ", "timestamp")
        
        # Voeg bericht toe met juiste kleur
        self.insert("end", f"{message}\n", level)
        
        # Scroll naar bottom
        self.see("end")
        
        # Disable editing
        self.config(state="disabled")

class StatusBar(ttk.Frame):
    """Status balk voor de applicatie"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup de status bar"""
        # Status message
        self.status_label = ttk.Label(
            self,
            text="Ready",
            padding=(5, 2)
        )
        self.status_label.pack(side="left")
        
        # Separator
        ttk.Separator(self, orient="vertical").pack(
            side="left",
            fill="y",
            padx=5
        )
        
        # Clock
        self.clock_label = ttk.Label(
            self,
            padding=(5, 2)
        )
        self.clock_label.pack(side="right")
        
    def set_status(self, message: str, level: str = "info"):
        self.status_label.config(
            text=message,
            foreground=UI_COLORS.get(level, UI_COLORS['info'])  # Was: Config.COLORS
        )
        
    def update_clock(self):
        """Update de klok"""
        time_str = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=time_str)