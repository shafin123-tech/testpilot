# Pipeline Doctor

Pipeline Doctor is a CI failure-analysis prototype built with Python, Docker, GitHub Actions, and a local Ollama LLM.

It reads a pipeline event, extracts failed jobs, classifies known failure patterns, asks an LLM for a structured investigation, and publishes the final JSON report as a GitHub Actions artifact.

## Problem

CI failures often require engineers to manually inspect logs and identify the likely root cause.

Pipeline Doctor helps by producing an initial investigation report containing:

- failure category
- summary of what failed
- likely root cause
- practical troubleshooting suggestions

The tool is designed to assist engineers, not replace human investigation.

## Architecture

See the detailed architecture:

[Architecture documentation](docs/architecture.md)

## Workflow

See the GitHub Actions execution flow:

[Workflow documentation](docs/workflow.md)

The workflow file is located at:

[`.github/workflows/pipeline-doctor.yaml`](.github/workflows/pipeline-doctor.yaml)

## Examples

Sample pipeline event:

[`examples/pipeline_event.json`](examples/pipeline_event.json)

Sample analysis report:

[`examples/pipeline_analysis.json`](examples/pipeline_analysis.json)

## Run locally

```bash
python3 -m http.server 8000


