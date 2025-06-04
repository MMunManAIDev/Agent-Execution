"""
AgentExecutive Main Application

De hoofdapplicatie class die alle UI componenten en handlers integreert.
"""

from .constants import (
    UI_EVENTS,
    UI_COLORS,
    WIDGET_STYLES,
    UI_CONFIG,
    configure_ui_styles
)

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime

from ..config import Config
from ..handlers import LLMHandler, WebPageHandler
from ..utils.constants import STATUS_CODES
from .tab import TabManager, ExecutionTab
from .widgets import StatusBar

class AgentExecutiveApp:
    """
    Hoofdapplicatie class voor AgentExecutive.
    Integreert alle componenten en beheert de hoofdinterface.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialiseer de hoofdapplicatie.
        
        Args:
            root: De Tkinter root widget
        """
        self.root = root
        self.logger = logging.getLogger(__name__)
        
        # Setup hoofdwindow
        self.setup_window()
        
        # Initialiseer handlers
        self.setup_handlers()
        
        # Setup UI
        self.setup_ui()
        
        # Setup event bindings
        self.setup_bindings()
        
        # Start periodic updates
        self.start_periodic_updates()
        
        self.logger.info("Application initialized successfully")

    def setup_window(self) -> None:
        """Configureer het hoofdvenster"""
        self.root.title(f"AgentExecutive v{Config.VERSION}")
        self.root.geometry(Config.WINDOW_SIZE)
        self.root.minsize(*Config.WINDOW_MIN_SIZE)
        
        # Configure styles
        configure_ui_styles(self.root)
        
        # Setup window manager callbacks
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Make the window resizable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def setup_handlers(self) -> None:
        """Initialiseer de core handlers"""
        try:
            self.llm_handler = LLMHandler()
            self.web_handler = WebPageHandler()
            self.logger.info("Handlers initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize handlers: {str(e)}")
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize handlers:\n{str(e)}")
            self.root.destroy()

    def setup_ui(self) -> None:
        """Setup de hoofdinterface"""
        # Create main menu
        self.setup_menu()
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Initialize tab manager
        self.tab_manager = TabManager(self.main_container, self)
        self.tab_manager.pack(expand=True, fill="both")
        
        # Add status bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        
        # Create first tab
        self.tab_manager.add_tab()

    def setup_menu(self) -> None:
        """Setup het hoofdmenu"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New Tab", command=self.on_new_tab)
        file_menu.add_command(label="Save Execution", command=self.on_save_execution)
        file_menu.add_command(label="Load Execution", command=self.on_load_execution)
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Show Logs", command=self.show_logs)
        view_menu.add_command(label="Show Screenshots", command=self.show_screenshots)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def setup_bindings(self) -> None:
        """Setup keyboard shortcuts en event bindings"""
        self.root.bind("<Control-n>", lambda e: self.on_new_tab())
        self.root.bind("<Control-s>", lambda e: self.on_save_execution())
        self.root.bind("<Control-o>", lambda e: self.on_load_execution())
        self.root.bind("<Control-w>", lambda e: self.on_close_tab())
        self.root.bind("<F5>", lambda e: self.on_refresh())

    def start_periodic_updates(self) -> None:
        """Start periodieke UI updates"""
        def update():
            self.status_bar.update_clock()
            self.root.after(1000, update)
        update()

    # Event Handlers
    def on_new_tab(self) -> None:
        """Handle nieuw tab request"""
        try:
            self.tab_manager.add_tab()
            self.status_bar.set_status("New tab created", "info")
        except Exception as e:
            self.logger.error(f"Failed to create new tab: {str(e)}")
            self.status_bar.set_status("Failed to create new tab", "error")

    def on_close_tab(self) -> None:
        """Handle tab sluiten request"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            if current_tab.is_executing:
                if not messagebox.askyesno("Warning", 
                    "An execution is in progress. Are you sure you want to close this tab?"):
                    return
            self.tab_manager.close_tab(current_tab)

    def on_save_execution(self) -> None:
        """Handle execution opslaan request"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        try:
            data = current_tab.get_execution_data()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"execution_{timestamp}.json"
            
            filename = tk.filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_name
            )
            
            if filename:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                self.status_bar.set_status(f"Execution saved to {filename}", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to save execution: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save execution:\n{str(e)}")

    def on_load_execution(self) -> None:
        """Handle execution laden request"""
        try:
            filename = tk.filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    
                new_tab = self.tab_manager.add_tab()
                new_tab.load_execution_data(data)
                self.status_bar.set_status(f"Execution loaded from {filename}", "success")
                
        except Exception as e:
            self.logger.error(f"Failed to load execution: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load execution:\n{str(e)}")

    def on_refresh(self) -> None:
        """Handle refresh request"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            current_tab.refresh()
            self.status_bar.set_status("Page refreshed", "info")

    def on_close(self) -> None:
        """Handle applicatie sluiten request"""
        if self.tab_manager.has_executing_tabs():
            if not messagebox.askyesno("Warning", 
                "There are still executions in progress. Are you sure you want to quit?"):
                return
        
        try:
            # Cleanup
            self.cleanup()
            
            # Destroy root window
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            messagebox.showerror("Shutdown Error", 
                               f"Error during shutdown:\n{str(e)}")

    # Utility Methods
    def cleanup(self) -> None:
        """Cleanup resources voor shutdown"""
        try:
            # Stop alle executies
            self.tab_manager.stop_all_executions()
            
            # Cleanup handlers
            if hasattr(self, 'web_handler'):
                self.web_handler.cleanup()
                
            self.logger.info("Cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            raise

    # UI Utility Windows
    def show_settings(self) -> None:
        """Toon settings window"""
        # TODO: Implement settings dialog
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")

    def show_logs(self) -> None:
        """Toon log viewer window"""
        # TODO: Implement log viewer
        messagebox.showinfo("Logs", "Log viewer not implemented yet")

    def show_screenshots(self) -> None:
        """Toon screenshot viewer window"""
        # TODO: Implement screenshot viewer
        messagebox.showinfo("Screenshots", "Screenshot viewer not implemented yet")

    def show_documentation(self) -> None:
        """Toon documentatie window"""
        # TODO: Implement documentation viewer
        messagebox.showinfo("Documentation", "Documentation not implemented yet")

    def show_about(self) -> None:
        """Toon about dialog"""
        about_text = f"""AgentExecutive v{Config.VERSION}

A tool for automating web tasks using LLMs.

Copyright © 2024
"""
        messagebox.showinfo("About AgentExecutive", about_text)

    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Centrale error handler voor de applicatie.
        
        Args:
            error: De exception die opgevangen is
            context: Context informatie over waar de error optrad
        """
        error_msg = f"{context + ': ' if context else ''}{str(error)}"
        self.logger.error(error_msg, exc_info=True)
        self.status_bar.set_status(error_msg, "error")
        messagebox.showerror("Error", error_msg)