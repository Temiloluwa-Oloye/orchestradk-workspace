"""
File operations utilities for OrchestrADK.

Provides helper functions for file and directory management.
"""

import os
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object for the directory
        
    Raises:
        OSError: If directory creation fails
    """
    path_obj = Path(path)
    
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path_obj}")
        return path_obj
    except OSError as e:
        logger.error(f"Failed to create directory {path_obj}: {str(e)}")
        raise


def write_file(path: Union[str, Path], content: str) -> None:
    """
    Write content to a file.
    
    Args:
        path: File path to write to
        content: Content to write
        
    Raises:
        OSError: If file write fails
    """
    path_obj = Path(path)
    
    try:
        # Ensure parent directory exists
        ensure_directory(path_obj.parent)
        
        # Write content
        path_obj.write_text(content, encoding='utf-8')
        logger.debug(f"Wrote file: {path_obj}")
    except OSError as e:
        logger.error(f"Failed to write file {path_obj}: {str(e)}")
        raise


def read_file(path: Union[str, Path]) -> str:
    """
    Read content from a file.
    
    Args:
        path: File path to read from
        
    Returns:
        File content as string
        
    Raises:
        OSError: If file read fails
        FileNotFoundError: If file doesn't exist
    """
    path_obj = Path(path)
    
    try:
        content = path_obj.read_text(encoding='utf-8')
        logger.debug(f"Read file: {path_obj}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {path_obj}")
        raise
    except OSError as e:
        logger.error(f"Failed to read file {path_obj}: {str(e)}")
        raise


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists.
    
    Args:
        path: File path to check
        
    Returns:
        True if file exists, False otherwise
    """
    return Path(path).is_file()


def directory_exists(path: Union[str, Path]) -> bool:
    """
    Check if a directory exists.
    
    Args:
        path: Directory path to check
        
    Returns:
        True if directory exists, False otherwise
    """
    return Path(path).is_dir()


def delete_file(path: Union[str, Path]) -> None:
    """
    Delete a file.
    
    Args:
        path: File path to delete
        
    Raises:
        OSError: If file deletion fails
    """
    path_obj = Path(path)
    
    try:
        if path_obj.is_file():
            path_obj.unlink()
            logger.debug(f"Deleted file: {path_obj}")
    except OSError as e:
        logger.error(f"Failed to delete file {path_obj}: {str(e)}")
        raise


def list_files(directory: Union[str, Path], pattern: str = "*") -> list[Path]:
    """
    List files in a directory matching a pattern.
    
    Args:
        directory: Directory to list files from
        pattern: Glob pattern to match (default: "*")
        
    Returns:
        List of Path objects for matching files
    """
    dir_obj = Path(directory)
    
    if not dir_obj.is_dir():
        logger.warning(f"Directory does not exist: {dir_obj}")
        return []
    
    return list(dir_obj.glob(pattern))


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        path: File path
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path_obj = Path(path)
    
    if not path_obj.is_file():
        raise FileNotFoundError(f"File not found: {path_obj}")
    
    return path_obj.stat().st_size


# Made with Bob