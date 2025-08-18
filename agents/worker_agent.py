"""
Worker Agent Base Class for MAOS

Provides atomic task execution capabilities for specialized workers.
Workers handle specific, focused tasks delegated by Team Lead agents.
"""

import asyncio
from abc import abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import uuid

from agents.base_agent import BaseAgent, AgentType
from core.state import Task, TaskStatus, LogLevel
from core.logger import get_logger

logger = get_logger("worker_agent")


class WorkerSpecialty(Enum):
    """Types of worker specialties within teams."""
    # Frontend specialties
    HTML_SPECIALIST = "html_specialist"
    CSS_SPECIALIST = "css_specialist"
    JS_SPECIALIST = "javascript_specialist"
    REACT_SPECIALIST = "react_specialist"
    
    # Backend specialties
    API_SPECIALIST = "api_specialist"
    DATABASE_SPECIALIST = "database_specialist"
    AUTH_SPECIALIST = "auth_specialist"
    INTEGRATION_SPECIALIST = "integration_specialist"
    
    # QA specialties
    UNIT_TEST_SPECIALIST = "unit_test_specialist"
    E2E_TEST_SPECIALIST = "e2e_test_specialist"
    PERFORMANCE_TEST_SPECIALIST = "performance_test_specialist"
    SECURITY_TEST_SPECIALIST = "security_test_specialist"
    QA_HTML = "qa_html_validator"
    QA_CSS = "qa_css_validator" 
    QA_JS = "qa_js_validator"
    QA_PERFORMANCE = "qa_performance_tester"
    
    # General specialties
    DOCUMENTATION_SPECIALIST = "documentation_specialist"
    REFACTORING_SPECIALIST = "refactoring_specialist"
    OPTIMIZATION_SPECIALIST = "optimization_specialist"


