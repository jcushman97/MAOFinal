"""
CLI Client for MAOS

Handles communication with LLM CLI tools through subprocess management
with proper timeout handling and error recovery.
"""

import asyncio
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile

from core.config import Config, ProviderConfig
from core.logger import get_logger

logger = get_logger("cli_client")


class CLIClientError(Exception):
    """Exception raised for CLI client errors."""
    pass


class CLIClient:
    """
    Manages communication with CLI-based LLM tools.
    
    Handles subprocess execution, timeout management, and output parsing
    for various LLM CLI interfaces.
    """
    
    def __init__(self, config: Config):
        """Initialize CLI client with configuration."""
        self.config = config
        
    async def call_model(
        self,
        model_name: str,
        prompt: str,
        expect_json: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call a specific model through its CLI interface.
        
        Args:
            model_name: Name of the model/provider to call
            prompt: Prompt text to send
            expect_json: Whether to expect JSON output
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with response and metadata
            
        Raises:
            CLIClientError: If model call fails
        """
        provider_config = self.config.get_provider_config(model_name)
        if not provider_config:
            raise CLIClientError(f"No configuration found for model: {model_name}")
        
        if timeout is None:
            timeout = provider_config.timeout
        
        # Optimize timeout based on prompt complexity
        optimized_timeout = self._optimize_timeout_for_prompt(prompt, timeout)
        
        logger.info(f"Calling model {model_name} with timeout {optimized_timeout}s")
        
        try:
            # Execute CLI command
            result = await self._execute_cli_command(
                provider_config=provider_config,
                prompt=prompt,
                timeout=optimized_timeout
            )
            
            # Debug: Log raw stdout for troubleshooting
            logger.debug(f"Raw stdout (length={len(result['stdout'])}): {result['stdout'][:300]}...")
            
            # Parse output based on configuration
            output = self._parse_cli_output(result["stdout"], provider_config)
            
            # Debug: Log parsed output
            logger.debug(f"Parsed output (length={len(output)}): {output[:300]}...")
            
            return {
                "output": output,
                "metadata": {
                    "model": model_name,
                    "execution_time": result.get("execution_time", 0),
                    "return_code": result.get("return_code", 0),
                    "tokens_used": self._estimate_tokens(prompt + output)
                }
            }
            
        except Exception as e:
            logger.error(f"Model call failed for {model_name}: {e}")
            raise CLIClientError(f"Model call failed: {e}")
    
    async def _execute_cli_command(
        self,
        provider_config: ProviderConfig,
        prompt: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Execute CLI command with proper subprocess management.
        
        Args:
            provider_config: Provider configuration
            prompt: Prompt text
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        import time
        start_time = time.time()
        
        # Build command
        cmd = provider_config.cmd + provider_config.extra_args + [prompt]
        
        logger.debug(f"Executing command: {' '.join(cmd[:2])} ...")  # Don't log full prompt
        
        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')
            
            logger.debug(f"Command completed in {execution_time:.2f}s with return code {process.returncode}")
            
            if process.returncode != 0:
                logger.error(f"CLI command failed with return code {process.returncode}")
                logger.error(f"STDERR: {stderr_text}")
                raise CLIClientError(f"CLI command failed: {stderr_text}")
            
            return {
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode,
                "execution_time": execution_time
            }
            
        except asyncio.TimeoutError:
            logger.error(f"CLI command timed out after {timeout}s")
            # Kill the process if it's still running
            if 'process' in locals() and process.returncode is None:
                process.kill()
                await process.wait()
            raise CLIClientError(f"CLI command timed out after {timeout}s")
        
        except Exception as e:
            logger.error(f"CLI command execution failed: {e}")
            raise CLIClientError(f"CLI command execution failed: {e}")
    
    def _parse_cli_output(self, output: str, provider_config: ProviderConfig) -> str:
        """
        Parse CLI output based on provider configuration.
        
        Args:
            output: Raw CLI output
            provider_config: Provider configuration with markers
            
        Returns:
            Parsed output text
        """
        if not output.strip():
            raise CLIClientError("Empty output from CLI command")
        
        # Handle JSON markers if configured
        if len(provider_config.json_markers) == 2:
            start_marker, end_marker = provider_config.json_markers
            
            if start_marker in output and end_marker in output:
                # Extract content between markers
                start_idx = output.find(start_marker) + len(start_marker)
                end_idx = output.find(end_marker)
                
                if start_idx >= 0 and end_idx >= 0 and end_idx > start_idx:
                    extracted = output[start_idx:end_idx].strip()
                    if extracted:
                        return extracted
        
        # Return full output if no markers found or extraction failed
        return output.strip()
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of token count.
        
        Uses a simple heuristic: ~4 characters per token on average.
        This is for tracking purposes only.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    async def test_model_connection(self, model_name: str) -> bool:
        """
        Test connection to a model with a simple prompt.
        
        Args:
            model_name: Name of model to test
            
        Returns:
            True if connection successful
        """
        try:
            result = await self.call_model(
                model_name=model_name,
                prompt="Hello, please respond with 'OK' to confirm you are working.",
                timeout=30
            )
            
            response = result["output"].lower()
            success = "ok" in response or "hello" in response
            
            if success:
                logger.info(f"Model {model_name} connection test successful")
            else:
                logger.warning(f"Model {model_name} responded but may not be working properly")
            
            return success
            
        except Exception as e:
            logger.error(f"Model {model_name} connection test failed: {e}")
            return False
    
    def _optimize_timeout_for_prompt(self, prompt: str, base_timeout: int) -> int:
        """
        Optimize timeout based on prompt complexity and content.
        
        Args:
            prompt: The prompt text to analyze
            base_timeout: Base timeout value
            
        Returns:
            Optimized timeout value
        """
        prompt_lower = prompt.lower()
        
        # Calculate complexity score
        complexity_score = 0
        
        # Length factor (longer prompts need more time)
        if len(prompt) > 1500:
            complexity_score += 1
        if len(prompt) > 3000:
            complexity_score += 1
            
        # Task complexity keywords that typically need more time
        complex_keywords = [
            "comprehensive", "detailed", "analyze", "implement", "create", "build",
            "generate", "design", "develop", "test", "debug", "optimize"
        ]
        complexity_score += sum(1 for keyword in complex_keywords if keyword in prompt_lower)
        
        # Simple task indicators (can reduce timeout)
        simple_keywords = ["simple", "basic", "quick", "brief", "short"]
        if any(keyword in prompt_lower for keyword in simple_keywords):
            complexity_score -= 1
            
        # Testing and debugging tasks often need more time
        if any(keyword in prompt_lower for keyword in ["test", "debug", "troubleshoot"]):
            complexity_score += 2
            
        # JSON requests might need extra parsing time
        if "json" in prompt_lower or "BEGIN_JSON" in prompt:
            complexity_score += 1
            
        # Code generation tasks
        if any(keyword in prompt_lower for keyword in ["code", "function", "class", "html", "css", "javascript"]):
            complexity_score += 1
            
        # Adjust timeout based on complexity score
        if complexity_score <= 0:
            # Simple tasks - reduce timeout
            return max(30, int(base_timeout * 0.6))
        elif complexity_score <= 2:
            # Normal complexity - use base timeout
            return base_timeout
        elif complexity_score <= 4:
            # Complex tasks - increase timeout moderately
            return int(base_timeout * 1.3)
        else:
            # Very complex tasks - increase timeout significantly but cap it
            return min(180, int(base_timeout * 1.6))