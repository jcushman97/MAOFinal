#!/usr/bin/env python3
"""
Multi-Model Integration Test for MAOS Phase 5

Tests the intelligent model routing system with multiple LLM providers.
"""

import asyncio
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.state import ProjectState, Task, TaskStatus
from core.model_router import IntelligentModelRouter
from providers.cli_client import CLIClient
from agents.base_agent import BaseAgent, AgentType


async def test_model_availability():
    """Test availability of configured models."""
    print("=== Testing Model Availability ===")
    
    config = Config.load()
    cli_client = CLIClient(config)
    
    available_models = []
    for model_name in config.slots.keys():
        print(f"Testing {model_name}...", end=" ")
        try:
            is_available = await cli_client.test_model_connection(model_name)
            if is_available:
                print("[OK] Available")
                available_models.append(model_name)
            else:
                print("[FAIL] Not responding properly")
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    print(f"\nAvailable models: {available_models}")
    return available_models


def test_model_router_selection():
    """Test intelligent model selection."""
    print("\n=== Testing Model Router Selection ===")
    
    config = Config.load()
    router = IntelligentModelRouter(config)
    
    # Test different task types
    test_tasks = [
        Task(
            id="test_1",
            description="Implement a React component with TypeScript",
            team="frontend",
            status=TaskStatus.QUEUED,
            dependencies=[],
            subtasks=[],
            artifacts=[],
            attempts=0
        ),
        Task(
            id="test_2", 
            description="Research modern web development best practices",
            team="research",
            status=TaskStatus.QUEUED,
            dependencies=[],
            subtasks=[],
            artifacts=[],
            attempts=0
        ),
        Task(
            id="test_3",
            description="Write comprehensive API documentation",
            team="documentation",
            status=TaskStatus.QUEUED,
            dependencies=[],
            subtasks=[],
            artifacts=[],
            attempts=0
        ),
        Task(
            id="test_4",
            description="Create Python backend service with authentication",
            team="backend",
            status=TaskStatus.QUEUED,
            dependencies=[],
            subtasks=[],
            artifacts=[],
            attempts=0
        )
    ]
    
    for task in test_tasks:
        model, confidence = router.select_model_for_task(task)
        print(f"Task: {task.description[:50]}...")
        print(f"  Selected Model: {model} (confidence: {confidence:.2f})")
        print(f"  Team: {task.team}")
        
        # Show recommendations
        recommendations = router.get_model_recommendations(task.team)
        print(f"  Recommendations: {recommendations}")
        print()


async def test_model_routing_with_agent():
    """Test model routing through agent execution."""
    print("\n=== Testing Agent Model Routing ===")
    
    # Create test project state
    with tempfile.TemporaryDirectory() as temp_dir:
        project_state = ProjectState(
            projectId="test_multimodel",
            objective="Test multi-model routing",
            createdAt=datetime.now(timezone.utc).isoformat(),
            updatedAt=datetime.now(timezone.utc).isoformat(),
            status="executing",
            tasks=[],
            agents={},
            logs=[]
        )
        
        # Set up the project directory
        project_state._base_dir = Path(temp_dir)
        
        config = Config.load()
        
        # Create test agent
        class TestAgent(BaseAgent):
            def get_capabilities(self):
                return ["testing"]
            
            async def execute_task(self, task):
                self.set_current_task(task)
                try:
                    # This should trigger intelligent routing
                    response = await self.call_llm(
                        prompt="Hello, please respond with the name of your model.",
                        task_type="general"
                    )
                    print(f"  Model responded: {response['response'][:100]}...")
                    return True
                finally:
                    self.set_current_task(None)
        
        agent = TestAgent(
            agent_id="test_agent",
            agent_type=AgentType.WORKER,
            config=config,
            project_state=project_state
        )
        
        # Test different task types
        test_tasks = [
            Task(
                id="test_frontend",
                description="Create a React component",
                team="frontend",
                status=TaskStatus.QUEUED,
                dependencies=[], subtasks=[], artifacts=[], attempts=0
            ),
            Task(
                id="test_research",
                description="Research AI trends",
                team="research", 
                status=TaskStatus.QUEUED,
                dependencies=[], subtasks=[], artifacts=[], attempts=0
            )
        ]
        
        for task in test_tasks:
            print(f"Testing task: {task.description}")
            try:
                success = await agent.execute_task(task)
                print(f"  Result: {'Success' if success else 'Failed'}")
            except Exception as e:
                print(f"  Error: {e}")
            print()


def test_routing_configuration():
    """Test routing configuration and fallbacks."""
    print("\n=== Testing Routing Configuration ===")
    
    config = Config.load()
    router = IntelligentModelRouter(config)
    
    print("Current routing configuration:")
    for task_type in ["plan", "python", "backend", "frontend", "research", "documentation"]:
        default_model = config.get_provider_for_task(task_type)
        print(f"  {task_type}: {default_model}")
    
    print("\nModel capabilities:")
    for model_name, profile in router.model_profiles.items():
        print(f"  {model_name}:")
        for capability, strength in profile.capabilities.items():
            print(f"    {capability.value}: {strength:.2f}")
        print(f"    Available: {profile.available}")
    
    print("\nFallback chains:")
    for primary, fallbacks in router.fallback_chains.items():
        print(f"  {primary} -> {fallbacks}")


async def test_fallback_behavior():
    """Test fallback behavior when models fail."""
    print("\n=== Testing Fallback Behavior ===")
    
    config = Config.load()
    router = IntelligentModelRouter(config)
    
    # Create a test task
    task = Task(
        id="test_fallback",
        description="Test fallback routing",
        team="general",
        status=TaskStatus.QUEUED,
        dependencies=[], subtasks=[], artifacts=[], attempts=0
    )
    
    # Test fallback for each model
    for model_name in router.model_profiles.keys():
        fallback = router.get_fallback_model(model_name, task)
        print(f"If {model_name} fails -> fallback to {fallback}")
    
    # Test performance tracking
    print("\nTesting performance tracking...")
    router.update_model_performance("claude", task, success=True, response_time=1.5)
    router.update_model_performance("gpt", task, success=False, response_time=0.0)
    router.update_model_performance("gemini", task, success=True, response_time=2.1)
    
    print("Updated usage statistics:")
    for key, stats in router.usage_stats.items():
        print(f"  {key}: {stats}")


async def main():
    """Run all multi-model integration tests."""
    print("MAOS Phase 5 Multi-Model Integration Test Suite")
    print("=" * 60)
    
    try:
        # Test model availability
        available_models = await test_model_availability()
        
        if not available_models:
            print("\n[WARNING] No models are available. Please check your configuration.")
            print("   - Ensure API keys are set (OPENAI_API_KEY, GEMINI_API_KEY)")
            print("   - Verify CLI tools are installed")
            return
        
        # Test routing logic
        test_model_router_selection()
        
        # Test configuration
        test_routing_configuration()
        
        # Test fallback behavior
        await test_fallback_behavior()
        
        # Test agent integration (only if Claude is available)
        if "claude" in available_models:
            await test_model_routing_with_agent()
        else:
            print("\n[WARNING] Skipping agent routing test (Claude not available)")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Multi-model integration tests completed!")
        print(f"   Available models: {', '.join(available_models)}")
        
    except Exception as e:
        print(f"\n[FAILED] Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())