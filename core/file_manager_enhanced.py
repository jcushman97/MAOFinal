"""
Enhanced File Management for MAOS Agents

Provides secure file creation and management for agent-generated artifacts.
Ensures agents can create actual deliverable files (HTML, CSS, JS, etc.) with improved
code extraction capabilities.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import re
import hashlib
from datetime import datetime

from core.logger import get_logger
from core.state import ProjectState

logger = get_logger("file_manager_enhanced")


class FileManagerEnhanced:
    """
    Enhanced file manager with improved code extraction and artifact processing.
    
    Provides secure file operations that allow agents to create
    actual deliverable files while maintaining security boundaries.
    """
    
    def __init__(self, project_state: ProjectState, base_dir: Path):
        """Initialize enhanced file manager for a project."""
        self.project_state = project_state
        self.project_dir = base_dir / project_state.projectId
        self.artifacts_dir = self.project_dir / "artifacts" 
        self.deliverables_dir = self.project_dir / "deliverables"
        
        # Create directories
        self.deliverables_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enhanced FileManager initialized for project {project_state.projectId}")
    
    def create_deliverable_file(
        self, 
        filename: str, 
        content: str, 
        file_type: str = "auto"
    ) -> Path:
        """
        Create a deliverable file (HTML, CSS, JS, etc.) from agent output.
        
        Args:
            filename: Name of file to create
            content: File content
            file_type: Type of file (html, css, js, py, auto)
            
        Returns:
            Path to created file
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Auto-detect file type if needed
        if file_type == "auto":
            file_type = self._detect_file_type(safe_filename, content)
        
        # Create file path
        file_path = self.deliverables_dir / safe_filename
        
        try:
            # Write file with appropriate encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created deliverable file: {safe_filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to create deliverable file {safe_filename}: {e}")
            raise
    
    def extract_code_from_artifact(self, artifact_content: str) -> Dict[str, str]:
        """
        Enhanced code extraction from agent artifact text.
        
        Args:
            artifact_content: Raw artifact content from agent
            
        Returns:
            Dictionary of {filename: content} for extracted code
        """
        extracted_files = {}
        
        # Multiple extraction strategies
        strategies = [
            self._extract_code_blocks,
            self._extract_inline_html,
            self._extract_inline_css,
            self._extract_inline_javascript,
            self._extract_permission_requests
        ]
        
        for strategy in strategies:
            files = strategy(artifact_content)
            for filename, content in files.items():
                if filename not in extracted_files and content.strip():
                    extracted_files[filename] = content.strip()
        
        return extracted_files
    
    def _extract_code_blocks(self, content: str) -> Dict[str, str]:
        """Extract code from markdown-style code blocks."""
        files = {}
        
        # Pattern to match code blocks with language
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for language, code in matches:
            if code.strip():
                filename = self._generate_filename(language or 'text', files)
                files[filename] = code
        
        return files
    
    def _extract_inline_html(self, content: str) -> Dict[str, str]:
        """Extract HTML content from various formats."""
        files = {}
        
        # Look for HTML patterns
        html_patterns = [
            r'<!DOCTYPE[^>]*>.*?</html>',
            r'<html[^>]*>.*?</html>',
            r'<(!DOCTYPE html>)?[^<]*<html[^>]*>.*?</html>'
        ]
        
        for pattern in html_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 50:
                    filename = self._generate_filename('html', files)
                    files[filename] = match
        
        return files
    
    def _extract_inline_css(self, content: str) -> Dict[str, str]:
        """Extract CSS content from various formats."""
        files = {}
        
        # Look for CSS patterns (selectors and rules)
        css_patterns = [
            r'([.#]?\w+\s*{[^}]*}(?:\s*[.#]?\w+\s*{[^}]*})*)',
            r'(body\s*{[^}]*}(?:\s*[.#]?\w+\s*{[^}]*})*)',
            r'(\*\s*{[^}]*}(?:\s*[.#]?\w+\s*{[^}]*})*)'
        ]
        
        for pattern in css_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if match and len(match.strip()) > 30 and '{' in match and '}' in match:
                    filename = self._generate_filename('css', files)
                    files[filename] = match
        
        return files
    
    def _extract_inline_javascript(self, content: str) -> Dict[str, str]:
        """Extract JavaScript content from various formats."""
        files = {}
        
        # Look for JavaScript patterns
        js_patterns = [
            r'((?:function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+)[^;]*(?:[^}]*})?[^;]*;?(?:\s*(?:function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+)[^;]*(?:[^}]*})?[^;]*;?)*)',
            r'(class\s+\w+[^}]*})',
            r'(document\.\w+[^;]*;(?:[^;]*;)*)',
            r'(window\.\w+[^;]*;(?:[^;]*;)*)'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if match and len(match.strip()) > 30:
                    filename = self._generate_filename('js', files)
                    files[filename] = match
        
        return files
    
    def _extract_permission_requests(self, content: str) -> Dict[str, str]:
        """Handle cases where agents mention code but don't provide it."""
        files = {}
        
        # Look for permission requests or incomplete implementations
        if any(phrase in content.lower() for phrase in [
            "permission to write",
            "need permissions", 
            "once permissions are granted",
            "would you like me to save",
            "ready to be saved"
        ]):
            # Agent mentioned code but couldn't write it - try to extract any code snippets
            # Look for any structured content that looks like code
            code_hints = re.findall(r'(?:html|css|javascript|js).*?(?:code|content|implementation)[^:]*:?\s*([^.!?]*)', 
                                  content, re.IGNORECASE | re.DOTALL)
            
            for hint in code_hints:
                if hint and len(hint.strip()) > 20:
                    # Try to determine what type of code this might be
                    if 'html' in hint.lower():
                        filename = self._generate_filename('html', files)
                        # Create a minimal HTML structure
                        files[filename] = f"<!-- Agent mentioned HTML code but couldn't write due to permissions -->\n{hint}"
                    elif 'css' in hint.lower():
                        filename = self._generate_filename('css', files)
                        files[filename] = f"/* Agent mentioned CSS code but couldn't write due to permissions */\n{hint}"
                    elif 'javascript' in hint.lower() or 'js' in hint.lower():
                        filename = self._generate_filename('js', files)
                        files[filename] = f"// Agent mentioned JavaScript code but couldn't write due to permissions\n{hint}"
        
        return files
    
    def _generate_filename(self, language: str, existing_files: Dict[str, str]) -> str:
        """Generate appropriate filename based on language/type."""
        extension_map = {
            'html': '.html',
            'css': '.css', 
            'javascript': '.js',
            'js': '.js',
            'python': '.py',
            'py': '.py',
            'text': '.txt'
        }
        
        extension = extension_map.get(language.lower(), f'.{language}' if language else '.txt')
        
        # Use preferred filenames for first occurrence
        preferred_names = {
            '.html': 'index.html',
            '.css': 'styles.css',
            '.js': 'script.js',
            '.py': 'main.py'
        }
        
        if extension in preferred_names and preferred_names[extension] not in existing_files:
            return preferred_names[extension]
        
        # Generate numbered filename if preferred name exists
        base_name = f"code{extension}"
        counter = 1
        while base_name in existing_files:
            name, ext = base_name.rsplit('.', 1)
            base_name = f"{name}_{counter}.{ext}"
            counter += 1
            
        return base_name
    
    def process_task_artifacts(self, task_id: str) -> List[Path]:
        """
        Process all artifacts for a task and create deliverable files.
        
        Args:
            task_id: ID of task to process
            
        Returns:
            List of created deliverable file paths
        """
        created_files = []
        
        # Find task
        task = self.project_state.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return created_files
        
        # Process each artifact
        for artifact_path_str in task.artifacts:
            artifact_path = Path(artifact_path_str)
            
            if artifact_path.exists():
                try:
                    # Read artifact content
                    with open(artifact_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract code from artifact with enhanced extraction
                    extracted_code = self.extract_code_from_artifact(content)
                    
                    # Create deliverable files
                    for filename, code in extracted_code.items():
                        file_path = self.create_deliverable_file(filename, code)
                        created_files.append(file_path)
                        
                        logger.info(f"Enhanced extraction: Created {filename} from task {task_id}")
                
                except Exception as e:
                    logger.error(f"Failed to process artifact {artifact_path}: {e}")
        
        return created_files
    
    def create_project_summary(self) -> Path:
        """Create a summary file with links to all deliverables."""
        summary_content = f"""# Project: {self.project_state.objective}

**Project ID:** {self.project_state.projectId}
**Status:** {self.project_state.status}
**Created:** {datetime.fromtimestamp(self.project_state.createdAt)}

## Deliverable Files:
"""
        
        # List all deliverable files
        if self.deliverables_dir.exists():
            for file_path in self.deliverables_dir.iterdir():
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_dir)
                    summary_content += f"- [{file_path.name}](./{relative_path})\n"
        
        summary_content += f"""
## Task Status:
"""
        
        # List task completion status
        for task in self.project_state.tasks:
            status_icon = "[PASS]" if task.status == "complete" else "[PROGRESS]" if task.status == "in_progress" else "[PENDING]"
            summary_content += f"- {status_icon} {task.description} ({task.team})\n"
        
        # Create summary file
        summary_path = self.project_dir / "README.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        logger.info("Created enhanced project summary")
        return summary_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe creation."""
        # Remove potentially dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Ensure reasonable length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        # Ensure it has an extension
        if '.' not in filename:
            filename += '.txt'
        
        return filename
    
    def _detect_file_type(self, filename: str, content: str) -> str:
        """Detect file type from filename and content."""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        if filename_lower.endswith('.html') or '<html>' in content_lower or '<!doctype' in content_lower:
            return 'html'
        elif filename_lower.endswith('.css') or any(pattern in content_lower for pattern in ['body {', '* {', '.', '#']):
            return 'css'
        elif filename_lower.endswith('.js') or any(pattern in content_lower for pattern in ['function(', 'const ', 'let ', 'var ']):
            return 'js'
        elif filename_lower.endswith('.py') or 'def ' in content_lower:
            return 'py'
        else:
            return 'text'
    
    def get_deliverables(self) -> List[Dict[str, Any]]:
        """Get list of all deliverable files with metadata."""
        deliverables = []
        
        if self.deliverables_dir.exists():
            for file_path in self.deliverables_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    deliverables.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'type': self._detect_file_type(file_path.name, '')
                    })
        
        return deliverables