"""
URL Utilities Module

Bevat functies voor URL validatie, normalisatie en manipulatie.
"""

import re
from urllib.parse import urlparse, urljoin, urlunparse
from typing import Tuple, Optional
import tldextract
import logging
from .constants import URLError, URL_SCHEMES, DEFAULT_SCHEME, MAX_URL_LENGTH

logger = logging.getLogger(__name__)

def clean_url(url: str) -> str:
    """
    Schoont een URL op en maakt deze gereed voor gebruik.
    
    Args:
        url: De ruwe URL string
        
    Returns:
        Opgeschoonde URL
        
    Raises:
        URLError: Als de URL invalid is of niet opgeschoond kan worden
    """
    try:
        # Verwijder whitespace
        url = url.strip()
        
        # Check basis validiteit
        if not url:
            raise URLError("Empty URL provided")
            
        if len(url) > MAX_URL_LENGTH:
            raise URLError(f"URL exceeds maximum length of {MAX_URL_LENGTH} characters")
        
        # Verwijder eventuele 'www.'
        if url.startswith(('http://www.', 'https://www.')):
            url = url.replace('www.', '', 1)
        elif url.startswith('www.'):
            url = url[4:]
            
        # Voeg schema toe als het ontbreekt
        if not any(url.startswith(scheme + '://') for scheme in URL_SCHEMES):
            url = f'{DEFAULT_SCHEME}://{url}'
            
        # Valideer de opgeschoonde URL
        if not validate_url(url):
            raise URLError("Invalid URL format after cleaning")
            
        return url
        
    except URLError:
        raise
    except Exception as e:
        raise URLError(f"Failed to clean URL: {str(e)}")

def validate_url(url: str) -> bool:
    """
    Controleert of een URL valide is.
    
    Args:
        url: De URL om te valideren
        
    Returns:
        True als de URL valide is, anders False
    """
    try:
        # Parse de URL
        parsed = urlparse(url)
        
        # Check basis vereisten
        has_scheme = parsed.scheme in URL_SCHEMES
        has_netloc = bool(parsed.netloc)
        
        # Check domein syntax
        domain_pattern = r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$'
        valid_domain = bool(re.match(domain_pattern, parsed.netloc))
        
        return all([has_scheme, has_netloc, valid_domain])
        
    except Exception as e:
        logger.debug(f"URL validation failed: {str(e)}")
        return False

def normalize_url(url: str) -> str:
    """
    Normaliseert een URL naar een standaard format.
    
    Args:
        url: De URL om te normaliseren
        
    Returns:
        Genormaliseerde URL
        
    Raises:
        URLError: Als de URL niet genormaliseerd kan worden
    """
    try:
        # Parse de URL
        parsed = urlparse(url)
        
        # Converteer naar lowercase
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/')
        
        # Verwijder default ports
        if parsed.scheme == 'http' and netloc.endswith(':80'):
            netloc = netloc[:-3]
        elif parsed.scheme == 'https' and netloc.endswith(':443'):
            netloc = netloc[:-4]
        
        # Reconstrueer de URL
        normalized = urlunparse((
            parsed.scheme,
            netloc,
            path or '/',
            parsed.params,
            parsed.query,
            ''  # Verwijder fragment
        ))
        
        return normalized
        
    except Exception as e:
        raise URLError(f"Failed to normalize URL: {str(e)}")

def get_domain(url: str, include_subdomain: bool = False) -> str:
    """
    Extraheert het domein uit een URL.
    
    Args:
        url: De URL om te verwerken
        include_subdomain: Of subdomein meegenomen moet worden
        
    Returns:
        Het domein (met of zonder subdomein)
        
    Raises:
        URLError: Als het domein niet geëxtraheerd kan worden
    """
    try:
        # Parse met tldextract voor betrouwbare domein extractie
        extract = tldextract.extract(url)
        
        if include_subdomain and extract.subdomain:
            return f"{extract.subdomain}.{extract.domain}.{extract.suffix}"
        else:
            return f"{extract.domain}.{extract.suffix}"
            
    except Exception as e:
        raise URLError(f"Failed to extract domain: {str(e)}")

def join_url(base: str, path: str) -> str:
    """
    Voegt een base URL en path samen.
    
    Args:
        base: De basis URL
        path: Het path gedeelte
        
    Returns:
        Gecombineerde URL
        
    Raises:
        URLError: Als de URLs niet samengevoegd kunnen worden
    """
    try:
        # Normalize inputs
        base = clean_url(base)
        path = path.lstrip('/')
        
        # Join en normalize
        joined = urljoin(base, path)
        return normalize_url(joined)
        
    except Exception as e:
        raise URLError(f"Failed to join URLs: {str(e)}")

def split_url(url: str) -> Tuple[str, str, str]:
    """
    Splitst een URL in schema, domein en path.
    
    Args:
        url: De URL om te splitsen
        
    Returns:
        Tuple van (schema, domein, path)
        
    Raises:
        URLError: Als de URL niet gesplitst kan worden
    """
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme,
            parsed.netloc,
            parsed.path + 
                (f"?{parsed.query}" if parsed.query else "") +
                (f"#{parsed.fragment}" if parsed.fragment else "")
        )
    except Exception as e:
        raise URLError(f"Failed to split URL: {str(e)}")

def get_url_parts(url: str) -> dict:
    """
    Krijg alle onderdelen van een URL.
    
    Args:
        url: De URL om te analyseren
        
    Returns:
        Dictionary met alle URL onderdelen
        
    Raises:
        URLError: Als de URL niet geanalyseerd kan worden
    """
    try:
        parsed = urlparse(url)
        extract = tldextract.extract(url)
        
        return {
            'scheme': parsed.scheme,
            'username': parsed.username,
            'password': parsed.password,
            'subdomain': extract.subdomain,
            'domain': extract.domain,
            'tld': extract.suffix,
            'port': parsed.port,
            'path': parsed.path,
            'query': parsed.query,
            'fragment': parsed.fragment
        }
        
    except Exception as e:
        raise URLError(f"Failed to get URL parts: {str(e)}")

def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Controleert of een URL veilig is om te bezoeken.
    
    Args:
        url: De URL om te controleren
        
    Returns:
        Tuple van (is_safe, reason)
    """
    try:
        # Basis validatie
        if not validate_url(url):
            return False, "Invalid URL format"
            
        # Check lengte
        if len(url) > MAX_URL_LENGTH:
            return False, "URL too long"
            
        # Parse de URL
        parsed = urlparse(url)
        
        # Check schema
        if parsed.scheme not in URL_SCHEMES:
            return False, f"Unsupported scheme: {parsed.scheme}"
            
        # Check credentials in URL
        if parsed.username or parsed.password:
            return False, "URL contains credentials"
            
        # Check bekende gevaarlijke patterns
        dangerous_patterns = [
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'file:',
        ]
        
        url_lower = url.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, url_lower):
                return False, f"URL contains dangerous pattern: {pattern}"
                
        return True, None
        
    except Exception as e:
        return False, f"URL check failed: {str(e)}"