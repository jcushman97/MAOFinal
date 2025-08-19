"""
Project Manager Agent for MAOS

The top-level agent responsible for project planning, task decomposition,
and overall project coordination.
"""

import uuid
from pathlib import Path
from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentType
from core.state import Task, TaskStatus, LogLevel
from core.logger import get_logger

logger = get_logger("project_manager")


class ProjectManagerAgent(BaseAgent):
    """
    Project Manager Agent - Top level of the agent hierarchy.
    
    Responsibilities:
    - Decompose project objectives into task DAGs
    - Assign tasks to appropriate teams
    - Monitor overall project progress
    - Integrate final outputs
    - Handle high-level planning and coordination
    """
    
    def __init__(self, agent_id: str, config, project_state):
        """Initialize Project Manager agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PM,
            config=config,
            project_state=project_state,
            model_preference=config.get_provider_for_task("plan")
        )
        
        # PM-specific configuration
        self.planning_prompts = self._load_planning_prompts()
    
    def _load_planning_prompts(self) -> Dict[str, str]:
        """Load planning prompt templates."""
        return {
            "project_planning": """
You are a Project Manager AI responsible for breaking down complex projects into manageable tasks.

PROJECT OBJECTIVE:
{objective}

Please analyze this objective and create a task breakdown structure. You must respond with valid JSON using the following format:

BEGIN_JSON
{{
  "analysis": {{
    "project_type": "web_app|api|library|analysis|other",
    "complexity": "simple|moderate|complex",
    "estimated_duration": "time estimate",
    "key_technologies": ["tech1", "tech2"]
  }},
  "task_breakdown": [
    {{
      "id": "unique_task_id",
      "description": "Clear task description",
      "team": "frontend|backend|qa|research|documentation|general",
      "dependencies": ["task_id1", "task_id2"],
      "priority": "high|medium|low",
      "estimated_effort": "time estimate"
    }}
  ]
}}
END_JSON

Guidelines:
1. Create 3-10 tasks for most projects
2. Ensure proper dependency ordering (no circular dependencies)
3. Use descriptive task descriptions
4. Assign tasks to appropriate teams based on content
5. Consider setup, implementation, testing, and documentation phases
6. Break testing into atomic tasks: HTML validation, CSS validation, JS validation, performance testing
7. Use 'qa' team for focused testing tasks that can be delegated to specialists
8. Avoid broad "test everything" tasks - be specific about what to test
            """,
            
            "task_execution": """
You are a Project Manager executing a specific task.

TASK: {task_description}
TEAM: {team}
PROJECT CONTEXT: {project_objective}

Please execute this task and provide the output. Focus on creating concrete deliverables.

If this task requires code, provide working code.
If this task requires documentation, provide complete documentation.
If this task requires analysis, provide detailed analysis.

