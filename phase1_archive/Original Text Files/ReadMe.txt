MULTI-AGENT ORCHESTRATION SYSTEM (MAOS)
A hierarchical AI agent system that coordinates multiple LLMs to tackle complex projects.
QUICK START
Prerequisites:
Python 3.8 or higher
Claude Code CLI installed (npm install -g @anthropic-ai/claude-code)
Gemini CLI installed (installation instructions in SETUP.txt)
GPT CLI or alternative (optional)
Node.js 18+ (for Claude wrapper)
PowerShell 5+ (for Windows wrapper scripts)
Installation:
Clone the repository
Install Python dependencies: pip install -r requirements.txt
Configure your CLI commands in providers/providers.json
Test your CLI wrappers: python test_wrappers.py
Run your first project: python main.py "Create a simple todo list web app"
Project Structure:
/maos
/agents          - Agent implementations (PM, Team Leads, Workers)
/core            - Core system components (state, router, prompts)
/providers       - LLM CLI configurations and clients
/wrappers        - CLI wrapper scripts for each model
/projects        - Generated project outputs and artifacts
/web             - Dashboard interface files
main.py          - Entry point
orchestrator.py  - Main orchestration logic
Basic Usage:
Run a simple task
python main.py "Write a Python function to calculate fibonacci"
Run a complex project
python main.py "Build a full-stack web application for task management with user authentication"
Monitor progress (in another terminal)
python monitor.py
View results
ls projects/[timestamp]/artifacts/
Configuration:
Edit providers/providers.json to configure:
CLI commands for each model
Model routing rules
Task type mappings
Complexity thresholds
Monitoring:
Option 1: Console monitoring
python monitor.py
Option 2: Web dashboard python web_server.py Open http://localhost:8000 in browser
Troubleshooting:
If CLI commands fail:
Test wrapper scripts individually
Check CLI tool installation
Verify PATH environment variables
See logs in projects/[timestamp]/logs/
For more details, see ARCHITECTURE.txt and SETUP.txt
