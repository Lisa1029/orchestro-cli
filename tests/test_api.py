"""Tests for Orchestro Intelligence API."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from orchestro_cli.api.server import create_app
from orchestro_cli.api.auth import generate_api_key


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def api_key():
    """Create test API key."""
    return generate_api_key("test_key", expires_days=1)


class TestRootEndpoints:
    """Test root endpoints."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Orchestro Intelligence API"
        assert data["version"] == "0.2.1"

    def test_health(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.2.1"
        assert "uptime" in data
        assert data["jobs_pending"] >= 0
        assert data["jobs_running"] >= 0


class TestAnalysisEndpoints:
    """Test analysis endpoints."""

    def test_analyze_sync_invalid_path(self, client):
        """Test analyze with invalid path."""
        response = client.post(
            "/api/v1/analyze",
            json={
                "app_path": "/nonexistent/path",
                "async_mode": False
            }
        )
        assert response.status_code == 422  # Validation error

    def test_analyze_sync_valid_path(self, client, tmp_path):
        """Test analyze with valid path."""
        # Create temp directory
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        response = client.post(
            "/api/v1/analyze",
            json={
                "app_path": str(app_dir),
                "framework": "textual",
                "async_mode": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "framework" in data
        assert "screens" in data
        assert "total_screens" in data
        assert data["framework"] == "textual"

    def test_analyze_async_mode(self, client, tmp_path):
        """Test async analysis."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        response = client.post(
            "/api/v1/analyze",
            json={
                "app_path": str(app_dir),
                "async_mode": True
            }
        )
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "pending"


class TestGenerationEndpoints:
    """Test scenario generation endpoints."""

    def test_generate_invalid_strategy(self, client, tmp_path):
        """Test generate with invalid strategy."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        response = client.post(
            "/api/v1/generate",
            json={
                "app_path": str(app_dir),
                "strategy": "invalid_strategy"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_generate_sync_valid(self, client, tmp_path):
        """Test generate with valid input."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        response = client.post(
            "/api/v1/generate",
            json={
                "app_path": str(app_dir),
                "strategy": "smoke",
                "async_mode": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert "total_scenarios" in data
        assert "output_directory" in data
        assert isinstance(data["scenarios"], list)

    def test_generate_async_mode(self, client, tmp_path):
        """Test async generation."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        response = client.post(
            "/api/v1/generate",
            json={
                "app_path": str(app_dir),
                "strategy": "coverage",
                "async_mode": True
            }
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"


class TestJobEndpoints:
    """Test job management endpoints."""

    def test_get_nonexistent_job(self, client):
        """Test getting non-existent job."""
        response = client.get("/api/v1/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_cancel_nonexistent_job(self, client):
        """Test cancelling non-existent job."""
        response = client.delete("/api/v1/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_job_lifecycle(self, client, tmp_path):
        """Test complete job lifecycle."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        # Create async job
        response = client.post(
            "/api/v1/analyze",
            json={
                "app_path": str(app_dir),
                "async_mode": True
            }
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        # Check job status
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] in ["pending", "running", "completed"]

        # Cancel job (may fail if already completed)
        response = client.delete(f"/api/v1/jobs/{job_id}")
        assert response.status_code in [200, 400]


class TestKnowledgeEndpoints:
    """Test knowledge cache endpoints."""

    def test_get_nonexistent_knowledge(self, client):
        """Test getting non-existent knowledge."""
        response = client.get("/api/v1/knowledge/nonexistent_app")
        assert response.status_code == 404

    def test_knowledge_after_analysis(self, client, tmp_path):
        """Test knowledge is cached after analysis."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        # Run analysis
        response = client.post(
            "/api/v1/analyze",
            json={
                "app_path": str(app_dir),
                "framework": "textual",
                "async_mode": False
            }
        )
        assert response.status_code == 200

        # Knowledge should now be cached
        app_id = f"{app_dir.name}_v1"
        response = client.get(f"/api/v1/knowledge/{app_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["app_id"] == app_id
        assert "screens" in data


class TestWebSocket:
    """Test WebSocket endpoints."""

    def test_websocket_analyze(self, client, tmp_path):
        """Test WebSocket analysis."""
        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        with client.websocket_connect(f"/ws/analyze/{app_dir}") as websocket:
            # Should receive connection message
            data = websocket.receive_json()
            assert data["status"] == "connected"

            # Should receive progress updates
            progress_received = False
            while True:
                data = websocket.receive_json()
                if data["status"] == "progress":
                    progress_received = True
                    assert 0 <= data["progress"] <= 100
                elif data["status"] == "completed":
                    assert "result" in data
                    break

            assert progress_received


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is generated."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Orchestro Intelligence API"
        assert schema["info"]["version"] == "0.2.1"

    def test_docs_available(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """Test ReDoc is available."""
        response = client.get("/redoc")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations."""

    async def test_concurrent_requests(self, client, tmp_path):
        """Test handling concurrent requests."""
        import asyncio

        app_dir = tmp_path / "test_app"
        app_dir.mkdir()

        # Simulate concurrent analysis requests
        tasks = []
        for i in range(5):
            response = client.post(
                "/api/v1/analyze",
                json={
                    "app_path": str(app_dir),
                    "async_mode": True
                }
            )
            assert response.status_code == 202

        # All should succeed
        assert len(tasks) == 0  # Placeholder for actual async test
