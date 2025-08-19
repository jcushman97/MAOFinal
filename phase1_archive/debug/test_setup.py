#!/usr/bin/env python3
"""
MAOS Setup Test Script

Validates system installation and configuration to ensure MAOS is ready to run.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.logger import setup_logging, get_logger
from providers.cli_client import CLIClient

logger = get_logger("test_setup")


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
        symbol = ""
    elif status == "FAIL":
        color = Colors.RED
        symbol = ""
    elif status == "WARN":
        color = Colors.YELLOW
        symbol = ""
    else:
        color = Colors.BLUE
        symbol = ""
    
    print(f"{color}{symbol}{Colors.ENDC} {message}")
    if details:
        print(f"   {details}")


async def test_python_environment():
    """Test Python environment requirements."""
    print_status("Python Environment", "INFO")
    
    # Check Python version
    import sys
    version = sys.version_info
    if version >= (3, 8):
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "PASS")
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "FAIL", 
                    "Python 3.8+ required")
        return False
    
    # Check required modules
    required_modules = [
        "pydantic", "pathlib", "asyncio", "json", "subprocess"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print_status(f"Module: {module}", "PASS")
        except ImportError:
            print_status(f"Module: {module}", "FAIL", "Module not found")
            missing_modules.append(module)
    
    if missing_modules:
        print_status("Missing modules", "FAIL", 
                    f"Install: pip install {' '.join(missing_modules)}")
        return False
    
    return True


async def test_directory_structure():
    """Test project directory structure."""
    print_status("Directory Structure", "INFO")
    
    required_dirs = [
        "agents", "core", "providers", "wrappers", 
        "projects", "logs", "tests", "web"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            print_status(f"Directory: {dir_name}/", "PASS")
        else:
            print_status(f"Directory: {dir_name}/", "FAIL", "Directory missing")
            all_exist = False
    
    return all_exist


async def test_configuration():
    """Test configuration loading and validation."""
    print_status("Configuration", "INFO")
    
    try:
        config = Config.load()
        print_status("Config loading", "PASS")
        
        # Test provider configuration
        if "claude" in config.slots:
            print_status("Claude provider config", "PASS")
        else:
            print_status("Claude provider config", "FAIL", "No Claude configuration found")
            return False
        
        # Test routing configuration
        if config.routing.general == "claude":
            print_status("Task routing config", "PASS")
        else:
            print_status("Task routing config", "WARN", "Routing may need adjustment")
        
        return True
        
    except Exception as e:
        print_status("Config loading", "FAIL", str(e))
        return False


async def test_cli_wrappers():
    """Test CLI wrapper scripts."""
    print_status("CLI Wrappers", "INFO")
    
    # Check wrapper files exist
    claude_wrapper = PROJECT_ROOT / "wrappers" / "claude_wrapper.py"
    if claude_wrapper.exists():
        print_status("Claude wrapper script", "PASS")
        
        # Test wrapper can be executed
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, str(claude_wrapper), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print_status("Claude wrapper execution", "PASS")
            else:
                print_status("Claude wrapper execution", "FAIL", 
                            "Wrapper script has errors")
                return False
                
        except Exception as e:
            print_status("Claude wrapper execution", "FAIL", str(e))
            return False
    else:
        print_status("Claude wrapper script", "FAIL", "Wrapper file missing")
        return False
    
    return True


async def test_claude_cli():
    """Test Claude CLI availability."""
    print_status("Claude CLI", "INFO")
    
    try:
        import subprocess
        result = subprocess.run([
            "claude", "--version"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_status("Claude CLI available", "PASS", result.stdout.strip())
            return True
        else:
            print_status("Claude CLI available", "FAIL", 
                        "Command failed - check installation and authentication")
            return False
            
    except FileNotFoundError:
        print_status("Claude CLI available", "FAIL", 
                    "claude command not found - install with: npm install -g @anthropic-ai/claude-code")
        return False
    except Exception as e:
        print_status("Claude CLI available", "FAIL", str(e))
        return False


async def test_model_connection():
    """Test actual model connection through CLI client."""
    print_status("Model Connection", "INFO")
    
    try:
        config = Config.load()
        cli_client = CLIClient(config)
        
        # Test connection with timeout
        success = await cli_client.test_model_connection("claude")
        
        if success:
            print_status("Claude model connection", "PASS")
            return True
        else:
            print_status("Claude model connection", "FAIL", 
                        "Model responded but may not be working properly")
            return False
            
    except Exception as e:
        print_status("Claude model connection", "FAIL", str(e))
        return False


async def test_file_permissions():
    """Test file system permissions."""
    print_status("File Permissions", "INFO")
    
    try:
        # Test project directory write access
        test_file = PROJECT_ROOT / "projects" / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print_status("Projects directory write", "PASS")
        
        # Test logs directory write access  
        test_file = PROJECT_ROOT / "logs" / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print_status("Logs directory write", "PASS")
        
        return True
        
    except Exception as e:
        print_status("File permissions", "FAIL", str(e))
        return False


async def main():
    """Run all setup tests."""
    print(f"{Colors.BOLD}MAOS Setup Test{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
    
    # Initialize logging
    setup_logging(level="INFO")
    
    # Run tests
    tests = [
        ("Python Environment", test_python_environment),
        ("Directory Structure", test_directory_structure),
        ("Configuration", test_configuration),
        ("CLI Wrappers", test_cli_wrappers),
        ("File Permissions", test_file_permissions),
        ("Claude CLI", test_claude_cli),
        ("Model Connection", test_model_connection),
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
        print(f"\n{Colors.GREEN}{Colors.BOLD} All tests passed! MAOS is ready to use.{Colors.ENDC}")
        print(f"\nTry running: python main.py \"Create a simple hello world Python script\"")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD} Some tests failed. Please fix issues before using MAOS.{Colors.ENDC}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))