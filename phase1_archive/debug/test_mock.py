#!/usr/bin/env python3
"""
Test MAOS with Mock Claude Wrapper

Tests the complete MAOS system using a mock Claude wrapper instead of the real CLI.
This allows testing all functionality without requiring Claude CLI installation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.orchestrator import Orchestrator
from core.logger import setup_logging, get_logger

logger = get_logger("test_mock")


async def test_mock_system():
    """Test MAOS with mock Claude wrapper."""
    print("🧪 Testing MAOS with Mock Claude Wrapper")
    print("=" * 50)
    
    try:
        # Setup logging
        setup_logging(level="INFO")
        
        # Load mock configuration
        mock_config_path = Path("providers/providers_mock.json")
        config = Config.load(mock_config_path)
        
        print("✅ Mock configuration loaded")
        
        # Create orchestrator
        orchestrator = Orchestrator(config)
        print("✅ Orchestrator initialized")
        
        # Test simple project
        test_objective = "Create a simple hello world Python script"
        print(f"\n🚀 Starting test project: {test_objective}")
        
        project_id = await orchestrator.start_project(test_objective)
        print(f"✅ Project completed: {project_id}")
        
        # Monitor the completed project
        print(f"\n📊 Project Summary:")
        success = await orchestrator.monitor_project(project_id)
        
        if success:
            print("\n🎉 MAOS Mock Test PASSED!")
            print("The system is working correctly with mock responses.")
            print("\nTo use with real Claude CLI:")
            print("1. Install Claude CLI: npm install -g @anthropic-ai/claude-code")
            print("2. Authenticate: claude auth login")
            print("3. Use: python main.py 'Your project description'")
            return True
        else:
            print("\n❌ Mock test failed during monitoring")
            return False
            
    except Exception as e:
        print(f"\n❌ Mock test failed: {e}")
        logger.error(f"Mock test error: {e}")
        return False


async def main():
    """Run mock test."""
    success = await test_mock_system()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))