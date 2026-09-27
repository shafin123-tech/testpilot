"""Convert GitHub Actions job data into Pipeline Doctor's event format."""

from datetime import datetime


def build_pipeline_event(jobs_response, logs_by_job_id, repository, run_id):
    """Build an event from a GitHub jobs response and downloaded job logs.

    GitHub reports a completed job's result in conclusion. Pipeline Doctor
    expects status and an attached log for each failed job.
    """
    jobs = []

    for job in jobs_response["jobs"]:
        if job.get("conclusion") != "failure":
            continue

        job_id = job["id"]
        if job_id not in logs_by_job_id:
            raise ValueError(f"Missing log for failed job {job_id}")

        started = job.get("started_at")
        completed = job.get("completed_at")
        duration_seconds = None
        if started and completed:
            start_time = datetime.fromisoformat(started.replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            duration_seconds = int((end_time - start_time).total_seconds())

        jobs.append({
            "name": job["name"],
            "status": "failed",
            "log": logs_by_job_id[job_id],
            "job_id": job_id,
            "duration_seconds": duration_seconds,
        })

    return {
        "pipeline_id": run_id,
        "repository": repository,
        "status": "failed" if jobs else "passed",
        "jobs": jobs,
    }
