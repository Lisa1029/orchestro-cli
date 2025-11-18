# Orchestro Intelligence API Documentation

**Version**: 0.2.1
**Status**: Production Ready
**Last Updated**: 2025-11-16

---

## Overview

The Orchestro Intelligence API provides RESTful and GraphQL interfaces for automated CLI/TUI test generation. It enables code analysis, intelligent test scenario generation, and real-time monitoring through WebSocket connections.

### Key Features

- **REST API**: Full CRUD operations for analysis and generation
- **GraphQL API**: Flexible querying with Strawberry
- **WebSocket**: Real-time analysis streaming
- **Async Jobs**: Background processing for long-running tasks
- **Authentication**: API key-based security
- **Rate Limiting**: Protection against abuse
- **Auto Documentation**: OpenAPI 3.0 (Swagger) and ReDoc

---

## Quick Start

### Installation

```bash
# Install with API dependencies
pip install orchestro-cli

# Or install from source
git clone https://github.com/vyb/orchestro-cli
cd orchestro-cli
pip install -e ".[dev]"
```

### Starting the Server

```bash
# Development mode (auto-reload)
orchestro api serve --reload

# Production mode (multiple workers)
orchestro api serve --workers 4 --log-level warning

# Custom host and port
orchestro api serve --host 0.0.0.0 --port 8080
```

### Server Information

```bash
orchestro api info
```

**Default URLs**:
- Server: http://localhost:8000
- OpenAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- GraphQL Playground: http://localhost:8000/graphql

---

## Authentication

### API Keys

All API endpoints require authentication via API key.

**Provide API key via**:
1. **Header** (recommended): `X-API-Key: orchestro_YOUR_KEY_HERE`
2. **Query parameter**: `?api_key=orchestro_YOUR_KEY_HERE`

### Generating API Keys

```python
from orchestro_cli.api.auth import generate_api_key

# Generate key that expires in 365 days
api_key = generate_api_key("my_app", expires_days=365)
print(f"Your API key: {api_key}")

# Generate key that never expires
api_key = generate_api_key("production_key", expires_days=None)
```

### Development Key

A development API key is automatically generated when the server starts:

```
🔑 Development API Key: orchestro_<random_token>
```

---

## REST API Endpoints

### Health Check

**GET** `/health`

Check API server health and status.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.2.1",
  "uptime": 3600.5,
  "jobs_pending": 2,
  "jobs_running": 1
}
```

---

### Analyze Application Code

**POST** `/api/v1/analyze`

Analyze application code to extract structure and generate knowledge graph.

**Request**:
```json
{
  "app_path": "./my_app",
  "framework": "textual",
  "async_mode": false
}
```

**Parameters**:
- `app_path` (required): Path to application directory
- `framework` (optional): Framework to analyze (`textual`, `click`, etc.)
- `async_mode` (optional): Run asynchronously (default: `false`)

**Synchronous Response** (async_mode=false):
```json
{
  "app_name": "my_app",
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
```

**Asynchronous Response** (async_mode=true):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "check_status": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: orchestro_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "app_path": "./my_textual_app",
    "framework": "textual",
    "async_mode": false
  }'
```

---

### Generate Test Scenarios

**POST** `/api/v1/generate`

Generate test scenarios from analyzed application.

**Request**:
```json
{
  "app_path": "./my_app",
  "strategy": "smoke",
  "output_dir": "./scenarios",
  "async_mode": false
}
```

**Parameters**:
- `app_path` (required): Path to analyzed application
- `strategy` (required): Generation strategy
  - `smoke`: Basic smoke tests
  - `coverage`: Coverage-driven tests
  - `keybinding`: Keybinding tests
  - `navigation`: Navigation flow tests
  - `all`: All strategies
- `output_dir` (optional): Directory to write scenarios
- `async_mode` (optional): Run asynchronously (default: `false`)

**Response**:
```json
{
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
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "X-API-Key: orchestro_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "app_path": "./my_app",
    "strategy": "coverage",
    "output_dir": "./generated_tests"
  }'
```

---

### Get Application Knowledge

**GET** `/api/v1/knowledge/{app_id}`

Retrieve cached application knowledge from previous analysis.

**Response**:
```json
{
  "app_id": "my_app_v1",
  "app_name": "my_app",
  "framework": "textual",
  "screens": [...],
  "indexed_at": "2025-11-16T11:00:00Z",
  "last_updated": "2025-11-16T11:00:00Z"
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/knowledge/my_app_v1 \
  -H "X-API-Key: orchestro_YOUR_KEY"
```

---

### Job Management

#### Get Job Status

**GET** `/api/v1/jobs/{job_id}`

Get status of asynchronous job.

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2025-11-16T12:00:00Z",
  "started_at": "2025-11-16T12:00:01Z",
  "completed_at": null,
  "progress": 45.5,
  "result": null,
  "error": null
}
```

**Status Values**:
- `pending`: Job queued, not started
- `running`: Job in progress
- `completed`: Job finished successfully
- `failed`: Job failed with error
- `cancelled`: Job cancelled by user

**Example**:
```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: orchestro_YOUR_KEY"
```

#### Cancel Job

**DELETE** `/api/v1/jobs/{job_id}`

Cancel a running or pending job.

**Response**:
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 cancelled"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: orchestro_YOUR_KEY"
```

