"""
Team Lead Agent Base Class for MAOS

Provides specialized team leadership functionality for Frontend, Backend, and QA teams.
Extends BaseAgent with team-specific capabilities and task delegation.
"""

import asyncio
from abc import abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from agents.base_agent import BaseAgent, AgentType
from core.state import Task, TaskStatus, LogLevel
from core.logger import get_logger

logger = get_logger("team_lead_agent")


@dataclass
class WorkerExecutionResult:
    """Result of worker task execution."""
    worker_id: str
    task_id: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    artifacts: List[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


@dataclass
class ParallelExecutionMetrics:
    """Metrics for parallel worker execution."""
    total_workers: int = 0
    successful_workers: int = 0
    failed_workers: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    max_execution_time: float = 0.0
    min_execution_time: float = 0.0
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.successful_workers / self.total_workers * 100) if self.total_workers > 0 else 0.0


class TeamType(Enum):
    """Types of teams that can be led."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    QA = "qa"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"


class TeamLeadAgent(BaseAgent):
    """
    Abstract base class for Team Lead agents.
    
    Team Leads manage specialized teams and coordinate with other team leads.
    They receive tasks from the Project Manager and delegate to Worker agents
    or execute tasks directly for Phase 2.
    
    Responsibilities:
    - Execute team-specific tasks with domain expertise
    - Coordinate with other team leads for dependencies
    - Manage team-specific context and best practices
    - Provide specialized prompts and validation
    """
    
    def __init__(
        self,
        agent_id: str,
        team_type: TeamType,
        config,
        project_state,
        model_preference: Optional[str] = None
    ):
        """
        Initialize Team Lead agent.
        
        Args:
            agent_id: Unique identifier for this team lead
            team_type: Type of team this agent leads
            config: System configuration
            project_state: Current project state
            model_preference: Preferred LLM model for this team
        """
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.LEAD,
            config=config,
            project_state=project_state,
            model_preference=model_preference or self._get_team_model_preference(team_type)
        )
        
        self.team_type = team_type
        self.team_context = self._initialize_team_context()
        self.specialized_prompts = self._load_specialized_prompts()
        
        logger.info(f"Team Lead {agent_id} initialized for {team_type.value} team")
    
    def _get_team_model_preference(self, team_type: TeamType) -> str:
        """Get preferred model for this team type."""
        # Phase 2: Team-specific model routing
        # Frontend might prefer models good at UI/UX
        # Backend might prefer models good at architecture
        # QA might prefer models good at edge case detection
        team_model_preferences = {
            TeamType.FRONTEND: "claude",  # Good at UI/UX and user experience
            TeamType.BACKEND: "claude",   # Good at system architecture
            TeamType.QA: "claude",        # Good at edge case detection
            TeamType.RESEARCH: "claude",  # Good at analysis and research
            TeamType.DOCUMENTATION: "claude"  # Good at clear communication
        }
        
        return team_model_preferences.get(team_type, "claude")
    
    def _initialize_team_context(self) -> Dict[str, Any]:
        """Initialize team-specific context and expertise."""
        return {
            "team_type": self.team_type.value,
            "expertise_areas": self._get_expertise_areas(),
            "best_practices": self._get_team_best_practices(),
            "common_tools": self._get_common_tools(),
            "quality_standards": self._get_quality_standards()
        }
    
    @abstractmethod
    def _get_expertise_areas(self) -> List[str]:
        """Get list of expertise areas for this team."""
        pass
    
    @abstractmethod
    def _get_team_best_practices(self) -> List[str]:
        """Get team-specific best practices and guidelines."""
        pass
    
    @abstractmethod
    def _get_common_tools(self) -> List[str]:
        """Get common tools and technologies used by this team."""
        pass
    
    @abstractmethod
    def _get_quality_standards(self) -> Dict[str, str]:
        """Get quality standards and validation criteria for this team."""
        pass
    
    @abstractmethod
    def _load_specialized_prompts(self) -> Dict[str, str]:
        """Load team-specific prompt templates."""
        pass
    
    async def execute_task(self, task: Task) -> bool:
        """
        Execute a team-specific task with specialized expertise.
        
        Phase 3: Can delegate to Worker agents for atomic tasks or execute directly.
        
        Args:
            task: Task to execute
            
        Returns:
            True if task completed successfully
        """
        self._log(LogLevel.INFO, f"Team Lead {self.team_type.value} executing: {task.description}")
        
        try:
            # Validate task is appropriate for this team
            if not self._validate_task_for_team(task):
                self._log(LogLevel.WARNING, f"Task {task.id} may not be suitable for {self.team_type.value} team")
            
            # Increment attempt counter
            task.attempts += 1
            
            # Phase 3: Check if task should be delegated to worker
            if await self._should_delegate_to_worker(task):
                return await self._delegate_to_worker(task)
            
            # Execute task directly with team expertise
            prompt = self._build_specialized_prompt(task)
            
            response = await self.call_llm(
                prompt=prompt,
                task_type=self._map_task_to_llm_type(task),
                expect_json=False
            )
            
            # Apply team-specific post-processing
            processed_output = await self._post_process_output(task, response["output"])
            
            # Save task output with team context
            await self._save_team_task_artifact(task, processed_output)
            
            self._log(LogLevel.INFO, f"Team task completed: {task.description}")
            return True
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Team task execution failed: {e}")
            task.error = str(e)
            return False
    
    def _validate_task_for_team(self, task: Task) -> bool:
        """Validate that task is appropriate for this team."""
        return task.team == self.team_type.value
    
    @abstractmethod
    def _build_specialized_prompt(self, task: Task) -> str:
        """Build a specialized prompt using team expertise and context."""
        pass
    
    def _map_task_to_llm_type(self, task: Task) -> str:
        """Map task to LLM type for proper model routing."""
        return task.team  # Use team name as task type
    
    async def _post_process_output(self, task: Task, output: str) -> str:
        """Apply team-specific post-processing to task output."""
        # Base implementation - subclasses can override
        return output
    
    async def _save_team_task_artifact(self, task: Task, output: str):
        """Save task output with team-specific artifact handling."""
        try:
            # Create artifacts directory
            project_dir = self.config.project_dir / self.project_state.projectId
            artifacts_dir = project_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create artifact file with team context
            artifact_filename = f"{task.id}_{self.team_type.value}_lead.txt"
            artifact_path = artifacts_dir / artifact_filename
            
            # Write output to artifact file with team metadata
            with open(artifact_path, 'w', encoding='utf-8') as f:
                f.write(f"Task: {task.description}\n")
                f.write(f"Team: {self.team_type.value} (Lead Agent)\n")
                f.write(f"Agent: {self.agent_id}\n")
                f.write(f"Generated: {self.project_state.updatedAt}\n")
                f.write(f"Expertise: {', '.join(self.team_context['expertise_areas'])}\n")
                f.write("-" * 50 + "\n")
                f.write(output)
            
            # Add artifact to task
            task.artifacts.append(str(artifact_path))
            
            # Create deliverable files using enhanced file manager
            await self._create_team_deliverables(task, output, project_dir)
            
            self._log(LogLevel.INFO, f"Saved team artifact: {artifact_filename}")
            
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to save team artifact: {e}")
    
    async def _create_team_deliverables(self, task: Task, output: str, project_dir):
        """Create deliverable files by parsing agent output for file creation instructions."""
        try:
            # Since agents now generate files directly through their LLM responses,
            # we don't need complex extraction - files should already exist
            # or be created through the agent's direct tool usage
            
            # Log that deliverable creation was attempted
            self._log(LogLevel.INFO, f"Team deliverable processing completed for task {task.id}")
            
            # The agent's LLM response should have created files directly
            # If additional processing is needed, it can be added here
            
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to process team deliverables: {e}")
    
    async def _process_deliverable_code(self, filename: str, code: str) -> str:
        """Apply team-specific processing to deliverable code."""
        # Base implementation - subclasses can override for team-specific processing
        return code
    
    def get_team_capabilities(self) -> List[str]:
        """Get team-specific capabilities."""
        base_capabilities = self.get_capabilities()
        team_capabilities = [
            f"{self.team_type.value}_expertise",
            f"{self.team_type.value}_best_practices",
            "team_coordination",
            "specialized_prompts",
            "quality_validation"
        ]
        return base_capabilities + team_capabilities
    
    def get_team_status(self) -> Dict[str, Any]:
        """Get current team status and context."""
        return {
            "team_type": self.team_type.value,
            "agent_id": self.agent_id,
            "expertise_areas": self.team_context["expertise_areas"],
            "active_tasks": len([t for t in self.project_state.tasks if t.team == self.team_type.value and t.status == TaskStatus.IN_PROGRESS]),
            "completed_tasks": len([t for t in self.project_state.tasks if t.team == self.team_type.value and t.status == TaskStatus.COMPLETE])
        }
    
    # Phase 3: Worker delegation methods
    
    async def _should_delegate_to_worker(self, task: Task) -> bool:
        """
        Determine if task should be delegated to a Worker agent.
        
        Delegation criteria:
        - Task is atomic and focused
        - Task matches a specific worker specialty
        - Worker availability exists
        """
        # Check if task is atomic (simple, focused task)
        task_description = task.description.lower()
        
        # Atomic task indicators
        atomic_indicators = [
            "create", "add", "style", "implement", "write", "generate",
            "update", "fix", "optimize", "refactor"
        ]
        
        # Complex task indicators (should be handled by Team Lead)
        complex_indicators = [
            "design system", "architecture", "coordinate", "integrate",
            "comprehensive", "full", "complete system", "end-to-end"
        ]
        
        # Don't delegate complex tasks
        if any(indicator in task_description for indicator in complex_indicators):
            return False
        
        # Delegate atomic tasks
        if any(indicator in task_description for indicator in atomic_indicators):
            return True
        
        return False
    
    async def _delegate_to_worker(self, task: Task) -> bool:
        """
        Delegate task to appropriate Worker agent.
        
        Args:
            task: Task to delegate
            
        Returns:
            True if delegation and execution succeeded
        """
        self._log(LogLevel.INFO, f"Team Lead delegating task to worker: {task.description}")
        
        try:
            # Get appropriate worker for task
            worker = await self._get_worker_for_task(task)
            
            if not worker:
                self._log(LogLevel.WARNING, f"No suitable worker found for task {task.id}, executing directly")
                return False
            
            # Execute task via worker
            success = await worker.execute_task(task)
            
            if success:
                self._log(LogLevel.INFO, f"Worker {worker.agent_id} completed task: {task.description}")
            else:
                self._log(LogLevel.WARNING, f"Worker {worker.agent_id} failed task: {task.description}")
            
            return success
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Worker delegation failed: {e}")
            return False
    
    async def _get_worker_for_task(self, task: Task):
        """
        Get appropriate Worker agent for a specific task.
        
        Should be implemented by specialized Team Lead agents.
        """
        # Base implementation returns None (no delegation)
        # Specialized team leads will override this
        return None
    
    # Phase 4: Parallel coordination methods
    
    async def execute_parallel_tasks(self, tasks: List[Task]) -> ParallelExecutionMetrics:
        """
        Execute multiple tasks in parallel using worker delegation.
        
        Args:
            tasks: List of tasks to execute in parallel
            
        Returns:
            ParallelExecutionMetrics with execution results
        """
        self._log(LogLevel.INFO, f"Team Lead {self.team_type.value} executing {len(tasks)} tasks in parallel")
        
        start_time = asyncio.get_event_loop().time()
        metrics = ParallelExecutionMetrics(total_workers=len(tasks))
        
        # Group tasks by delegation suitability
        delegatable_tasks = []
        direct_tasks = []
        
        for task in tasks:
            if await self._should_delegate_to_worker(task):
                delegatable_tasks.append(task)
            else:
                direct_tasks.append(task)
        
        # Execute delegatable tasks in parallel via workers
        worker_results = []
        if delegatable_tasks:
            worker_results = await self._execute_parallel_workers(delegatable_tasks)
        
        # Execute direct tasks sequentially (Team Lead capacity limit)
        direct_results = []
        for task in direct_tasks:
            success = await self.execute_task(task)
            execution_time = asyncio.get_event_loop().time() - start_time
            direct_results.append(WorkerExecutionResult(
                worker_id=self.agent_id,
                task_id=task.id,
                success=success,
                execution_time=execution_time
            ))
        
        # Combine results and update metrics
        all_results = worker_results + direct_results
        self._update_parallel_metrics(metrics, all_results)
        
        total_time = asyncio.get_event_loop().time() - start_time
        metrics.total_execution_time = total_time
        
        self._log(LogLevel.INFO, 
                 f"Parallel execution completed: {metrics.successful_workers}/{metrics.total_workers} successful, "
                 f"{total_time:.1f}s total time, {metrics.calculate_success_rate():.1f}% success rate")
        
        return metrics
    
    async def _execute_parallel_workers(self, tasks: List[Task]) -> List[WorkerExecutionResult]:
        """Execute multiple tasks in parallel using workers."""
        # Create worker tasks
        worker_futures = {}
        
        for task in tasks:
            # Create async task for worker execution
            future = asyncio.create_task(self._execute_worker_with_tracking(task))
            worker_futures[task.id] = future
        
        # Wait for all workers to complete
        results = await asyncio.gather(*worker_futures.values(), return_exceptions=True)
        
        # Process results
        worker_results = []
        for i, (task_id, result) in enumerate(zip(worker_futures.keys(), results)):
            if isinstance(result, Exception):
                self._log(LogLevel.ERROR, f"Worker execution failed for task {task_id}: {result}")
                worker_results.append(WorkerExecutionResult(
                    worker_id="unknown",
                    task_id=task_id,
                    success=False,
                    execution_time=0.0,
                    error_message=str(result)
                ))
            elif isinstance(result, WorkerExecutionResult):
                worker_results.append(result)
            else:
                # Unexpected result type
                worker_results.append(WorkerExecutionResult(
                    worker_id="unknown",
                    task_id=task_id,
                    success=False,
                    execution_time=0.0,
                    error_message=f"Unexpected result type: {type(result)}"
                ))
        
        return worker_results
    
    async def _execute_worker_with_tracking(self, task: Task) -> WorkerExecutionResult:
        """Execute a single task via worker with execution tracking."""
        start_time = asyncio.get_event_loop().time()
        worker = None
        
        try:
            # Get worker for task
            worker = await self._get_worker_for_task(task)
            
            if not worker:
                return WorkerExecutionResult(
                    worker_id="none",
                    task_id=task.id,
                    success=False,
                    execution_time=0.0,
                    error_message="No suitable worker found"
                )
            
            # Execute via worker
            success = await worker.execute_task(task)
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return WorkerExecutionResult(
                worker_id=worker.agent_id,
                task_id=task.id,
                success=success,
                execution_time=execution_time,
                artifacts=task.artifacts.copy() if task.artifacts else []
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            worker_id = worker.agent_id if worker else "unknown"
            
            self._log(LogLevel.ERROR, f"Worker {worker_id} execution failed: {e}")
            
            return WorkerExecutionResult(
                worker_id=worker_id,
                task_id=task.id,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def _update_parallel_metrics(self, metrics: ParallelExecutionMetrics, results: List[WorkerExecutionResult]):
        """Update parallel execution metrics based on results."""
        execution_times = []
        
        for result in results:
            if result.success:
                metrics.successful_workers += 1
            else:
                metrics.failed_workers += 1
            
            execution_times.append(result.execution_time)
        
        if execution_times:
            metrics.average_execution_time = sum(execution_times) / len(execution_times)
            metrics.max_execution_time = max(execution_times)
            metrics.min_execution_time = min(execution_times)
    
    async def balance_worker_load(self, tasks: List[Task], max_workers: int = 5) -> List[List[Task]]:
        """
        Balance task load across available workers.
        
        Args:
            tasks: Tasks to balance
            max_workers: Maximum number of workers to use
            
        Returns:
            List of task groups for parallel execution
        """
        if not tasks:
            return []
        
        # Group tasks by complexity/estimated duration
        task_weights = []
        for task in tasks:
            weight = self._estimate_task_complexity(task)
            task_weights.append((task, weight))
        
        # Sort by weight (heaviest first for better distribution)
        task_weights.sort(key=lambda x: x[1], reverse=True)
        
        # Distribute tasks across workers using round-robin with weight consideration
        worker_groups = [[] for _ in range(min(max_workers, len(tasks)))]
        worker_loads = [0.0] * len(worker_groups)
        
        for task, weight in task_weights:
            # Find worker with lowest current load
            min_load_idx = worker_loads.index(min(worker_loads))
            worker_groups[min_load_idx].append(task)
            worker_loads[min_load_idx] += weight
        
        # Remove empty groups
        balanced_groups = [group for group in worker_groups if group]
        
        self._log(LogLevel.INFO, f"Balanced {len(tasks)} tasks across {len(balanced_groups)} worker groups")
        
        return balanced_groups
    
    def _estimate_task_complexity(self, task: Task) -> float:
        """Estimate task complexity for load balancing."""
        # Base complexity on description length and keywords
        base_complexity = len(task.description) / 50.0
        
        # Complexity modifiers based on keywords
        complexity_keywords = {
            "simple": 0.5, "basic": 0.5, "quick": 0.5,
            "complex": 2.0, "comprehensive": 2.5, "full": 2.0,
            "optimize": 1.5, "refactor": 1.8, "integrate": 1.7,
            "test": 0.8, "validate": 0.7, "check": 0.6
        }
        
        task_lower = task.description.lower()
        complexity_modifier = 1.0
        
        for keyword, modifier in complexity_keywords.items():
            if keyword in task_lower:
                complexity_modifier = modifier
                break
        
        return max(0.5, base_complexity * complexity_modifier)
    
    async def monitor_parallel_progress(self, active_tasks: Dict[str, asyncio.Task]) -> Dict[str, Any]:
        """
        Monitor progress of parallel task execution.
        
        Args:
            active_tasks: Dictionary of task_id -> asyncio.Task
            
        Returns:
            Progress information dictionary
        """
        total_tasks = len(active_tasks)
        completed_tasks = sum(1 for task in active_tasks.values() if task.done())
        running_tasks = total_tasks - completed_tasks
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Check for failed tasks
        failed_tasks = []
        for task_id, task in active_tasks.items():
            if task.done() and task.exception():
                failed_tasks.append({
                    "task_id": task_id,
                    "error": str(task.exception())
                })
        
        progress_info = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "running_tasks": running_tasks,
            "failed_tasks": len(failed_tasks),
            "completion_rate": completion_rate,
            "failure_details": failed_tasks,
            "team_lead": self.agent_id,
            "team_type": self.team_type.value
        }
        
        return progress_info
    
    def get_parallel_capabilities(self) -> Dict[str, Any]:
        """Get parallel execution capabilities for this team lead."""
        return {
            "supports_parallel_execution": True,
            "max_concurrent_workers": 5,  # Configurable per team
            "worker_delegation_enabled": True,
            "load_balancing_enabled": True,
            "progress_monitoring_enabled": True,
            "team_type": self.team_type.value,
            "estimated_parallel_speedup": 2.5  # Estimated speedup factor
        }