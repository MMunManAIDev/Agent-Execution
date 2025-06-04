"""
Test suite voor AgentExecutive.
Bevat fixtures en gemeenschappelijke test utilities.
"""

import pytest
import os
import tempfile
from pathlib import Path
from typing import Generator, Any

@pytest.fixture
def temp_dir() -> Generator[Path, Any, None]:
    """Fixture voor tijdelijke directory"""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_config(temp_dir):
    """Fixture voor test configuratie"""
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    old_screenshot_dir = os.environ.get("SCREENSHOT_DIR")
    old_log_dir = os.environ.get("LOG_DIR")
    
    os.environ["SCREENSHOT_DIR"] = str(temp_dir / "screenshots")
    os.environ["LOG_DIR"] = str(temp_dir / "logs")
    
    yield
    
    if old_screenshot_dir:
        os.environ["SCREENSHOT_DIR"] = old_screenshot_dir
    if old_log_dir:
        os.environ["LOG_DIR"] = old_log_dir