"""
Basic Web Dashboard for MAOS

Simple FastAPI-based dashboard for monitoring project status and progress.
This implements the basic monitoring interface specified for Phase 1.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
from typing import List, Dict, Any
import asyncio

# Add project root to path for imports
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import Config
from core.state import StateManager
from core.logger import get_logger

logger = get_logger("dashboard")

# Initialize FastAPI app
app = FastAPI(title="MAOS Dashboard", description="Multi-Agent Orchestration System Dashboard")

# Setup templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Global state manager (initialized on startup)
state_manager: StateManager = None
config: Config = None


@app.on_event("startup")
async def startup():
    """Initialize dashboard on startup."""
    global state_manager, config
    
    try:
        config = Config.load()
        state_manager = StateManager(config.project_dir)
        logger.info("Dashboard initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize dashboard: {e}")
        raise


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Render main dashboard page."""
    try:
        # Get list of all projects
        projects = state_manager.list_projects()
        
        # Load summary info for each project
        project_summaries = []
        for project_id in projects[-10:]:  # Last 10 projects
            try:
                project_state = await state_manager.load_state(project_id)
                if project_state:
                    summary = {
                        "id": project_id,
                        "objective": project_state.objective,
                        "status": project_state.status,
                        "created": project_state.createdAt,
                        "updated": project_state.updatedAt,
                        "task_count": len(project_state.tasks),
                        "completed_tasks": sum(1 for task in project_state.tasks if task.status == "complete")
                    }
                    project_summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to load project {project_id}: {e}")
        
        # Sort by updated timestamp (most recent first)
        project_summaries.sort(key=lambda x: x["updated"], reverse=True)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "projects": project_summaries,
            "total_projects": len(projects)
        })
        
    except Exception as e:
        logger.error(f"Dashboard home error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """Render detailed project view."""
    try:
        project_state = await state_manager.load_state(project_id)
        
        if not project_state:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Organize tasks by status
        tasks_by_status = {
            "queued": [],
            "in_progress": [],
            "complete": [],
            "failed": []
        }
        
        for task in project_state.tasks:
            status = task.status
            tasks_by_status[status].append({
                "id": task.id,
                "description": task.description,
                "team": task.team,
                "dependencies": task.dependencies,
                "artifacts": task.artifacts,
                "attempts": task.attempts,
                "error": task.error
            })
        
        # Get recent logs
        recent_logs = project_state.logs[-20:] if project_state.logs else []
        
        return templates.TemplateResponse("project_detail.html", {
            "request": request,
            "project": {
                "id": project_id,
                "objective": project_state.objective,
                "status": project_state.status,
                "created": project_state.createdAt,
                "updated": project_state.updatedAt
            },
            "tasks": tasks_by_status,
            "logs": recent_logs,
            "agents": project_state.agents
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project detail error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/projects")
async def api_projects():
    """API endpoint to get list of projects."""
    try:
        projects = state_manager.list_projects()
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"API projects error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/project/{project_id}")
async def api_project_detail(project_id: str):
    """API endpoint to get project details."""
    try:
        project_state = await state_manager.load_state(project_id)
        
        if not project_state:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project_state.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API project detail error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/project/{project_id}/status")
async def api_project_status(project_id: str):
    """API endpoint for real-time project status updates."""
    try:
        project_state = await state_manager.load_state(project_id)
        
        if not project_state:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Task status counts
        task_counts = {"queued": 0, "in_progress": 0, "complete": 0, "failed": 0}
        for task in project_state.tasks:
            task_counts[task.status] += 1
        
        return {
            "project_id": project_id,
            "status": project_state.status,
            "updated": project_state.updatedAt,
            "task_counts": task_counts,
            "total_tasks": len(project_state.tasks),
            "progress": task_counts["complete"] / len(project_state.tasks) if project_state.tasks else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API project status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "maos-dashboard"}


if __name__ == "__main__":
    import uvicorn
    
    # Run dashboard server
    print("Starting MAOS Dashboard...")
    print("Open http://localhost:8000 in your browser")
    
    uvicorn.run(
        "dashboard:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )