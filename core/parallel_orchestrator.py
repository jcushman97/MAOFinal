"""
Parallel Orchestration Engine for MAOS

Manages parallel task execution with intelligent dependency resolution,
resource management, and quality assurance while maintaining the
hierarchical delegation system.
"""

import asyncio
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from core.dependency_analyzer import DependencyAnalyzer, TaskGroup, ParallelExecutionPlan, ParallelStrategy
from core.state import Task, TaskStatus, ProjectState, LogLevel
from core.logger import get_logger
from agents.project_manager import ProjectManagerAgent
from agents.frontend_lead import FrontendTeamLead
from agents.backend_lead import BackendTeamLead
from agents.qa_lead import QATeamLead

logger = get_logger("parallel_orchestrator")


class ExecutionMode(Enum):
    """Execution modes for the parallel orchestrator."""
    SEQUENTIAL = "sequential"     # Traditional sequential execution
    PARALLEL = "parallel"         # Full parallel execution
    HYBRID = "hybrid"            # Mix of sequential and parallel based on analysis


@dataclass
class ExecutionMetrics:
    """Metrics for parallel execution tracking."""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    parallel_groups_executed: int = 0
    stages_completed: int = 0
    max_concurrent_groups: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    speedup_factor: float = 0.0
    
    def get_completion_rate(self) -> float:
        """Get completion rate as percentage."""
        return (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0.0
    
    def get_execution_time(self) -> float:
        """Get total execution time in minutes."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60.0
        return 0.0


@dataclass
class GroupExecutionResult:
    """Result of executing a task group."""
    group_id: str
    success: bool
    execution_time: float
    completed_tasks: List[str]
    failed_tasks: List[str]
    resource_usage: Dict[str, float]
    error_message: Optional[str] = None


class ParallelOrchestrator:
    """
    Advanced orchestrator for parallel task execution.
    
    Manages the complete parallel execution lifecycle including:
    - Dependency analysis and task grouping
    - Resource allocation and management
    - Parallel agent coordination
    - Progress monitoring and error recovery
    - Quality assurance across parallel execution
    """
    
    def __init__(self, config, strategy: ParallelStrategy = ParallelStrategy.BALANCED):
        """Initialize parallel orchestrator."""
        self.config = config
        self.strategy = strategy
        self.dependency_analyzer = DependencyAnalyzer(strategy)
        self.execution_metrics = None
        self.active_groups: Dict[str, asyncio.Task] = {}
        self.completed_groups: Set[str] = set()
        self.failed_groups: Set[str] = set()
        
        # Resource tracking
        self.current_resource_usage = {"tokens": 0.0, "memory": 0.0, "cpu": 0.0}
        self.resource_limits = {"tokens": 1.0, "memory": 1.0, "cpu": 1.0}
        
        # Execution control
        self.max_retries = 2
        self.execution_timeout = 1800  # 30 minutes max for any single group
        
        logger.info(f"Parallel orchestrator initialized with {strategy.value} strategy")
    
    async def execute_project_parallel(
        self, 
        project_state: ProjectState, 
        mode: ExecutionMode = ExecutionMode.PARALLEL
    ) -> bool:
        """
        Execute project tasks using parallel orchestration.
        
        Args:
            project_state: Project state with tasks to execute
            mode: Execution mode (sequential, parallel, or hybrid)
            
        Returns:
            True if all tasks completed successfully
        """
        logger.info(f"Starting parallel execution for project {project_state.projectId} in {mode.value} mode")
        
        # Initialize metrics
        self.execution_metrics = ExecutionMetrics(
            start_time=datetime.now(timezone.utc),
            total_tasks=len(project_state.tasks)
        )
        
        try:
            # Choose execution strategy based on mode
            if mode == ExecutionMode.SEQUENTIAL:
                return await self._execute_sequential(project_state)
            elif mode == ExecutionMode.PARALLEL:
                return await self._execute_parallel(project_state)
            else:  # HYBRID
                return await self._execute_hybrid(project_state)
                
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return False
        finally:
            # Finalize metrics
            if self.execution_metrics:
                self.execution_metrics.end_time = datetime.now(timezone.utc)
                self._log_execution_summary()
    
    async def _execute_parallel(self, project_state: ProjectState) -> bool:
        """Execute project using full parallel strategy."""
        # Get ready tasks (no dependencies or dependencies satisfied)
        ready_tasks = project_state.get_ready_tasks()
        
        if not ready_tasks:
            logger.warning("No ready tasks found for parallel execution")
            return True
        
        # Analyze dependencies and create execution plan
        execution_plan = self.dependency_analyzer.analyze_dependencies(ready_tasks)
        
        project_state.add_log_entry(
            LogLevel.INFO, 
            "parallel_orchestrator", 
            f"Created parallel execution plan: {len(execution_plan.task_groups)} groups, "
            f"{len(execution_plan.execution_stages)} stages"
        )
        
        # Execute stages in sequence, groups within stages in parallel
        for stage_idx, stage in enumerate(execution_plan.execution_stages):
            logger.info(f"Executing stage {stage_idx + 1}/{len(execution_plan.execution_stages)} "
                       f"with {len(stage)} parallel groups")
            
            stage_success = await self._execute_stage(stage, project_state)
            
            if not stage_success:
                logger.error(f"Stage {stage_idx + 1} failed, stopping execution")
                return False
            
            self.execution_metrics.stages_completed += 1
        
        # Check final completion status
        success = self._all_groups_completed()
        
        if success:
            logger.info("All parallel task groups completed successfully")
        else:
            logger.error("Some parallel task groups failed")
        
        return success
    
    async def _execute_stage(self, stage: List[TaskGroup], project_state: ProjectState) -> bool:
        """Execute a stage of parallel task groups."""
        if not stage:
            return True
        
        # Start all groups in this stage concurrently
        group_tasks = {}
        
        for group in stage:
            logger.info(f"Starting parallel execution of group {group.id} with {len(group.tasks)} tasks")
            
            # Create async task for group execution
            task = asyncio.create_task(
                self._execute_group_with_timeout(group, project_state)
            )
            group_tasks[group.id] = task
            self.active_groups[group.id] = task
        
        # Wait for all groups in stage to complete
        stage_results = await asyncio.gather(*group_tasks.values(), return_exceptions=True)
        
        # Process results
        stage_success = True
        for i, (group_id, result) in enumerate(zip(group_tasks.keys(), stage_results)):
            # Remove from active groups
            self.active_groups.pop(group_id, None)
            
            if isinstance(result, Exception):
                logger.error(f"Group {group_id} failed with exception: {result}")
                self.failed_groups.add(group_id)
                stage_success = False
            elif isinstance(result, GroupExecutionResult):
                if result.success:
                    logger.info(f"Group {group_id} completed successfully in {result.execution_time:.1f}s")
                    self.completed_groups.add(group_id)
                    self.execution_metrics.completed_tasks += len(result.completed_tasks)
                    
                    # Update task statuses in project state
                    for task_id in result.completed_tasks:
                        project_state.update_task_status(task_id, TaskStatus.COMPLETE)
                else:
                    logger.error(f"Group {group_id} failed: {result.error_message}")
                    self.failed_groups.add(group_id)
                    self.execution_metrics.failed_tasks += len(result.failed_tasks)
                    stage_success = False
                    
                    # Update failed task statuses
                    for task_id in result.failed_tasks:
                        project_state.update_task_status(task_id, TaskStatus.FAILED, result.error_message)
                
                # Update resource usage
                self._update_resource_usage(result.resource_usage)
            else:
                logger.error(f"Unexpected result type from group {group_id}: {type(result)}")
                stage_success = False
        
        # Update max concurrent groups metric
        self.execution_metrics.max_concurrent_groups = max(
            self.execution_metrics.max_concurrent_groups,
            len(group_tasks)
        )
        
        return stage_success
    
    async def _execute_group_with_timeout(
        self, 
        group: TaskGroup, 
        project_state: ProjectState
    ) -> GroupExecutionResult:
        """Execute a task group with timeout protection."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_group(group, project_state),
                timeout=self.execution_timeout
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Group {group.id} timed out after {execution_time:.1f}s")
            
            return GroupExecutionResult(
                group_id=group.id,
                success=False,
                execution_time=execution_time,
                completed_tasks=[],
                failed_tasks=[task.id for task in group.tasks],
                resource_usage={},
                error_message=f"Group execution timed out after {execution_time:.1f}s"
            )
        
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Group {group.id} execution failed: {e}")
            
            return GroupExecutionResult(
                group_id=group.id,
                success=False,
                execution_time=execution_time,
                completed_tasks=[],
                failed_tasks=[task.id for task in group.tasks],
                resource_usage={},
                error_message=str(e)
            )
    
    async def _execute_group(self, group: TaskGroup, project_state: ProjectState) -> GroupExecutionResult:
        """Execute a single task group using appropriate team agents."""
        logger.info(f"Executing group {group.id} with {len(group.tasks)} tasks")
        
        completed_tasks = []
        failed_tasks = []
        total_resource_usage = {"tokens": 0.0, "memory": 0.0, "cpu": 0.0}
        
        # Group tasks by team for efficient agent usage
        team_groups = self._group_tasks_by_team(group.tasks)
        
        # Execute each team's tasks
        for team, team_tasks in team_groups.items():
            logger.info(f"Executing {len(team_tasks)} {team} tasks in group {group.id}")
            
            # Get appropriate agent for team
            agent = await self._get_team_agent(team, project_state)
            
            # Execute team tasks (agents may further parallelize internally)
            for task in team_tasks:
                try:
                    # Update task status
                    project_state.update_task_status(task.id, TaskStatus.IN_PROGRESS)
                    
                    # Execute task through agent
                    success = await agent.execute_task(task)
                    
                    if success:
                        completed_tasks.append(task.id)
                        logger.debug(f"Task {task.id} completed successfully")
                    else:
                        failed_tasks.append(task.id)
                        logger.warning(f"Task {task.id} failed")
                    
                    # Track resource usage (estimated)
                    task_resources = self._estimate_task_resource_usage(task, agent)
                    for resource, amount in task_resources.items():
                        total_resource_usage[resource] += amount
                        
                except Exception as e:
                    failed_tasks.append(task.id)
                    logger.error(f"Task {task.id} execution error: {e}")
                    project_state.update_task_status(task.id, TaskStatus.FAILED, str(e))
        
        # Determine overall success
        success = len(failed_tasks) == 0
        
        return GroupExecutionResult(
            group_id=group.id,
            success=success,
            execution_time=0.0,  # Will be set by caller
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            resource_usage=total_resource_usage,
            error_message=f"{len(failed_tasks)} tasks failed" if failed_tasks else None
        )
    
    def _group_tasks_by_team(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by team for efficient agent coordination."""
        team_groups = {}
        for task in tasks:
            team = task.team or "general"
            if team not in team_groups:
                team_groups[team] = []
            team_groups[team].append(task)
        return team_groups
    
    async def _get_team_agent(self, team: str, project_state: ProjectState):
        """Get appropriate team agent for task execution."""
        agent_id = f"{team}_lead_{project_state.projectId[:8]}"
        
        if team == "frontend":
            return FrontendTeamLead(agent_id, self.config, project_state)
        elif team == "backend":
            return BackendTeamLead(agent_id, self.config, project_state)
        elif team == "qa":
            return QATeamLead(agent_id, self.config, project_state)
        else:
            # Default to project manager for general tasks
            return ProjectManagerAgent("pm_001", self.config, project_state)
    
    def _estimate_task_resource_usage(self, task: Task, agent) -> Dict[str, float]:
        """Estimate resource usage for a task execution."""
        # Base resource usage by team
        base_resources = {
            "frontend": {"tokens": 0.15, "memory": 0.1, "cpu": 0.15},
            "backend": {"tokens": 0.2, "memory": 0.15, "cpu": 0.2},
            "qa": {"tokens": 0.1, "memory": 0.05, "cpu": 0.1},
            "documentation": {"tokens": 0.15, "memory": 0.05, "cpu": 0.1},
            "research": {"tokens": 0.25, "memory": 0.1, "cpu": 0.15}
        }
        
        return base_resources.get(task.team, {"tokens": 0.15, "memory": 0.1, "cpu": 0.15})
    
    def _update_resource_usage(self, usage: Dict[str, float]):
        """Update current resource usage tracking."""
        for resource, amount in usage.items():
            self.current_resource_usage[resource] = (
                self.current_resource_usage.get(resource, 0.0) + amount
            )
            
        # Update metrics
        if self.execution_metrics:
            for resource, amount in usage.items():
                current = self.execution_metrics.resource_usage.get(resource, 0.0)
                self.execution_metrics.resource_usage[resource] = max(current, amount)
    
    async def _execute_sequential(self, project_state: ProjectState) -> bool:
        """Fallback to sequential execution (original Phase 1-3 behavior)."""
        logger.info("Using sequential execution mode")
        
        # Use original sequential logic with iteration until all tasks complete
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            # Get ready tasks (queued with all dependencies complete)
            ready_tasks = project_state.get_ready_tasks()
            
            if not ready_tasks:
                # No more ready tasks, check if we're done
                if self._all_tasks_complete_or_failed(project_state):
                    break
                else:
                    # Might be a dependency deadlock
                    logger.warning("No ready tasks found but project not complete")
                    break
            
            # Execute first ready task (sequential execution)
            task = ready_tasks[0]
            logger.info(f"Executing task: {task.description}")
            
            # Update task status to in progress
            project_state.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            
            try:
                # Get appropriate agent for task
                agent = await self._get_team_agent(task.team or "general", project_state)
                success = await agent.execute_task(task)
                
                if success:
                    project_state.update_task_status(task.id, TaskStatus.COMPLETE)
                    self.execution_metrics.completed_tasks += 1
                    logger.info(f"Task completed successfully: {task.description}")
                else:
                    project_state.update_task_status(task.id, TaskStatus.FAILED, "Task execution failed")
                    self.execution_metrics.failed_tasks += 1
                    logger.error(f"Task failed: {task.description}")
                
            except Exception as e:
                project_state.update_task_status(task.id, TaskStatus.FAILED, str(e))
                self.execution_metrics.failed_tasks += 1
                logger.error(f"Task execution error: {e}")
            
            iteration += 1
        
        if iteration >= max_iterations:
            logger.error("Maximum task execution iterations reached")
            return False
        
        return self.execution_metrics.failed_tasks == 0
    
    async def _execute_hybrid(self, project_state: ProjectState) -> bool:
        """Execute using hybrid strategy (intelligent mix of sequential and parallel)."""
        logger.info("Using hybrid execution mode")
        
        ready_tasks = project_state.get_ready_tasks()
        
        # Analyze parallelism opportunities
        opportunities = self.dependency_analyzer.get_parallelism_opportunities(ready_tasks)
        
        # Use parallel execution if significant opportunities exist
        if opportunities["parallelism_factor"] > 1.5:
            logger.info(f"Good parallelism opportunities detected (factor: {opportunities['parallelism_factor']}), using parallel execution")
            return await self._execute_parallel(project_state)
        else:
            logger.info(f"Limited parallelism opportunities (factor: {opportunities['parallelism_factor']}), using sequential execution")
            return await self._execute_sequential(project_state)
    
    def _all_groups_completed(self) -> bool:
        """Check if all groups have completed (successfully or failed)."""
        return len(self.active_groups) == 0
    
    def _all_tasks_complete_or_failed(self, project_state: ProjectState) -> bool:
        """Check if all tasks are either COMPLETE or FAILED."""
        return all(
            task.status in [TaskStatus.COMPLETE, TaskStatus.FAILED] 
            for task in project_state.tasks
        )
    
    def _log_execution_summary(self):
        """Log summary of parallel execution metrics."""
        if not self.execution_metrics:
            return
        
        metrics = self.execution_metrics
        execution_time = metrics.get_execution_time()
        completion_rate = metrics.get_completion_rate()
        
        # Calculate estimated speedup
        estimated_sequential_time = metrics.total_tasks * 5.0  # Assume 5 min per task
        speedup = estimated_sequential_time / execution_time if execution_time > 0 else 1.0
        metrics.speedup_factor = speedup
        
        logger.info(f"Parallel execution completed:")
        logger.info(f"  Total tasks: {metrics.total_tasks}")
        logger.info(f"  Completed: {metrics.completed_tasks}")
        logger.info(f"  Failed: {metrics.failed_tasks}")
        logger.info(f"  Completion rate: {completion_rate:.1f}%")
        logger.info(f"  Execution time: {execution_time:.1f} minutes")
        logger.info(f"  Stages: {metrics.stages_completed}")
        logger.info(f"  Max concurrent groups: {metrics.max_concurrent_groups}")
        logger.info(f"  Estimated speedup: {speedup:.1f}x")
        logger.info(f"  Resource usage: {metrics.resource_usage}")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status for monitoring."""
        if not self.execution_metrics:
            return {"status": "not_started"}
        
        return {
            "status": "running" if self.active_groups else "completed",
            "total_tasks": self.execution_metrics.total_tasks,
            "completed_tasks": self.execution_metrics.completed_tasks,
            "failed_tasks": self.execution_metrics.failed_tasks,
            "completion_rate": self.execution_metrics.get_completion_rate(),
            "execution_time": self.execution_metrics.get_execution_time(),
            "active_groups": len(self.active_groups),
            "completed_groups": len(self.completed_groups),
            "failed_groups": len(self.failed_groups),
            "resource_usage": self.current_resource_usage,
            "estimated_speedup": self.execution_metrics.speedup_factor
        }
    
    async def cancel_execution(self):
        """Cancel all active parallel execution."""
        logger.info("Cancelling parallel execution")
        
        # Cancel all active group tasks
        for group_id, task in self.active_groups.items():
            logger.info(f"Cancelling group {group_id}")
            task.cancel()
        
        # Wait for cancellations to complete
        if self.active_groups:
            await asyncio.gather(*self.active_groups.values(), return_exceptions=True)
        
        self.active_groups.clear()
        logger.info("Parallel execution cancelled")