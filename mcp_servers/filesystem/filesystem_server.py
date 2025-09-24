#!/usr/bin/env python3
"""
Filesystem MCP Server using FastMCP
Provides tools for reading, writing, and managing files and directories.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Filesystem Server")

# Configuration - allowed root directories
ALLOWED_ROOTS = [
    Path.cwd(),  # Current working directory
    Path.home() / "Documents",  # User documents
    Path("/tmp") if os.name != "nt" else Path.cwd() / "temp",  # Temp directory
]

def is_path_allowed(file_path: str) -> bool:
    """Check if the given path is within allowed directories"""
    try:
        path = Path(file_path).resolve()
        for root in ALLOWED_ROOTS:
            try:
                path.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False

def safe_path(file_path: str) -> Path:
    """Get a safe path object, raising error if not allowed"""
    if not is_path_allowed(file_path):
        raise ValueError(f"Access denied: Path '{file_path}' is outside allowed directories")
    return Path(file_path).resolve()

@mcp.tool()
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        encoding: Text encoding to use (default: utf-8)
    
    Returns:
        File contents as string
    """
    try:
        path = safe_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"
        
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"
        
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        encoding: Text encoding to use (default: utf-8)
        create_dirs: Whether to create parent directories if they don't exist
    
    Returns:
        Success or error message
    """
    try:
        path = safe_path(file_path)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def append_file(file_path: str, content: str, encoding: str = "utf-8") -> str:
    """
    Append content to a file.
    
    Args:
        file_path: Path to the file to append to
        content: Content to append to the file
        encoding: Text encoding to use (default: utf-8)
    
    Returns:
        Success or error message
    """
    try:
        path = safe_path(file_path)
        
        with open(path, 'a', encoding=encoding) as f:
            f.write(content)
        
        return f"Successfully appended {len(content)} characters to '{file_path}'"
    except Exception as e:
        return f"Error appending to file: {str(e)}"

@mcp.tool()
def list_directory(directory_path: str, show_hidden: bool = False) -> str:
    """
    List contents of a directory.
    
    Args:
        directory_path: Path to the directory to list
        show_hidden: Whether to show hidden files (starting with .)
    
    Returns:
        JSON string with directory contents
    """
    try:
        path = safe_path(directory_path)
        
        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist"
        
        if not path.is_dir():
            return f"Error: '{directory_path}' is not a directory"
        
        items = []
        for item in path.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
            
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "modified": item.stat().st_mtime
            }
            items.append(item_info)
        
        # Sort: directories first, then files, both alphabetically
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        
        return json.dumps({
            "directory": str(path),
            "items": items,
            "total_items": len(items)
        }, indent=2)
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def create_directory(directory_path: str, parents: bool = True) -> str:
    """
    Create a new directory.
    
    Args:
        directory_path: Path to the directory to create
        parents: Whether to create parent directories if they don't exist
    
    Returns:
        Success or error message
    """
    try:
        path = safe_path(directory_path)
        
        if path.exists():
            return f"Error: Directory '{directory_path}' already exists"
        
        path.mkdir(parents=parents, exist_ok=False)
        return f"Successfully created directory '{directory_path}'"
        
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
def delete_file(file_path: str) -> str:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file to delete
    
    Returns:
        Success or error message
    """
    try:
        path = safe_path(file_path)
        
        if not path.exists():
            return f"Error: File '{file_path}' does not exist"
        
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"
        
        path.unlink()
        return f"Successfully deleted file '{file_path}'"
        
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@mcp.tool()
def delete_directory(directory_path: str, recursive: bool = False) -> str:
    """
    Delete a directory.
    
    Args:
        directory_path: Path to the directory to delete
        recursive: Whether to delete non-empty directories recursively
    
    Returns:
        Success or error message
    """
    try:
        path = safe_path(directory_path)
        
        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist"
        
        if not path.is_dir():
            return f"Error: '{directory_path}' is not a directory"
        
        if recursive:
            import shutil
            shutil.rmtree(path)
        else:
            path.rmdir()  # Only works if empty
        
        return f"Successfully deleted directory '{directory_path}'"
        
    except Exception as e:
        return f"Error deleting directory: {str(e)}"

