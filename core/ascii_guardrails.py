"""
ASCII Guardrails System for MAOS

Prevents Unicode/emoji/non-ASCII characters in code generation to ensure
compatibility with Windows CLI and subprocess communication.
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ASCIIViolation:
    """Represents a non-ASCII character violation."""
    line_number: int
    column: int
    character: str
    unicode_code: str
    suggestion: Optional[str] = None


class ASCIIGuardrails:
    """
    ASCII-only enforcement system for code generation.
    
    Prevents Unicode characters, emojis, and non-ASCII symbols that can
    cause encoding issues in Windows CLI subprocess communication.
    """
    
    def __init__(self):
        """Initialize ASCII guardrails."""
        self.enabled = True
        self.strict_mode = True  # Reject any non-ASCII characters
        self.replacement_map = {
            # Common Unicode replacements for code  
            '\u2192': '->',      # Arrow to ASCII arrow
            '\u2190': '<-',      # Left arrow 
            '\u21D2': '=>',      # Double arrow
            '\u2264': '<=',      # Less than or equal
            '\u2265': '>=',      # Greater than or equal
            '\u2260': '!=',      # Not equal
            '\u2261': '==',      # Equivalent
            '\u2234': '// therefore',
            '\u2235': '// because',
            
            # Status symbols to text
            '\u2705': '[PASS]',
            '\u274C': '[FAIL]',
            '\u26A0\uFE0F': '[WARN]',
            '\u26A0': '[WARN]',
            '\U0001F504': '[PROGRESS]',
            '\U0001F4CB': '[INFO]',
            '\u23F3': '[PENDING]',
            '\U0001F3AF': '[TARGET]',
            '\U0001F6A8': '[ALERT]',
            '\U0001F4A1': '[IDEA]',
            '\U0001F4CA': '[DATA]',
            '\U0001F50D': '[SEARCH]',
            '\u2B50': '[STAR]',
            '\U0001F389': '[SUCCESS]',
            '\U0001F4A5': '[ERROR]',
            '\u2713': 'OK',
            '\u2717': 'X',
            '\u2139': 'i',
            
            # UI symbols
            '\U0001F4C4': '[DOC]',
            '\U0001F680': '[START]',
            '\U0001F527': '[CONFIG]',
            '\u23F9\uFE0F': '[STOP]',
            '\u23F9': '[STOP]',
            '\U0001F9EA': '[TEST]',
            '\U0001F4C1': '[FOLDER]',
            '\U0001F310': '[WEB]',
            '\U0001F4F1': '[MOBILE]'
        }
        
        # File types to check
        self.code_extensions = {'.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.yml', '.yaml'}
        
    def validate_content(self, content: str, filename: str = "") -> Tuple[bool, List[ASCIIViolation]]:
        """
        Validate content for ASCII-only compliance.
        
        Args:
            content: Content to validate
            filename: Optional filename for context
            
        Returns:
            (is_valid, violations_list)
        """
        if not self.enabled:
            return True, []
        
        violations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line, 1):
                if ord(char) > 127:  # Non-ASCII character
                    violation = ASCIIViolation(
                        line_number=line_num,
                        column=col_num,
                        character=char,
                        unicode_code=f"U+{ord(char):04X}",
                        suggestion=self.replacement_map.get(char)
                    )
                    violations.append(violation)
        
        is_valid = len(violations) == 0
        
        if violations:
            logger.warning(f"ASCII violations found in {filename or 'content'}: {len(violations)} characters")
            
        return is_valid, violations
    
    def sanitize_content(self, content: str, mode: str = "replace") -> str:
        """
        Sanitize content by removing or replacing non-ASCII characters.
        
        Args:
            content: Content to sanitize
            mode: "replace" (use replacement map) or "remove" (strip out)
            
        Returns:
            Sanitized content
        """
        if not self.enabled:
            return content
        
        if mode == "replace":
            # Replace known characters with ASCII equivalents
            for unicode_char, ascii_replacement in self.replacement_map.items():
                content = content.replace(unicode_char, ascii_replacement)
            
            # Remove any remaining non-ASCII characters
            content = ''.join(char for char in content if ord(char) <= 127)
            
        elif mode == "remove":
            # Simply remove all non-ASCII characters
            content = ''.join(char for char in content if ord(char) <= 127)
        
        return content
    
    def enforce_ascii_generation(self, agent_prompt: str) -> str:
        """
        Add ASCII-only enforcement to agent prompts.
        
        Args:
            agent_prompt: Original agent prompt
            
        Returns:
            Enhanced prompt with ASCII enforcement
        """
        ascii_enforcement = """