class WorkerAgent(BaseAgent):
    """
    Worker Agent for atomic task execution.
    
    Workers are the most specialized agents in the hierarchy, handling
    specific, focused tasks with deep expertise in narrow domains.
    They execute tasks in parallel within their teams.
    
    Responsibilities:
    - Execute atomic, focused tasks
    - Apply deep specialty expertise
    - Work in parallel with other workers
    - Report progress to Team Leads
    - Optimize for speed and quality
    """
    
    def __init__(
        self,
        agent_id: str,
        specialty: WorkerSpecialty,
        team_type: str,
        config,
        project_state,
        model_preference: Optional[str] = None
    ):
        """
        Initialize Worker agent.
        
        Args:
            agent_id: Unique identifier for this worker
            specialty: Worker's area of specialization
            team_type: Team this worker belongs to
            config: System configuration
            project_state: Current project state
            model_preference: Preferred LLM model for this specialty
        """
        # Generate unique worker ID if not provided
        if not agent_id:
            agent_id = f"worker_{specialty.value}_{uuid.uuid4().hex[:8]}"
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.WORKER,
            config=config,
            project_state=project_state,
            model_preference=model_preference or self._get_specialty_model_preference(specialty)
        )
        
        self.specialty = specialty
        self.team_type = team_type
        self.execution_context = self._initialize_execution_context()
        self.performance_metrics = self._initialize_metrics()
        
        logger.info(f"Worker {agent_id} initialized with {specialty.value} specialty")
    
    def _get_specialty_model_preference(self, specialty: WorkerSpecialty) -> str:
        """Get preferred model for this specialty."""
        # Phase 3: Specialty-specific model routing
        # Different specialties might prefer different models
        specialty_model_preferences = {
            # Frontend specialties - Claude for UI/UX
            WorkerSpecialty.HTML_SPECIALIST: "claude",
            WorkerSpecialty.CSS_SPECIALIST: "claude",
            WorkerSpecialty.JS_SPECIALIST: "claude",
            WorkerSpecialty.REACT_SPECIALIST: "claude",
            
            # Backend specialties - Could use GPT for some tasks
            WorkerSpecialty.API_SPECIALIST: "claude",
            WorkerSpecialty.DATABASE_SPECIALIST: "claude",
            WorkerSpecialty.AUTH_SPECIALIST: "claude",
            WorkerSpecialty.INTEGRATION_SPECIALIST: "claude",
            
            # QA specialties - Could use specialized models
            WorkerSpecialty.UNIT_TEST_SPECIALIST: "claude",
            WorkerSpecialty.E2E_TEST_SPECIALIST: "claude",
            WorkerSpecialty.PERFORMANCE_TEST_SPECIALIST: "claude",
            WorkerSpecialty.SECURITY_TEST_SPECIALIST: "claude",
            
            # General specialties
            WorkerSpecialty.DOCUMENTATION_SPECIALIST: "claude",
            WorkerSpecialty.REFACTORING_SPECIALIST: "claude",
            WorkerSpecialty.OPTIMIZATION_SPECIALIST: "claude"
        }
        
        return specialty_model_preferences.get(specialty, "claude")
    
    def _initialize_execution_context(self) -> Dict[str, Any]:
        """Initialize execution context for this worker."""
        return {
            "specialty": self.specialty.value,
            "team": self.team_type,
            "parallel_capable": True,
            "atomic_execution": True,
            "max_execution_time": 120,  # 2 minutes for atomic tasks
            "retry_on_failure": True,
            "quality_threshold": 0.9
        }
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize performance metrics tracking."""
        return {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_execution_time": 0,
            "quality_score": 1.0,
            "parallel_executions": 0,
            "tokens_per_task": 0
        }
    
    async def execute_task(self, task: Task) -> bool:
        """
        Execute an atomic task with specialty expertise.
        
        Args:
            task: Task to execute
            
        Returns:
            True if task completed successfully
        """
        self._log(LogLevel.INFO, f"Worker {self.specialty.value} executing: {task.description}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate task is appropriate for this worker
            if not self._validate_task_for_specialty(task):
                self._log(LogLevel.WARNING, f"Task {task.id} may not match {self.specialty.value} specialty")
            
            # Increment attempt counter
            task.attempts += 1
            
            # Build atomic execution prompt
            prompt = self._build_atomic_prompt(task)
            
            # Execute with specialty expertise
            response = await self.call_llm(
                prompt=prompt,
                task_type=self._map_specialty_to_task_type(),
                expect_json=False,
                max_retries=2  # Fewer retries for atomic tasks
            )
            
            # Process and validate output
            processed_output = await self._process_atomic_output(task, response["output"])
            
            # Save atomic task result
            await self._save_atomic_result(task, processed_output)
            
            # Update metrics
            execution_time = asyncio.get_event_loop().time() - start_time
            self._update_metrics(True, execution_time, response.get("metadata", {}))
            
            self._log(LogLevel.INFO, f"Atomic task completed in {execution_time:.2f}s: {task.description}")
            return True
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Atomic task execution failed: {e}")
            task.error = str(e)
            
            # Update metrics
            execution_time = asyncio.get_event_loop().time() - start_time
            self._update_metrics(False, execution_time, {})
            
            return False
    
    def _validate_task_for_specialty(self, task: Task) -> bool:
        """Validate that task matches worker's specialty."""
        # Override in specialized workers for specific validation
        return True
    
    @abstractmethod
    def _build_atomic_prompt(self, task: Task) -> str:
        """Build a prompt for atomic task execution."""
        pass
    
    def _map_specialty_to_task_type(self) -> str:
        """Map specialty to task type for LLM routing."""
        # Map specialties to general categories
        if "test" in self.specialty.value:
            return "testing"
        elif any(x in self.specialty.value for x in ["html", "css", "js", "react"]):
            return "frontend"
        elif any(x in self.specialty.value for x in ["api", "database", "auth", "integration"]):
            return "backend"
        else:
            return "general"
    
    async def _process_atomic_output(self, task: Task, output: str) -> str:
        """Process output from atomic task execution."""
        # Base implementation - specialized workers can override
        return output
    
    async def _save_atomic_result(self, task: Task, output: str):
        """Save atomic task result."""
        try:
            # Create artifacts directory
            project_dir = self.config.project_dir / self.project_state.projectId
            artifacts_dir = project_dir / "artifacts" / "workers"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create artifact file with worker context
            artifact_filename = f"{task.id}_{self.specialty.value}_{self.agent_id[-8:]}.txt"
            artifact_path = artifacts_dir / artifact_filename
            
            # Write output to artifact file
            with open(artifact_path, 'w', encoding='utf-8') as f:
                f.write(f"Task: {task.description}\n")
                f.write(f"Worker: {self.agent_id}\n")
                f.write(f"Specialty: {self.specialty.value}\n")
                f.write(f"Team: {self.team_type}\n")
                f.write(f"Generated: {self.project_state.updatedAt}\n")
                f.write("-" * 50 + "\n")
                f.write(output)
            
            # Add artifact to task
            task.artifacts.append(str(artifact_path))
            
            self._log(LogLevel.INFO, f"Saved atomic result: {artifact_filename}")
            
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to save atomic result: {e}")
    
    def _update_metrics(self, success: bool, execution_time: float, metadata: Dict[str, Any]):
        """Update performance metrics."""
        if success:
            self.performance_metrics["tasks_completed"] += 1
        else:
            self.performance_metrics["tasks_failed"] += 1
        
        # Update average execution time
        total_tasks = self.performance_metrics["tasks_completed"] + self.performance_metrics["tasks_failed"]
        current_avg = self.performance_metrics["average_execution_time"]
        self.performance_metrics["average_execution_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
        
        # Update tokens per task
        tokens_used = metadata.get("tokens_used", 0)
        if tokens_used > 0:
            current_tokens = self.performance_metrics["tokens_per_task"]
            self.performance_metrics["tokens_per_task"] = (
                (current_tokens * (total_tasks - 1) + tokens_used) / total_tasks
            )
    
    def get_capabilities(self) -> List[str]:
        """Get worker capabilities."""
        return [
            f"specialty_{self.specialty.value}",
            "atomic_execution",
            "parallel_processing",
            "focused_expertise",
            "rapid_execution",
            "quality_validation"
        ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()
    
    async def can_execute_parallel(self, task: Task) -> bool:
        """Check if this worker can execute task in parallel."""
        # Check if task has no blocking dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                dep_task = self.project_state.get_task(dep_id)
                if dep_task and dep_task.status != TaskStatus.COMPLETE:
                    return False
        
        # Check if worker is not overloaded
        if self.performance_metrics["parallel_executions"] >= 3:
            return False
        
        return True
    
    async def execute_parallel(self, tasks: List[Task]) -> List[bool]:
        """Execute multiple tasks in parallel."""
        self._log(LogLevel.INFO, f"Worker {self.agent_id} executing {len(tasks)} tasks in parallel")
        
        # Track parallel executions
        self.performance_metrics["parallel_executions"] = len(tasks)
        
        # Execute tasks concurrently
        results = await asyncio.gather(
            *[self.execute_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Reset parallel execution count
        self.performance_metrics["parallel_executions"] = 0
        
        # Process results
        success_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._log(LogLevel.ERROR, f"Parallel task {tasks[i].id} failed: {result}")
                success_results.append(False)
            else:
                success_results.append(result)
        
        return success_results
    
    # Phase 4: Enhanced concurrency capabilities
    
    async def execute_concurrent_batch(self, tasks: List[Task], batch_size: int = 3) -> Dict[str, Any]:
        """
        Execute tasks in batches for better resource management.
        
        Args:
            tasks: Tasks to execute
            batch_size: Number of tasks per batch
            
        Returns:
            Execution results and metrics
        """
        self._log(LogLevel.INFO, f"Worker {self.agent_id} executing {len(tasks)} tasks in batches of {batch_size}")
        
        start_time = asyncio.get_event_loop().time()
        all_results = []
        batch_metrics = {
            "total_tasks": len(tasks),
            "successful_tasks": 0,
            "failed_tasks": 0,
            "batches_processed": 0,
            "average_batch_time": 0.0,
            "resource_efficiency": 0.0
        }
        
        # Process tasks in batches
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_start = asyncio.get_event_loop().time()
            
            self._log(LogLevel.DEBUG, f"Processing batch {batch_metrics['batches_processed'] + 1} with {len(batch)} tasks")
            
            # Execute batch
            batch_results = await self.execute_parallel(batch)
            all_results.extend(batch_results)
            
            # Update metrics
            batch_metrics["batches_processed"] += 1
            batch_metrics["successful_tasks"] += sum(1 for r in batch_results if r)
            batch_metrics["failed_tasks"] += sum(1 for r in batch_results if not r)
            
            batch_time = asyncio.get_event_loop().time() - batch_start
            batch_metrics["average_batch_time"] = (
                (batch_metrics["average_batch_time"] * (batch_metrics["batches_processed"] - 1) + batch_time) /
                batch_metrics["batches_processed"]
            )
            
            # Brief pause between batches to allow resource recovery
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.1)
        
        # Calculate overall metrics
        total_time = asyncio.get_event_loop().time() - start_time
        batch_metrics["total_execution_time"] = total_time
        batch_metrics["resource_efficiency"] = self._calculate_resource_efficiency(batch_metrics)
        
        self._log(LogLevel.INFO, 
                 f"Batch execution completed: {batch_metrics['successful_tasks']}/{batch_metrics['total_tasks']} successful, "
                 f"{total_time:.1f}s total time")
        
        return {
            "results": all_results,
            "metrics": batch_metrics
        }
    
    def _calculate_resource_efficiency(self, metrics: Dict[str, Any]) -> float:
        """Calculate resource efficiency score (0-100)."""
        success_rate = metrics["successful_tasks"] / metrics["total_tasks"] if metrics["total_tasks"] > 0 else 0
        
        # Efficiency based on success rate and speed
        # Perfect efficiency = 100% success rate with minimal time
        time_efficiency = 1.0 / max(1.0, metrics["average_batch_time"] / 30.0)  # 30s baseline
        time_efficiency = min(1.0, time_efficiency)
        
        return (success_rate * 0.7 + time_efficiency * 0.3) * 100
    
    async def check_resource_availability(self) -> Dict[str, Any]:
        """Check current resource availability for concurrency decisions."""
        # Simulate resource checking (in real implementation, would check actual system resources)
        return {
            "memory_available": True,
            "cpu_available": True,
            "token_budget_remaining": 0.8,  # 80% remaining
            "concurrent_capacity": max(0, 3 - self.performance_metrics.get("parallel_executions", 0)),
            "optimal_batch_size": self._get_optimal_batch_size(),
            "resource_status": "available"  # available, limited, exhausted
        }
    
    def _get_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on current performance."""
        # Base batch size on recent performance
        avg_time = self.performance_metrics.get("average_execution_time", 30.0)
        
        if avg_time < 10.0:
            return 5  # Fast tasks can be batched more
        elif avg_time < 30.0:
            return 3  # Medium tasks use standard batching
        else:
            return 2  # Slow tasks need smaller batches
    
    async def coordinate_with_peers(self, peer_workers: List['WorkerAgent']) -> Dict[str, Any]:
        """
        Coordinate with peer workers to optimize resource usage.
        
        Args:
            peer_workers: Other worker agents in the same execution context
            
        Returns:
            Coordination recommendations
        """
        if not peer_workers:
            return {"coordination_needed": False}
        
        # Analyze peer performance
        peer_metrics = []
        for peer in peer_workers:
            if hasattr(peer, 'performance_metrics'):
                peer_metrics.append({
                    "worker_id": peer.agent_id,
                    "specialty": getattr(peer, 'specialty', 'unknown'),
                    "current_load": peer.performance_metrics.get("parallel_executions", 0),
                    "average_time": peer.performance_metrics.get("average_execution_time", 0)
                })
        
        # Determine coordination strategy
        coordination = {
            "coordination_needed": len(peer_metrics) > 0,
            "peer_count": len(peer_metrics),
            "recommended_actions": [],
            "load_balancing_suggestion": None
        }
        
        if peer_metrics:
            # Check for load imbalance
            loads = [pm["current_load"] for pm in peer_metrics]
            my_load = self.performance_metrics.get("parallel_executions", 0)
            
            avg_load = (sum(loads) + my_load) / (len(loads) + 1)
            
            if my_load > avg_load * 1.5:
                coordination["recommended_actions"].append("reduce_load")
                coordination["load_balancing_suggestion"] = "defer_new_tasks"
            elif my_load < avg_load * 0.5:
                coordination["recommended_actions"].append("accept_more_load")
                coordination["load_balancing_suggestion"] = "accept_additional_tasks"
        
        return coordination
    
    async def execute_with_resource_monitoring(self, task: Task) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute task with detailed resource monitoring.
        
        Args:
            task: Task to execute
            
        Returns:
            Tuple of (success, resource_usage_report)
        """
        # Check resources before execution
        pre_resources = await self.check_resource_availability()
        start_time = asyncio.get_event_loop().time()
        
        # Execute task
        success = await self.execute_task(task)
        
        # Check resources after execution
        post_resources = await self.check_resource_availability()
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Generate resource usage report
        resource_report = {
            "execution_time": execution_time,
            "success": success,
            "pre_execution_resources": pre_resources,
            "post_execution_resources": post_resources,
            "resource_efficiency": self._calculate_execution_efficiency(execution_time, success),
            "recommendations": self._generate_resource_recommendations(pre_resources, post_resources, execution_time)
        }
        
        return success, resource_report
    
    def _calculate_execution_efficiency(self, execution_time: float, success: bool) -> float:
        """Calculate efficiency score for a single execution."""
        if not success:
            return 0.0
        
        # Efficiency based on speed compared to average
        avg_time = self.performance_metrics.get("average_execution_time", 30.0)
        if avg_time > 0:
            time_efficiency = min(1.0, avg_time / execution_time)
        else:
            time_efficiency = 1.0
        
        return time_efficiency * 100
    
    def _generate_resource_recommendations(
        self, 
        pre_resources: Dict[str, Any], 
        post_resources: Dict[str, Any], 
        execution_time: float
    ) -> List[str]:
        """Generate recommendations based on resource usage."""
        recommendations = []
        
        # Check if resources were depleted
        if (pre_resources.get("token_budget_remaining", 1.0) > 0.5 and 
            post_resources.get("token_budget_remaining", 1.0) < 0.3):
            recommendations.append("Consider smaller batch sizes to conserve tokens")
        
        # Check execution time
        avg_time = self.performance_metrics.get("average_execution_time", 30.0)
        if execution_time > avg_time * 1.5:
            recommendations.append("Task took longer than average, check for optimization opportunities")
        
        # Check concurrent capacity
        if post_resources.get("concurrent_capacity", 0) == 0:
            recommendations.append("At maximum concurrent capacity, avoid additional parallel tasks")
        
        return recommendations
    
    def get_concurrency_status(self) -> Dict[str, Any]:
        """Get current concurrency status and capabilities."""
        return {
            "worker_id": self.agent_id,
            "specialty": getattr(self, 'specialty', 'unknown'),
            "current_parallel_executions": self.performance_metrics.get("parallel_executions", 0),
            "max_parallel_capacity": 3,
            "can_accept_more_tasks": self.performance_metrics.get("parallel_executions", 0) < 3,
            "average_execution_time": self.performance_metrics.get("average_execution_time", 0),
            "success_rate": self._calculate_success_rate(),
            "optimal_batch_size": self._get_optimal_batch_size(),
            "resource_efficiency": self.performance_metrics.get("resource_efficiency", 100.0)
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate current success rate."""
        completed = self.performance_metrics.get("tasks_completed", 0)
        failed = self.performance_metrics.get("tasks_failed", 0)
        total = completed + failed
        
        return (completed / total * 100) if total > 0 else 100.0
    
    async def optimize_for_parallel_execution(self) -> Dict[str, Any]:
        """Optimize worker configuration for parallel execution."""
        current_metrics = self.get_performance_metrics()
        
        # Analyze performance patterns
        avg_time = current_metrics.get("average_execution_time", 30.0)
        success_rate = self._calculate_success_rate()
        
        optimizations = {
            "applied_optimizations": [],
            "recommended_batch_size": self._get_optimal_batch_size(),
            "performance_score": (success_rate * 0.6 + (100 - min(100, avg_time)) * 0.4)
        }
        
        # Apply optimizations based on performance
        if avg_time > 60.0:
            # Tasks are taking too long
            optimizations["applied_optimizations"].append("increased_timeout_threshold")
            self.execution_context["max_execution_time"] = min(180, avg_time * 1.5)
        
        if success_rate < 80.0:
            # Too many failures
            optimizations["applied_optimizations"].append("increased_retry_attempts")
            self.execution_context["retry_on_failure"] = True
        
        if current_metrics.get("parallel_executions", 0) > 0:
            # Currently executing in parallel
            optimizations["applied_optimizations"].append("parallel_execution_monitoring")
        
        self._log(LogLevel.INFO, f"Worker optimization applied: {optimizations['applied_optimizations']}")
        
        return optimizations