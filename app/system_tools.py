#!/usr/bin/env python3
"""
System Monitoring Tools for Complete Self System

Provides:
- System health checks
- Resource monitoring
- Process management
- Performance metrics
- Self-healing capabilities
"""

import os
import json
import time
import platform
import psutil
import socket
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime


class SystemTools:
    """
    System monitoring and management tools.
    
    Features:
    - System information
    - Resource monitoring (CPU, memory, disk)
    - Process management
    - Network information
    - Performance metrics
    - Self-healing actions
    """
    
    def __init__(self):
        """Initialize SystemTools."""
        self.start_time = time.time()
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information.
        
        Returns:
            Dictionary with system information
        """
        try:
            import psutil
            
            # Basic info
            info = {
                "os": {
                    "system": platform.system(),
                    "node_name": platform.node(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture(),
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler(),
                },
                "process": {
                    "pid": os.getpid(),
                    "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                    "uptime": time.time() - self.start_time,
                },
            }
            
            # CPU
            cpu = psutil.cpu_times_percent(interval=0.1, percpu=True)
            info["cpu"] = {
                "cores": psutil.cpu_count(logical=True),
                "physical_cores": psutil.cpu_count(logical=False),
                "usage_per_core": [float(f"{c:.1f}") for c in cpu],
                "total_usage": float(f"{sum(cpu):.1f}"),
                "frequency": psutil.cpu_freq()._asdict() if hasattr(psutil.cpu_freq(), '_asdict') else {},
            }
            
            # Memory
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.free,
                "percent_used": mem.percent,
            }
            
            # Swap
            swap = psutil.swap_memory()
            info["swap"] = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent_used": swap.percent,
            }
            
            # Disk
            disks = psutil.disk_partitions(all=False)
            disk_info = []
            for disk in disks:
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    disk_info.append({
                        "device": disk.device,
                        "mountpoint": disk.mountpoint,
                        "fstype": disk.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent_used": usage.percent,
                    })
                except Exception:
                    pass
            info["disk"] = disk_info
            
            # Network
            net_io = psutil.net_io_counters()
            info["network"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "interfaces": {},
            }
            
            # Network interfaces
            for interface, addrs in psutil.net_if_addrs().items():
                info["network"]["interfaces"][interface] = [
                    {"family": addr.family.name, "address": addr.address}
                    for addr in addrs
                ]
            
            # Users
            users = psutil.users()
            info["users"] = [
                {"name": u.name, "terminal": u.terminal, "host": u.host}
                for u in users
            ]
            
            # Boot time
            boot_time = psutil.boot_time()
            info["boot_time"] = datetime.fromtimestamp(boot_time).isoformat()
            
            return {"success": True, "info": info}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Get CPU usage information.
        
        Returns:
            Dictionary with CPU usage
        """
        try:
            cpu = psutil.cpu_times_percent(interval=0.1, percpu=True)
            return {
                "success": True,
                "cores": psutil.cpu_count(logical=True),
                "usage_per_core": [float(f"{c:.1f}") for c in cpu],
                "total_usage": float(f"{sum(cpu):.1f}"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage information.
        
        Returns:
            Dictionary with memory usage
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "success": True,
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.free,
                "percent_used": mem.percent,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """
        Get disk usage for a specific path.
        
        Args:
            path: Path to check
            
        Returns:
            Dictionary with disk usage
        """
        try:
            usage = psutil.disk_usage(path)
            return {
                "success": True,
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent_used": usage.percent,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_processes(self, limit: int = 20) -> Dict[str, Any]:
        """
        List running processes.
        
        Args:
            limit: Maximum number of processes to return
            
        Returns:
            Dictionary with process list
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "username": proc.info['username'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                    })
                except Exception:
                    pass
                
                if len(processes) >= limit:
                    break
            
            return {"success": True, "processes": processes, "count": len(processes)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """
        Get information about a specific process.
        
        Args:
            pid: Process ID
            
        Returns:
            Dictionary with process information
        """
        try:
            proc = psutil.Process(pid)
            info = proc.as_dict(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'create_time'])
            info['create_time'] = datetime.fromtimestamp(info['create_time']).isoformat()
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def kill_process(self, pid: int) -> Dict[str, Any]:
        """
        Kill a process.
        
        Args:
            pid: Process ID to kill
            
        Returns:
            Dictionary with result
        """
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return {"success": True, "message": f"Process {pid} terminated"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_port(self, port: int, host: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Check if a port is in use.
        
        Args:
            port: Port number to check
            host: Host to check
            
        Returns:
            Dictionary with port status
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result == 0:
                    return {"success": True, "port": port, "host": host, "in_use": True}
                else:
                    return {"success": True, "port": port, "host": host, "in_use": False}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network statistics.
        
        Returns:
            Dictionary with network stats
        """
        try:
            net_io = psutil.net_io_counters()
            return {
                "success": True,
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_hostname(self) -> Dict[str, Any]:
        """
        Get the system hostname.
        
        Returns:
            Dictionary with hostname
        """
        try:
            return {
                "success": True,
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_ip_addresses(self) -> Dict[str, Any]:
        """
        Get all IP addresses.
        
        Returns:
            Dictionary with IP addresses
        """
        try:
            addresses = []
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)
            
            for ip in ip_list[2]:
                addresses.append({"address": ip, "type": "IPv4"})
            
            # Get all interfaces
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family.name == "AF_INET":
                        addresses.append({
                            "address": addr.address,
                            "type": "IPv4",
                            "interface": interface,
                        })
                    elif addr.family.name == "AF_INET6":
                        addresses.append({
                            "address": addr.address,
                            "type": "IPv6",
                            "interface": interface,
                        })
            
            return {"success": True, "addresses": addresses}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def ping(self, host: str, count: int = 1) -> Dict[str, Any]:
        """
        Ping a host.
        
        Args:
            host: Host to ping
            count: Number of pings
            
        Returns:
            Dictionary with ping result
        """
        try:
            import subprocess
            
            # Windows
            if platform.system().lower() == "windows":
                command = ["ping", "-n", str(count), host]
            # Linux/Mac
            else:
                command = ["ping", "-c", str(count), host]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "success": True,
                "host": host,
                "count": count,
                "output": result.stdout,
                "returncode": result.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def self_heal(self) -> Dict[str, Any]:
        """
        Perform self-healing actions.
        
        Returns:
            Dictionary with healing actions performed
        """
        actions = []
        
        # Check memory usage
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            actions.append({
                "action": "high_memory_warning",
                "message": f"Memory usage is high: {mem.percent}%",
                "severity": "warning"
            })
        
        # Check CPU usage
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > 90:
            actions.append({
                "action": "high_cpu_warning",
                "message": f"CPU usage is high: {cpu}%",
                "severity": "warning"
            })
        
        # Check disk space
        disks = psutil.disk_partitions(all=False)
        for disk in disks:
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                if usage.percent > 90:
                    actions.append({
                        "action": "low_disk_warning",
                        "message": f"Disk {disk.mountpoint} is almost full: {usage.percent}%",
                        "severity": "warning"
                    })
            except Exception:
                pass
        
        # Check if critical services are running
        # (This would be customized based on your system)
        
        if not actions:
            actions.append({
                "action": "system_healthy",
                "message": "System is running normally",
                "severity": "info"
            })
        
        return {
            "success": True,
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }


# Global instance
system_tools = SystemTools()


def create_system_tools() -> SystemTools:
    """
    Create a SystemTools instance.
    
    Returns:
        SystemTools instance
    """
    return SystemTools()
