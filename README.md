# Pipeline Doctor

**AI-assisted CI failure investigation that turns failed pipeline evidence into a structured troubleshooting report.**

Pipeline Doctor is a portfolio project built with Python, FastAPI, Docker, GitHub Actions, JavaScript, and a local Ollama LLM.

It accepts a pipeline event, extracts failed jobs, classifies known failure patterns, asks an LLM for structured troubleshooting guidance, and returns the result through a REST API. A browser dashboard consumes that API and renders the analysis dynamically.

---

## Demo

Pipeline Doctor includes a browser-based dashboard for investigating CI failures.

The demo shows:

- failed pipeline information
- FastAPI `POST /analyze`
- rule-based failure classification
- Ollama / Qwen analysis
- structured troubleshooting results
- HTTP response status
- analysis duration
- raw JSON API response

![Pipeline Doctor demo](docs/demo/pipeline-doctor-demo.gif)

[Watch higher-quality MP4](docs/demo/pipeline-doctor-demo.mp4)

---

## Architecture

```text
Browser Dashboard
      |
      | POST /analyze
      v
FastAPI :8080
      |
      v
Pipeline Doctor Core
      |
      +----> Failed-job extraction
      |
      +----> Rule-based classifier
      |
      +----> Ollama / Qwen
      |
      v
Structured JSON response
      |
      v
Browser renders analysis
```

The application runs in Docker. Ollama currently runs on the development host and is reached from the container through `host.docker.internal:11434`.

---

## How the Analysis Works

```text
Pipeline Event
      |
      v
Extract Failed Jobs
      |
      v
Rule-based Classification
      |
      v
LLM Analysis
      |
      v
Structured JSON
      |
      v
Web Dashboard
```

The classifier currently identifies common failure categories using deterministic Python rules.

Examples:

```text
"copy failed"        -> docker_build
"connection refused" -> connection
"permission denied"  -> permission
"assertionerror"      -> test_failure
```

The classifier is intentionally simple and deterministic. It is not a machine-learning classifier.

The LLM is used for the less deterministic part of the investigation:

- summarize the failure
- suggest a likely root cause
- generate troubleshooting actions

---

## Web Interface

The frontend is currently implemented with HTML, CSS, and JavaScript.

JavaScript calls the FastAPI backend using `fetch()`:

```text
Analyze Pipeline button
        |
        v
JavaScript fetch()
        |
        | POST /analyze
        v
FastAPI
        |
        v
Pipeline Doctor
        |
        v
JSON response
        |
        v
Dynamic dashboard rendering
```

The dashboard displays:

- repository
- pipeline ID
- pipeline status
- failed-job count
- failure categories
- original failure log
- analysis summary
- likely root cause
- recommended actions
- API HTTP status
- analysis duration
- model information
- raw API response

---

## API

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

### Analyze Pipeline

```http
POST /analyze
Content-Type: application/json
```

The endpoint accepts a pipeline event and returns structured failure analysis.

---

## Example Pipeline Event

```json
{
  "pipeline_id": 4812,
  "repository": "payment-service",
  "status": "failed",
  "jobs": [
    {
      "name": "unit-tests",
      "status": "passed",
      "duration_seconds": 48
    },
    {
      "name": "docker-build",
      "status": "failed",
      "duration_seconds": 32,
      "log": "COPY failed: requirements.txt not found"
    },
    {
      "name": "integration-tests",
      "status": "failed",
      "duration_seconds": 61,
      "log": "Connection refused: database:5432"
    }
  ]
}
```

Pipeline Doctor extracts only the failed jobs for analysis.

---

## Example Analysis

```json
{
  "name": "docker-build",
  "log": "COPY failed: requirements.txt not found",
  "category": "docker_build",
  "analysis_status": "success",
  "analysis": {
    "summary": "The Docker build failed because requirements.txt could not be copied.",
    "likely_root_cause": "The file may not be available in the Docker build context or the COPY path may be incorrect.",
    "suggestions": [
      "Verify that requirements.txt exists in the expected location.",
      "Check the Dockerfile COPY path.",
      "Inspect the Docker build context."
    ]
  }
}
```

