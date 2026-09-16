"""
Web Tools Plugin for Complete Self System

Provides web-related utilities including search, scraping, and URL operations
"""

import json
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin


def web_search(args: Dict[str, Any]) -> str:
    """Search the web using a search engine API"""
    query = args.get('query', '')
    limit = int(args.get('limit', 5))
    
    if not query:
        return "No search query provided"
    
    try:
        # Using a simple web search approach
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Parse results (simplified)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for g in soup.find_all('div', class_='g'):
            link = g.find('a')
            if link and 'href' in link.attrs:
                url = link['href']
                title = g.find('h3')
                if title:
                    results.append({'title': title.get_text(), 'url': url})
            if len(results) >= limit:
                break
        
        return json.dumps(results, indent=2)
    except ImportError:
        return "BeautifulSoup not installed. Install with: pip install beautifulsoup4"
    except Exception as e:
        return f"Search failed: {str(e)}"


def fetch_url(args: Dict[str, Any]) -> str:
    """Fetch content from a URL"""
    url = args.get('url', '')
    timeout = int(args.get('timeout', 10))
    
    if not url:
        return "No URL provided"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            return response.text[:10000]  # Limit to 10KB
        elif 'application/json' in content_type:
            return json.dumps(response.json(), indent=2)
        else:
            return f"Content type: {content_type}\nSize: {len(response.content)} bytes"
    except Exception as e:
        return f"Fetch failed: {str(e)}"


def extract_links(args: Dict[str, Any]) -> str:
    """Extract all links from a webpage"""
    url = args.get('url', '')
    
    if not url:
        return "No URL provided"
    
    try:
        from bs4 import BeautifulSoup
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                parsed = urlparse(url)
                links.append(f"{parsed.scheme}://{parsed.netloc}{href}")
        
        return json.dumps(links, indent=2)
    except ImportError:
        return "BeautifulSoup not installed"
    except Exception as e:
        return f"Link extraction failed: {str(e)}"


def get_url_info(args: Dict[str, Any]) -> str:
    """Get information about a URL (domain, path, query params)"""
    url = args.get('url', '')
    
    if not url:
        return "No URL provided"
    
    try:
        parsed = urlparse(url)
        info = {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
            'is_absolute': bool(parsed.netloc),
            'is_secure': parsed.scheme == 'https'
        }
        
        # Parse query parameters
        if parsed.query:
            from urllib.parse import parse_qs
            info['query_params'] = parse_qs(parsed.query)
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"URL parsing failed: {str(e)}"


def check_url_health(args: Dict[str, Any]) -> str:
    """Check if a URL is accessible and healthy"""
    url = args.get('url', '')
    timeout = int(args.get('timeout', 5))
    
    if not url:
        return "No URL provided"
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return json.dumps({
            'url': url,
            'final_url': response.url,
            'status_code': response.status_code,
            'healthy': response.status_code < 400,
            'content_type': response.headers.get('Content-Type', ''),
            'response_time': f"{response.elapsed.total_seconds():.2f}s"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'url': url,
            'healthy': False,
            'error': str(e)
        }, indent=2)


def shorten_url(args: Dict[str, Any]) -> str:
    """Shorten a URL using a URL shortening service"""
    url = args.get('url', '')
    service = args.get('service', 'tinyurl')
    
    if not url:
        return "No URL provided"
    
    try:
        if service == 'tinyurl':
            api_url = f"http://tinyurl.com/api-create.php?url={requests.utils.quote(url)}"
            response = requests.get(api_url, timeout=10)
            return response.text
        elif service == 'bitly':
            # Would need API key for Bitly
            return "Bitly requires API key"
        else:
            return f"Unsupported shortening service: {service}"
    except Exception as e:
        return f"URL shortening failed: {str(e)}"


PLUGIN_NAME = "web_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Web-related utilities including search, scraping, and URL operations"

AVAILABLE_FUNCTIONS = {
    'web_search': {
        'description': 'Search the web for information',
        'parameters': {
            'query': {'type': 'string', 'required': True, 'description': 'Search query'},
            'limit': {'type': 'integer', 'required': False, 'description': 'Number of results (default: 5)', 'default': 5}
        },
        'handler': web_search
    },
    'fetch_url': {
        'description': 'Fetch content from a URL',
        'parameters': {
            'url': {'type': 'string', 'required': True, 'description': 'URL to fetch'},
            'timeout': {'type': 'integer', 'required': False, 'description': 'Timeout in seconds (default: 10)', 'default': 10}
        },
        'handler': fetch_url
    },
    'extract_links': {
        'description': 'Extract all links from a webpage',
        'parameters': {
            'url': {'type': 'string', 'required': True, 'description': 'URL to extract links from'}
        },
        'handler': extract_links
    },
    'get_url_info': {
        'description': 'Get detailed information about a URL',
        'parameters': {
            'url': {'type': 'string', 'required': True, 'description': 'URL to analyze'}
        },
        'handler': get_url_info
    },
    'check_url_health': {
        'description': 'Check if a URL is accessible and healthy',
        'parameters': {
            'url': {'type': 'string', 'required': True, 'description': 'URL to check'},
            'timeout': {'type': 'integer', 'required': False, 'description': 'Timeout in seconds (default: 5)', 'default': 5}
        },
        'handler': check_url_health
    },
    'shorten_url': {
        'description': 'Shorten a URL using a shortening service',
        'parameters': {
            'url': {'type': 'string', 'required': True, 'description': 'URL to shorten'},
            'service': {'type': 'string', 'required': False, 'description': 'Shortening service (default: tinyurl)', 'default': 'tinyurl'}
        },
        'handler': shorten_url
    }
}


def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}
