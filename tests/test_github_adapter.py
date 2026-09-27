import pytest

from github_adapter import build_pipeline_event
from pipeline_doctor import extract_failed_jobs


def test_github_jobs_feed_the_existing_failure_analyzer():
    github_response = {
        "jobs": [
            {"id": 10, "name": "unit-tests", "conclusion": "success"},
            {
                "id": 11,
                "name": "docker-build",
                "conclusion": "failure",
                "started_at": "2026-09-27T10:00:00Z",
                "completed_at": "2026-09-27T10:00:32Z",
            },
        ]
    }
    event = build_pipeline_event(
        github_response,
        {11: "COPY failed: requirements.txt not found"},
        "shafin123-tech/testpilot",
        4812,
    )

    assert event["pipeline_id"] == 4812
    assert event["status"] == "failed"
    assert event["jobs"][0]["duration_seconds"] == 32
    assert extract_failed_jobs(event) == [
        {"name": "docker-build", "log": "COPY failed: requirements.txt not found"}
    ]


def test_missing_failed_job_log_is_reported_instead_of_analyzed():
    github_response = {
        "jobs": [{"id": 11, "name": "docker-build", "conclusion": "failure"}]
    }

    with pytest.raises(ValueError, match="Missing log for failed job 11"):
        build_pipeline_event(
            github_response, {}, "shafin123-tech/testpilot", 4812
        )


def test_successful_run_has_no_failed_jobs():
    github_response = {
        "jobs": [{"id": 10, "name": "unit-tests", "conclusion": "success"}]
    }

    event = build_pipeline_event(
        github_response, {}, "shafin123-tech/testpilot", 4812
    )

    assert event["status"] == "passed"
    assert extract_failed_jobs(event) == []
