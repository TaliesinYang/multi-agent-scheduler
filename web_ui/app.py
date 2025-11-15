"""
Web UI for Multi-Agent Scheduler

Provides a web interface for monitoring and managing the scheduler.
"""

from fastapi import FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.health import get_health_status

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Scheduler UI",
    description="Web interface for Multi-Agent Scheduler",
    version="3.0.0"
)

# Set up templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    health = get_health_status()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "health": health,
        "title": "Dashboard"
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """Tasks management page"""
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "title": "Tasks"
    })


@app.get("/workflows", response_class=HTMLResponse)
async def workflows_page(request: Request):
    """Workflows page"""
    return templates.TemplateResponse("workflows.html", {
        "request": request,
        "title": "Workflows"
    })


@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    """Monitoring page"""
    return templates.TemplateResponse("monitoring.html", {
        "request": request,
        "title": "Monitoring"
    })


@app.get("/api/health")
async def api_health():
    """Health check API"""
    return get_health_status()


@app.get("/api/tasks")
async def api_tasks():
    """Get tasks list"""
    # TODO: Implement actual task retrieval
    return {"tasks": [], "total": 0}


@app.get("/api/metrics")
async def api_metrics():
    """Get metrics summary"""
    health = get_health_status()
    return {
        "active_tasks": health.get("active_tasks", 0),
        "total_errors": health.get("total_errors", 0),
        "uptime": health.get("uptime", 0)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