@mcp.tool()
def file_info(file_path: str) -> str:
    """
    Get detailed information about a file or directory.
    
    Args:
        file_path: Path to the file or directory
    
    Returns:
        JSON string with file information
    """
    try:
        path = safe_path(file_path)
        
        if not path.exists():
            return f"Error: Path '{file_path}' does not exist"
        
        stat = path.stat()
        info = {
            "path": str(path),
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "permissions": oct(stat.st_mode)[-3:],
            "is_hidden": path.name.startswith('.'),
        }
        
        if path.is_file():
            info["extension"] = path.suffix
        
        return json.dumps(info, indent=2)
        
    except Exception as e:
        return f"Error getting file info: {str(e)}"

@mcp.tool()
def search_files(directory_path: str, pattern: str, recursive: bool = True) -> str:
    """
    Search for files matching a pattern in a directory.
    
    Args:
        directory_path: Directory to search in
        pattern: Glob pattern to match (e.g., "*.txt", "**/*.py")
        recursive: Whether to search recursively in subdirectories
    
    Returns:
        JSON string with matching files
    """
    try:
        path = safe_path(directory_path)
        
        if not path.exists():
            return f"Error: Directory '{directory_path}' does not exist"
        
        if not path.is_dir():
            return f"Error: '{directory_path}' is not a directory"
        
        if recursive and not pattern.startswith("**/"):
            pattern = f"**/{pattern}"
        
        matches = list(path.glob(pattern))
        
        # Filter to only allowed paths
        allowed_matches = []
        for match in matches:
            if is_path_allowed(str(match)):
                allowed_matches.append({
                    "path": str(match),
                    "name": match.name,
                    "type": "directory" if match.is_dir() else "file",
                    "size": match.stat().st_size if match.is_file() else None
                })
        
        return json.dumps({
            "search_directory": str(path),
            "pattern": pattern,
            "matches": allowed_matches,
            "total_matches": len(allowed_matches)
        }, indent=2)
        
    except Exception as e:
        return f"Error searching files: {str(e)}"

@mcp.tool()
def get_allowed_directories() -> str:
    """
    Get list of allowed root directories for file operations.
    
    Returns:
        JSON string with allowed directories
    """
    allowed_dirs = []
    for root in ALLOWED_ROOTS:
        try:
            resolved = root.resolve()
            if resolved.exists():
                allowed_dirs.append({
                    "path": str(resolved),
                    "exists": True,
                    "writable": os.access(resolved, os.W_OK)
                })
        except Exception:
            allowed_dirs.append({
                "path": str(root),
                "exists": False,
                "writable": False
            })
    
    return json.dumps({
        "allowed_directories": allowed_dirs,
        "note": "File operations are restricted to these directories and their subdirectories"
    }, indent=2)

# Resource for current working directory
@mcp.resource("file://cwd")
def current_working_directory() -> str:
    """Current working directory information"""
    cwd = Path.cwd()
    return json.dumps({
        "current_directory": str(cwd),
        "exists": cwd.exists(),
        "is_allowed": is_path_allowed(str(cwd))
    }, indent=2)

if __name__ == "__main__":
    # Add custom allowed directories from command line args
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            try:
                custom_path = Path(arg).resolve()
                if custom_path.exists() and custom_path.is_dir():
                    ALLOWED_ROOTS.append(custom_path)
                    print(f"Added allowed directory: {custom_path}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Could not add directory '{arg}': {e}", file=sys.stderr)
    
    # Print allowed directories to stderr for debugging
    print("Filesystem MCP Server starting...", file=sys.stderr)
    print(f"Allowed directories:", file=sys.stderr)
    for root in ALLOWED_ROOTS:
        print(f"  - {root}", file=sys.stderr)
    
    # Run the server
    mcp.run()