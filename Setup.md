# DETAILED SETUP GUIDE

This guide walks through setting up the Multi-Agent Orchestration System on your local machine.

## SYSTEM REQUIREMENTS

### Minimum Requirements:
- **OS:** Windows 10/11, Ubuntu 20.04+, or macOS 11+
- **RAM:** 8GB (16GB recommended)
- **Storage:** 10GB free space
- **CPU:** 4 cores (8 recommended)
- **Internet:** Required for initial setup only

### Software Requirements:
- Python 3.8 or higher
- Node.js 18 or higher
- PowerShell 5+ (Windows only)
- Git (for cloning repository)

## STEP 1: INSTALL PREREQUISITES

### Windows:

#### Install Python:
1. Download from [python.org](https://python.org)
2. Check "Add Python to PATH" during installation
3. Verify: `python --version`

#### Install Node.js:
1. Download from [nodejs.org](https://nodejs.org)
2. Use LTS version
3. Verify: `node --version`

#### PowerShell:
- PowerShell should be pre-installed
- Verify: `powershell -version`

### Linux/Mac:

#### Install Python:
- **Ubuntu:** `sudo apt-get install python3 python3-pip`
- **Mac:** `brew install python3`
- Verify: `python3 --version`

#### Install Node.js:
- **Ubuntu:** `sudo apt-get install nodejs npm`
- **Mac:** `brew install node`
- Verify: `node --version`

## STEP 2: INSTALL CLI TOOLS

### Claude Code CLI:
1. Install globally via npm: `npm install -g @anthropic-ai/claude-code`
2. Authenticate: `claude auth login`
3. Verify installation: `claude --version`
4. Test basic command: `claude chat --model claude-3.5-sonnet`

### Gemini CLI:
> **Note:** Replace with actual Gemini CLI installation when available
1. Install Gemini CLI following official documentation
2. Authenticate with Google account
3. Verify installation

### GPT CLI (Optional):
> **Note:** Replace with actual GPT CLI installation when available
1. Install GPT CLI or alternative
2. Set up authentication
3. Verify installation

## STEP 3: CLONE AND SETUP PROJECT

1. **Clone repository:**
   ```bash
   git clone [repository-url]
   cd maos
   ```

2. **Create Python virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - **Windows:** `venv\Scripts\activate`
   - **Linux/Mac:** `source venv/bin/activate`

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create required directories:**
   ```bash
   mkdir projects
   mkdir projects/archive
   mkdir logs
   mkdir wrappers
   ```

## STEP 4: CONFIGURE CLI WRAPPERS

1. **Copy wrapper templates:**
   ```bash
   cp templates/claude-wrapper.ps1 wrappers/
   cp templates/claude_wrapper.py wrappers/
   cp templates/claude-wrapper.js wrappers/
   ```

2. **Test Claude wrapper:**
   - **Windows PowerShell:**
     ```powershell
     powershell -ExecutionPolicy Bypass -File wrappers\claude-wrapper.ps1 -Prompt "Hello"
     ```
   - **Python:**
     ```bash
     python wrappers/claude_wrapper.py "Hello"
     ```
   - **Node.js:**
     ```bash
     node wrappers/claude-wrapper.js "Hello"
     ```

3. Choose working wrapper and note for configuration

## STEP 5: CONFIGURE PROVIDERS

Edit `providers/providers.json`:

```json
{
  "slots": {
    "claude": {
      "cmd": ["python", "wrappers/claude_wrapper.py"],
      "extra_args": ["--model", "claude-3.5-sonnet"],
      "json_markers": ["BEGIN_JSON", "END_JSON"]
    },
    "gemini": {
      "cmd": ["gemini", "prompt"],
      "extra_args": ["--model", "gemini-1.5-pro"],
      "json_markers": ["BEGIN_JSON", "END_JSON"]
    },
    "gpt": {
      "cmd": ["gpt", "chat"],
      "extra_args": ["--model", "gpt-4"],
      "json_markers": ["BEGIN_JSON", "END_JSON"]
    }
  },
  "routing": {
    "plan": "gpt",
    "python": "claude",
    "backend": "claude",
    "frontend": "gpt",
    "research": "gemini",
    "documentation": "gemini",
    "general": "gpt"
  }
}
```

## STEP 6: VERIFY INSTALLATION

1. **Run test script:**
   ```bash
   python test_setup.py
   ```
   
   This will verify:
   - Python environment
   - CLI tools accessible
   - Wrappers functioning
   - File permissions
   - Directory structure

2. **Run simple test:**
   ```bash
   python main.py "Write hello world in Python"
   ```

3. **Check output:**
   ```bash
   ls projects/
   cat projects/[timestamp]/state.json
   ```

## STEP 7: OPTIONAL COMPONENTS

### Web Dashboard:
1. **Install additional dependencies:**
   ```bash
   pip install fastapi uvicorn
   ```

2. **Start web server:**
   ```bash
   python web_server.py
   ```

3. **Open browser to:** http://localhost:8000

### Monitoring Script:
1. **In new terminal:**
   ```bash
   python monitor.py
   ```
2. Will show real-time project progress

## TROUBLESHOOTING

### Issue: Claude CLI requires interactive terminal
**Solution:**
- Use wrapper script approach
- Ensure wrapper script has correct path to claude
- Test wrapper independently first
- Check PowerShell execution policy on Windows

### Issue: Permission denied errors
**Solution:**
- Check file permissions
- Ensure projects/ directory is writable
- Wrapper scripts must be executable
- Virtual environment activated

### Issue: Model timeouts
**Solution:**
- Increase timeout in configuration
- Edit timeout values in providers.json
- Consider task complexity when setting timeouts
- Add retry logic for transient failures

### Issue: JSON parsing errors
**Solution:**
- Verify marker configuration
- Ensure prompts include correct markers
- Check CLI output format
- Add debug logging to see raw output

## ENVIRONMENT VARIABLES

Optional environment variables for configuration:
- `MAOS_PROJECT_DIR=/path/to/projects`
- `MAOS_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`
- `MAOS_DEFAULT_TIMEOUT=300`
- `MAOS_MAX_RETRIES=3`
- `MAOS_WRAPPER_TYPE=powershell|python|node`

## NEXT STEPS

1. Run increasingly complex projects to test system
2. Monitor token usage and costs
3. Customize prompts for your use cases
4. Add new agent types as needed
5. Set up automated backups of projects directory

For questions and issues, see `TROUBLESHOOTING.md`