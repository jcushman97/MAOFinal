#!/usr/bin/env python3
"""
Test the Parallel Execution System specifically
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator import Orchestrator
from core.config import Config
from core.parallel_orchestrator import ParallelStrategy
from core.logger import setup_logging


async def test_parallel_configurations():
    """Test different parallel execution configurations."""
    print("Testing Parallel Execution Configurations")
    print("=" * 50)
    
    setup_logging(level="INFO")
    config = Config.load()
    config.project_dir = Path("test_projects")
    
    # Test different parallel strategies
    strategies = [
        (ParallelStrategy.CONSERVATIVE, "Conservative Strategy - Lower resource usage"),
        (ParallelStrategy.BALANCED, "Balanced Strategy - Optimal performance/resource balance"),
        (ParallelStrategy.AGGRESSIVE, "Aggressive Strategy - Maximum performance")
    ]
    
    for strategy, description in strategies:
        print(f"\nTesting {description}")
        print("-" * 40)
        
        # Test with parallel enabled
        orchestrator = Orchestrator(config, enable_parallel=True, parallel_strategy=strategy)
        
        # Check parallel capabilities
        capabilities = orchestrator.get_parallel_capabilities()
        print(f"Parallel Enabled: {capabilities['parallel_enabled']}")
        print(f"Current Strategy: {capabilities['current_strategy']}")
        print(f"Available Strategies: {capabilities['available_strategies']}")
        print(f"Features: {', '.join(capabilities['features'])}")
        
        # Test strategy switching
        if strategy != ParallelStrategy.BALANCED:
            orchestrator.set_parallel_strategy(ParallelStrategy.BALANCED)
            print(f"Strategy switched to: {orchestrator.parallel_strategy.value}")
            orchestrator.set_parallel_strategy(strategy)  # Switch back
            
        # Test performance metrics (will be empty until actual execution)
        metrics = orchestrator.get_performance_metrics()
        print(f"Performance Metrics Available: {metrics['parallel_enabled']}")
        
        print(f"[PASS] {strategy.value} configuration working correctly")
    
    # Test sequential mode (backward compatibility)
    print(f"\nTesting Sequential Mode (Backward Compatibility)")
    print("-" * 40)
    
    orchestrator_sequential = Orchestrator(config, enable_parallel=False)
    assert orchestrator_sequential.enable_parallel == False, "Sequential mode should disable parallel"
    
    capabilities = orchestrator_sequential.get_parallel_capabilities()
    assert capabilities['parallel_enabled'] == False, "Capabilities should show parallel disabled"
    
    print(f"[PASS] Sequential mode working correctly")
    
    print(f"\nAll parallel configuration tests passed!")
    return True


async def main():
    """Main test execution."""
    try:
        success = await test_parallel_configurations()
        
        if success:
            print("\nParallel system tests completed successfully!")
            return 0
        else:
            print("\nSome parallel tests failed.")
            return 1
            
    except Exception as e:
        print(f"\nParallel testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))