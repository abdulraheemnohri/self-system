"""
Network Tools Plugin

Provides network-related tools for HTTP requests, connectivity checks, and network information.
"""

import json
import socket
import urllib.parse
from typing import Dict, Any, List, Optional, Union


def http_get(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Dict[str, Any]:
    """Make an HTTP GET request."""
    try:
        import requests
        response = requests.get(url, headers=headers, timeout=timeout)
        return {
            "url": url,
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": dict(response.headers),
            "content": response.text[:10000] if response.text else "",
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": len(response.content),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "url": url, "success": False}


def http_post(url: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None,
              headers: Dict[str, str] = None, timeout: int = 30) -> Dict[str, Any]:
    """Make an HTTP POST request."""
    try:
        import requests
        if headers is None:
            headers = {}
        if json_data:
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=json_data, headers=headers, timeout=timeout)
        elif data:
            response = requests.post(url, data=data, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, timeout=timeout)
        return {
            "url": url,
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": dict(response.headers),
            "content": response.text[:10000] if response.text else "",
            "content_type": response.headers.get("Content-Type", ""),
            "content_length": len(response.content),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "url": url, "success": False}


def check_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: int = 5) -> Dict[str, Any]:
    """Check network connectivity to a host."""
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return {
            "host": host,
            "port": port,
            "connected": True,
            "message": f"Successfully connected to {host}:{port}",
            "success": True,
        }
    except Exception as e:
        return {
            "host": host,
            "port": port,
            "connected": False,
            "error": str(e),
            "success": False,
        }


def check_internet() -> Dict[str, Any]:
    """Check if internet is available."""
    hosts = [
        ("8.8.8.8", 53, "Google DNS"),
        ("1.1.1.1", 53, "Cloudflare DNS"),
        ("github.com", 443, "GitHub"),
        ("google.com", 443, "Google"),
    ]
    
    results = []
    connected_count = 0
    
    for host, port, name in hosts:
        try:
            socket.create_connection((host, port), timeout=5).close()
            results.append({"host": host, "port": port, "name": name, "connected": True})
            connected_count += 1
        except Exception as e:
            results.append({"host": host, "port": port, "name": name, "connected": False, "error": str(e)})
    
    return {
        "internet_available": connected_count > 0,
        "connected_count": connected_count,
        "total_checks": len(hosts),
        "results": results,
        "success": True,
    }


def get_public_ip() -> Dict[str, Any]:
    """Get the public IP address."""
    try:
        import requests
        services = ["https://api.ipify.org", "https://ident.me", "https://ifconfig.me/ip"]
        for service in services:
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    return {"ip": ip, "service": service, "success": True}
            except Exception:
                continue
        return {"error": "Could not determine public IP", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def get_local_ip() -> Dict[str, Any]:
    """Get the local IP address."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        all_ips = []
        for addr in socket.getaddrinfo(hostname, None):
            ip = addr[4][0]
            if ip not in all_ips and not ip.startswith("127."):
                all_ips.append(ip)
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "all_ips": all_ips,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def parse_url(url: str) -> Dict[str, Any]:
    """Parse a URL into its components."""
    try:
        parsed = urllib.parse.urlparse(url)
        return {
            "url": url,
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "password": "***" if parsed.password else None,
            "is_absolute": bool(parsed.scheme),
            "is_relative": not bool(parsed.scheme),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "url": url, "success": False}


def get_url_query_params(url: str) -> Dict[str, Any]:
    """Extract query parameters from a URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        flat_params = {}
        for key, value in params.items():
            if len(value) == 1:
                flat_params[key] = value[0]
            else:
                flat_params[key] = value
        return {"url": url, "query": parsed.query, "params": flat_params, "success": True}
    except Exception as e:
        return {"error": str(e), "url": url, "success": False}


def check_port(host: str, port: int, timeout: int = 3) -> Dict[str, Any]:
    """Check if a specific port is open on a host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            if result == 0:
                return {"host": host, "port": port, "open": True, "message": f"Port {port} is open on {host}", "success": True}
            else:
                return {"host": host, "port": port, "open": False, "message": f"Port {port} is closed on {host}", "success": True}
    except Exception as e:
        return {"error": str(e), "host": host, "port": port, "success": False}


def dns_lookup(hostname: str) -> Dict[str, Any]:
    """Perform DNS lookup for a hostname."""
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        ips = []
        for info in addr_info:
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
        return {"hostname": hostname, "ips": ips, "count": len(ips), "success": True}
    except Exception as e:
        return {"error": str(e), "hostname": hostname, "success": False}


def reverse_dns(ip: str) -> Dict[str, Any]:
    """Perform reverse DNS lookup for an IP address."""
    try:
        hostname = socket.gethostbyaddr(ip)
        return {"ip": ip, "hostname": hostname[0], "aliases": hostname[1], "addresses": hostname[2], "success": True}
    except Exception as e:
        return {"error": str(e), "ip": ip, "success": False}


PLUGIN_METADATA = {
    "name": "network_tools",
    "version": "1.0.0",
    "description": "Network-related tools for HTTP requests and connectivity checks",
    "author": "Self System",
    "functions": [
        {"name": "http_get", "description": "Make HTTP GET request"},
        {"name": "http_post", "description": "Make HTTP POST request"},
        {"name": "check_connectivity", "description": "Check connectivity to a host"},
        {"name": "check_internet", "description": "Check internet availability"},
        {"name": "get_public_ip", "description": "Get public IP address"},
        {"name": "get_local_ip", "description": "Get local IP address"},
        {"name": "parse_url", "description": "Parse URL into components"},
        {"name": "get_url_query_params", "description": "Extract query parameters from URL"},
        {"name": "check_port", "description": "Check if port is open"},
        {"name": "dns_lookup", "description": "Perform DNS lookup"},
        {"name": "reverse_dns", "description": "Perform reverse DNS lookup"},
    ],
}


def get_metadata() -> Dict[str, Any]:
    """Return plugin metadata."""
    return PLUGIN_METADATA
