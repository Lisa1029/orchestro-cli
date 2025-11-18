"""FastAPI server for Orchestro Intelligence API."""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    GenerateRequest,
    GenerateResponse,
    JobStatus,
    JobResponse,
    KnowledgeResponse,
    HealthResponse,
    ScreenInfo,
    ScenarioInfo,
)


# Job storage (in-memory for MVP, would use Redis in production)
jobs: Dict[str, JobResponse] = {}

# App knowledge cache
knowledge_cache: Dict[str, KnowledgeResponse] = {}

# Server start time
server_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("🚀 Orchestro Intelligence API starting...")
    yield
    # Shutdown
    print("🛑 Orchestro Intelligence API shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="Orchestro Intelligence API",
        description="REST/GraphQL API for automated CLI/TUI test generation",
        version="0.2.1",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "name": "Orchestro Intelligence API",
            "version": "0.2.1",
            "docs": "/docs",
            "health": "/health"
        }

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health():
        """Health check endpoint."""
        uptime = time.time() - server_start_time
        pending = sum(1 for j in jobs.values() if j.status == JobStatus.PENDING)
        running = sum(1 for j in jobs.values() if j.status == JobStatus.RUNNING)

        return HealthResponse(
            status="healthy",
            version="0.2.1",
            uptime=uptime,
            jobs_pending=pending,
            jobs_running=running
        )

    @app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
    async def analyze_sync(request: AnalyzeRequest, background_tasks: BackgroundTasks):
        """
        Analyze application code synchronously.

        For long-running analysis, use async_mode=True to get a job_id instead.
        """
        if request.async_mode:
            # Return job ID for async processing
            job_id = str(uuid.uuid4())
            job = JobResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                progress=0.0
            )
            jobs[job_id] = job

            # Schedule background task
            background_tasks.add_task(run_analysis_async, job_id, request)

            return JSONResponse(
                status_code=202,
                content={"job_id": job_id, "status": "pending", "check_status": f"/api/v1/jobs/{job_id}"}
            )

        # Synchronous analysis
        start_time = time.time()

        # Mock implementation (replace with actual intelligence system)
        app_path = Path(request.app_path)

        # TODO: Integrate with actual ASTAnalyzer
        result = AnalyzeResponse(
            app_name=app_path.name,
            framework=request.framework or "unknown",
            screens=[
                ScreenInfo(
                    name="MainScreen",
                    class_name="MainScreen",
                    keybindings=[{"key": "q", "action": "quit"}],
                    widgets=["Button", "Input"],
                    navigation_targets=["SettingsScreen"]
                )
            ],
            total_screens=1,
            total_keybindings=1,
            entry_point=str(app_path / "main.py"),
            analysis_time=time.time() - start_time
        )

        # Cache knowledge
        app_id = f"{app_path.name}_v1"
        knowledge_cache[app_id] = KnowledgeResponse(
            app_id=app_id,
            app_name=result.app_name,
            framework=result.framework,
            screens=result.screens,
            indexed_at=datetime.now(),
            last_updated=datetime.now()
        )

        return result

    @app.post("/api/v1/generate", response_model=GenerateResponse, tags=["Generation"])
    async def generate_sync(request: GenerateRequest, background_tasks: BackgroundTasks):
        """
        Generate test scenarios synchronously.

        For long-running generation, use async_mode=True to get a job_id instead.
        """
        if request.async_mode:
            # Return job ID for async processing
            job_id = str(uuid.uuid4())
            job = JobResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                progress=0.0
            )
            jobs[job_id] = job

            # Schedule background task
            background_tasks.add_task(run_generation_async, job_id, request)

            return JSONResponse(
                status_code=202,
                content={"job_id": job_id, "status": "pending", "check_status": f"/api/v1/jobs/{job_id}"}
            )

        # Synchronous generation
        start_time = time.time()

        # Mock implementation (replace with actual ScenarioGenerator)
        app_path = Path(request.app_path)
        output_dir = Path(request.output_dir) if request.output_dir else app_path / "scenarios"
        output_dir.mkdir(parents=True, exist_ok=True)

        # TODO: Integrate with actual ScenarioGenerator
        result = GenerateResponse(
            scenarios=[
                ScenarioInfo(
                    name="smoke_test_main",
                    path=str(output_dir / "smoke_test_main.yaml"),
                    strategy=request.strategy,
                    steps=5,
                    validations=3
                )
            ],
            total_scenarios=1,
            output_directory=str(output_dir),
            generation_time=time.time() - start_time
        )

        return result

    @app.get("/api/v1/knowledge/{app_id}", response_model=KnowledgeResponse, tags=["Knowledge"])
    async def get_knowledge(app_id: str):
        """Retrieve cached application knowledge."""
        if app_id not in knowledge_cache:
            raise HTTPException(
                status_code=404,
                detail=f"No knowledge found for app_id: {app_id}"
            )

        return knowledge_cache[app_id]

    @app.get("/api/v1/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
    async def get_job_status(job_id: str):
        """Get status of asynchronous job."""
        if job_id not in jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}"
            )

        return jobs[job_id]

    @app.delete("/api/v1/jobs/{job_id}", tags=["Jobs"])
    async def cancel_job(job_id: str):
        """Cancel a running job."""
        if job_id not in jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Job not found: {job_id}"
            )

        job = jobs[job_id]
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job in {job.status} state"
            )

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()

        return {"message": f"Job {job_id} cancelled"}

    @app.websocket("/ws/analyze/{app_path:path}")
    async def websocket_analyze(websocket: WebSocket, app_path: str):
        """WebSocket endpoint for real-time analysis streaming."""
        await websocket.accept()

        try:
            # Send initial message
            await websocket.send_json({"status": "connected", "message": "Starting analysis..."})

            # Mock streaming progress (replace with actual analysis)
            for progress in range(0, 101, 10):
                await asyncio.sleep(0.5)  # Simulate work
                await websocket.send_json({
                    "status": "progress",
                    "progress": progress,
                    "message": f"Analyzing... {progress}%"
                })

            # Send final result
            await websocket.send_json({
                "status": "completed",
                "result": {
                    "app_name": Path(app_path).name,
                    "screens": 3,
                    "keybindings": 12
                }
            })

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for {app_path}")
        except Exception as e:
            await websocket.send_json({"status": "error", "message": str(e)})
            await websocket.close()

    return app


