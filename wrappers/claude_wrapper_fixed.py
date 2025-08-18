#!/usr/bin/env python3
"""
Fixed Claude CLI Wrapper for MAOS

Uses direct path to Claude CLI to avoid PATH issues.
"""

import sys
import subprocess
import argparse
import json
import os


CLAUDE_CLI_PATH = r"C:\Users\jcushman\AppData\Local\Programs\node-v22.17.0-win-x64\claude.cmd"


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
            prompt += "\n\nPlease wrap your JSON response with BEGIN_JSON and END_JSON markers."
        
        # Build claude command with direct path and enable tools for file creation
        cmd = [
            CLAUDE_CLI_PATH,
            "--print",  # Non-interactive output
            "--model", args.model,
            "--allowedTools", "Write",  # Enable file writing tools
            "--permission-mode", "bypassPermissions"  # Allow file operations
        ]
        
        # Execute claude command with prompt via stdin
        result = subprocess.run(
            cmd,
            input=prompt,  # Pass prompt via stdin
            text=True,
            capture_output=True,
            timeout=args.timeout,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            print(f"ERROR: Claude CLI failed with return code {result.returncode}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            print(f"STDOUT: {result.stdout}", file=sys.stderr)
            print(f"COMMAND: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(1)
        
        # Output the response
        print(result.stdout.strip())
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Claude CLI timed out after {args.timeout} seconds", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: Claude CLI not found at: {CLAUDE_CLI_PATH}", file=sys.stderr)
        print("Please check the path in this wrapper script.", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()