---

## WebSocket API

### Real-Time Analysis

**WS** `/ws/analyze/{app_path}`

WebSocket endpoint for real-time analysis with progress updates.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analyze/my_app');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.status === 'connected') {
    console.log('Analysis started');
  } else if (data.status === 'progress') {
    console.log(`Progress: ${data.progress}%`);
  } else if (data.status === 'completed') {
    console.log('Analysis complete:', data.result);
  } else if (data.status === 'error') {
    console.error('Error:', data.message);
  }
};
```

**Message Types**:
1. **Connected**: `{"status": "connected", "message": "Starting analysis..."}`
2. **Progress**: `{"status": "progress", "progress": 45.5, "message": "Analyzing..."}`
3. **Completed**: `{"status": "completed", "result": {...}}`
4. **Error**: `{"status": "error", "message": "Error description"}`

---

## GraphQL API

### Endpoint

**POST** `/graphql`

GraphQL endpoint with interactive playground.

### Queries

#### Health Check

```graphql
query {
  health
}
```

#### Get Job Status

```graphql
query GetJob($jobId: String!) {
  job(jobId: $jobId) {
    jobId
    status
    progress
    createdAt
    startedAt
    completedAt
  }
}
```

#### Get Application Knowledge

```graphql
query GetKnowledge($appId: String!) {
  knowledge(appId: $appId) {
    appId
    appName
    framework
    screens {
      name
      className
      keybindings
      widgets
    }
    indexedAt
    lastUpdated
  }
}
```

#### List Jobs

```graphql
query ListJobs($status: JobStatusEnum) {
  listJobs(status: $status) {
    jobId
    status
    progress
    createdAt
  }
}
```

### Mutations

#### Analyze Application

```graphql
mutation Analyze($appPath: String!, $framework: String, $asyncMode: Boolean!) {
  analyze(appPath: $appPath, framework: $framework, asyncMode: $asyncMode)
}
```

#### Generate Scenarios

```graphql
mutation Generate(
  $appPath: String!,
  $strategy: String!,
  $outputDir: String,
  $asyncMode: Boolean!
) {
  generate(
    appPath: $appPath,
    strategy: $strategy,
    outputDir: $outputDir,
    asyncMode: $asyncMode
  )
}
```

#### Cancel Job

```graphql
mutation CancelJob($jobId: String!) {
  cancelJob(jobId: $jobId)
}
```

---

## Client Examples

### Python

```python
import httpx

API_URL = "http://localhost:8000"
API_KEY = "orchestro_YOUR_KEY"

headers = {"X-API-Key": API_KEY}

# Analyze application
response = httpx.post(
    f"{API_URL}/api/v1/analyze",
    json={
        "app_path": "./my_app",
        "framework": "textual",
        "async_mode": False
    },
    headers=headers
)
result = response.json()
print(f"Found {result['total_screens']} screens")

# Generate scenarios
response = httpx.post(
    f"{API_URL}/api/v1/generate",
    json={
        "app_path": "./my_app",
        "strategy": "smoke"
    },
    headers=headers
)
result = response.json()
print(f"Generated {result['total_scenarios']} scenarios")
```

### JavaScript/TypeScript

```typescript
const API_URL = 'http://localhost:8000';
const API_KEY = 'orchestro_YOUR_KEY';

// Analyze application
const analyzeResponse = await fetch(`${API_URL}/api/v1/analyze`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    app_path: './my_app',
    framework: 'textual',
    async_mode: false
  })
});

const result = await analyzeResponse.json();
console.log(`Found ${result.total_screens} screens`);

// Generate scenarios
const generateResponse = await fetch(`${API_URL}/api/v1/generate`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    app_path: './my_app',
    strategy: 'coverage'
  })
});

const scenarios = await generateResponse.json();
console.log(`Generated ${scenarios.total_scenarios} scenarios`);
```

### cURL

```bash
# Analyze
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: orchestro_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"app_path": "./my_app", "framework": "textual"}'

# Generate
curl -X POST http://localhost:8000/api/v1/generate \
  -H "X-API-Key: orchestro_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"app_path": "./my_app", "strategy": "smoke"}'

