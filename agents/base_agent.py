"""
Base Agent Class for MAOS

Provides common functionality for all agent types in the hierarchical system.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.config import Config, ProviderConfig
from core.state import ProjectState, Agent, AgentType, LogLevel, Task
from core.logger import get_logger
from core.ascii_guardrails import ascii_guardrails, enforce_ascii_prompt
from core.model_router import IntelligentModelRouter
from providers.cli_client import CLIClient

logger = get_logger("base_agent")


class BaseAgent(ABC):
    """
    Abstract base class for all MAOS agents.
    
    Provides common functionality including:
    - LLM communication through CLI wrappers
    - State management and logging
    - Error handling and retries
    - Token usage tracking
    """
    
    def __init__(
        self, 
        agent_id: str,
        agent_type: AgentType,
        config: Config,
        project_state: ProjectState,
        model_preference: Optional[str] = None
    ):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type of agent (PM, LEAD, WORKER)
            config: System configuration
            project_state: Current project state
            model_preference: Preferred LLM model, defaults to routing rules
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.project_state = project_state
        self.model_preference = model_preference
        
        # Initialize CLI client and model router
        self.cli_client = CLIClient(config)
        self.model_router = IntelligentModelRouter(config)
        
        # Register agent in project state if not exists
        if agent_id not in project_state.agents:
            project_state.agents[agent_id] = Agent(
                type=agent_type,
                model=self._get_preferred_model(),
                tokensUsed=0,
                callCount=0
            )
        
        # Initialize task tracking for intelligent routing
        self._current_task = None
        
        logger.info(f"Agent {agent_id} ({agent_type}) initialized")
    
    def _get_preferred_model(self) -> str:
        """Get the preferred model for this agent."""
        if self.model_preference:
            return self.model_preference
        # Default to general routing or claude
        return self.config.get_provider_for_task("general")
    
    async def call_llm(
        self, 
        prompt: str, 
        task_type: str = "general",
        expect_json: bool = False,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call LLM through CLI wrapper with retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            task_type: Type of task for routing (plan, python, etc.)
            expect_json: Whether to expect JSON response
            max_retries: Maximum retry attempts
            
        Returns:
            Dictionary with response data and metadata
        """
        if max_retries is None:
            max_retries = self.config.max_retries
        
        # Enhance prompt with ASCII-only enforcement
        enhanced_prompt = enforce_ascii_prompt(prompt)
        
        # Use intelligent model routing for optimal model selection
        if hasattr(self, '_current_task') and self._current_task:
            model_name, confidence = self.model_router.select_model_for_task(
                self._current_task, 
                preferred_model=self.model_preference
            )
            self._log(LogLevel.INFO, f"Intelligent routing selected {model_name} (confidence: {confidence:.2f})")
        else:
            # Fallback to preference or default routing
            model_name = self.model_preference or self.config.get_provider_for_task(task_type)
        
        self._log(LogLevel.INFO, f"Calling {model_name} for {task_type} task")
        
        for attempt in range(max_retries + 1):
            try:
                # Call CLI client with enhanced prompt
                result = await self.cli_client.call_model(
                    model_name=model_name,
                    prompt=enhanced_prompt,
                    expect_json=expect_json
                )
                
                # Validate and sanitize the response for ASCII compliance
                if 'response' in result:
                    is_valid, sanitized_response = ascii_guardrails.validate_agent_output(
                        result['response'], 
                        f"{self.agent_id}"
                    )
                    if not is_valid:
                        result['response'] = sanitized_response
                        self._log(LogLevel.WARNING, "Agent output sanitized for ASCII compliance")
                
                # Update agent statistics
                tokens_used = result.get('metadata', {}).get('tokens_used', 0)
                execution_time = result.get('metadata', {}).get('execution_time', 0)
                self.project_state.update_agent_stats(self.agent_id, tokens_used)
                
                # Update model router performance statistics
                if hasattr(self, '_current_task') and self._current_task:
                    self.model_router.update_model_performance(
                        model_name, 
                        self._current_task, 
                        success=True,
                        response_time=execution_time
                    )
                
                self._log(LogLevel.INFO, f"LLM call successful (attempt {attempt + 1})")
                return result
                
            except Exception as e:
                self._log(LogLevel.WARNING, f"LLM call failed (attempt {attempt + 1}): {e}")
                
                # Update model router with failure
                if hasattr(self, '_current_task') and self._current_task:
                    self.model_router.update_model_performance(
                        model_name, 
                        self._current_task, 
                        success=False
                    )
                
                if attempt < max_retries:
                    # Try fallback model on first failure if available
                    if attempt == 0 and hasattr(self, '_current_task') and self._current_task:
                        fallback_model = self.model_router.get_fallback_model(model_name, self._current_task)
                        if fallback_model and fallback_model != model_name:
                            self._log(LogLevel.INFO, f"Trying fallback model: {fallback_model}")
                            model_name = fallback_model
                    
                    # Exponential backoff
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    self._log(LogLevel.ERROR, f"LLM call failed after {max_retries + 1} attempts")
                    raise
        
        # Should not reach here, but just in case
        raise RuntimeError(f"LLM call failed after all retry attempts")
    
    def set_current_task(self, task: Optional[Task]):
        """Set the current task for intelligent routing context."""
        self._current_task = task
    
    def _log(self, level: LogLevel, message: str):
        """Log a message with agent context."""
        self.project_state.add_log_entry(level, self.agent_id, message)
    
    def _create_task_id(self) -> str:
        """Generate a unique task ID."""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}"
    
    def _format_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """
        Format a prompt template with context.
        
        Args:
            base_prompt: Base prompt template
            context: Context variables to substitute
            
        Returns:
            Formatted prompt string
        """
        try:
            return base_prompt.format(**context)
        except KeyError as e:
            self._log(LogLevel.ERROR, f"Missing template variable: {e}")
            raise ValueError(f"Prompt template missing variable: {e}")
    
    async def _validate_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Validate and extract JSON from response.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed JSON data
        """
        json_text = ""
        try:
            # Look for JSON markers if present
            start_marker = "BEGIN_JSON"
            end_marker = "END_JSON"
            
            if start_marker in response_text and end_marker in response_text:
                start_idx = response_text.find(start_marker) + len(start_marker)
                end_idx = response_text.find(end_marker)
                json_text = response_text[start_idx:end_idx].strip()
            else:
                # Try to parse entire response as JSON
                json_text = response_text.strip()
            
            if not json_text:
                self._log(LogLevel.ERROR, f"Empty JSON text after extraction from response: {response_text[:200]}...")
                raise ValueError("Empty JSON text after extraction")
            
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            self._log(LogLevel.ERROR, f"Failed to parse JSON response: {e}")
            self._log(LogLevel.ERROR, f"JSON text was: '{json_text[:200]}...'" if json_text else "Empty JSON text")
            self._log(LogLevel.ERROR, f"Original response: '{response_text[:200]}...'")
            raise ValueError(f"Invalid JSON in LLM response: {e}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Unexpected error in JSON validation: {e}")
            self._log(LogLevel.ERROR, f"Response text: '{response_text[:200]}...'")
            raise
    
    @abstractmethod
    async def execute_task(self, task: Task) -> bool:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: Task to execute
            
        Returns:
            True if task completed successfully
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this agent can handle.
        
        Returns:
            List of capability strings
        """
        pass