async def run_analysis_async(job_id: str, request: AnalyzeRequest):
    """Run analysis in background."""
    job = jobs[job_id]
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now()

    try:
        # Simulate long-running analysis
        for i in range(10):
            await asyncio.sleep(0.5)
            job.progress = (i + 1) * 10.0

        # TODO: Integrate with actual ASTAnalyzer
        app_path = Path(request.app_path)

        result = {
            "app_name": app_path.name,
            "framework": request.framework or "unknown",
            "screens": [
                {
                    "name": "MainScreen",
                    "class_name": "MainScreen",
                    "keybindings": [{"key": "q", "action": "quit"}],
                    "widgets": ["Button", "Input"],
                    "navigation_targets": ["SettingsScreen"]
                }
            ],
            "total_screens": 1,
            "total_keybindings": 1,
            "entry_point": str(app_path / "main.py"),
            "analysis_time": 5.0
        }

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        job.progress = 100.0
        job.result = result

    except Exception as e:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now()
        job.error = str(e)


async def run_generation_async(job_id: str, request: GenerateRequest):
    """Run scenario generation in background."""
    job = jobs[job_id]
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now()

    try:
        # Simulate long-running generation
        for i in range(10):
            await asyncio.sleep(0.5)
            job.progress = (i + 1) * 10.0

        # TODO: Integrate with actual ScenarioGenerator
        app_path = Path(request.app_path)
        output_dir = Path(request.output_dir) if request.output_dir else app_path / "scenarios"

        result = {
            "scenarios": [
                {
                    "name": "smoke_test_main",
                    "path": str(output_dir / "smoke_test_main.yaml"),
                    "strategy": request.strategy,
                    "steps": 5,
                    "validations": 3
                }
            ],
            "total_scenarios": 1,
            "output_directory": str(output_dir),
            "generation_time": 5.0
        }

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now()
        job.progress = 100.0
        job.result = result

    except Exception as e:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now()
        job.error = str(e)
