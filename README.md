Postman collection [workflow automation.postman_collection.json](workflow%20automation.postman_collection.json)

Scaling Plan [Scaling Plan.md](Scaling%20Plan.md)
# Workflow Automation

## Overview
A Python-based workflow automation system designed to define, execute, and manage automated workflows. The project supports extensible connectors, persistent storage, and API integration.

## Features
- Define workflows using JSON files
- Execute and monitor workflow runs
- Extensible connector system (webhooks, delays, etc.)
- REST API for workflow management
- Dockerized deployment

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/kd17290/workflow-automation.git
   cd workflow-automation
   ```

2. Build the docker image:
   ```bash
   make build
   ```

3. Start the service:
   ```bash
   make up
   ```

## Usage
Checkout the swagger documentation at `http://localhost:8001/docs` for interactive API usage.
Check the logs

```bash
    docker container logs -f --tail 1000 workflow_automation
```

# Architecture
## Event-Driven Design
- HTTP triggers create workflow runs
- Background tasks execute workflows asynchronously
- Each step publishes results to the next step

## Connector Abstraction
- BaseConnector interface for all connectors
- Pluggable architecture for adding new connector types
- Context passing between steps

## Data Flow
1. Trigger: HTTP request creates workflow run
2. Execution: Background task processes steps sequentially
3. Logging: Each step result is persisted
4. Completion: Final status is saved

## API Endpoints

### Create a Workflow

**POST** `/api/workflows`

Example request body:
```json
{
  "id": "example_workflow",
  "name": "Example Notification Workflow",
  "description": "A simple workflow that delays and then sends a webhook notification",
  "steps": [
    {
      "name": "wait_step",
      "type": "delay",
      "config": {
        "duration": 2
      }
    },
    {
      "name": "notify_step",
      "type": "webhook",
      "config": {
        "url": "https://httpbin.org/post",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "message": "Workflow completed",
          "user_data": "${payload.user_id}",
          "timestamp": "${payload.timestamp}"
        }
      }
    }
  ]
}
```

### Retrieve a Workflow

**GET** `/api/workflows/{workflow_id}/`

Example:
```
GET localhost:8001/api/workflows/example_workflow/
```

### Trigger a Workflow

**POST** `/api/trigger/`

Example request body:
```json
{
  "workflow_id": "example_workflow",
  "payload": {
    "user_id": "user123",
    "timestamp": "2025-07-07T10:00:00Z",
    "event": "user_signup"
  }
}
```

### Retrieve a Run

**GET** `/api/runs/{run_id}`

Example:
```
GET localhost:8001/api/runs/95d1610f-9bb9-43f3-959e-7e52fcaaf31d
```

### List All Runs

**GET** `/api/runs/`

Example:
```
GET localhost:8001/api/runs/
```

## Project Structure

- `app/` - Core application logic
  - `main.py` - Application entry point
  - `api.py` - REST API implementation
  - `engine.py` - Workflow execution engine
  - `models.py` - Data models
  - `storage.py` - Persistence layer
- `connector/` - Workflow connectors (webhook, delay, etc.)
- `data/` - Workflow and run data
- `Dockerfile` - Containerization setup
- `docker-compose.yml` - Multi-container orchestration
- `Makefile` - Common development commands
- `pyproject.toml` / `poetry.lock` - Dependency management

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Run
```bash
    make lint
```
   to ensure linter pass

4. Run
```bash
    make tests
```
   to ensure tests passes

5. Commit your changes
6Push to your branch and open a pull request

## License

Specify your license here (e.g., MIT, Apache 2.0).

## Contact

For questions or support, contact author.
```
This version includes detailed API endpoint documentation and example requests for easier onboarding and usage.
