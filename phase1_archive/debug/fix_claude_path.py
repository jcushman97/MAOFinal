#!/usr/bin/env python3
"""
Fix Claude CLI Path Issues

This script finds the correct paths for Node.js, npm, and Claude CLI
and provides solutions for the PATH issue.
"""

import subprocess
import sys
import os
from pathlib import Path


def find_nodejs_installation():
    """Find Node.js installation directory."""
    print("[SEARCH] Looking for Node.js installation...")
    
    # Common Windows Node.js locations
    possible_locations = [
        Path("C:/Program Files/nodejs"),
        Path("C:/Program Files (x86)/nodejs"), 
        Path(os.environ.get('APPDATA', '')) / "npm",
        Path(os.environ.get('LOCALAPPDATA', '')) / "Programs" / "node-v22.17.0-win-x64",
        Path("C:/Users") / os.environ.get('USERNAME', '') / "AppData" / "Local" / "Programs" / "node-v22.17.0-win-x64"
    ]
    
    found_paths = []
    for location in possible_locations:
        if location.exists():
            print(f"[FOUND] Node.js directory: {location}")
            found_paths.append(location)
            
            # List contents
            for item in location.iterdir():
                print(f"  - {item.name}")
                
    return found_paths


def test_direct_paths():
    """Test Claude CLI with direct paths."""
    print("\n[TEST] Testing direct path access...")
    
    # Common npm global installation paths on Windows
    username = os.environ.get('USERNAME', '')
    possible_npm_dirs = [
        Path(f"C:/Users/{username}/AppData/Roaming/npm"),
        Path(f"C:/Users/{username}/AppData/Local/npm"),
        Path("C:/Program Files/nodejs"),
        Path(f"C:/Users/{username}/AppData/Local/Programs/node-v22.17.0-win-x64")
    ]
    
    claude_found = []
    
    for npm_dir in possible_npm_dirs:
        if npm_dir.exists():
            print(f"[CHECK] Checking {npm_dir}")
            
            # Look for claude executables
            for pattern in ["claude*", "*claude*"]:
                try:
                    matches = list(npm_dir.glob(pattern))
                    for match in matches:
                        print(f"  [FOUND] {match}")
                        
                        # Test if it's executable
                        try:
                            result = subprocess.run([str(match), "--version"], 
                                                  capture_output=True, text=True, timeout=10)
                            if result.returncode == 0:
                                print(f"  [SUCCESS] Working Claude CLI: {match}")
                                claude_found.append(str(match))
                            else:
                                print(f"  [FAIL] Not working: {match}")
                        except Exception as e:
                            print(f"  [ERROR] Testing {match}: {e}")
                except Exception as e:
                    print(f"  [ERROR] Searching {npm_dir}: {e}")
    
    return claude_found


def create_wrapper_fix(claude_path: str):
    """Create fixed wrapper with direct path."""
    print(f"\n[FIX] Creating fixed wrapper for: {claude_path}")
    
    wrapper_content = f'''#!/usr/bin/env python3
"""
Fixed Claude CLI Wrapper for MAOS

Uses direct path to Claude CLI to avoid PATH issues.
"""

import sys
import subprocess
import argparse
import json
import os


CLAUDE_CLI_PATH = r"{claude_path}"


def main():
    """Main entry point for Claude wrapper."""
    parser = argparse.ArgumentParser(description="Claude CLI Wrapper for MAOS")
    parser.add_argument("prompt", help="Prompt to send to Claude")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Claude model to use")
    parser.add_argument("--json", action="store_true", help="Request JSON output with markers")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    try:
        # Prepare the prompt
        prompt = args.prompt
        
        # Add JSON instruction if requested
        if args.json:
            prompt += "\\n\\nPlease wrap your JSON response with BEGIN_JSON and END_JSON markers."
        
        # Build claude command with direct path
        cmd = [
            CLAUDE_CLI_PATH,
            "chat",
            "--model", args.model,
            "--no-stream"  # Disable streaming for consistent output
        ]
        
        # Execute claude command with prompt as stdin
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=args.timeout,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            print(f"ERROR: Claude CLI failed with return code {{result.returncode}}", file=sys.stderr)
            print(f"STDERR: {{result.stderr}}", file=sys.stderr)
            sys.exit(1)
        
        # Output the response
        print(result.stdout.strip())
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Claude CLI timed out after {{args.timeout}} seconds", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: Claude CLI not found at: {{CLAUDE_CLI_PATH}}", file=sys.stderr)
        print("Please check the path in this wrapper script.", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"ERROR: Unexpected error: {{e}}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
'''
    
    # Write fixed wrapper
    wrapper_path = Path("wrappers/claude_wrapper_fixed.py")
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)
    
    print(f"[SUCCESS] Created fixed wrapper: {wrapper_path}")
    return wrapper_path


def main():
    """Main function."""
    print("Claude CLI Path Fix Tool")
    print("=" * 40)
    
    # 1. Find Node.js installation
    nodejs_paths = find_nodejs_installation()
    
    # 2. Test direct paths for Claude CLI
    claude_paths = test_direct_paths()
    
    if claude_paths:
        print(f"\n[SUCCESS] Found working Claude CLI installations:")
        for path in claude_paths:
            print(f"  {path}")
        
        # Create fixed wrapper with the first working path
        wrapper_path = create_wrapper_fix(claude_paths[0])
        
        print(f"\n[INSTRUCTIONS] To use the fixed wrapper:")
        print(f"1. Update providers.json to use the fixed wrapper:")
        print(f'   "cmd": ["python", "wrappers/claude_wrapper_fixed.py"]')
        print(f"2. Or run: python test_setup_fixed.py")
        
    else:
        print(f"\n[FAIL] No working Claude CLI found.")
        print(f"[FIX] Manual installation steps:")
        print(f"1. Find your npm global directory:")
        print(f"   - Open PowerShell as Administrator")
        print(f"   - Run: npm config get prefix")
        print(f"   - Run: npm list -g @anthropic-ai/claude-code")
        print(f"2. Add npm global bin to your system PATH")
        print(f"3. Restart all terminals and try again")


if __name__ == "__main__":
    main()