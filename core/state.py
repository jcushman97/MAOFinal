"""
State Management for MAOS

Handles project state persistence and recovery using the exact JSON schema
from Architecture.md.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import asyncio
import aiofiles
from core.logger import get_logger

logger = get_logger("state")


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    EXECUTING = "executing" 
    PAUSED = "paused"
    COMPLETE = "complete"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class LogLevel(str, Enum):
    """Log level enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AgentType(str, Enum):
    """Agent type enumeration."""
    PM = "pm"
    LEAD = "lead"  
    WORKER = "worker"


class LogEntry(BaseModel):
    """Log entry model."""
    timestamp: float
    level: LogLevel
    agent: str
    message: str


class Agent(BaseModel):
    """Agent information model."""
    type: AgentType
    model: str
    tokensUsed: int = 0
    callCount: int = 0


class Task(BaseModel):
    """Task model following exact Architecture.md schema."""
    id: str
    description: str
    team: str
    status: TaskStatus = TaskStatus.QUEUED
    dependencies: List[str] = Field(default_factory=list)
    subtasks: List['Task'] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    attempts: int = 0
    error: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ProjectState(BaseModel):
    """
    Project state model following exact JSON schema from Architecture.md.
    
    This matches the state schema defined in the architecture documentation
    to ensure consistency and compatibility.
    """
    projectId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objective: str
    createdAt: float = Field(default_factory=lambda: datetime.now().timestamp())
    updatedAt: float = Field(default_factory=lambda: datetime.now().timestamp())
    status: ProjectStatus = ProjectStatus.PLANNING
    tasks: List[Task] = Field(default_factory=list)
    agents: Dict[str, Agent] = Field(default_factory=dict)
    logs: List[LogEntry] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
    
    def update_timestamp(self):
        """Update the updatedAt timestamp."""
        self.updatedAt = datetime.now().timestamp()
    
    def add_log_entry(self, level: LogLevel, agent: str, message: str):
        """Add a log entry to the project state."""
        entry = LogEntry(
            timestamp=datetime.now().timestamp(),
            level=level,
            agent=agent,
            message=message
        )
        self.logs.append(entry)
        self.update_timestamp()
        logger.info(f"[{agent}] {message}")
    
    def add_task(self, task: Task):
        """Add a task to the project."""
        self.tasks.append(task)
        self.update_timestamp()
        self.add_log_entry(LogLevel.INFO, "system", f"Task added: {task.description}")
    
    def update_task_status(self, task_id: str, status: TaskStatus, error: Optional[str] = None):
        """Update task status."""
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                if error:
                    task.error = error
                self.update_timestamp()
                self.add_log_entry(
                    LogLevel.INFO if status != TaskStatus.FAILED else LogLevel.ERROR,
                    "system",
                    f"Task {task_id} status changed to {status}"
                )
                return
        
        logger.warning(f"Task {task_id} not found for status update")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (queued with all dependencies complete)."""
        ready_tasks = []
        for task in self.tasks:
            if task.status == TaskStatus.QUEUED:
                # Check if all dependencies are complete
                dependencies_complete = all(
                    self.get_task(dep_id) and self.get_task(dep_id).status == TaskStatus.COMPLETE
                    for dep_id in task.dependencies
                )
                if dependencies_complete:
                    ready_tasks.append(task)
        return ready_tasks
    
    def update_agent_stats(self, agent_id: str, tokens_used: int = 0):
        """Update agent usage statistics."""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found for stats update")
            return
        
        # Handle both Agent objects and dictionaries (for backward compatibility)
        agent = self.agents[agent_id]
        if isinstance(agent, dict):
            agent['tokensUsed'] = agent.get('tokensUsed', 0) + tokens_used
            agent['callCount'] = agent.get('callCount', 0) + 1
        else:
            agent.tokensUsed += tokens_used
            agent.callCount += 1
        self.update_timestamp()


class StateManager:
    """
    Manages project state persistence and recovery.
    
    Handles atomic writes, backup creation, and state validation to ensure
    data integrity and support for pause/resume functionality.
    """
    
    def __init__(self, project_dir: Path):
        """Initialize state manager with project directory."""
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_state_file(self, project_id: str) -> Path:
        """Get the state file path for a project."""
        return self.project_dir / project_id / "state.json"
    
    def _get_backup_file(self, project_id: str) -> Path:
        """Get the backup state file path for a project."""
        return self.project_dir / project_id / "state_backup.json"
    
    async def save_state(self, state: ProjectState) -> bool:
        """
        Save project state with atomic write operation.
        
        Creates a backup before writing to prevent corruption.
        """
        try:
            state_file = self._get_state_file(state.projectId)
            backup_file = self._get_backup_file(state.projectId)
            
            # Ensure project directory exists
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if current state exists
            if state_file.exists():
                async with aiofiles.open(state_file, 'r') as src:
                    content = await src.read()
                async with aiofiles.open(backup_file, 'w') as dst:
                    await dst.write(content)
            
            # Write new state atomically
            temp_file = state_file.with_suffix('.tmp')
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(state.model_dump_json(indent=2))
            
            # Atomic move
            temp_file.replace(state_file)
            
            logger.debug(f"State saved for project {state.projectId}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state for project {state.projectId}: {e}")
            return False
    
    async def load_state(self, project_id: str) -> Optional[ProjectState]:
        """
        Load project state from file.
        
        Attempts to load from backup if main file is corrupted.
        """
        state_file = self._get_state_file(project_id)
        backup_file = self._get_backup_file(project_id)
        
        # Try main state file first
        for file_path in [state_file, backup_file]:
            if file_path.exists():
                try:
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                    
                    state_data = json.loads(content)
                    state = ProjectState.model_validate(state_data)
                    
                    logger.info(f"State loaded for project {project_id}")
                    return state
                    
                except Exception as e:
                    logger.warning(f"Failed to load state from {file_path}: {e}")
                    continue
        
        logger.error(f"Could not load state for project {project_id}")
        return None
    
    def list_projects(self) -> List[str]:
        """List all available project IDs."""
        project_ids = []
        for item in self.project_dir.iterdir():
            if item.is_dir() and (item / "state.json").exists():
                project_ids.append(item.name)
        return project_ids
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its files."""
        try:
            project_path = self.project_dir / project_id
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
                logger.info(f"Project {project_id} deleted")
                return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
        return False


# Enable forward references for recursive Task model
Task.model_rebuild()