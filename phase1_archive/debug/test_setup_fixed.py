#!/usr/bin/env python3
"""
MAOS Setup Test with Fixed Claude CLI Configuration

Tests the system using the fixed Claude CLI wrapper that uses direct paths.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.logger import setup_logging, get_logger
from providers.cli_client import CLIClient

logger = get_logger("test_setup_fixed")


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_status(message: str, status: str, details: str = ""):
    """Print formatted status message."""
    if status == "PASS":
        color = Colors.GREEN
        symbol = "[SUCCESS]"
    elif status == "FAIL":
        color = Colors.RED
        symbol = "[FAIL]"
    elif status == "WARN":
        color = Colors.YELLOW
        symbol = "[WARN]"
    else:
        color = Colors.BLUE
        symbol = "[INFO]"
    
    print(f"{color}{symbol}{Colors.ENDC} {message}")
    if details:
        print(f"   {details}")


async def test_fixed_claude_cli():
    """Test the fixed Claude CLI wrapper."""
    print_status("Fixed Claude CLI", "INFO")
    
    try:
        # Load fixed configuration
        config_path = Path("providers/providers_fixed.json")
        config = Config.load(config_path)
        print_status("Fixed config loading", "PASS")
        
        # Test CLI client
        cli_client = CLIClient(config)
        
        # Test simple connection
        result = await cli_client.test_model_connection("claude")
        
        if result:
            print_status("Fixed Claude CLI connection", "PASS")
            return True
        else:
            print_status("Fixed Claude CLI connection", "FAIL", 
                        "Connection test failed")
            return False
            
    except Exception as e:
        print_status("Fixed Claude CLI connection", "FAIL", str(e))
        return False


async def test_real_claude_call():
    """Test a real Claude API call with planning."""
    print_status("Real Claude Planning Test", "INFO")
    
    try:
        config_path = Path("providers/providers_fixed.json")
        config = Config.load(config_path)
        cli_client = CLIClient(config)
        
        # Test with a simple planning prompt
        prompt = """You are a project manager. Please create a simple task breakdown for this project:

"Create a hello world Python script"

Please respond with a brief plan in this format:
1. Task name - description
2. Task name - description
etc.
"""
        
        result = await cli_client.call_model(
            model_name="claude",
            prompt=prompt,
            timeout=30
        )
        
        if result and result.get("output"):
            print_status("Claude planning call", "PASS")
            print(f"   Response preview: {result['output'][:100]}...")
            return True
        else:
            print_status("Claude planning call", "FAIL", "No output received")
            return False
            
    except Exception as e:
        print_status("Claude planning call", "FAIL", str(e))
        return False


async def main():
    """Run fixed setup tests."""
    print(f"{Colors.BOLD}MAOS Fixed Setup Test{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
    
    # Initialize logging
    setup_logging(level="INFO")
    
    # Run tests
    tests = [
        ("Fixed Claude CLI Connection", test_fixed_claude_cli),
        ("Real Claude API Call", test_real_claude_call),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print()
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print_status(f"{test_name} (unexpected error)", "FAIL", str(e))
            results[test_name] = False
    
    # Summary
    print(f"\n{Colors.BOLD}Test Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{'-' * 30}{Colors.ENDC}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print_status(test_name, status)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] Claude CLI is now working!{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Ready to run MAOS:{Colors.ENDC}")
        print(f"python main.py --config providers/providers_fixed.json \"Create a simple hello world Python script\"")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}[FAIL] Some tests still failing.{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))