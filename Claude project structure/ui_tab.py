"""
Tab Management Module
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from .constants import UI_EVENTS, UI_COLORS, WIDGET_STYLES, UI_CONFIG
from .widgets import (
    SnapshotViewer,
    ActionPanel,
    LogViewer,
    UrlBar
)

class ExecutionTab(ttk.Frame):
    """
    Een individuele executie tab die één automatisering sessie beheert.
    """
    
    def __init__(self, parent: ttk.Notebook, app, tab_id: int):
        """
        Initialiseer een nieuwe executie tab.
        
        Args:
            parent: De parent notebook widget
            app: Referentie naar de hoofdapplicatie
            tab_id: Unieke identifier voor deze tab
        """
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.tab_id = tab_id
        self.logger = logging.getLogger(f"ExecutionTab_{tab_id}")
        
        # State
        self.is_executing = False
        self.execution_history = []
        
        # Setup UI
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        """Setup de tab interface"""
        # Main container met grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # URL Bar bovenaan
        self.url_bar = UrlBar(self, self.on_url_navigate)
        self.url_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Left side - Role & Goal
        left_frame = ttk.LabelFrame(content_frame, text="Configuration")
        left_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        # Role input
        ttk.Label(left_frame, text="Role:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.role_entry = ttk.Entry(left_frame, width=40)
        self.role_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        # Goal input
        ttk.Label(left_frame, text="Goal:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.goal_entry = ttk.Entry(left_frame, width=40)
        self.goal_entry.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        
        self.start_button = ttk.Button(
            button_frame,
            text="▶ Start",
            command=self.start_execution,
            style="AgentExecutive.TButton"
        )
        self.start_button.pack(side="left", padx=2)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_execution,
            state="disabled",
            style="AgentExecutive.TButton"
        )
        self.stop_button.pack(side="left", padx=2)
        
        # Right side - Content area with notebook
        self.content_notebook = ttk.Notebook(content_frame)
        self.content_notebook.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        # Tab 1: Execution View
        execution_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(execution_frame, text="Execution")
        
        # Snapshot viewer
        self.snapshot_viewer = SnapshotViewer(execution_frame)
        self.snapshot_viewer.pack(fill="x", padx=5, pady=5)
        
        # Action panel
        self.action_panel = ActionPanel(
            execution_frame,
            on_execute=self.execute_action
        )
        self.action_panel.pack(fill="x", padx=5, pady=5)
        
        # Tab 2: History View
        history_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(history_frame, text="History")
        
        self.history_viewer = LogViewer(history_frame)
        self.history_viewer.pack(fill="both", expand=True)
        
        # Tab 3: Debug View
        debug_frame = ttk.Frame(self.content_notebook)
        self.content_notebook.add(debug_frame, text="Debug")
        
        self.debug_viewer = LogViewer(debug_frame)
        self.debug_viewer.pack(fill="both", expand=True)

    def setup_bindings(self):
        """Setup event bindings"""
        # Keyboard shortcuts
        self.bind("<Control-Return>", lambda e: self.execute_action())
        self.bind("<Escape>", lambda e: self.stop_execution())
        
        # URL bar bindings
        self.url_bar.entry.bind("<Return>", lambda e: self.on_url_navigate())
        
    def on_url_navigate(self, event=None):
        """Handle URL navigatie"""
        url = self.url_bar.get_url()
        if not url:
            return
            
        try:
            self.app.web_handler.load_page(url)
            self.update_snapshot()
            self.log_action("navigation", f"Navigated to {url}")
        except Exception as e:
            self.handle_error(f"Navigation failed: {str(e)}")

    def start_execution(self):
        """Start de automatische executie"""
        if self.is_executing:
            return
            
        role = self.role_entry.get().strip()
        goal = self.goal_entry.get().strip()
        
        if not role or not goal:
            self.handle_error("Please specify both role and goal")
            return
            
        try:
            self.is_executing = True
            self.update_ui_state()
            self.log_action("execution", "Started automated execution")
            
            # Start eerste actie
            self.execute_next_action()
            
        except Exception as e:
            self.handle_error(f"Failed to start execution: {str(e)}")
            self.stop_execution()

    def stop_execution(self):
        """Stop de automatische executie"""
        if not self.is_executing:
            return
            
        self.is_executing = False
        self.update_ui_state()
        self.log_action("execution", "Stopped automated execution")

    def execute_next_action(self):
        """Bepaal en voer de volgende actie uit"""
        if not self.is_executing:
            return
            
        try:
            # Krijg snapshot van huidige pagina
            snapshot = self.app.web_handler.get_snapshot()
            
            # Vraag LLM om volgende actie
            action = self.app.llm_handler.get_llm_action(
                snapshot,
                self.role_entry.get(),
                self.goal_entry.get()
            )
            
            # Update UI met voorgestelde actie
            self.action_panel.set_action(action)
            
            # Auto-execute als dat geconfigureerd is
            if Config.AUTO_EXECUTE_ACTIONS:
                self.execute_action()
                
        except Exception as e:
            self.handle_error(f"Failed to determine next action: {str(e)}")
            self.stop_execution()

    def execute_action(self):
        """Voer de huidige actie uit"""
        action = self.action_panel.get_action()
        if not action:
            return
            
        try:
            # Voer actie uit
            success, message = self.app.web_handler.perform_action(action)
            
            # Log resultaat
            if success:
                self.log_action("action", f"Executed {action['type']}: {message}")
                # Update snapshot
                self.update_snapshot()
                # Bepaal volgende actie als we in executie zijn
                if self.is_executing:
                    self.execute_next_action()
            else:
                self.handle_error(f"Action failed: {message}")
                
        except Exception as e:
            self.handle_error(f"Failed to execute action: {str(e)}")

    def update_snapshot(self):
        """Update het snapshot beeld"""
        try:
            success, filename = self.app.web_handler.take_screenshot()
            if success:
                self.snapshot_viewer.update_image(filename)
        except Exception as e:
            self.logger.error(f"Failed to update snapshot: {str(e)}")

    def update_ui_state(self):
        """Update UI elementen gebaseerd op huidige state"""
        # Update buttons
        if self.is_executing:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.role_entry.config(state="disabled")
            self.goal_entry.config(state="disabled")
        else:
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.role_entry.config(state="normal")
            self.goal_entry.config(state="normal")

    def log_action(self, action_type: str, message: str):
        """
        Log een actie in de history.
        
        Args:
            action_type: Type van de actie
            message: Beschrijving van de actie
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "type": action_type,
            "message": message
        }
        self.execution_history.append(entry)
        
        # Update history viewer
        self.history_viewer.append_log(
            f"[{timestamp}] {action_type.upper()}: {message}"
        )

    def handle_error(self, message: str):
        """
        Handle een error in deze tab.
        
        Args:
            message: Error message
        """
        self.logger.error(message)
        self.debug_viewer.append_log(f"ERROR: {message}", "error")
        self.app.status_bar.set_status(message, "error")

    def get_execution_data(self) -> Dict[str, Any]:
        """
        Verzamel alle executie data voor opslaan.
        
        Returns:
            Dictionary met alle tab data
        """
        return {
            "url": self.url_bar.get_url(),
            "role": self.role_entry.get(),
            "goal": self.goal_entry.get(),
            "history": self.execution_history,
            "timestamp": datetime.now().isoformat()
        }

    def load_execution_data(self, data: Dict[str, Any]):
        """
        Laad executie data in deze tab.
        
        Args:
            data: Dictionary met tab data
        """
        self.url_bar.set_url(data.get("url", ""))
        self.role_entry.insert(0, data.get("role", ""))
        self.goal_entry.insert(0, data.get("goal", ""))
        
        # Laad history
        for entry in data.get("history", []):
            self.history_viewer.append_log(
                f"[{entry['timestamp']}] {entry['type'].upper()}: {entry['message']}"
            )
            self.execution_history.append(entry)

