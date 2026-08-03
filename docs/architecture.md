# Architecture

```text
GitHub Actions
      |
      v
Self-hosted Linux runner
      |
      +--> starts Python HTTP server on port 8000
      |
      +--> runs Docker Compose
              |
              v
      Pipeline Doctor container
              |
              +--> GET pipeline event
              |
              +--> classify failed logs
              |
              +--> POST logs to Ollama
              |
              v
      pipeline_analysis.json
              |
              v
      GitHub Actions artifact
