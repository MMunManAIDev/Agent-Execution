"""
AgentExecutive UI Package

Dit package bevat alle UI-gerelateerde componenten.
"""

from .constants import (
    UI_EVENTS,
    UI_COLORS,
    WIDGET_STYLES,
    UI_CONFIG
)

from .app import AgentExecutiveApp
from .tab import TabManager, ExecutionTab
from .widgets import (
    SnapshotViewer,
    ActionPanel,
    LogViewer,
    UrlBar,
    StatusBar
)

__all__ = [
    # Main components
    'AgentExecutiveApp',
    'TabManager',
    'ExecutionTab',
    
    # Widgets
    'SnapshotViewer',
    'ActionPanel',
    'LogViewer',
    'UrlBar',
    'StatusBar',
    
    # Constants
    'UI_EVENTS',
    'UI_COLORS',
    'WIDGET_STYLES',
    'UI_CONFIG'
]

# UI versie informatie
__ui_version__ = '0.0.4'

# UI event types voor communicatie tussen componenten
UI_EVENTS = {
    # Tab events
    'TAB_CREATED': 'tab_created',
    'TAB_CLOSED': 'tab_closed',
    'TAB_SWITCHED': 'tab_switched',
    
    # Execution events
    'EXECUTION_STARTED': 'execution_started',
    'EXECUTION_STOPPED': 'execution_stopped',
    'EXECUTION_COMPLETED': 'execution_completed',
    'EXECUTION_ERROR': 'execution_error',
    
    # Action events
    'ACTION_PENDING': 'action_pending',
    'ACTION_EXECUTED': 'action_executed',
    'ACTION_FAILED': 'action_failed',
    
    # UI update events
    'SNAPSHOT_UPDATED': 'snapshot_updated',
    'LOG_UPDATED': 'log_updated',
    'STATUS_UPDATED': 'status_updated'
}

# Kleurenschema voor verschillende UI states
UI_COLORS = {
    'success': '#28a745',
    'error': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'pending': '#6c757d'
}

# Custom widget styles
WIDGET_STYLES = {
    'button': {
        'padding': '5 10',
        'relief': 'flat',
        'borderwidth': 1
    },
    'entry': {
        'relief': 'solid',
        'borderwidth': 1
    },
    'frame': {
        'relief': 'groove',
        'borderwidth': 2
    }
}

def configure_ui_styles(root):
    """
    Configureer globale UI styles voor de applicatie.
    
    Args:
        root: De Tkinter root widget
    """
    from tkinter import ttk
    import tkinter as tk
    
    # Maak style object
    style = ttk.Style(root)
    
    # Configureer algemene styles
    style.configure('AgentExecutive.TButton',
                   padding=WIDGET_STYLES['button']['padding'],
                   relief=WIDGET_STYLES['button']['relief'])
                   
    style.configure('AgentExecutive.TEntry',
                   relief=WIDGET_STYLES['entry']['relief'])
                   
    style.configure('AgentExecutive.TFrame',
                   relief=WIDGET_STYLES['frame']['relief'])

def create_tooltip(widget, text):
    """
    Maak een tooltip voor een widget.
    
    Args:
        widget: De widget waar de tooltip aan toegevoegd moet worden
        text: De tekst voor de tooltip
    """
    import tkinter as tk
    
    def show_tooltip(event=None):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1)
        label.pack()
        
        def hide_tooltip():
            tooltip.destroy()
            
        tooltip.bind('<Leave>', lambda e: hide_tooltip())
        widget.bind('<Leave>', lambda e: hide_tooltip())
    
    widget.bind('<Enter>', show_tooltip)

class UIEvent:
    """
    Event class voor UI communicatie.
    """
    def __init__(self, event_type, data=None):
        """
        Args:
            event_type: Type van het event (uit UI_EVENTS)
            data: Optional data voor het event
        """
        if event_type not in UI_EVENTS.values():
            raise ValueError(f"Invalid event type: {event_type}")
            
        self.type = event_type
        self.data = data or {}
        self.timestamp = __import__('time').time()

def publish_event(event):
    """
    Publiceer een UI event naar alle subscribers.
    
    Args:
        event: UIEvent instance
    """
    # Dit is een placeholder - in de echte implementatie
    # zou je hier een event system gebruiken
    pass

# Validatie van UI configuratie
def validate_ui_config():
    """
    Valideer de UI configuratie.
    Returns: (bool, str) - (is_valid, error_message)
    """
    try:
        from ..config import Config
        
        # Controleer window settings
        if not hasattr(Config, 'WINDOW_SIZE'):
            return False, "Window size not configured"
            
        # Controleer font settings
        if not hasattr(Config, 'FONT_FAMILY'):
            return False, "Font family not configured"
            
        # Controleer color settings
        if not hasattr(Config, 'COLORS'):
            return False, "Colors not configured"
            
        return True, None
        
    except ImportError as e:
        return False, f"Configuration error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during UI validation: {str(e)}"