Respond with your work output directly. Be thorough and professional.
            """
        }
    
    async def plan_project(self) -> bool:
        """
        Create initial project plan and task breakdown.
        
        Returns:
            True if planning completed successfully
        """
        self._log(LogLevel.INFO, "Starting project planning phase")
        
        try:
            # Format planning prompt
            prompt = self._format_prompt(
                self.planning_prompts["project_planning"],
                {"objective": self.project_state.objective}
            )
            
            # Call LLM for planning
            response = await self.call_llm(
                prompt=prompt,
                task_type="plan",
                expect_json=True
            )
            
            # Extract and validate JSON response
            plan_data = await self._validate_json_response(response["output"])
            
            # Process task breakdown
            await self._process_task_breakdown(plan_data)
            
            self._log(LogLevel.INFO, "Project planning completed successfully")
            return True
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Project planning failed: {e}")
            return False
    
    async def _process_task_breakdown(self, plan_data: Dict[str, Any]):
        """Process the task breakdown from planning response."""
        analysis = plan_data.get("analysis", {})
        task_breakdown = plan_data.get("task_breakdown", [])
        
        # Log analysis results
        self._log(
            LogLevel.INFO, 
            f"Project analysis: {analysis.get('project_type', 'unknown')} "
            f"({analysis.get('complexity', 'unknown')} complexity)"
        )
        
        # Create tasks from breakdown
        for task_data in task_breakdown:
            task = Task(
                id=task_data.get("id", self._create_task_id()),
                description=task_data["description"],
                team=task_data.get("team", "general"),
                dependencies=task_data.get("dependencies", []),
                status=TaskStatus.QUEUED
            )
            
            self.project_state.add_task(task)
            self._log(
                LogLevel.INFO, 
                f"Created task: {task.description} (team: {task.team})"
            )
        
        # Validate task dependencies
        self._validate_task_dependencies()
    
    def _validate_task_dependencies(self):
        """Validate that task dependencies are valid and non-circular."""
        task_ids = {task.id for task in self.project_state.tasks}
        
        # Check that all dependencies reference valid tasks
        for task in self.project_state.tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    self._log(
                        LogLevel.WARNING, 
                        f"Task {task.id} has invalid dependency: {dep_id}"
                    )
                    task.dependencies.remove(dep_id)
        
        # Circular dependency detection - Phase 2 enhancement
        # Will be implemented with full team lead agent hierarchy
    
    async def execute_task(self, task: Task) -> bool:
        """
        Execute a task (temporary implementation for Phase 1).
        
        In future phases, this will delegate to appropriate team lead agents.
        For now, the PM handles all task execution.
        
        Args:
            task: Task to execute
            
        Returns:
            True if task completed successfully
        """
        # Set task context for intelligent routing
        self.set_current_task(task)
        
        self._log(LogLevel.INFO, f"PM executing task: {task.description}")
        
        try:
            # Increment attempt counter
            task.attempts += 1
            
            # Format task execution prompt
            prompt = self._format_prompt(
                self.planning_prompts["task_execution"],
                {
                    "task_description": task.description,
                    "team": task.team,
                    "project_objective": self.project_state.objective
                }
            )
            
            # Route to appropriate model based on team
            task_type = self._map_team_to_task_type(task.team)
            
            # Execute task via LLM
            response = await self.call_llm(
                prompt=prompt,
                task_type=task_type
            )
            
            # Save task output as artifact
            await self._save_task_artifact(task, response["response"])
            
            self._log(LogLevel.INFO, f"Task completed: {task.description}")
            return True
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Task execution failed: {e}")
            task.error = str(e)
            return False
        
        finally:
            # Clear task context
            self.set_current_task(None)
    
    def _map_team_to_task_type(self, team: str) -> str:
        """Map team name to task type for LLM routing."""
        team_mapping = {
            "frontend": "frontend",
            "backend": "backend", 
            "research": "research",
            "documentation": "documentation",
            "python": "python",
            "general": "general"
        }
        return team_mapping.get(team, "general")
    
    async def _save_task_artifact(self, task: Task, output: str):
        """
        Save task output as an artifact file and create deliverable files.
        
        Args:
            task: Task that produced the output
            output: Task output content
        """
        try:
            # Create artifacts directory
            project_dir = self.config.project_dir / self.project_state.projectId
            artifacts_dir = project_dir / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create artifact file (for logging/debug)
            artifact_filename = f"{task.id}_{task.team}.txt"
            artifact_path = artifacts_dir / artifact_filename
            
            # Write output to artifact file
            with open(artifact_path, 'w', encoding='utf-8') as f:
                f.write(f"Task: {task.description}\n")
                f.write(f"Team: {task.team}\n") 
                f.write(f"Generated: {self.project_state.updatedAt}\n")
                f.write("-" * 50 + "\n")
                f.write(output)
            
            # Add artifact to task
            task.artifacts.append(str(artifact_path))
            
            # NEW: Create deliverable files from code in output
            await self._create_deliverable_files(task, output, project_dir)
            
            self._log(LogLevel.INFO, f"Saved artifact: {artifact_filename}")
            
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to save artifact: {e}")
    
    async def _create_deliverable_files(self, task: Task, output: str, project_dir: Path):
        """Create actual deliverable files from agent output."""
        try:
            # Import here to avoid circular imports
            from core.file_manager_enhanced import FileManagerEnhanced
            
            file_manager = FileManagerEnhanced(self.project_state, self.config.project_dir)
            
            # Extract and create deliverable files
            created_files = file_manager.process_task_artifacts(task.id)
            
            # If no files were extracted from artifacts, try extracting from output directly
            if not created_files:
                extracted_code = file_manager.extract_code_from_artifact(output)
                
                for filename, code in extracted_code.items():
                    file_path = file_manager.create_deliverable_file(filename, code)
                    created_files.append(file_path)
                    self._log(LogLevel.INFO, f"Created deliverable: {filename}")
            
            # Update project summary
            if created_files:
                file_manager.create_project_summary()
            
        except Exception as e:
            self._log(LogLevel.WARNING, f"Failed to create deliverable files: {e}")
    
    def get_capabilities(self) -> List[str]:
        """Get PM agent capabilities."""
        return [
            "project_planning",
            "task_breakdown", 
            "dependency_management",
            "progress_monitoring",
            "team_coordination",
            "output_integration"
        ]
    
    async def generate_project_summary(self) -> str:
        """
        Generate a summary of the completed project.
        
        Returns:
            Project summary text
        """
        completed_tasks = [
            task for task in self.project_state.tasks 
            if task.status == TaskStatus.COMPLETE
        ]
        
        summary = f"Project: {self.project_state.objective}\n"
        summary += f"Status: {self.project_state.status}\n"
        summary += f"Completed Tasks: {len(completed_tasks)}/{len(self.project_state.tasks)}\n\n"
        
        if completed_tasks:
            summary += "Completed Tasks:\n"
            for task in completed_tasks:
                summary += f"- {task.description} ({task.team})\n"
                if task.artifacts:
                    summary += f"  Artifacts: {len(task.artifacts)} files\n"
        
        return summary