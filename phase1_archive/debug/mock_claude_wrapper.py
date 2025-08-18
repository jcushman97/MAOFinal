#!/usr/bin/env python3
"""
Mock Claude Wrapper for MAOS Testing

This is a mock wrapper for testing MAOS without requiring Claude CLI installation.
It simulates Claude responses for development and testing purposes.

Usage: Use this wrapper when Claude CLI is not available for testing.
"""

import sys
import argparse
import json
import time
import random


def generate_mock_response(prompt: str, use_json: bool = False) -> str:
    """Generate mock response based on prompt content."""
    
    # Simulate processing time
    time.sleep(random.uniform(0.5, 2.0))
    
    # Detect if this is a planning request
    if "task breakdown" in prompt.lower() or "project" in prompt.lower():
        if use_json:
            response = """
I'll analyze this project and create a task breakdown.

BEGIN_JSON
{
  "analysis": {
    "project_type": "web_app",
    "complexity": "simple",
    "estimated_duration": "2-3 hours",
    "key_technologies": ["python", "html", "javascript"]
  },
  "task_breakdown": [
    {
      "id": "setup_project",
      "description": "Set up project structure and dependencies",
      "team": "backend",
      "dependencies": [],
      "priority": "high",
      "estimated_effort": "30 minutes"
    },
    {
      "id": "create_backend",
      "description": "Create backend API with task CRUD operations",
      "team": "backend", 
      "dependencies": ["setup_project"],
      "priority": "high",
      "estimated_effort": "1 hour"
    },
    {
      "id": "create_frontend",
      "description": "Create frontend interface for task management",
      "team": "frontend",
      "dependencies": ["create_backend"],
      "priority": "high", 
      "estimated_effort": "1 hour"
    },
    {
      "id": "testing",
      "description": "Test the application functionality",
      "team": "general",
      "dependencies": ["create_frontend"],
      "priority": "medium",
      "estimated_effort": "30 minutes"
    }
  ]
}
END_JSON
            """
        else:
            response = "I'll help you plan this project by breaking it down into manageable tasks with proper dependencies and team assignments."
    
    elif "hello" in prompt.lower() and "ok" in prompt.lower():
        response = "OK - Mock Claude is working correctly!"
    
    elif "python" in prompt.lower() or "code" in prompt.lower():
        response = """Here's a Python implementation for your request:

```python
def hello_world():
    print("Hello, World!")
    return "Success"

if __name__ == "__main__":
    hello_world()
```

This code creates a simple function that prints "Hello, World!" and can be executed directly."""
    
    elif "frontend" in prompt.lower() or "html" in prompt.lower():
        response = """Here's an HTML implementation:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Task Manager</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .task { padding: 10px; border: 1px solid #ddd; margin: 5px; }
    </style>
</head>
<body>
    <h1>Task Manager</h1>
    <div id="tasks"></div>
    <script>
        console.log("Task manager loaded");
    </script>
</body>
</html>
```"""
    
    else:
        response = f"I understand you want me to help with: {prompt[:100]}...\n\nI'm a mock Claude instance for testing purposes. In a real implementation, I would provide detailed assistance with this request."
    
    return response.strip()


def main():
    """Main entry point for mock Claude wrapper."""
    parser = argparse.ArgumentParser(description="Mock Claude CLI Wrapper for MAOS Testing")
    parser.add_argument("prompt", help="Prompt to send to mock Claude")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Model name (ignored in mock)")
    parser.add_argument("--json", action="store_true", help="Request JSON output with markers")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout (ignored in mock)")
    
    args = parser.parse_args()
    
    try:
        # Generate mock response
        response = generate_mock_response(args.prompt, args.json)
        print(response)
        
    except Exception as e:
        print(f"ERROR: Mock Claude wrapper failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()