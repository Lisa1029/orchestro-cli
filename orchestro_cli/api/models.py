"""API request/response models using Pydantic."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalyzeRequest(BaseModel):
    """Request to analyze application code."""

    app_path: str = Field(..., description="Path to application code directory")
    framework: Optional[str] = Field(None, description="Framework to analyze (textual, click, etc.)")
    async_mode: bool = Field(False, description="Run analysis asynchronously")

    @validator("app_path")
    def validate_path(cls, v):
        """Ensure path exists."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return str(path.absolute())

    class Config:
        schema_extra = {
            "example": {
                "app_path": "./my_app",
                "framework": "textual",
                "async_mode": True
            }
        }


class ScreenInfo(BaseModel):
    """Screen information from analysis."""

    name: str
    class_name: str
    keybindings: List[Dict[str, str]]
    widgets: List[str]
    navigation_targets: List[str]


class AnalyzeResponse(BaseModel):
    """Response from code analysis."""

    app_name: str
    framework: str
    screens: List[ScreenInfo]
    total_screens: int
    total_keybindings: int
    entry_point: Optional[str]
    analysis_time: float

    class Config:
        schema_extra = {
            "example": {
                "app_name": "MyApp",
                "framework": "textual",
                "screens": [
                    {
                        "name": "MainScreen",
                        "class_name": "MainScreen",
                        "keybindings": [{"key": "q", "action": "quit"}],
                        "widgets": ["Button", "Input"],
                        "navigation_targets": ["SettingsScreen"]
                    }
                ],
                "total_screens": 3,
                "total_keybindings": 12,
                "entry_point": "main.py",
                "analysis_time": 1.23
            }
        }


class GenerateRequest(BaseModel):
    """Request to generate test scenarios."""

    app_path: str = Field(..., description="Path to analyzed application")
    strategy: str = Field("smoke", description="Generation strategy (smoke, coverage, keybinding, navigation)")
    output_dir: Optional[str] = Field(None, description="Directory to write scenarios")
    async_mode: bool = Field(False, description="Run generation asynchronously")

    @validator("strategy")
    def validate_strategy(cls, v):
        """Ensure valid strategy."""
        valid = ["smoke", "coverage", "keybinding", "navigation", "all"]
        if v not in valid:
            raise ValueError(f"Invalid strategy. Must be one of: {', '.join(valid)}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "app_path": "./my_app",
                "strategy": "smoke",
                "output_dir": "./scenarios",
                "async_mode": True
            }
        }


class ScenarioInfo(BaseModel):
    """Generated scenario information."""

    name: str
    path: str
    strategy: str
    steps: int
    validations: int


class GenerateResponse(BaseModel):
    """Response from scenario generation."""

    scenarios: List[ScenarioInfo]
    total_scenarios: int
    output_directory: str
    generation_time: float

    class Config:
        schema_extra = {
            "example": {
                "scenarios": [
                    {
                        "name": "smoke_test_main",
                        "path": "./scenarios/smoke_test_main.yaml",
                        "strategy": "smoke",
                        "steps": 5,
                        "validations": 3
                    }
                ],
                "total_scenarios": 5,
                "output_directory": "./scenarios",
                "generation_time": 0.45
            }
        }


class JobResponse(BaseModel):
    """Response for asynchronous job."""

    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "created_at": "2025-11-16T12:00:00Z",
                "started_at": "2025-11-16T12:00:01Z",
                "progress": 45.5,
                "result": None,
                "error": None
            }
        }


class KnowledgeResponse(BaseModel):
    """Response for application knowledge retrieval."""

    app_id: str
    app_name: str
    framework: str
    screens: List[ScreenInfo]
    indexed_at: datetime
    last_updated: datetime

    class Config:
        schema_extra = {
            "example": {
                "app_id": "my_app_v1",
                "app_name": "MyApp",
                "framework": "textual",
                "screens": [],
                "indexed_at": "2025-11-16T11:00:00Z",
                "last_updated": "2025-11-16T11:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    uptime: float
    jobs_pending: int
    jobs_running: int

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.2.1",
                "uptime": 3600.5,
                "jobs_pending": 2,
                "jobs_running": 1
            }
        }
