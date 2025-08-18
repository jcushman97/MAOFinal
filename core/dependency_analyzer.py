"""
Dependency Analysis Engine for MAOS Parallel Execution

Analyzes task dependencies to create optimal parallel execution groups
while preventing deadlocks and maximizing concurrency opportunities.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from core.state import Task, TaskStatus
from core.logger import get_logger

logger = get_logger("dependency_analyzer")


class ParallelStrategy(Enum):
    """Strategies for parallel task execution."""
    AGGRESSIVE = "aggressive"      # Maximum parallelism, higher resource usage
    BALANCED = "balanced"         # Balanced parallelism and resource usage
    CONSERVATIVE = "conservative" # Limited parallelism, lower resource usage


@dataclass
class TaskGroup:
    """Group of tasks that can execute in parallel."""
    id: str
    tasks: List[Task]
    priority: int
    estimated_duration: float
    resource_requirements: Dict[str, float]
    dependencies: List[str]  # IDs of other TaskGroups this depends on
    
    def __len__(self) -> int:
        return len(self.tasks)
    
    def get_total_complexity(self) -> float:
        """Calculate total complexity score for this group."""
        return sum(self._estimate_task_complexity(task) for task in self.tasks)
    
    def _estimate_task_complexity(self, task: Task) -> float:
        """Estimate complexity of a single task."""
        # Base complexity on description length and team type
        base_complexity = len(task.description) / 100.0
        
        # Team-specific complexity multipliers
        team_multipliers = {
            "frontend": 1.0,
            "backend": 1.2,
            "qa": 0.8,        # QA tasks are more atomic in Phase 3
            "research": 1.5,
            "documentation": 0.7
        }
        
        multiplier = team_multipliers.get(task.team, 1.0)
        return base_complexity * multiplier


@dataclass
class ParallelExecutionPlan:
    """Plan for parallel task execution."""
    task_groups: List[TaskGroup]
    execution_stages: List[List[TaskGroup]]  # Groups that can run simultaneously
    estimated_total_time: float
    max_concurrent_groups: int
    resource_allocation: Dict[str, float]
    
    def get_parallelism_factor(self) -> float:
        """Calculate how much parallelism this plan achieves."""
        total_tasks = sum(len(group) for group in self.task_groups)
        sequential_groups = len(self.execution_stages)
        return total_tasks / sequential_groups if sequential_groups > 0 else 1.0


class DependencyAnalyzer:
    """
    Analyzes task dependencies to create optimal parallel execution plans.
    
    Uses directed acyclic graph (DAG) analysis to identify independent task
    groups that can execute in parallel while respecting dependencies.
    """
    
    def __init__(self, strategy: ParallelStrategy = ParallelStrategy.BALANCED):
        """Initialize dependency analyzer with execution strategy."""
        self.strategy = strategy
        self.max_group_size = self._get_max_group_size()
        self.max_concurrent_groups = self._get_max_concurrent_groups()
        
    def _get_max_group_size(self) -> int:
        """Get maximum tasks per group based on strategy."""
        return {
            ParallelStrategy.AGGRESSIVE: 8,
            ParallelStrategy.BALANCED: 5,
            ParallelStrategy.CONSERVATIVE: 3
        }[self.strategy]
    
    def _get_max_concurrent_groups(self) -> int:
        """Get maximum concurrent groups based on strategy."""
        return {
            ParallelStrategy.AGGRESSIVE: 6,
            ParallelStrategy.BALANCED: 4,
            ParallelStrategy.CONSERVATIVE: 2
        }[self.strategy]
    
    def analyze_dependencies(self, tasks: List[Task]) -> ParallelExecutionPlan:
        """
        Analyze task dependencies and create parallel execution plan.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            ParallelExecutionPlan with optimized task grouping
        """
        logger.info(f"Analyzing dependencies for {len(tasks)} tasks with {self.strategy.value} strategy")
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tasks)
        
        # Validate graph for cycles
        if not self._validate_dag(dependency_graph):
            raise ValueError("Circular dependencies detected in task graph")
        
        # Create task groups based on dependencies
        task_groups = self._create_task_groups(tasks, dependency_graph)
        
        # Optimize groups for parallel execution
        optimized_groups = self._optimize_groups(task_groups, dependency_graph)
        
        # Create execution stages
        execution_stages = self._create_execution_stages(optimized_groups, dependency_graph)
        
        # Calculate resource allocation
        resource_allocation = self._calculate_resource_allocation(optimized_groups)
        
        # Estimate execution time
        estimated_time = self._estimate_execution_time(execution_stages)
        
        plan = ParallelExecutionPlan(
            task_groups=optimized_groups,
            execution_stages=execution_stages,
            estimated_total_time=estimated_time,
            max_concurrent_groups=self.max_concurrent_groups,
            resource_allocation=resource_allocation
        )
        
        logger.info(f"Created parallel execution plan: {len(optimized_groups)} groups, "
                   f"{len(execution_stages)} stages, {plan.get_parallelism_factor():.1f}x parallelism")
        
        return plan
    
    def _build_dependency_graph(self, tasks: List[Task]) -> nx.DiGraph:
        """Build directed graph of task dependencies."""
        graph = nx.DiGraph()
        
        # Add all tasks as nodes
        for task in tasks:
            graph.add_node(task.id, task=task)
        
        # Add dependency edges
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in [t.id for t in tasks]:  # Only add edges for tasks in our list
                    graph.add_edge(dep_id, task.id)
        
        return graph
    
    def _validate_dag(self, graph: nx.DiGraph) -> bool:
        """Validate that graph is a directed acyclic graph (no cycles)."""
        try:
            nx.find_cycle(graph)
            return False  # Cycle found
        except nx.NetworkXNoCycle:
            return True   # No cycle, valid DAG
    
    def _create_task_groups(self, tasks: List[Task], graph: nx.DiGraph) -> List[TaskGroup]:
        """Create initial task groups based on dependencies and characteristics."""
        task_groups = []
        grouped_tasks = set()
        
        # Find tasks with no dependencies (can start immediately)
        root_tasks = [task for task in tasks if not task.dependencies]
        
        # Group tasks by team and dependency level
        team_groups = self._group_by_team(tasks)
        dependency_levels = self._calculate_dependency_levels(tasks, graph)
        
        group_id = 0
        for team, team_tasks in team_groups.items():
            # Further group by dependency level within team
            level_groups = {}
            for task in team_tasks:
                level = dependency_levels[task.id]
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(task)
            
            # Create groups for each level
            for level, level_tasks in level_groups.items():
                # Split large groups
                while level_tasks:
                    group_tasks = level_tasks[:self.max_group_size]
                    level_tasks = level_tasks[self.max_group_size:]
                    
                    if group_tasks:
                        group = TaskGroup(
                            id=f"group_{group_id}",
                            tasks=group_tasks,
                            priority=self._calculate_group_priority(group_tasks, level),
                            estimated_duration=self._estimate_group_duration(group_tasks),
                            resource_requirements=self._estimate_resource_requirements(group_tasks),
                            dependencies=self._find_group_dependencies(group_tasks, task_groups)
                        )
                        task_groups.append(group)
                        group_id += 1
                        grouped_tasks.update(task.id for task in group_tasks)
        
        return task_groups
    
    def _group_by_team(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Group tasks by team assignment."""
        teams = {}
        for task in tasks:
            team = task.team or "general"
            if team not in teams:
                teams[team] = []
            teams[team].append(task)
        return teams
    
    def _calculate_dependency_levels(self, tasks: List[Task], graph: nx.DiGraph) -> Dict[str, int]:
        """Calculate dependency level for each task (0 = no dependencies)."""
        levels = {}
        
        def calculate_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]
            
            # Find the task
            task = next((t for t in tasks if t.id == task_id), None)
            if not task or not task.dependencies:
                levels[task_id] = 0
                return 0
            
            # Level is max dependency level + 1
            max_dep_level = max(calculate_level(dep_id) for dep_id in task.dependencies)
            levels[task_id] = max_dep_level + 1
            return levels[task_id]
        
        for task in tasks:
            calculate_level(task.id)
        
        return levels
    
    def _calculate_group_priority(self, tasks: List[Task], level: int) -> int:
        """Calculate priority for a task group."""
        # Higher priority for:
        # - Earlier dependency levels (should execute first)
        # - Critical teams (frontend for user-facing features)
        # - Shorter estimated duration (quick wins)
        
        base_priority = 100 - (level * 10)  # Earlier levels get higher priority
        
        # Team-based priority adjustments
        team_priorities = {
            "frontend": 10,
            "backend": 8,
            "qa": 6,
            "documentation": 4,
            "research": 2
        }
        
        team_bonus = max(team_priorities.get(task.team, 0) for task in tasks)
        
        return base_priority + team_bonus
    
    def _estimate_group_duration(self, tasks: List[Task]) -> float:
        """Estimate execution duration for a task group."""
        # Base duration estimates by team (in minutes)
        base_durations = {
            "frontend": 8.0,
            "backend": 10.0,
            "qa": 5.0,        # Optimized in Phase 3
            "documentation": 6.0,
            "research": 12.0
        }
        
        total_duration = 0.0
        for task in tasks:
            base = base_durations.get(task.team, 8.0)
            # Adjust for task complexity
            complexity_factor = len(task.description) / 50.0  # Longer descriptions = more complex
            complexity_factor = max(0.5, min(2.0, complexity_factor))  # Clamp between 0.5x and 2x
            total_duration += base * complexity_factor
        
        # Parallel execution within group reduces total time
        parallel_factor = 1.0 / min(len(tasks), 3)  # Up to 3 tasks can run in parallel within group
        return total_duration * parallel_factor
    
    def _estimate_resource_requirements(self, tasks: List[Task]) -> Dict[str, float]:
        """Estimate resource requirements for a task group."""
        # Resource estimates (normalized 0.0-1.0)
        team_resources = {
            "frontend": {"tokens": 0.3, "memory": 0.2, "cpu": 0.3},
            "backend": {"tokens": 0.4, "memory": 0.3, "cpu": 0.4},
            "qa": {"tokens": 0.2, "memory": 0.1, "cpu": 0.2},
            "documentation": {"tokens": 0.3, "memory": 0.1, "cpu": 0.2},
            "research": {"tokens": 0.5, "memory": 0.2, "cpu": 0.3}
        }
        
        resources = {"tokens": 0.0, "memory": 0.0, "cpu": 0.0}
        
        for task in tasks:
            task_resources = team_resources.get(task.team, {"tokens": 0.3, "memory": 0.2, "cpu": 0.3})
            for resource, amount in task_resources.items():
                resources[resource] += amount
        
        # Normalize by group size (parallel execution shares some resources)
        group_size = len(tasks)
        sharing_factor = 0.7 if group_size > 1 else 1.0
        
        return {k: v * sharing_factor for k, v in resources.items()}
    
    def _find_group_dependencies(self, group_tasks: List[Task], existing_groups: List[TaskGroup]) -> List[str]:
        """Find which existing groups this group depends on."""
        group_deps = set()
        
        for task in group_tasks:
            for dep_id in task.dependencies:
                # Find which group contains this dependency
                for group in existing_groups:
                    if any(t.id == dep_id for t in group.tasks):
                        group_deps.add(group.id)
                        break
        
        return list(group_deps)
    
    def _optimize_groups(self, groups: List[TaskGroup], graph: nx.DiGraph) -> List[TaskGroup]:
        """Optimize task groups for better parallel execution."""
        # Sort groups by priority
        groups.sort(key=lambda g: g.priority, reverse=True)
        
        # Try to merge small groups that don't have conflicting dependencies
        optimized = []
        
        for group in groups:
            merged = False
            
            # Try to merge with existing compatible group
            for existing in optimized:
                if self._can_merge_groups(group, existing, graph):
                    # Merge groups
                    existing.tasks.extend(group.tasks)
                    existing.resource_requirements = self._merge_resources(
                        existing.resource_requirements, 
                        group.resource_requirements
                    )
                    existing.estimated_duration = max(
                        existing.estimated_duration, 
                        group.estimated_duration
                    )
                    merged = True
                    break
            
            if not merged:
                optimized.append(group)
        
        return optimized
    
    def _can_merge_groups(self, group1: TaskGroup, group2: TaskGroup, graph: nx.DiGraph) -> bool:
        """Check if two groups can be merged safely."""
        # Don't merge if total size would exceed limit
        if len(group1) + len(group2) > self.max_group_size:
            return False
        
        # Don't merge groups from different teams (different expertise required)
        team1 = group1.tasks[0].team if group1.tasks else None
        team2 = group2.tasks[0].team if group2.tasks else None
        if team1 != team2:
            return False
        
        # Don't merge if there are dependencies between the groups
        group1_ids = {task.id for task in group1.tasks}
        group2_ids = {task.id for task in group2.tasks}
        
        for task1_id in group1_ids:
            for task2_id in group2_ids:
                if graph.has_edge(task1_id, task2_id) or graph.has_edge(task2_id, task1_id):
                    return False
        
        # Check resource compatibility
        merged_resources = self._merge_resources(
            group1.resource_requirements, 
            group2.resource_requirements
        )
        
        if any(amount > 1.0 for amount in merged_resources.values()):
            return False
        
        return True
    
    def _merge_resources(self, res1: Dict[str, float], res2: Dict[str, float]) -> Dict[str, float]:
        """Merge resource requirements from two groups."""
        merged = res1.copy()
        for resource, amount in res2.items():
            merged[resource] = merged.get(resource, 0.0) + amount
        return merged
    
    def _create_execution_stages(self, groups: List[TaskGroup], graph: nx.DiGraph) -> List[List[TaskGroup]]:
        """Create execution stages where groups in same stage can run in parallel."""
        stages = []
        remaining_groups = groups.copy()
        completed_groups = set()
        
        while remaining_groups:
            current_stage = []
            
            # Find groups that can execute now (all dependencies completed)
            ready_groups = []
            for group in remaining_groups:
                if all(dep_id in completed_groups for dep_id in group.dependencies):
                    ready_groups.append(group)
            
            if not ready_groups:
                # Shouldn't happen with valid DAG, but handle gracefully
                logger.warning("No ready groups found, adding first remaining group")
                ready_groups = [remaining_groups[0]]
            
            # Select groups for this stage (respect concurrency limits)
            ready_groups.sort(key=lambda g: g.priority, reverse=True)
            
            current_resources = {"tokens": 0.0, "memory": 0.0, "cpu": 0.0}
            
            for group in ready_groups:
                if len(current_stage) >= self.max_concurrent_groups:
                    break
                
                # Check if we have resources for this group
                can_add = True
                for resource, amount in group.resource_requirements.items():
                    if current_resources.get(resource, 0.0) + amount > 1.0:
                        can_add = False
                        break
                
                if can_add:
                    current_stage.append(group)
                    for resource, amount in group.resource_requirements.items():
                        current_resources[resource] = current_resources.get(resource, 0.0) + amount
            
            # If no groups could be added due to resource constraints, add highest priority group anyway
            if not current_stage and ready_groups:
                current_stage.append(ready_groups[0])
            
            stages.append(current_stage)
            
            # Mark groups as completed
            for group in current_stage:
                remaining_groups.remove(group)
                completed_groups.add(group.id)
        
        return stages
    
    def _calculate_resource_allocation(self, groups: List[TaskGroup]) -> Dict[str, float]:
        """Calculate total resource allocation for the execution plan."""
        total_resources = {"tokens": 0.0, "memory": 0.0, "cpu": 0.0}
        
        for group in groups:
            for resource, amount in group.resource_requirements.items():
                total_resources[resource] = max(total_resources.get(resource, 0.0), amount)
        
        return total_resources
    
    def _estimate_execution_time(self, stages: List[List[TaskGroup]]) -> float:
        """Estimate total execution time for all stages."""
        total_time = 0.0
        
        for stage in stages:
            # Stage time is the maximum duration of groups in that stage
            stage_time = max(group.estimated_duration for group in stage) if stage else 0.0
            total_time += stage_time
        
        return total_time
    
    def get_parallelism_opportunities(self, tasks: List[Task]) -> Dict[str, int]:
        """Analyze parallelism opportunities in the task list."""
        plan = self.analyze_dependencies(tasks)
        
        return {
            "total_tasks": len(tasks),
            "total_groups": len(plan.task_groups),
            "execution_stages": len(plan.execution_stages),
            "max_concurrent_groups": max(len(stage) for stage in plan.execution_stages) if plan.execution_stages else 0,
            "parallelism_factor": round(plan.get_parallelism_factor(), 2),
            "estimated_speedup": round(len(tasks) / plan.estimated_total_time * 5, 2)  # Assume 5min per task sequentially
        }