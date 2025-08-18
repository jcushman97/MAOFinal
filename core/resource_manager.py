"""
Resource Management Framework for MAOS Parallel Execution

Intelligent resource allocation and monitoring for optimal parallel performance
while preventing resource exhaustion and maintaining quality standards.
"""

import asyncio
import psutil
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from core.logger import get_logger

logger = get_logger("resource_manager")


class ResourceType(Enum):
    """Types of resources managed by the system."""
    TOKENS = "tokens"         # LLM token usage
    MEMORY = "memory"         # System memory usage
    CPU = "cpu"              # CPU utilization
    CONCURRENT_AGENTS = "concurrent_agents"  # Number of active agents
    NETWORK = "network"       # Network bandwidth (future)


class ResourceStatus(Enum):
    """Resource availability status."""
    AVAILABLE = "available"   # Resources available for allocation
    LIMITED = "limited"       # Resources available but limited
    EXHAUSTED = "exhausted"   # Resources not available
    CRITICAL = "critical"     # Critical resource shortage


@dataclass
class ResourceAllocation:
    """Resource allocation for a task or group."""
    tokens: float = 0.0
    memory: float = 0.0  # In MB
    cpu: float = 0.0     # As percentage
    concurrent_agents: int = 0
    priority: int = 5    # 1-10 scale, 10 = highest
    timeout: float = 300.0  # Timeout in seconds
    
    def get_total_score(self) -> float:
        """Calculate total resource score for allocation decisions."""
        return (self.tokens * 0.4 + 
                self.memory * 0.3 + 
                self.cpu * 0.2 + 
                self.concurrent_agents * 0.1)


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    allocated: ResourceAllocation = field(default_factory=ResourceAllocation)
    used: ResourceAllocation = field(default_factory=ResourceAllocation)
    peak: ResourceAllocation = field(default_factory=ResourceAllocation)
    start_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_utilization_rate(self) -> Dict[str, float]:
        """Get utilization rate for each resource type."""
        if self.allocated.tokens == 0:
            return {"tokens": 0.0, "memory": 0.0, "cpu": 0.0, "agents": 0.0}
        
        return {
            "tokens": (self.used.tokens / self.allocated.tokens) * 100,
            "memory": (self.used.memory / self.allocated.memory) * 100 if self.allocated.memory > 0 else 0.0,
            "cpu": (self.used.cpu / self.allocated.cpu) * 100 if self.allocated.cpu > 0 else 0.0,
            "agents": (self.used.concurrent_agents / self.allocated.concurrent_agents) * 100 if self.allocated.concurrent_agents > 0 else 0.0
        }


@dataclass
class SystemResourceInfo:
    """System resource information."""
    total_memory_mb: float
    available_memory_mb: float
    cpu_count: int
    cpu_percent: float
    load_average: Tuple[float, float, float]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_memory_usage_percent(self) -> float:
        """Get memory usage as percentage."""
        used_memory = self.total_memory_mb - self.available_memory_mb
        return (used_memory / self.total_memory_mb) * 100 if self.total_memory_mb > 0 else 0.0


