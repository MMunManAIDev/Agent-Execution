"""
Tests voor UI componenten
"""

import pytest
import tkinter as tk
from agent_executive.ui import UrlBar, SnapshotViewer, ActionPanel, LogViewer

@pytest.fixture
def root():
    """Fixture voor Tkinter root window"""
    root = tk.Tk()
    yield root
    root.destroy()

def test_url_bar(root):
    """Test URL bar widget"""
    def on_navigate():
        pass
    
    url_bar = UrlBar(root, on_navigate)
    
    # Test URL setting/getting
    test_url = "https://example.com"
    url_bar.set_url(test_url)
    assert url_bar.get_url() == test_url

def test_action_panel(root):
    """Test action panel widget"""
    def on_execute():
        pass
    
    panel = ActionPanel(root, on_execute)
    
    # Test action setting
    action = {"type": "CLICK", "target": "//button"}
    panel.set_action(action)
    assert panel.get_action() == action

def test_log_viewer(root):
    """Test log viewer widget"""
    viewer = LogViewer(root)
    
    # Test log appending
    test_message = "Test log message"
    viewer.append_log(test_message)
    
    content = viewer.get("1.0", tk.END)
    assert test_message in content