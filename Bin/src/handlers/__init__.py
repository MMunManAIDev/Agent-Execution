"""
AgentExecutive Handlers Package

Dit package bevat de core handlers voor LLM en web interacties.
"""

from .llm_handler import LLMHandler
from .web_handler import WebPageHandler

# Expose de hoofdklassen
__all__ = [
    'LLMHandler',
    'WebPageHandler',
]

# Handler versie informatie voor logging doeleinden
__handler_versions__ = {
    'LLMHandler': '0.0.1',
    'WebPageHandler': '0.0.1'
}

# Handler configuratie validatie
def validate_handler_config():
    """
    Valideer de configuratie van alle handlers.
    Returns: (bool, str) - (is_valid, error_message)
    """
    try:
        from ..config import Config
        
        # Check LLM configuratie
        if not Config.OPENAI_API_KEY:
            return False, "OpenAI API key is not configured"
            
        # Check Chrome configuratie
        if not Config.CHROME_OPTIONS:
            return False, "Chrome options are not configured"
            
        return True, None
        
    except ImportError as e:
        return False, f"Configuration error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during handler validation: {str(e)}"