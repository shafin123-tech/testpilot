"""Read completed GitHub Actions jobs and logs for Pipeline Doctor."""

import os
import re

import requests

from github_adapter import build_pipeline_event


def fetch_github_run_event(repository, run_id, token=None):
    """Fetch one workflow run's jobs and return a Pipeline Doctor event.

    A token with Actions read access is needed for private repositories.
    Public repositories can be read without one.
    """
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must look like owner/name")
    if not isinstance(run_id, int) or run_id <= 0:
        raise ValueError("run_id must be a positive integer")

    headers = {"Accept": "application/vnd.github+json"}
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base_url = f"https://api.github.com/repos/{repository}/actions"
    jobs_response = requests.get(
        f"{base_url}/runs/{run_id}/jobs",
        headers=headers,
        params={"per_page": 100},
        timeout=15,
    )
    jobs_response.raise_for_status()
    payload = jobs_response.json()
    jobs = payload["jobs"]

    # A partial run could lead to a misleading report.
    if payload["total_count"] > len(jobs):
        raise ValueError("This run has more than 100 jobs; pagination is required")
    if any(job.get("status") != "completed" for job in jobs):
        raise ValueError("Wait for all jobs to complete before analyzing the run")

    logs_by_job_id = {}
    for job in jobs:
        if job.get("conclusion") != "failure":
            continue

        log_response = requests.get(
            f"{base_url}/jobs/{job['id']}/logs",
            headers=headers,
            timeout=30,
        )
        log_response.raise_for_status()
        if not log_response.text.strip():
            raise ValueError(f"Empty log for failed job {job['id']}")
        logs_by_job_id[job["id"]] = log_response.text

    return build_pipeline_event(payload, logs_by_job_id, repository, run_id)