class ResourceManager:
    """
    Intelligent resource manager for parallel execution.
    
    Manages allocation, monitoring, and optimization of system resources
    including tokens, memory, CPU, and concurrent agents to ensure
    optimal parallel performance without system overload.
    """
    
    def __init__(self, config):
        """Initialize resource manager with configuration."""
        self.config = config
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.usage_tracking: Dict[str, ResourceUsage] = {}
        self.system_info: Optional[SystemResourceInfo] = None
        
        # Resource limits (configurable)
        self.resource_limits = {
            ResourceType.TOKENS: 10000.0,      # Max tokens per minute
            ResourceType.MEMORY: 2048.0,       # Max memory in MB
            ResourceType.CPU: 80.0,            # Max CPU percentage
            ResourceType.CONCURRENT_AGENTS: 8  # Max concurrent agents
        }
        
        # Resource allocation thresholds
        self.thresholds = {
            "warning": 0.7,   # 70% usage warning
            "critical": 0.85, # 85% usage critical
            "maximum": 0.95   # 95% absolute maximum
        }
        
        # Monitoring
        self.monitoring_enabled = True
        self.monitoring_interval = 5.0  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance optimization
        self.auto_scaling_enabled = True
        self.resource_history: List[Tuple[datetime, Dict[str, float]]] = []
        self.history_limit = 100
        
        logger.info("Resource manager initialized")
    
    async def start_monitoring(self):
        """Start continuous resource monitoring."""
        if self.monitoring_enabled and not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                # Update system resource information
                await self._update_system_info()
                
                # Check resource usage and adjust if needed
                await self._check_and_adjust_resources()
                
                # Clean up expired allocations
                self._cleanup_expired_allocations()
                
                # Record usage history
                self._record_usage_history()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_system_info(self):
        """Update system resource information."""
        try:
            # Get memory info
            memory = psutil.virtual_memory()
            
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            
            # Get load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Windows doesn't have getloadavg
                load_avg = (cpu_percent / 100.0, 0.0, 0.0)
            
            self.system_info = SystemResourceInfo(
                total_memory_mb=memory.total / 1024 / 1024,
                available_memory_mb=memory.available / 1024 / 1024,
                cpu_count=cpu_count,
                cpu_percent=cpu_percent,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.warning(f"Failed to update system info: {e}")
    
    async def allocate_resources(
        self, 
        task_id: str, 
        requirements: ResourceAllocation,
        force: bool = False
    ) -> bool:
        """
        Allocate resources for a task or group.
        
        Args:
            task_id: Unique identifier for the task/group
            requirements: Required resource allocation
            force: Force allocation even if resources are limited
            
        Returns:
            True if allocation successful, False otherwise
        """
        logger.debug(f"Allocating resources for task {task_id}: {requirements}")
        
        # Check if resources are available
        if not force and not await self._check_resource_availability(requirements):
            logger.warning(f"Insufficient resources for task {task_id}")
            return False
        
        # Allocate resources
        self.allocations[task_id] = requirements
        
        # Initialize usage tracking
        self.usage_tracking[task_id] = ResourceUsage(
            allocated=requirements,
            used=ResourceAllocation(),
            peak=ResourceAllocation()
        )
        
        logger.info(f"Resources allocated for task {task_id}")
        return True
    
    async def _check_resource_availability(self, requirements: ResourceAllocation) -> bool:
        """Check if required resources are available."""
        current_usage = self._calculate_current_usage()
        
        # Check each resource type
        for resource_type in ResourceType:
            required = getattr(requirements, resource_type.value, 0)
            current = getattr(current_usage, resource_type.value, 0)
            limit = self.resource_limits.get(resource_type, float('inf'))
            
            if current + required > limit * self.thresholds["maximum"]:
                logger.warning(f"Resource {resource_type.value} would exceed limit: "
                             f"{current + required} > {limit * self.thresholds['maximum']}")
                return False
        
        return True
    
    def _calculate_current_usage(self) -> ResourceAllocation:
        """Calculate current total resource usage."""
        total = ResourceAllocation()
        
        for usage in self.usage_tracking.values():
            total.tokens += usage.used.tokens
            total.memory += usage.used.memory
            total.cpu += usage.used.cpu
            total.concurrent_agents += usage.used.concurrent_agents
        
        return total
    
    async def update_usage(self, task_id: str, used_resources: ResourceAllocation):
        """Update resource usage for a task."""
        if task_id not in self.usage_tracking:
            logger.warning(f"No tracking found for task {task_id}")
            return
        
        usage = self.usage_tracking[task_id]
        usage.used = used_resources
        usage.last_updated = datetime.now()
        
        # Update peak usage
        usage.peak.tokens = max(usage.peak.tokens, used_resources.tokens)
        usage.peak.memory = max(usage.peak.memory, used_resources.memory)
        usage.peak.cpu = max(usage.peak.cpu, used_resources.cpu)
        usage.peak.concurrent_agents = max(usage.peak.concurrent_agents, used_resources.concurrent_agents)
        
        # Check for resource threshold violations
        await self._check_usage_thresholds(task_id)
    
    async def _check_usage_thresholds(self, task_id: str):
        """Check if resource usage exceeds thresholds."""
        if task_id not in self.usage_tracking:
            return
        
        usage = self.usage_tracking[task_id]
        utilization = usage.get_utilization_rate()
        
        # Check each resource for threshold violations
        for resource, rate in utilization.items():
            if rate > self.thresholds["critical"] * 100:
                logger.warning(f"Task {task_id} {resource} usage critical: {rate:.1f}%")
            elif rate > self.thresholds["warning"] * 100:
                logger.info(f"Task {task_id} {resource} usage warning: {rate:.1f}%")
    
    async def release_resources(self, task_id: str):
        """Release resources allocated to a task."""
        if task_id in self.allocations:
            del self.allocations[task_id]
            logger.debug(f"Resources released for task {task_id}")
        
        # Keep usage tracking for analysis but mark as completed
        if task_id in self.usage_tracking:
            self.usage_tracking[task_id].last_updated = datetime.now()
    
    def _cleanup_expired_allocations(self):
        """Clean up expired resource allocations."""
        now = datetime.now()
        expired_tasks = []
        
        for task_id, usage in self.usage_tracking.items():
            # Remove tracking older than 1 hour
            if now - usage.last_updated > timedelta(hours=1):
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            if task_id in self.allocations:
                del self.allocations[task_id]
            if task_id in self.usage_tracking:
                del self.usage_tracking[task_id]
            logger.debug(f"Cleaned up expired allocation for task {task_id}")
    
    def _record_usage_history(self):
        """Record current resource usage in history."""
        if not self.system_info:
            return
        
        current_usage = self._calculate_current_usage()
        
        usage_snapshot = {
            "tokens": current_usage.tokens,
            "memory": current_usage.memory,
            "cpu": self.system_info.cpu_percent,
            "agents": current_usage.concurrent_agents,
            "system_memory_percent": self.system_info.get_memory_usage_percent()
        }
        
        self.resource_history.append((datetime.now(), usage_snapshot))
        
        # Limit history size
        if len(self.resource_history) > self.history_limit:
            self.resource_history = self.resource_history[-self.history_limit:]
    
    async def _check_and_adjust_resources(self):
        """Check system resources and adjust allocations if needed."""
        if not self.auto_scaling_enabled or not self.system_info:
            return
        
        # Check system memory
        memory_usage = self.system_info.get_memory_usage_percent()
        if memory_usage > 85:
            logger.warning(f"High system memory usage: {memory_usage:.1f}%")
            await self._reduce_memory_allocations()
        
        # Check CPU usage
        if self.system_info.cpu_percent > 90:
            logger.warning(f"High CPU usage: {self.system_info.cpu_percent:.1f}%")
            await self._reduce_cpu_intensive_tasks()
        
        # Check concurrent agents
        total_agents = sum(usage.used.concurrent_agents for usage in self.usage_tracking.values())
        if total_agents > self.resource_limits[ResourceType.CONCURRENT_AGENTS]:
            logger.warning(f"Too many concurrent agents: {total_agents}")
            await self._limit_concurrent_agents()
    
    async def _reduce_memory_allocations(self):
        """Reduce memory allocations when system memory is high."""
        # Implementation would reduce memory-intensive allocations
        logger.info("Reducing memory allocations due to high system usage")
        
        # For now, just reduce memory limits by 20%
        self.resource_limits[ResourceType.MEMORY] *= 0.8
    
    async def _reduce_cpu_intensive_tasks(self):
        """Reduce CPU-intensive tasks when system CPU is high."""
        logger.info("Reducing CPU-intensive tasks due to high system usage")
        
        # Reduce CPU limits by 30%
        self.resource_limits[ResourceType.CPU] *= 0.7
    
    async def _limit_concurrent_agents(self):
        """Limit concurrent agents when too many are active."""
        logger.info("Limiting concurrent agents due to high usage")
        
        # Reduce concurrent agent limit
        current_limit = self.resource_limits[ResourceType.CONCURRENT_AGENTS]
        self.resource_limits[ResourceType.CONCURRENT_AGENTS] = max(2, int(current_limit * 0.8))
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status for monitoring."""
        current_usage = self._calculate_current_usage()
        
        status = {
            "system_info": {
                "memory_total_mb": self.system_info.total_memory_mb if self.system_info else 0,
                "memory_available_mb": self.system_info.available_memory_mb if self.system_info else 0,
                "memory_usage_percent": self.system_info.get_memory_usage_percent() if self.system_info else 0,
                "cpu_percent": self.system_info.cpu_percent if self.system_info else 0,
                "cpu_count": self.system_info.cpu_count if self.system_info else 0,
            },
            "current_usage": {
                "tokens": current_usage.tokens,
                "memory": current_usage.memory,
                "cpu": current_usage.cpu,
                "concurrent_agents": current_usage.concurrent_agents
            },
            "resource_limits": dict(self.resource_limits),
            "active_allocations": len(self.allocations),
            "tracked_tasks": len(self.usage_tracking)
        }
        
        # Add utilization percentages
        status["utilization"] = {}
        for resource_type, limit in self.resource_limits.items():
            current = getattr(current_usage, resource_type.value, 0)
            if isinstance(limit, (int, float)) and limit > 0:
                status["utilization"][resource_type.value] = (current / limit) * 100
        
        return status
    
    def get_optimal_concurrency(self) -> int:
        """Get optimal concurrency level based on current resources."""
        if not self.system_info:
            return 3  # Conservative default
        
        # Base concurrency on CPU cores and memory
        cpu_based = min(self.system_info.cpu_count, 6)
        
        # Adjust based on current system load
        load_factor = 1.0 - (self.system_info.cpu_percent / 100.0)
        memory_factor = self.system_info.available_memory_mb / 1024.0  # GB
        memory_factor = min(memory_factor, 1.0)
        
        optimal = int(cpu_based * load_factor * memory_factor)
        
        # Ensure reasonable bounds
        return max(1, min(optimal, self.resource_limits[ResourceType.CONCURRENT_AGENTS]))
    
    def predict_resource_needs(self, task_count: int, task_complexity: float = 1.0) -> ResourceAllocation:
        """Predict resource needs for a given number of tasks."""
        # Base resource needs per task
        base_per_task = ResourceAllocation(
            tokens=100.0 * task_complexity,
            memory=50.0 * task_complexity,
            cpu=10.0 * task_complexity,
            concurrent_agents=1
        )
        
        # Scale based on task count with efficiency gains
        efficiency_factor = 0.8 + (0.2 / task_count) if task_count > 1 else 1.0
        
        predicted = ResourceAllocation(
            tokens=base_per_task.tokens * task_count * efficiency_factor,
            memory=base_per_task.memory * task_count * efficiency_factor,
            cpu=base_per_task.cpu * min(task_count, self.get_optimal_concurrency()),
            concurrent_agents=min(task_count, self.get_optimal_concurrency())
        )
        
        return predicted
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for analysis."""
        if not self.resource_history:
            return {}
        
        # Calculate averages over recent history
        recent_history = self.resource_history[-20:]  # Last 20 samples
        
        avg_cpu = sum(sample[1]["cpu"] for sample in recent_history) / len(recent_history)
        avg_memory = sum(sample[1]["system_memory_percent"] for sample in recent_history) / len(recent_history)
        avg_agents = sum(sample[1]["agents"] for sample in recent_history) / len(recent_history)
        
        return {
            "average_cpu_usage": avg_cpu,
            "average_memory_usage": avg_memory,
            "average_concurrent_agents": avg_agents,
            "resource_efficiency": self._calculate_efficiency_score(),
            "optimization_opportunities": self._identify_optimization_opportunities()
        }
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate overall resource efficiency score (0-100)."""
        if not self.system_info:
            return 50.0
        
        # Efficiency based on balanced resource utilization
        current_usage = self._calculate_current_usage()
        
        scores = []
        for resource_type, limit in self.resource_limits.items():
            if isinstance(limit, (int, float)) and limit > 0:
                current = getattr(current_usage, resource_type.value, 0)
                utilization = current / limit
                
                # Optimal utilization is around 60-70%
                if 0.6 <= utilization <= 0.7:
                    scores.append(100.0)
                elif utilization < 0.6:
                    scores.append(utilization / 0.6 * 100)
                else:
                    scores.append(max(0, 100 - (utilization - 0.7) * 200))
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _identify_optimization_opportunities(self) -> List[str]:
        """Identify opportunities for resource optimization."""
        opportunities = []
        
        if not self.system_info:
            return opportunities
        
        current_usage = self._calculate_current_usage()
        
        # Check for underutilization
        for resource_type, limit in self.resource_limits.items():
            if isinstance(limit, (int, float)) and limit > 0:
                current = getattr(current_usage, resource_type.value, 0)
                utilization = current / limit
                
                if utilization < 0.3:
                    opportunities.append(f"Increase {resource_type.value} utilization (currently {utilization*100:.1f}%)")
                elif utilization > 0.9:
                    opportunities.append(f"Consider increasing {resource_type.value} limits (currently {utilization*100:.1f}%)")
        
        # System-level recommendations
        if self.system_info.cpu_percent < 30:
            opportunities.append("CPU underutilized - consider increasing parallel tasks")
        
        if self.system_info.get_memory_usage_percent() < 40:
            opportunities.append("Memory underutilized - consider larger task groups")
        
        return opportunities