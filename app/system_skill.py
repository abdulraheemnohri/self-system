"""
System Skill for Complete Self System

Provides system information, monitoring, and management capabilities
"""

import json
import os
import sys
import time
import platform
import socket
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime


class SystemSkill:
    def __init__(self):
        self.name = "system_skill"
        self.description = "System information, monitoring, and management"
        self.version = "1.0.0"
    
    def get_system_info(self) -> Dict[str, Any]:
        try:
            return {
                'system': {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'platform_release': platform.release(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'node_name': platform.node(),
                },
                'python': {
                    'version': sys.version,
                    'executable': sys.executable,
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': f'Failed to get system info: {str(e)}'}
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'capabilities': ['Comprehensive system information', 'Resource monitoring', 'Process listing', 'Environment inspection', 'Command execution', 'Port checking']
        }

system_skill = SystemSkill()