#!/usr/bin/env python3
"""
Claude CLI Wrapper for MAOS

Wrapper script for claude-code CLI tool to standardize input/output format
and handle interactive terminal requirements.

IMPORTANT: This wrapper is designed to work with Claude Code CLI.
Future agents implementing other models should create similar wrappers for:
- Gemini CLI (gemini_wrapper.py)  
- GPT CLI (gpt_wrapper.py)
- Other LLM CLIs as needed

Each wrapper should:
1. Accept prompt as command line argument
2. Handle authentication and model selection
3. Return clean output with optional JSON markers
4. Provide consistent error handling
5. Support timeout and interrupt handling
"""

import sys
import subprocess
import argparse
import json
import os
from pathlib import Path


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
        
        # Build claude command
        cmd = [
            "claude",
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
            print(f"ERROR: Claude CLI failed with return code {result.returncode}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        
        # Output the response
        print(result.stdout.strip())
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Claude CLI timed out after {args.timeout} seconds", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print("ERROR: claude command not found. Please ensure claude-code CLI is installed.", file=sys.stderr)
        print("Installation: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()


"""
FUTURE MODEL IMPLEMENTATION GUIDE:

To add support for additional models, create similar wrapper scripts:

1. GEMINI WRAPPER (wrappers/gemini_wrapper.py):
   - Use `gemini prompt` or equivalent CLI command
   - Handle Google authentication if required
   - Support model selection (gemini-1.5-pro, etc.)
   - Maintain consistent argument interface

2. GPT WRAPPER (wrappers/gpt_wrapper.py):
   - Use OpenAI CLI or equivalent tool
   - Handle API key authentication
   - Support model selection (gpt-4, gpt-3.5-turbo, etc.)
   - Maintain consistent argument interface

3. CUSTOM WRAPPER TEMPLATE:
   ```python
   #!/usr/bin/env python3
   import sys
   import subprocess
   import argparse
   
   def main():
       parser = argparse.ArgumentParser(description="[MODEL] CLI Wrapper for MAOS")
       parser.add_argument("prompt", help="Prompt to send to [MODEL]")
       parser.add_argument("--model", default="[default-model]", help="Model to use")
       parser.add_argument("--json", action="store_true", help="Request JSON output")
       parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
       
       args = parser.parse_args()
       
       # Build command for your specific CLI tool
       cmd = ["your-cli-tool", "arguments", "--model", args.model]
       
       # Execute and handle results
       # ... implementation specific to your CLI tool ...
   ```

4. CONFIGURATION UPDATES:
   After creating wrappers, update providers/providers.json:
   ```json
   {
     "slots": {
       "claude": {
         "cmd": ["python", "wrappers/claude_wrapper.py"],
         "extra_args": ["--model", "claude-3-5-sonnet-20241022"],
         "json_markers": ["BEGIN_JSON", "END_JSON"]
       },
       "gemini": {
         "cmd": ["python", "wrappers/gemini_wrapper.py"],
         "extra_args": ["--model", "gemini-1.5-pro"],
         "json_markers": ["BEGIN_JSON", "END_JSON"]
       },
       "gpt": {
         "cmd": ["python", "wrappers/gpt_wrapper.py"],
         "extra_args": ["--model", "gpt-4"],
         "json_markers": ["BEGIN_JSON", "END_JSON"]
       }
     }
   }
   ```

5. ROUTING CONFIGURATION:
   Update the routing section to assign different models to different task types:
   ```json
   {
     "routing": {
       "plan": "gpt",           # GPT for planning tasks
       "python": "claude",       # Claude for coding tasks
       "backend": "claude",      # Claude for backend development
       "frontend": "gpt",        # GPT for frontend tasks
       "research": "gemini",     # Gemini for research tasks
       "documentation": "gemini", # Gemini for documentation
       "general": "claude"       # Claude as fallback
     }
   }
   ```

This modular approach allows easy addition of new models without modifying core system code.
Each wrapper handles the specifics of its CLI tool while maintaining a consistent interface.
"""