CRITICAL ASCII-ONLY REQUIREMENT:
- Generate ONLY ASCII characters (codes 0-127)
- NO Unicode symbols, emojis, or extended characters
- NO arrows like → ← ⇒, use -> <- => instead
- NO check marks ✅ or X marks ❌, use [PASS] [FAIL] instead
- NO status emojis 🔄 📋 ⚠️, use [PROGRESS] [INFO] [WARN] instead
- This prevents Windows CLI encoding errors

ASCII Status Symbols to Use:
- [PASS] instead of ✅
- [FAIL] instead of ❌  
- [WARN] instead of ⚠️
- [PROGRESS] instead of 🔄
- [INFO] instead of 📋
- [PENDING] instead of ⏳

ASCII Arrows to Use:
- -> instead of →
- <- instead of ←
- => instead of ⇒
- <= instead of ≤
- >= instead of ≥
- != instead of ≠

VERIFY: All output must pass ASCII-only validation before submission.
"""
        return agent_prompt + ascii_enforcement
    
    def validate_agent_output(self, output: str, agent_name: str = "") -> Tuple[bool, str]:
        """
        Validate and sanitize agent output for ASCII compliance.
        
        Args:
            output: Agent output to validate
            agent_name: Name of agent for logging
            
        Returns:
            (is_valid, sanitized_output)
        """
        is_valid, violations = self.validate_content(output, f"{agent_name} output")
        
        if violations:
            logger.warning(f"Agent {agent_name} generated {len(violations)} non-ASCII characters")
            
            # Log detailed violations
            for violation in violations[:10]:  # Limit to first 10
                logger.warning(
                    f"  Line {violation.line_number}, Col {violation.column}: "
                    f"'{violation.character}' ({violation.unicode_code})"
                    + (f" -> Suggest: '{violation.suggestion}'" if violation.suggestion else "")
                )
            
            # Sanitize the output
            sanitized = self.sanitize_content(output, mode="replace")
            return False, sanitized
        
        return True, output
    
    def get_file_validation_report(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Generate detailed validation report for a file.
        
        Args:
            file_path: Path to file being validated
            content: File content
            
        Returns:
            Validation report dictionary
        """
        is_valid, violations = self.validate_content(content, file_path)
        
        report = {
            "file_path": file_path,
            "is_valid": is_valid,
            "violation_count": len(violations),
            "violations": [],
            "sanitized_content": self.sanitize_content(content) if violations else content
        }
        
        for violation in violations:
            report["violations"].append({
                "line": violation.line_number,
                "column": violation.column,
                "character": violation.character,
                "unicode_code": violation.unicode_code,
                "suggestion": violation.suggestion
            })
        
        return report
    
    def create_agent_wrapper(self, original_agent_class):
        """
        Create ASCII-enforced wrapper for agent classes.
        
        Args:
            original_agent_class: Original agent class to wrap
            
        Returns:
            Wrapped agent class with ASCII enforcement
        """
        class ASCIIEnforcedAgent(original_agent_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.guardrails = ASCIIGuardrails()
            
            async def execute_task(self, task):
                """Execute task with ASCII enforcement."""
                # Enhance prompts with ASCII requirements
                if hasattr(self, 'prompts'):
                    for key, prompt in self.prompts.items():
                        self.prompts[key] = self.guardrails.enforce_ascii_generation(prompt)
                
                # Execute original task
                result = await super().execute_task(task)
                
                # Validate any generated content
                if hasattr(task, 'output') and task.output:
                    is_valid, sanitized = self.guardrails.validate_agent_output(
                        task.output, 
                        self.__class__.__name__
                    )
                    if not is_valid:
                        task.output = sanitized
                        logger.info(f"Sanitized output for {self.__class__.__name__}")
                
                return result
        
        return ASCIIEnforcedAgent


# Global guardrails instance
ascii_guardrails = ASCIIGuardrails()


def validate_file_content(file_path: str, content: str) -> Dict[str, Any]:
    """Convenience function for file validation."""
    return ascii_guardrails.get_file_validation_report(file_path, content)


def sanitize_for_cli(content: str) -> str:
    """Convenience function for CLI-safe sanitization."""
    return ascii_guardrails.sanitize_content(content, mode="replace")


def enforce_ascii_prompt(prompt: str) -> str:
    """Convenience function for prompt enhancement."""
    return ascii_guardrails.enforce_ascii_generation(prompt)