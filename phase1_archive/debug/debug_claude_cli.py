#!/usr/bin/env python3
"""
Debug Claude CLI Installation

This script helps diagnose why the Claude CLI command is not found
even though the npm package was installed successfully.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> tuple:
    """Run a command and return result."""
    print(f"\n[CMD] {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}")
        return -1, "", str(e)


def main():
    """Main debugging function."""
    print("Claude CLI Installation Debugger")
    print("=" * 50)
    
    # 1. Check npm installation and global packages
    run_command(["npm", "--version"], "Check npm version")
    run_command(["npm", "list", "-g", "--depth=0"], "List global npm packages")
    
    # 2. Check npm global installation paths
    run_command(["npm", "config", "get", "prefix"], "Get npm global prefix")
    run_command(["npm", "bin", "-g"], "Get npm global bin directory")
    
    # 3. Check current PATH
    print(f"\n[PATH] Current PATH environment variable:")
    path_env = os.environ.get('PATH', '')
    for path_dir in path_env.split(os.pathsep):
        print(f"  {path_dir}")
    
    # 4. Test various possible Claude command names
    possible_commands = [
        ["claude", "--version"],
        ["claude-code", "--version"], 
        ["anthropic-claude", "--version"],
        ["anthropic", "--version"],
        ["claude-cli", "--version"]
    ]
    
    print(f"\n[TEST] Testing possible Claude command names:")
    working_commands = []
    for cmd in possible_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[SUCCESS] {cmd[0]} works! Version: {result.stdout.strip()}")
                working_commands.append(cmd[0])
            else:
                print(f"[FAIL] {cmd[0]} failed (return code {result.returncode})")
        except FileNotFoundError:
            print(f"[NOT FOUND] {cmd[0]} not found")
        except Exception as e:
            print(f"[ERROR] {cmd[0]} error: {e}")
    
    # 5. Check if Claude Code CLI is actually installed
    run_command(["npm", "list", "-g", "@anthropic-ai/claude-code"], "Check Claude Code CLI installation")
    
    # 6. Look for the executable in common locations
    print(f"\n[SEARCH] Searching for Claude executables:")
    
    # Get npm global bin directory
    try:
        result = subprocess.run(["npm", "bin", "-g"], capture_output=True, text=True)
        if result.returncode == 0:
            npm_bin = Path(result.stdout.strip())
            print(f"NPM global bin directory: {npm_bin}")
            
            if npm_bin.exists():
                print(f"Contents of {npm_bin}:")
                for item in npm_bin.iterdir():
                    if 'claude' in item.name.lower():
                        print(f"  [FOUND] {item.name} - {item}")
                    else:
                        print(f"     {item.name}")
            else:
                print(f"[ERROR] NPM bin directory does not exist: {npm_bin}")
    except Exception as e:
        print(f"[ERROR] Could not get npm bin directory: {e}")
    
    # 7. Check Windows-specific locations
    if sys.platform == "win32":
        print(f"\n[WINDOWS] Windows-specific checks:")
        
        # Check AppData npm location
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            npm_path = Path(appdata) / "npm"
            print(f"Checking {npm_path}")
            if npm_path.exists():
                for item in npm_path.iterdir():
                    if 'claude' in item.name.lower():
                        print(f"  [FOUND] Found: {item}")
        
        # Check ProgramFiles npm location  
        program_files = os.environ.get('ProgramFiles', '')
        if program_files:
            nodejs_path = Path(program_files) / "nodejs"
            print(f"Checking {nodejs_path}")
            if nodejs_path.exists():
                for item in nodejs_path.iterdir():
                    if 'claude' in item.name.lower():
                        print(f"  [FOUND] Found: {item}")
    
    # 8. Provide recommendations
    print(f"\n[RECOMMENDATIONS]:")
    if working_commands:
        print(f"[SUCCESS] Working commands found: {', '.join(working_commands)}")
        print(f"[SUCCESS] Update the wrapper to use: {working_commands[0]}")
    else:
        print(f"[FAIL] No working Claude commands found")
        print(f"[FIX] Try these fixes:")
        print(f"   1. Restart your terminal/PowerShell")
        print(f"   2. Check if npm global bin is in your PATH")
        print(f"   3. Try: npm uninstall -g @anthropic-ai/claude-code")
        print(f"      Then: npm install -g @anthropic-ai/claude-code")
        print(f"   4. Try running PowerShell as Administrator")
        print(f"   5. Check npm configuration: npm config list")


if __name__ == "__main__":
    main()