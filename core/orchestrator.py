"""
Main Orchestrator for MAOS

Handles the main orchestration loop, task scheduling, and agent coordination.
Implements async execution from the start as requested.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from core.config import Config
from core.state import StateManager, ProjectState, ProjectStatus, TaskStatus, LogLevel
from core.logger import get_logger
from core.parallel_orchestrator import ParallelOrchestrator, ExecutionMode, ParallelStrategy
from core.resource_manager import ResourceManager
from agents.project_manager import ProjectManagerAgent
from agents.frontend_lead import FrontendTeamLead
from agents.backend_lead import BackendTeamLead
from agents.qa_lead import QATeamLead
from agents.team_lead_agent import TeamType

logger = get_logger("orchestrator")


class Orchestrator:
    """
    Main orchestration controller for the MAOS system.
    
    Manages project lifecycle, coordinates agents, and handles task execution
    with async execution patterns for future scalability.
    """
    
    def __init__(self, config: Config, enable_parallel: bool = True, parallel_strategy: ParallelStrategy = ParallelStrategy.BALANCED):
        """Initialize orchestrator with configuration."""
        self.config = config
        self.state_manager = StateManager(config.project_dir)
        self.active_projects: Dict[str, ProjectState] = {}
        
        # Phase 4: Parallel execution capabilities
        self.enable_parallel = enable_parallel
        self.parallel_strategy = parallel_strategy
        self.parallel_orchestrator = None
        self.resource_manager = None
        
        if enable_parallel:
            self.parallel_orchestrator = ParallelOrchestrator(config, parallel_strategy)
            self.resource_manager = ResourceManager(config)
        
        logger.info(f"Orchestrator initialized with parallel execution: {enable_parallel}")
        if enable_parallel:
            logger.info(f"Parallel strategy: {parallel_strategy.value}")
    
    async def start_project(self, objective: str, dry_run: bool = False) -> str:
        """
        Start a new project with the given objective.
        
        Args:
            objective: Project description and goals
            dry_run: If True, show what would be done without executing
            
        Returns:
            Project ID of the created project
        """
        logger.info(f"Starting new project: {objective}")
        
        # Create new project state
        project_state = ProjectState(objective=objective)
        
        if dry_run:
            logger.info(f"DRY RUN - Would create project {project_state.projectId}")
            return project_state.projectId
        
        # Initialize project manager agent
        pm_agent = ProjectManagerAgent(
            agent_id="pm_001",
            config=self.config,
            project_state=project_state
        )
        
        try:
            # Add project to active projects
            self.active_projects[project_state.projectId] = project_state
            
            # Save initial state
            await self.state_manager.save_state(project_state)
            
            # Start planning phase
            project_state.status = ProjectStatus.PLANNING
            project_state.add_log_entry(LogLevel.INFO, "orchestrator", "Project planning started")
            
            # Have PM create initial task breakdown
            await pm_agent.plan_project()
            
            # Transition to execution phase
            project_state.status = ProjectStatus.EXECUTING
            project_state.add_log_entry(LogLevel.INFO, "orchestrator", "Project execution started")
            
            # Phase 4: Choose execution strategy (parallel or sequential)
            if self.enable_parallel and self.parallel_orchestrator:
                # Start resource monitoring
                if self.resource_manager:
                    await self.resource_manager.start_monitoring()
                
                # Use parallel execution
                await self._execute_project_tasks_parallel(project_state)
                
                # Stop resource monitoring
                if self.resource_manager:
                    await self.resource_manager.stop_monitoring()
            else:
                # Use traditional sequential execution
                await self._execute_project_tasks(project_state)
            
            # Mark project as complete if all tasks successful
            if self._all_tasks_complete(project_state):
                project_state.status = ProjectStatus.COMPLETE
                project_state.add_log_entry(LogLevel.INFO, "orchestrator", "Project completed successfully")
            else:
                project_state.status = ProjectStatus.FAILED
                project_state.add_log_entry(LogLevel.ERROR, "orchestrator", "Project failed to complete")
            
            # Save final state
            await self.state_manager.save_state(project_state)
            
            logger.info(f"Project {project_state.projectId} completed with status: {project_state.status}")
            return project_state.projectId
            
        except Exception as e:
            logger.error(f"Project execution failed: {e}")
            project_state.status = ProjectStatus.FAILED
            project_state.add_log_entry(LogLevel.ERROR, "orchestrator", f"Project failed with error: {str(e)}")
            await self.state_manager.save_state(project_state)
            raise
        finally:
            # Remove from active projects
            self.active_projects.pop(project_state.projectId, None)
    
    async def resume_project(self, project_id: str) -> bool:
        """
        Resume a paused project.
        
        Args:
            project_id: ID of the project to resume
            
        Returns:
            True if project was successfully resumed
        """
        logger.info(f"Resuming project {project_id}")
        
        # Load project state
        project_state = await self.state_manager.load_state(project_id)
        if not project_state:
            logger.error(f"Could not load project {project_id}")
            return False
        
        # Check if project can be resumed
        if project_state.status in [ProjectStatus.COMPLETE, ProjectStatus.FAILED]:
            logger.error(f"Cannot resume project {project_id} with status {project_state.status}")
            return False
        
        try:
            # Add to active projects
            self.active_projects[project_id] = project_state
            
            # Resume execution
            project_state.status = ProjectStatus.EXECUTING
            project_state.add_log_entry(LogLevel.INFO, "orchestrator", "Project resumed")
            
            # Continue task execution
            await self._execute_project_tasks(project_state)
            
            # Update final status
            if self._all_tasks_complete(project_state):
                project_state.status = ProjectStatus.COMPLETE
                project_state.add_log_entry(LogLevel.INFO, "orchestrator", "Project completed successfully")
            else:
                project_state.status = ProjectStatus.FAILED
                project_state.add_log_entry(LogLevel.ERROR, "orchestrator", "Project failed to complete")
            
            # Save final state
            await self.state_manager.save_state(project_state)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume project {project_id}: {e}")
            project_state.status = ProjectStatus.FAILED
            project_state.add_log_entry(LogLevel.ERROR, "orchestrator", f"Resume failed: {str(e)}")
            await self.state_manager.save_state(project_state)
            return False
        finally:
            # Remove from active projects
            self.active_projects.pop(project_id, None)
    
    async def monitor_project(self, project_id: str) -> bool:
        """
        Monitor an active project (read-only mode).
        
        Args:
            project_id: ID of the project to monitor
            
        Returns:
            True if monitoring was successful
        """
        logger.info(f"Monitoring project {project_id}")
        
        # Load project state
        project_state = await self.state_manager.load_state(project_id)
        if not project_state:
            logger.error(f"Could not load project {project_id}")
            return False
        
        # Display project status
        print(f"\nProject: {project_state.objective}")
        print(f"Status: {project_state.status}")
        print(f"Created: {datetime.fromtimestamp(project_state.createdAt)}")
        print(f"Updated: {datetime.fromtimestamp(project_state.updatedAt)}")
        print(f"Tasks: {len(project_state.tasks)}")
        
        # Display task summary
        task_counts = {
            TaskStatus.QUEUED: 0,
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.COMPLETE: 0,
            TaskStatus.FAILED: 0
        }
        
        for task in project_state.tasks:
            task_counts[task.status] += 1
        
        print(f"Task Status:")
        for status, count in task_counts.items():
            print(f"  {status}: {count}")
        
        # Display recent logs
        if project_state.logs:
            print(f"\nRecent Logs:")
            for log_entry in project_state.logs[-10:]:  # Last 10 logs
                timestamp = datetime.fromtimestamp(log_entry.timestamp)
                print(f"  {timestamp} [{log_entry.agent}] {log_entry.level}: {log_entry.message}")
        
        return True
    
    async def _execute_project_tasks(self, project_state: ProjectState):
        """
        Execute project tasks sequentially.
        
        This implements sequential execution as specified for Phase 1.
        Future versions will support parallel execution.
        """
        logger.info(f"Executing tasks for project {project_state.projectId}")
        
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
            await self.state_manager.save_state(project_state)
            
            try:
                # Phase 2: Route tasks to appropriate team lead agents
                executing_agent = await self._get_task_agent(task, project_state)
                
                success = await executing_agent.execute_task(task)
                
                if success:
                    project_state.update_task_status(task.id, TaskStatus.COMPLETE)
                    logger.info(f"Task completed successfully: {task.description}")
                else:
                    project_state.update_task_status(task.id, TaskStatus.FAILED, "Task execution failed")
                    logger.error(f"Task failed: {task.description}")
                
            except Exception as e:
                project_state.update_task_status(task.id, TaskStatus.FAILED, str(e))
                logger.error(f"Task execution error: {e}")
            
            # Save state after each task
            await self.state_manager.save_state(project_state)
            
            iteration += 1
        
        if iteration >= max_iterations:
            logger.error("Maximum task execution iterations reached")
            project_state.add_log_entry(LogLevel.ERROR, "orchestrator", "Maximum iterations reached")
    
    async def _execute_project_tasks_parallel(self, project_state: ProjectState):
        """
        Execute project tasks using parallel orchestration.
        
        Phase 4: Intelligent parallel execution with dependency management,
        resource allocation, and quality assurance.
        """
        logger.info(f"Starting parallel execution for project {project_state.projectId}")
        
        # Use hybrid mode for intelligent parallel/sequential selection
        success = await self.parallel_orchestrator.execute_project_parallel(
            project_state, 
            mode=ExecutionMode.HYBRID
        )
        
        if success:
            logger.info("Parallel execution completed successfully")
        else:
            logger.error("Parallel execution failed")
            
        # Log execution metrics
        if hasattr(self.parallel_orchestrator, 'execution_metrics') and self.parallel_orchestrator.execution_metrics:
            metrics = self.parallel_orchestrator.execution_metrics
            project_state.add_log_entry(
                LogLevel.INFO, 
                "parallel_orchestrator",
                f"Execution metrics: {metrics.completed_tasks}/{metrics.total_tasks} completed, "
                f"{metrics.get_execution_time():.1f}min total, "
                f"{metrics.speedup_factor:.1f}x speedup"
            )
    
    def _all_tasks_complete(self, project_state: ProjectState) -> bool:
        """Check if all tasks are in COMPLETE status."""
        return all(task.status == TaskStatus.COMPLETE for task in project_state.tasks)
    
    def _all_tasks_complete_or_failed(self, project_state: ProjectState) -> bool:
        """Check if all tasks are either COMPLETE or FAILED."""
        return all(
            task.status in [TaskStatus.COMPLETE, TaskStatus.FAILED] 
            for task in project_state.tasks
        )
    
    def list_projects(self) -> list[str]:
        """List all available project IDs."""
        return self.state_manager.list_projects()
    
    async def _get_task_agent(self, task, project_state):
        """
        Route task to appropriate agent based on team and task characteristics.
        
        Phase 2: Implement hierarchical task delegation
        - PM agent for planning tasks
        - Team Lead agents for specialized execution
        - Fallback to PM for unspecified teams
        
        Args:
            task: Task to be executed
            project_state: Current project state
            
        Returns:
            Agent instance capable of executing the task
        """
        team_type = task.team.lower() if task.team else "general"
        
        # Route based on team assignment
        if team_type == TeamType.FRONTEND.value:
            agent_id = f"frontend_lead_{project_state.projectId[:8]}"
            return FrontendTeamLead(
                agent_id=agent_id,
                config=self.config,
                project_state=project_state
            )
        
        elif team_type == TeamType.BACKEND.value:
            agent_id = f"backend_lead_{project_state.projectId[:8]}"
            return BackendTeamLead(
                agent_id=agent_id,
                config=self.config,
                project_state=project_state
            )
        
        elif team_type == TeamType.QA.value:
            agent_id = f"qa_lead_{project_state.projectId[:8]}"
            return QATeamLead(
                agent_id=agent_id,
                config=self.config,
                project_state=project_state
            )
        
        else:
            # Default to Project Manager for planning, general, or unspecified tasks
            return ProjectManagerAgent(
                agent_id="pm_001",
                config=self.config,
                project_state=project_state
            )
    
    def get_agent_status(self, project_state: ProjectState) -> Dict[str, Any]:
        """
        Get status of all active agents for this project.
        
        Returns:
            Dictionary with agent status information
        """
        agent_status = {}
        
        # Count tasks by team
        for task in project_state.tasks:
            team = task.team or "general"
            if team not in agent_status:
                agent_status[team] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "failed_tasks": 0
                }
            
            agent_status[team]["total_tasks"] += 1
            if task.status == TaskStatus.COMPLETE:
                agent_status[team]["completed_tasks"] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                agent_status[team]["in_progress_tasks"] += 1
            elif task.status == TaskStatus.FAILED:
                agent_status[team]["failed_tasks"] += 1
        
        return agent_status
    
    # Phase 4: Parallel execution monitoring and control methods
    
    def get_parallel_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get parallel execution status for a project.
        
        Args:
            project_id: Project ID to check
            
        Returns:
            Parallel execution status and metrics
        """
        if not self.enable_parallel or not self.parallel_orchestrator:
            return {"parallel_enabled": False}
        
        # Get orchestrator status
        orchestrator_status = self.parallel_orchestrator.get_execution_status()
        
        # Get resource manager status
        resource_status = {}
        if self.resource_manager:
            resource_status = self.resource_manager.get_resource_status()
        
        return {
            "parallel_enabled": True,
            "strategy": self.parallel_strategy.value,
            "execution_status": orchestrator_status,
            "resource_status": resource_status,
            "project_id": project_id
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics for parallel execution."""
        if not self.enable_parallel:
            return {"parallel_enabled": False}
        
        metrics = {
            "parallel_enabled": True,
            "strategy": self.parallel_strategy.value
        }
        
        # Get orchestrator metrics
        if self.parallel_orchestrator and hasattr(self.parallel_orchestrator, 'execution_metrics'):
            if self.parallel_orchestrator.execution_metrics:
                metrics["execution_metrics"] = {
                    "total_tasks": self.parallel_orchestrator.execution_metrics.total_tasks,
                    "completed_tasks": self.parallel_orchestrator.execution_metrics.completed_tasks,
                    "failed_tasks": self.parallel_orchestrator.execution_metrics.failed_tasks,
                    "completion_rate": self.parallel_orchestrator.execution_metrics.get_completion_rate(),
                    "execution_time": self.parallel_orchestrator.execution_metrics.get_execution_time(),
                    "speedup_factor": self.parallel_orchestrator.execution_metrics.speedup_factor
                }
        
        # Get resource metrics
        if self.resource_manager:
            try:
                resource_metrics = self.resource_manager.get_performance_metrics()
                metrics["resource_metrics"] = resource_metrics
            except Exception as e:
                logger.warning(f"Failed to get resource metrics: {e}")
        
        return metrics
    
    async def optimize_parallel_execution(self) -> Dict[str, Any]:
        """Optimize parallel execution settings based on performance data."""
        if not self.enable_parallel:
            return {"parallel_enabled": False}
        
        optimizations = {
            "parallel_enabled": True,
            "applied_optimizations": []
        }
        
        # Get current performance
        metrics = self.get_performance_metrics()
        
        # Optimize resource manager
        if self.resource_manager:
            try:
                resource_status = self.resource_manager.get_resource_status()
                
                # Check for resource optimization opportunities
                utilization = resource_status.get("utilization", {})
                
                for resource, usage in utilization.items():
                    if usage < 30:  # Underutilized
                        optimizations["applied_optimizations"].append(f"increase_{resource}_allocation")
                    elif usage > 90:  # Overutilized
                        optimizations["applied_optimizations"].append(f"reduce_{resource}_allocation")
                
            except Exception as e:
                logger.warning(f"Failed to optimize resource management: {e}")
        
        # Optimize parallel strategy based on performance
        if "execution_metrics" in metrics:
            exec_metrics = metrics["execution_metrics"]
            completion_rate = exec_metrics.get("completion_rate", 0)
            speedup_factor = exec_metrics.get("speedup_factor", 1.0)
            
            if completion_rate < 80:  # Low success rate
                if self.parallel_strategy == ParallelStrategy.AGGRESSIVE:
                    self.parallel_strategy = ParallelStrategy.BALANCED
                    optimizations["applied_optimizations"].append("reduced_strategy_to_balanced")
                elif self.parallel_strategy == ParallelStrategy.BALANCED:
                    self.parallel_strategy = ParallelStrategy.CONSERVATIVE
                    optimizations["applied_optimizations"].append("reduced_strategy_to_conservative")
            
            elif speedup_factor < 1.2:  # Low speedup
                if self.parallel_strategy == ParallelStrategy.CONSERVATIVE:
                    self.parallel_strategy = ParallelStrategy.BALANCED
                    optimizations["applied_optimizations"].append("increased_strategy_to_balanced")
                elif self.parallel_strategy == ParallelStrategy.BALANCED:
                    self.parallel_strategy = ParallelStrategy.AGGRESSIVE
                    optimizations["applied_optimizations"].append("increased_strategy_to_aggressive")
        
        logger.info(f"Applied parallel execution optimizations: {optimizations['applied_optimizations']}")
        
        return optimizations
    
    async def cancel_parallel_execution(self, project_id: str) -> bool:
        """Cancel parallel execution for a specific project."""
        if not self.enable_parallel or not self.parallel_orchestrator:
            return False
        
        try:
            await self.parallel_orchestrator.cancel_execution()
            logger.info(f"Cancelled parallel execution for project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel parallel execution: {e}")
            return False
    
    def set_parallel_strategy(self, strategy: ParallelStrategy):
        """Change the parallel execution strategy."""
        old_strategy = self.parallel_strategy
        self.parallel_strategy = strategy
        
        if self.parallel_orchestrator:
            self.parallel_orchestrator.strategy = strategy
            self.parallel_orchestrator.dependency_analyzer.strategy = strategy
        
        logger.info(f"Changed parallel strategy from {old_strategy.value} to {strategy.value}")
    
    def get_parallel_capabilities(self) -> Dict[str, Any]:
        """Get parallel execution capabilities and recommendations."""
        if not self.enable_parallel:
            return {"parallel_enabled": False}
        
        capabilities = {
            "parallel_enabled": True,
            "current_strategy": self.parallel_strategy.value,
            "available_strategies": [s.value for s in ParallelStrategy],
            "features": [
                "dependency_analysis",
                "resource_management", 
                "load_balancing",
                "performance_monitoring",
                "intelligent_task_grouping",
                "error_recovery",
                "hybrid_execution"
            ]
        }
        
        # Add resource capabilities
        if self.resource_manager:
            try:
                optimal_concurrency = self.resource_manager.get_optimal_concurrency()
                capabilities["optimal_concurrency"] = optimal_concurrency
                capabilities["resource_monitoring"] = True
            except Exception as e:
                logger.warning(f"Failed to get resource capabilities: {e}")
        
        return capabilities