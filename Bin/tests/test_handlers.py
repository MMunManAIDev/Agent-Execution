"""
Tests voor handlers
"""

import pytest
from unittest.mock import Mock, patch
from agent_executive.handlers import LLMHandler, WebPageHandler

@pytest.fixture
def mock_openai():
    """Fixture voor mock OpenAI responses"""
    with patch('openai.ChatCompletion.create') as mock:
        mock.return_value.choices = [
            Mock(message=Mock(content='{"type": "CLICK", "target": "//button"}'))
        ]
        yield mock

@pytest.fixture
def mock_webdriver():
    """Fixture voor mock Selenium WebDriver"""
    with patch('selenium.webdriver.Chrome') as mock:
        yield mock

def test_llm_handler(mock_openai):
    """Test LLM handler"""
    handler = LLMHandler(api_key="test-key")
    
    action = handler.get_llm_action(
        snapshot='{"elements": []}',
        role="tester",
        goal="test"
    )
    
    assert action["type"] == "CLICK"
    assert action["target"] == "//button"
    assert mock_openai.called

def test_web_handler(mock_webdriver):
    """Test web handler"""
    handler = WebPageHandler()
    
    # Test page loading
    success, _ = handler.load_page("https://example.com")
    assert success
    
    # Test screenshot
    success, _ = handler.take_screenshot()
    assert success