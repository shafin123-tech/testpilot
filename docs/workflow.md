# GitHub Actions Workflow

The Pipeline Doctor workflow is defined in:

[`.github/workflows/pipeline-doctor.yaml`](../.github/workflows/pipeline-doctor.yaml)

## Purpose

The workflow runs Pipeline Doctor on a self-hosted Linux runner.

It retrieves a pipeline event, analyzes failed jobs with a local Ollama model, generates a JSON report, and uploads the report as a GitHub Actions artifact.

## Trigger

The workflow currently uses:

```yaml
on:
  workflow_dispatch:
