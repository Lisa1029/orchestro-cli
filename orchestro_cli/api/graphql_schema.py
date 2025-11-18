"""GraphQL schema using Strawberry."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter


@strawberry.enum
class JobStatusEnum(strawberry.Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.type
class ScreenInfo:
    """Screen information from analysis."""
    name: str
    class_name: str
    keybindings: List[str]
    widgets: List[str]
    navigation_targets: List[str]


@strawberry.type
class AnalysisResult:
    """Result of code analysis."""
    app_name: str
    framework: str
    screens: List[ScreenInfo]
    total_screens: int
    total_keybindings: int
    entry_point: Optional[str]
    analysis_time: float


@strawberry.type
class ScenarioInfo:
    """Generated scenario information."""
    name: str
    path: str
    strategy: str
    steps: int
    validations: int


@strawberry.type
class GenerationResult:
    """Result of scenario generation."""
    scenarios: List[ScenarioInfo]
    total_scenarios: int
    output_directory: str
    generation_time: float


@strawberry.type
class Job:
    """Asynchronous job."""
    job_id: str
    status: JobStatusEnum
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float


@strawberry.type
class AppKnowledge:
    """Application knowledge cache."""
    app_id: str
    app_name: str
    framework: str
    screens: List[ScreenInfo]
    indexed_at: datetime
    last_updated: datetime


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    def health(self) -> str:
        """Health check."""
        return "healthy"

    @strawberry.field
    def job(self, job_id: str) -> Optional[Job]:
        """Get job status by ID."""
        # TODO: Integrate with job storage
        return None

    @strawberry.field
    def knowledge(self, app_id: str) -> Optional[AppKnowledge]:
        """Get cached application knowledge."""
        # TODO: Integrate with knowledge cache
        return None

    @strawberry.field
    def list_jobs(self, status: Optional[JobStatusEnum] = None) -> List[Job]:
        """List all jobs, optionally filtered by status."""
        # TODO: Integrate with job storage
        return []


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    def analyze(
        self,
        app_path: str,
        framework: Optional[str] = None,
        async_mode: bool = False
    ) -> str:
        """
        Analyze application code.

        Returns job_id if async_mode=True, otherwise returns status.
        """
        # TODO: Integrate with analysis service
        if async_mode:
            return "job_uuid_placeholder"
        return "analysis_started"

    @strawberry.mutation
    def generate(
        self,
        app_path: str,
        strategy: str = "smoke",
        output_dir: Optional[str] = None,
        async_mode: bool = False
    ) -> str:
        """
        Generate test scenarios.

        Returns job_id if async_mode=True, otherwise returns status.
        """
        # TODO: Integrate with generation service
        if async_mode:
            return "job_uuid_placeholder"
        return "generation_started"

    @strawberry.mutation
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        # TODO: Integrate with job storage
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)


def create_graphql_router() -> GraphQLRouter:
    """Create GraphQL router for FastAPI."""
    return GraphQLRouter(schema, path="/graphql")
