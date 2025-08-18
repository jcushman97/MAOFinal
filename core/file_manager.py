"""
File Management for MAOS Agents (Deprecated - Use file_manager_enhanced.py)

This file is kept for backwards compatibility but is no longer used.
All new code should use FileManagerEnhanced for improved capabilities.
"""

# Import the enhanced version to maintain API compatibility
from .file_manager_enhanced import FileManagerEnhanced as FileManager

__all__ = ['FileManager']