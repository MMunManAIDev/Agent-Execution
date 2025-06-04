"""
UI Constants Module

Bevat constanten en configuratie voor de UI componenten.
"""

import tkinter as tk
from tkinter import ttk

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

# Widget styles
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

# UI configuratie
UI_CONFIG = {
    'WINDOW_TITLE': 'AgentExecutive',
    'DEFAULT_TAB_TITLE': 'Execution',
    'SNAPSHOT_SIZE': (300, 200),
    'MAX_LOG_LINES': 1000
}

def configure_ui_styles(root: tk.Tk) -> None:
    """
    Configureer globale UI styles voor de applicatie.
    
    Args:
        root: De Tkinter root widget
    """
    style = ttk.Style(root)
    
    # Configureer algemene styles
    style.configure('AgentExecutive.TButton',
                   padding=WIDGET_STYLES['button']['padding'],
                   relief=WIDGET_STYLES['button']['relief'])
                   
    style.configure('AgentExecutive.TEntry',
                   relief=WIDGET_STYLES['entry']['relief'])
                   
    style.configure('AgentExecutive.TFrame',
                   relief=WIDGET_STYLES['frame']['relief'])