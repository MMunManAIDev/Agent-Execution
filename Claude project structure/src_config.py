"""
AgentExecutive Configuration

Centrale configuratie voor de AgentExecutive applicatie.
Definieert alle constanten en configuratie-instellingen.
"""

import os
from pathlib import Path

class Config:
    """Centrale configuratie class voor de applicatie"""
    
    # Versie informatie
    VERSION = "0.1.0"
    
    # API Keys en externe services
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-3.5-turbo"  # of "gpt-4" voor meer capaciteit
    
    # Basis directories
    BASE_DIR = Path(__file__).parent.parent  # src directory
    SCREENSHOT_DIR = BASE_DIR / "screenshots"
    LOG_DIR = BASE_DIR / "logs"
    
    # Window settings
    WINDOW_TITLE = "AgentExecutive"
    WINDOW_SIZE = "1200x900"
    WINDOW_MIN_SIZE = (800, 600)
    
    # UI settings
    SNAPSHOT_SIZE = (300, 200)  # Miniature size
    MAX_LOG_LINES = 1000        # Maximum aantal log regels in UI
    FONT_FAMILY = "Arial"       # Default font
    FONT_SIZE = 10             # Default font size
    
    # Timeouts en delays
    PAGE_LOAD_TIMEOUT = 30     # Seconden
    ELEMENT_TIMEOUT = 10       # Seconden
    ACTION_DELAY = 1           # Seconden tussen acties
    SCREENSHOT_DELAY = 0.5     # Seconden na actie voor screenshot
    
    # Browser settings
    CHROME_OPTIONS = [
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1920,1080"
    ]
    
    # LLM settings
    SYSTEM_PROMPT_TEMPLATE = """
    Je bent een {role}. Je doel is: {goal}.
    Analyseer de gegeven webpagina snapshot en bepaal de volgende actie.
    Geef alleen JSON terug met de structuur:
    {{
        "type": "<CLICK|SCROLL|INPUT|WAIT>",
        "target": "<xpath>",
        "value": "<waarde bij INPUT>",
        "reasoning": "<uitleg waarom deze actie>",
        "progress": "<inschatting voortgang in %>",
        "next_expected_state": "<wat verwacht je te zien na deze actie>"
    }}
    """
    
    LLM_TEMPERATURE = 0.7
    MAX_TOKENS = 500
    
    # Logging settings
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVEL = "INFO"
    LOG_FILE_MAX_BYTES = 10_485_760  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # UI Colors
    COLORS = {
        "primary": "#007bff",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
        "light": "#f8f9fa",
        "dark": "#343a40",
        "background": "#ffffff",
        "text": "#212529"
    }
    
    # UI Styles
    STYLES = {
        "button": {
            "padding": "5 10",
            "font": (FONT_FAMILY, FONT_SIZE),
        },
        "entry": {
            "padding": "5",
            "font": (FONT_FAMILY, FONT_SIZE),
        },
        "label": {
            "font": (FONT_FAMILY, FONT_SIZE),
            "padding": "5",
        },
        "text": {
            "font": (FONT_FAMILY, FONT_SIZE),
            "padding": "5",
            "wrap": "word",
        }
    }
    
    # Error messages
    ERRORS = {
        "no_url": "Please enter a URL",
        "invalid_url": "Invalid URL format",
        "connection_failed": "Could not connect to the website",
        "timeout": "The request timed out",
        "not_found": "Page not found (404)",
        "server_error": "Server error occurred",
        "element_not_found": "Could not find the element on the page",
        "action_failed": "Failed to perform the action",
    }

    @classmethod
    def validate_directories(cls):
        """Controleer en maak benodigde directories aan"""
        cls.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_chrome_options(cls):
        """Return een lijst van Chrome opties voor Selenium"""
        return cls.CHROME_OPTIONS

    @classmethod
    def get_log_config(cls):
        """Return logging configuratie als dictionary"""
        return {
            "format": cls.LOG_FORMAT,
            "level": cls.LOG_LEVEL,
            "filename": cls.LOG_DIR / "agent_executive.log",
            "maxBytes": cls.LOG_FILE_MAX_BYTES,
            "backupCount": cls.LOG_BACKUP_COUNT
        }

    @classmethod
    def get_style(cls, widget_type):
        """Return style configuratie voor een specifiek widget type"""
        return cls.STYLES.get(widget_type, {})

    @classmethod
    def get_error_message(cls, error_code):
        """Return een gebruikersvriendelijke error message"""
        return cls.ERRORS.get(error_code, "An unknown error occurred")