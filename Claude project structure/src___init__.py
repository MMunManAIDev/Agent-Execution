"""
AgentExecutive Package

Een automatiseringstool die LLM's gebruikt om webtaken uit te voeren.
"""

# Version info
__version__ = '0.0.4'
__author__ = 'Mike van Munster - Mantjes'

# Expose main application components
from .handlers.llm_handler import LLMHandler
from .handlers.web_handler import WebPageHandler
from .ui.app import AgentExecutiveApp

# Expose utility functions
from .utils.url_utils import clean_url
from .utils.threading import threaded

# Expose configuration
from .config import Config

# Package level exports
__all__ = [
    'LLMHandler',
    'WebPageHandler',
    'AgentExecutiveApp',
    'clean_url',
    'threaded',
    'Config',
]