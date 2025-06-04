"""
Tests voor logging utilities
"""

import pytest
import logging
from agent_executive.utils import setup_logging, get_logger, LogCapture
from agent_executive.utils import LoggingError

def test_setup_logging(temp_dir):
    """Test logging setup"""
    log_file = temp_dir / "test.log"
    
    # Test basic setup
    setup_logging(log_file=log_file, level="INFO")
    logger = get_logger("test")
    logger.info("Test message")
    
    # Verify log file
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content

def test_log_capture():
    """Test log capture functionaliteit"""
    logger = get_logger("test_capture")
    
    with LogCapture() as capture:
        logger.info("Info message")
        logger.error("Error message")
        
        logs = capture.get_logs()
        assert len(logs) == 2
        assert logs[0].message == "Info message"
        assert logs[1].levelname == "ERROR"

def test_context_logger():
    """Test context logger"""
    logger = get_logger("test_context")
    logger.set_context(user="test", action="login")
    
    with LogCapture() as capture:
        logger.info("User action")
        logs = capture.get_logs()
        assert "user" in str(logs[0].extra)
        assert "action" in str(logs[0].extra)