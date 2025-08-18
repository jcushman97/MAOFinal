"""
Configuration Management for MAOS

Handles loading and validation of system configuration settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    
    cmd: list[str] = Field(..., description="Command array for CLI execution")
    extra_args: list[str] = Field(default_factory=list, description="Additional command arguments")
    json_markers: list[str] = Field(default=["BEGIN_JSON", "END_JSON"], description="JSON output markers")
    timeout: int = Field(default=300, description="Timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class RoutingConfig(BaseModel):
    """Task routing configuration mapping task types to models."""
    
    plan: str = Field(default="claude", description="Planning tasks")
    python: str = Field(default="claude", description="Python code tasks")
    backend: str = Field(default="claude", description="Backend development")
    frontend: str = Field(default="claude", description="Frontend development")
    research: str = Field(default="claude", description="Research tasks")
    documentation: str = Field(default="claude", description="Documentation tasks")
    general: str = Field(default="claude", description="General tasks")


class Config(BaseModel):
    """Main configuration class for MAOS."""
    
    # Directory settings
    project_dir: Path = Field(default_factory=lambda: Path("projects"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))
    
    # Execution settings
    default_timeout: int = Field(default=300, description="Default timeout in seconds")
    max_parallel_tasks: int = Field(default=1, description="Max parallel tasks (1 for sequential)")
    
    # Provider settings
    slots: Dict[str, ProviderConfig] = Field(default_factory=dict)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    
    # Retry and error handling
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Base retry delay in seconds")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        
    @validator('project_dir', 'logs_dir')
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory paths exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = Path("providers/providers.json")
            
        if config_path.exists():
            with open(config_path) as f:
                config_data = json.load(f)
                
            # Convert slot configs to ProviderConfig objects
            if 'slots' in config_data:
                for slot_name, slot_config in config_data['slots'].items():
                    config_data['slots'][slot_name] = ProviderConfig(**slot_config)
                    
            return cls(**config_data)
        else:
            # Create default configuration with Claude focus
            return cls._create_default_config(config_path)
    
    @classmethod
    def _create_default_config(cls, config_path: Path) -> 'Config':
        """Create default configuration focused on Claude."""
        config = cls(
            slots={
                "claude": ProviderConfig(
                    cmd=["python", "wrappers/claude_wrapper.py"],
                    extra_args=["--model", "claude-3.5-sonnet"],
                    json_markers=["BEGIN_JSON", "END_JSON"],
                    timeout=300,
                    max_retries=3
                )
                # Phase 2: Additional models will be added here using wrapper template:
                # "gemini": ProviderConfig(
                #     cmd=["gemini", "prompt"],
                #     extra_args=["--model", "gemini-1.5-pro"],
                #     json_markers=["BEGIN_JSON", "END_JSON"],
                #     timeout=300,
                #     max_retries=3
                # ),
                # "gpt": ProviderConfig(
                #     cmd=["gpt", "chat"],
                #     extra_args=["--model", "gpt-4"],
                #     json_markers=["BEGIN_JSON", "END_JSON"], 
                #     timeout=300,
                #     max_retries=3
                # )
            },
            routing=RoutingConfig()  # All routes default to claude
        )
        
        # Save default config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            config_dict = config.model_dump()
            # Convert ProviderConfig objects back to dicts for JSON serialization
            for slot_name, slot_config in config_dict['slots'].items():
                if hasattr(slot_config, 'model_dump'):
                    config_dict['slots'][slot_name] = slot_config.model_dump()
            json.dump(config_dict, f, indent=2, default=str)
            
        return config
    
    def get_provider_for_task(self, task_type: str) -> str:
        """Get the appropriate provider for a given task type."""
        routing_dict = self.routing.model_dump()
        return routing_dict.get(task_type, routing_dict['general'])
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.slots.get(provider_name)