"""
System Tools Plugin

Provides system information and monitoring tools.
"""

import os
import sys
import platform
import socket
import uuid
import time
from typing import Dict, Any, List, Optional


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    try:
        import psutil
        
        system_info = {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "platform": platform.platform(),
        }
        
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
        }
        
        try:
            freq = psutil.cpu_freq()
            cpu_info["max_frequency"] = freq.max
            cpu_info["min_frequency"] = freq.min
            cpu_info["current_frequency"] = freq.current
        except Exception:
            pass
        
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "free": memory.free,
            "percent_used": memory.percent,
        }
        
        swap = psutil.swap_memory()
        swap_info = {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent_used": swap.percent,
        }
        
        disk_info = []
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent_used": usage.percent,
                })
            except Exception:
                continue
        
        network_info = {
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
        }
        
        process = psutil.Process(os.getpid())
        process_info = {
            "pid": process.pid,
            "name": process.name(),
            "cmdline": process.cmdline(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_info": process.memory_info()._asdict(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        }
        
        python_info = {
            "version": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "path": sys.path[:5],
        }
        
        return {
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "swap": swap_info,
            "disks": disk_info,
            "network": network_info,
            "process": process_info,
            "python": python_info,
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def get_cpu_info() -> Dict[str, Any]:
    """Get CPU information."""
    try:
        import psutil
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "per_cpu_usage": psutil.cpu_percent(interval=1, percpu=True),
        }
        try:
            freq = psutil.cpu_freq()
            cpu_info["max_frequency"] = freq.max
            cpu_info["min_frequency"] = freq.min
            cpu_info["current_frequency"] = freq.current
        except Exception:
            pass
        return cpu_info
    except Exception as e:
        return {"error": str(e), "success": False}


def get_memory_info() -> Dict[str, Any]:
    """Get memory information."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "virtual_memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent_used": memory.percent,
            },
            "swap_memory": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent_used": swap.percent,
            },
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def get_disk_info() -> Dict[str, Any]:
    """Get disk information."""
    try:
        import psutil
        disk_info = []
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent_used": usage.percent,
                })
            except Exception:
                continue
        disk_io = psutil.disk_io_counters()
        return {
            "partitions": disk_info,
            "io_counters": {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
            },
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def get_network_info() -> Dict[str, Any]:
    """Get network information."""
    try:
        import psutil
        interfaces = psutil.net_if_addrs()
        net_info = {}
        for name, addrs in interfaces.items():
            net_info[name] = []
            for addr in addrs:
                net_info[name].append({
                    "family": addr.family.name,
                    "address": addr.address,
                    "netmask": addr.netmask if hasattr(addr, 'netmask') else None,
                    "broadcast": addr.broadcast if hasattr(addr, 'broadcast') else None,
                })
        net_io = psutil.net_io_counters()
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            connections.append({
                "fd": conn.fd,
                "family": conn.family.name,
                "type": conn.type.name,
                "laddr": conn.laddr,
                "raddr": conn.raddr,
                "status": conn.status,
                "pid": conn.pid,
            })
        return {
            "interfaces": net_info,
            "io_counters": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            },
            "connections": connections,
            "hostname": socket.gethostname(),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def get_process_info(pid: int = None) -> Dict[str, Any]:
    """Get information about a specific process."""
    try:
        import psutil
        if pid is None:
            pid = os.getpid()
        process = psutil.Process(pid)
        info = {
            "pid": process.pid,
            "name": process.name(),
            "executable": process.exe(),
            "cmdline": process.cmdline(),
            "status": process.status(),
            "username": process.username(),
            "create_time": process.create_time(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_info": process.memory_info()._asdict(),
            "open_files": [f._asdict() for f in process.open_files()],
            "connections": [c._asdict() for c in process.connections()],
            "num_threads": process.num_threads(),
            "ppid": process.ppid(),
        }
        cpu_times = process.cpu_times()
        info["cpu_times"] = {
            "user": cpu_times.user,
            "system": cpu_times.system,
            "children_user": cpu_times.children_user,
            "children_system": cpu_times.children_system,
        }
        return info
    except Exception as e:
        return {"error": str(e), "pid": pid, "success": False}


def get_all_processes() -> Dict[str, Any]:
    """Get information about all running processes."""
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except Exception:
                continue
        return {"processes": processes, "count": len(processes), "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


def get_environment() -> Dict[str, Any]:
    """Get environment variables."""
    try:
        env = dict(os.environ)
        sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'API_KEY', 'ACCESS']
        filtered_env = {}
        for key, value in env.items():
            if not any(s.lower() in key.lower() for s in sensitive_keys):
                filtered_env[key] = value
            else:
                filtered_env[key] = "***"
        return {"variables": filtered_env, "count": len(filtered_env), "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


def get_system_uptime() -> Dict[str, Any]:
    """Get system uptime."""
    try:
        import psutil
        import datetime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime_seconds_remaining = int(uptime_seconds % 60)
        return {
            "boot_time": datetime.datetime.fromtimestamp(boot_time).isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human": f"{uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes, {uptime_seconds_remaining} seconds",
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def get_host_info() -> Dict[str, Any]:
    """Get host information."""
    try:
        return {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "ip_addresses": [addr[4][0] for addr in socket.getaddrinfo(socket.gethostname(), None)],
            "mac_address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)]),
            "success": True,
        }
    except Exception as e:
        return {"error": str(e), "success": False}


PLUGIN_METADATA = {
    "name": "system_tools",
    "version": "1.0.0",
    "description": "System information and monitoring tools",
    "author": "Self System",
    "functions": [
        {"name": "get_system_info", "description": "Get comprehensive system information"},
        {"name": "get_cpu_info", "description": "Get CPU information"},
        {"name": "get_memory_info", "description": "Get memory information"},
        {"name": "get_disk_info", "description": "Get disk information"},
        {"name": "get_network_info", "description": "Get network information"},
        {"name": "get_process_info", "description": "Get process information"},
        {"name": "get_all_processes", "description": "Get all running processes"},
        {"name": "get_environment", "description": "Get environment variables"},
        {"name": "get_system_uptime", "description": "Get system uptime"},
        {"name": "get_host_info", "description": "Get host information"},
    ],
}


def get_metadata() -> Dict[str, Any]:
    """Return plugin metadata."""
    return PLUGIN_METADATA