LLM-generated root causes are troubleshooting hypotheses and should be validated against real evidence.

---

## GitHub Actions Workflow

Pipeline Doctor also runs through GitHub Actions using a self-hosted Linux runner.

Current workflow:

```text
workflow_dispatch
      |
      v
Self-hosted Linux Runner
      |
      v
Checkout Repository
      |
      v
docker compose up -d --build
      |
      v
Wait for GET /health
      |
      v
POST pipeline_event.json to /analyze
      |
      v
Generate analysis report
      |
      v
Upload GitHub Actions artifact
      |
      v
Collect logs and stop containers
```

### Trigger

The workflow currently uses a manual trigger:

```yaml
on:
  workflow_dispatch:
```

This means the workflow is started manually from GitHub Actions. Automatic `push` or `pull_request` triggers can be added later.

---

## Run Locally

### 1. Make sure Ollama is running

Pipeline Doctor currently uses:

```text
qwen2.5-coder:7b
```

Verify Ollama:

```bash
curl http://localhost:11434/api/tags
```

### 2. Start Pipeline Doctor

```bash
docker compose up -d --build
```

Check the container:

```bash
docker compose ps
```

### 3. Verify FastAPI

```bash
curl http://localhost:8080/health
```

Expected:

```json
{
  "status": "healthy"
}
```

### 4. Open the Dashboard

Open:

```text
http://localhost:8080
```

Click **Analyze Pipeline**. The browser sends the pipeline event to `POST /analyze` and dynamically displays the returned analysis.

### 5. Call the API Directly

```bash
curl --silent --show-error --fail \
  -X POST \
  http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  --data @pipeline_event.json \
  | python3 -m json.tool
```

---

## Docker Runtime

The Docker image contains the FastAPI backend and frontend assets:

```text
api.py
pipeline_doctor.py
templates/
static/
```

FastAPI serves:

```text
GET /
-> web dashboard

GET /static/*
-> CSS and JavaScript

GET /health
-> health API

POST /analyze
-> pipeline analysis API
```

The application container communicates with Ollama using:

```text
http://host.docker.internal:11434
```

---

## Technologies Used

- **Python** — backend and CI failure-analysis logic
- **FastAPI** — REST API and web application server
- **HTML / CSS / JavaScript** — browser dashboard
- **Requests** — HTTP communication with Ollama
- **Ollama** — local LLM runtime
- **Qwen2.5-Coder 7B** — troubleshooting analysis
- **Docker** — application packaging
- **Docker Compose** — local service execution
- **GitHub Actions** — CI workflow
- **Self-hosted GitHub Actions Runner** — executes the workflow with Docker and Ollama access
- **JSON** — pipeline input and structured analysis output

---

## Manual Agent Experiment

The repository also contains a separate manual agent implementation under `manual_agent/`.

It was built to understand agent mechanics before using an agent framework. The agent can choose between tools such as:

```text
search_log
read_file
list_files
```

The Python application controls:

- allowed tools
- tool execution
- conversation state
- duplicate tool-call prevention
- maximum investigation steps

The manual agent is currently an experimental component and is **not yet integrated into the main FastAPI `/analyze` flow**.

---

## Current Limitations

Pipeline Doctor is currently a working portfolio prototype rather than a production service.

Current limitations include:

- pipeline events currently use sample CI data
- Ollama runs locally
- no API authentication or authorization
- CI logs are not yet redacted for secrets before LLM analysis
- LLM output validation is limited
- retry handling needs improvement
- large-log handling is limited
- automated test coverage still needs to be expanded
- the model name displayed by the frontend is currently not fully runtime-driven
- the manual agent is not yet integrated into the main analysis flow

---

## Planned Improvements

Planned improvements include:

- add reliable automated unit and API tests
- add schema validation for API input and output
- improve structured logging and error handling
- add secret redaction before LLM processing
- add retry and timeout handling
- improve large-log extraction
- return runtime model metadata from the backend
- integrate agent-based investigation where useful
- improve GitHub Actions integration with real failed workflow evidence
- deploy Pipeline Doctor as a hosted service
- optionally migrate the frontend to React + TypeScript for a larger production UI
