#!/usr/bin/env python3
"""
File Operations Tools for Complete Self System

Provides safe file operations:
- Read files
- Write files (with safety checks)
- List directory contents
- File search
- File metadata
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class FileTools:
    """
    Safe file operations for the Complete Self System.
    
    Features:
    - Read text and binary files
    - Write files with safety checks
    - List directory contents
    - Search files by pattern
    - Get file metadata
    """
    
    # Allowed directories for file operations
    ALLOWED_DIRS = [
        "storage",
        "plugins",
        "generated_skills",
        "tests",
        "temp",
        "/tmp",
    ]
    
    # Blocked file extensions
    BLOCKED_EXTENSIONS = [
        ".py",
        ".sh",
        ".bat",
        ".exe",
        ".dll",
        ".so",
        ".com",
        ".msi",
        ".app",
        ".js",
        ".html",
        ".php",
        ".rb",
        ".go",
        ".java",
        ".c",
        ".cpp",
        ".h",
    ]
    
    # Allowed extensions for write operations
    ALLOWED_WRITE_EXTENSIONS = [
        ".txt",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".csv",
        ".log",
        ".data",
        ".config",
    ]
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None,
                 blocked_extensions: Optional[List[str]] = None):
        """
        Initialize FileTools.
        
        Args:
            allowed_dirs: List of allowed directories
            blocked_extensions: List of blocked file extensions
        """
        if allowed_dirs:
            self.ALLOWED_DIRS = allowed_dirs
        if blocked_extensions:
            self.BLOCKED_EXTENSIONS = blocked_extensions
    
    def _is_safe_path(self, path: str) -> bool:
        """
        Check if a path is safe to access.
        
        Args:
            path: File path to check
            
        Returns:
            True if path is safe
        """
        path = str(path).strip()
        if not path:
            return False
        
        # Check for path traversal
        if ".." in path or path.startswith("/") or path.startswith("\\"):
            # Only allow specific absolute paths
            if path.startswith("/tmp") or path.startswith("temp"):
                return True
            return False
        
        # Check if path is in allowed directories
        for allowed_dir in self.ALLOWED_DIRS:
            if path.startswith(allowed_dir + "/") or path.startswith(allowed_dir + "\\"):
                return True
            if path == allowed_dir:
                return True
        
        return False
    
    def _is_safe_extension(self, path: str, for_write: bool = False) -> bool:
        """
        Check if a file extension is safe.
        
        Args:
            path: File path
            for_write: Whether this is for write operation
            
        Returns:
            True if extension is safe
        """
        path = str(path).lower()
        
        # Extract extension
        if "." in path:
            ext = "." + path.rsplit(".", 1)[-1]
        else:
            ext = ""
        
        # Check blocked extensions
        if ext in [e.lower() for e in self.BLOCKED_EXTENSIONS]:
            return False
        
        # For write operations, check allowed extensions
        if for_write and ext not in [e.lower() for e in self.ALLOWED_WRITE_EXTENSIONS]:
            return False
        
        return True
    
    def read_text_file(self, path: str, max_chars: int = 10000) -> Dict[str, Any]:
        """
        Read a text file.
        
        Args:
            path: Path to the file
            max_chars: Maximum characters to read
            
        Returns:
            Dictionary with content or error
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        if not self._is_safe_extension(path):
            return {"success": False, "error": "Access denied: blocked file extension"}
        
        try:
            full_path = Path(path)
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not full_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars)
            
            return {
                "success": True,
                "path": str(full_path),
                "content": content,
                "size": len(content),
                "truncated": len(content) >= max_chars
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_text_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write a text file.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            Dictionary with success status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        if not self._is_safe_extension(path, for_write=True):
            return {"success": False, "error": "Access denied: blocked file extension for writing"}
        
        try:
            full_path = Path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(str(content))
            
            return {
                "success": True,
                "path": str(full_path),
                "bytes_written": len(content.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def append_text_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Append content to a text file.
        
        Args:
            path: Path to the file
            content: Content to append
            
        Returns:
            Dictionary with success status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        if not self._is_safe_extension(path, for_write=True):
            return {"success": False, "error": "Access denied: blocked file extension for writing"}
        
        try:
            full_path = Path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(str(content))
            
            return {
                "success": True,
                "path": str(full_path),
                "bytes_appended": len(content.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with success status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        try:
            full_path = Path(path)
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not full_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            full_path.unlink()
            
            return {"success": True, "path": str(full_path), "message": "File deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
        """
        List directory contents.
        
        Args:
            path: Directory path
            recursive: Whether to list recursively
            
        Returns:
            Dictionary with directory listing
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        try:
            full_path = Path(path)
            if not full_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            if not full_path.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}
            
            files = []
            dirs = []
            
            for item in full_path.iterdir():
                if recursive and item.is_dir():
                    subdir_files = self.list_directory(str(item), recursive=True)
                    if subdir_files.get("success"):
                        files.extend(subdir_files.get("files", []))
                        dirs.extend(subdir_files.get("dirs", []))
                    continue
                
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(full_path)),
                        "size": item.stat().st_size,
                        "is_file": True,
                        "is_dir": False
                    })
                elif item.is_dir():
                    dirs.append({
                        "name": item.name,
                        "path": str(item.relative_to(full_path)),
                        "is_file": False,
                        "is_dir": True
                    })
            
            return {
                "success": True,
                "path": str(full_path),
                "files": files,
                "dirs": dirs,
                "total_files": len(files),
                "total_dirs": len(dirs)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_files(self, path: str = ".", pattern: str = "*", recursive: bool = True) -> Dict[str, Any]:
        """
        Search for files matching a pattern.
        
        Args:
            path: Directory to search in
            pattern: File pattern (e.g., "*.txt")
            recursive: Whether to search recursively
            
        Returns:
            Dictionary with matching files
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        try:
            full_path = Path(path)
            if not full_path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            matches = []
            
            if recursive:
                for file_path in full_path.rglob(pattern):
                    if file_path.is_file():
                        matches.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(full_path)),
                            "size": file_path.stat().st_size
                        })
            else:
                for file_path in full_path.glob(pattern):
                    if file_path.is_file():
                        matches.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(full_path)),
                            "size": file_path.stat().st_size
                        })
            
            return {
                "success": True,
                "path": str(full_path),
                "pattern": pattern,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get file metadata.
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Access denied: path not in allowed directories"}
        
        try:
            full_path = Path(path)
            if not full_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            stat = full_path.stat()
            
            return {
                "success": True,
                "path": str(full_path),
                "name": full_path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime,
                "is_file": full_path.is_file(),
                "is_dir": full_path.is_dir(),
                "extension": full_path.suffix if full_path.is_file() else ""
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
file_tools = FileTools()


def create_file_tools(allowed_dirs: Optional[List[str]] = None,
                      blocked_extensions: Optional[List[str]] = None) -> FileTools:
    """
    Create a FileTools instance.
    
    Args:
        allowed_dirs: List of allowed directories
        blocked_extensions: List of blocked file extensions
        
    Returns:
        FileTools instance
    """
    return FileTools(allowed_dirs, blocked_extensions)
