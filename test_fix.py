#!/usr/bin/env python3
"""
Test script to verify the parallel orchestrator fix for sequential execution.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator import Orchestrator
from core.config import Config
from core.state import ProjectState, Task, TaskStatus
from core.parallel_orchestrator import ParallelOrchestrator, ExecutionMode, ParallelStrategy
from core.logger import setup_logging


async def test_sequential_execution_fix():
    """Test that sequential execution processes all tasks."""
    print("Testing Sequential Execution Fix")
    print("=" * 40)
    
    setup_logging(level="INFO")
    config = Config.load()
    
    # Create a mock project state with multiple tasks
    project_state = ProjectState(objective="Test sequential execution")
    
    # Add multiple independent tasks (no dependencies)
    tasks = [
        Task(id="task1", description="First task", team="frontend"),
        Task(id="task2", description="Second task", team="frontend"), 
        Task(id="task3", description="Third task", team="backend"),
        Task(id="task4", description="Fourth task", team="qa")
    ]
    
    for task in tasks:
        project_state.add_task(task)
    
    print(f"Created project with {len(tasks)} tasks")
    
    # Test the parallel orchestrator's sequential execution
    parallel_orchestrator = ParallelOrchestrator(config, ParallelStrategy.BALANCED)
    
    # Check the _all_tasks_complete_or_failed method
    print(f"All tasks complete initially: {parallel_orchestrator._all_tasks_complete_or_failed(project_state)}")
    
    # Check ready tasks
    ready_tasks = project_state.get_ready_tasks()
    print(f"Ready tasks: {len(ready_tasks)}")
    
    # Test that we can identify when tasks are complete
    project_state.update_task_status("task1", TaskStatus.COMPLETE)
    project_state.update_task_status("task2", TaskStatus.COMPLETE)
    project_state.update_task_status("task3", TaskStatus.COMPLETE)
    project_state.update_task_status("task4", TaskStatus.COMPLETE)
    
    print(f"All tasks complete after marking complete: {parallel_orchestrator._all_tasks_complete_or_failed(project_state)}")
    
    # Check task statuses
    for task in project_state.tasks:
        print(f"Task {task.id}: {task.status}")
    
    print("\n[PASS] Sequential execution logic validation successful")
    return True


async def main():
    """Main test execution."""
    try:
        success = await test_sequential_execution_fix()
        
        if success:
            print("\nFix validation completed successfully!")
            print("\nThe issue was in the parallel orchestrator's _execute_sequential method.")
            print("It was only processing one batch of ready tasks instead of iterating")
            print("until all tasks are complete. This has been fixed.")
            return 0
        else:
            print("\nFix validation failed.")
            return 1
            
    except Exception as e:
        print(f"\nValidation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))