# Get job status
curl http://localhost:8000/api/v1/jobs/JOB_ID \
  -H "X-API-Key: orchestro_YOUR_KEY"
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful synchronous request
- `202 Accepted`: Asynchronous job created
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "app_path"],
      "msg": "Path does not exist: /nonexistent/path",
      "type": "value_error"
    }
  ]
}
```

---

## Rate Limiting

**Current Limits**:
- 100 requests per minute per API key (configurable)
- Concurrent jobs: No limit (memory-based queue)

**Future Enhancements**:
- Redis-based distributed rate limiting
- Per-endpoint rate limits
- Burst allowance

---

## Best Practices

### 1. Use Async Mode for Large Applications

```python
# Large codebase? Use async
response = httpx.post(
    f"{API_URL}/api/v1/analyze",
    json={"app_path": "./large_app", "async_mode": True},
    headers=headers
)
job_id = response.json()["job_id"]

# Poll for completion
while True:
    status = httpx.get(f"{API_URL}/api/v1/jobs/{job_id}", headers=headers)
    job = status.json()

    if job["status"] == "completed":
        result = job["result"]
        break
    elif job["status"] == "failed":
        print(f"Error: {job['error']}")
        break

    time.sleep(2)  # Poll every 2 seconds
```

### 2. Cache Knowledge for Repeated Generation

```python
# Analyze once
analyze_response = httpx.post(
    f"{API_URL}/api/v1/analyze",
    json={"app_path": "./my_app"},
    headers=headers
)

# Knowledge is cached - generate multiple times
for strategy in ["smoke", "coverage", "keybinding"]:
    httpx.post(
        f"{API_URL}/api/v1/generate",
        json={"app_path": "./my_app", "strategy": strategy},
        headers=headers
    )
```

### 3. Use WebSocket for Real-Time Feedback

```python
import asyncio
import websockets

async def analyze_realtime():
    uri = f"ws://localhost:8000/ws/analyze/my_app"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)

            if data["status"] == "progress":
                print(f"Progress: {data['progress']}%")
            elif data["status"] == "completed":
                print("Done:", data["result"])
                break

asyncio.run(analyze_realtime())
```

---

## Deployment

### Production Configuration

```bash
# Use multiple workers
orchestro api serve --workers 4 --log-level warning

# With Gunicorn (recommended for production)
gunicorn orchestro_cli.api.server:create_app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY . .

EXPOSE 8000

CMD ["orchestro", "api", "serve", "--host", "0.0.0.0", "--workers", "4"]
```

### Environment Variables

```bash
# API Configuration
export ORCHESTRO_API_HOST="0.0.0.0"
export ORCHESTRO_API_PORT="8000"
export ORCHESTRO_API_WORKERS="4"
export ORCHESTRO_API_LOG_LEVEL="info"

# Security
export ORCHESTRO_API_KEYS_FILE="/path/to/api_keys.json"
export ORCHESTRO_RATE_LIMIT="100"  # requests per minute
```

---

## Monitoring

### Health Endpoint

Monitor server health with `/health`:

```bash
curl http://localhost:8000/health
```

**Metrics**:
- `status`: Server health status
- `uptime`: Server uptime in seconds
- `jobs_pending`: Number of queued jobs
- `jobs_running`: Number of running jobs

### Logging

```python
# Enable debug logging
orchestro api serve --log-level debug

# Access logs
orchestro api serve --access-log

# Custom logging configuration
import logging
logging.basicConfig(level=logging.INFO)
```

---

## Troubleshooting

### Common Issues

#### 1. API Key Not Working

```bash
# Check if key exists
curl http://localhost:8000/health \
  -H "X-API-Key: YOUR_KEY"

# If 401, generate new key
python -c "from orchestro_cli.api.auth import generate_api_key; print(generate_api_key('test'))"
```

#### 2. Job Stuck in "running" Status

```bash
# Cancel and retry
curl -X DELETE http://localhost:8000/api/v1/jobs/JOB_ID \
  -H "X-API-Key: YOUR_KEY"
```

#### 3. WebSocket Connection Fails

```bash
# Check if server supports WebSockets
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws/analyze/test
```

---

## API Changelog

### v0.2.1 (2025-11-16)

**Added**:
- Complete REST API with FastAPI
- GraphQL API with Strawberry
- WebSocket support for real-time analysis
- API key authentication
- Async job queue
- Auto-generated OpenAPI documentation
- Comprehensive test suite

---

## Future Roadmap

- [ ] Redis-based job queue
- [ ] Distributed rate limiting
- [ ] OAuth2 authentication
- [ ] Webhook notifications
- [ ] Batch operations
- [ ] API usage analytics
- [ ] Cost estimation endpoints
- [ ] Multi-tenant support

---

*For issues or feature requests, visit [GitHub Issues](https://github.com/vyb/orchestro-cli/issues)*