class TabManager(ttk.Notebook):
    """
    Beheert alle executie tabs.
    """
    
    def __init__(self, parent: tk.Widget, app):
        """
        Initialiseer de tab manager.
        
        Args:
            parent: Parent widget
            app: Referentie naar hoofdapplicatie
        """
        super().__init__(parent)
        self.app = app
        self.tabs: List[ExecutionTab] = []
        self.tab_counter = 0
        
        # Bind tab events
        self.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def add_tab(self) -> ExecutionTab:
        """
        Voeg een nieuwe tab toe.
        
        Returns:
            De nieuwe ExecutionTab
        """
        self.tab_counter += 1
        tab = ExecutionTab(self, self.app, self.tab_counter)
        self.tabs.append(tab)
        self.add(tab, text=f"Execution {self.tab_counter}")
        self.select(tab)
        return tab
        
    def close_tab(self, tab: ExecutionTab):
        """
        Sluit een tab.
        
        Args:
            tab: De tab om te sluiten
        """
        if tab in self.tabs:
            tab_index = self.index(tab)
            self.forget(tab_index)
            self.tabs.remove(tab)
            
            # Voeg een nieuwe tab toe als dit de laatste was
            if not self.tabs:
                self.add_tab()

    def get_current_tab(self) -> Optional[ExecutionTab]:
        """
        Krijg de huidige actieve tab.
        
        Returns:
            De huidige ExecutionTab of None
        """
        try:
            current = self.select()
            index = self.index(current)
            return self.tabs[index]
        except:
            return None

    def on_tab_changed(self, event):
        """Handle tab switch event"""
        current_tab = self.get_current_tab()
        if current_tab:
            # Update status bar
            self.app.status_bar.set_status(
                f"Active: Execution {current_tab.tab_id}",
                "info"
            )

    def has_executing_tabs(self) -> bool:
        """
        Check of er nog tabs aan het executeren zijn.
        
        Returns:
            True als er nog executerende tabs zijn
        """
        return any(tab.is_executing for tab in self.tabs)

    def stop_all_executions(self):
        """Stop alle lopende executies"""
        for tab in self.tabs:
            if tab.is_executing:
                tab.stop_execution()