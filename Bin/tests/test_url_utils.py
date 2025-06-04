"""
Tests voor URL utilities
"""

import pytest
from agent_executive.utils import clean_url, validate_url, normalize_url, get_domain
from agent_executive.utils import URLError

def test_clean_url():
    """Test URL cleaning functionaliteit"""
    # Test basic cleaning
    assert clean_url("www.example.com") == "https://example.com"
    assert clean_url("http://www.example.com") == "http://example.com"
    
    # Test error cases
    with pytest.raises(URLError):
        clean_url("")
    with pytest.raises(URLError):
        clean_url("not a url")

def test_validate_url():
    """Test URL validatie"""
    assert validate_url("https://example.com") == True
    assert validate_url("not a url") == False
    assert validate_url("ftp://example.com") == False

def test_normalize_url():
    """Test URL normalisatie"""
    assert normalize_url("HTTPS://ExAmPlE.com/PATH/") == "https://example.com/path"
    assert normalize_url("http://example.com:80") == "http://example.com"

def test_get_domain():
    """Test domein extractie"""
    assert get_domain("https://sub.example.com/path") == "example.com"
    assert get_domain("https://sub.example.com/path", include_subdomain=True) == "sub.example.com"
