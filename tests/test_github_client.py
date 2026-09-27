from unittest.mock import Mock

import pytest
import requests

import github_client
from pipeline_doctor import extract_failed_jobs


def response(*, payload=None, body="", status=200):
    result = Mock(status_code=status, text=body)
    result.json.return_value = payload
    result.raise_for_status.side_effect = (
        requests.HTTPError(response=result) if status >= 400 else None
    )
    return result


def test_fetches_only_failed_job_logs_and_builds_existing_event(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    jobs = {
        "total_count": 2,
        "jobs": [
            {"id": 1, "name": "unit-tests", "status": "completed", "conclusion": "success"},
            {"id": 2, "name": "build", "status": "completed", "conclusion": "failure"},
        ],
    }
    get = Mock(side_effect=[
        response(payload=jobs),
        response(body="COPY failed: requirements.txt not found"),
    ])
    monkeypatch.setattr(github_client.requests, "get", get)

    event = github_client.fetch_github_run_event("shafin123-tech/testpilot", 123, "abc")

    assert extract_failed_jobs(event) == [
        {"name": "build", "log": "COPY failed: requirements.txt not found"}
    ]
    assert get.call_count == 2
    assert get.call_args_list[0].args[0].endswith("/runs/123/jobs")
    assert get.call_args_list[1].args[0].endswith("/jobs/2/logs")
    assert get.call_args_list[0].kwargs["headers"]["Authorization"] == "Bearer abc"


def test_fails_when_github_does_not_return_the_log(monkeypatch):
    jobs = {
        "total_count": 1,
        "jobs": [{"id": 2, "name": "build", "status": "completed", "conclusion": "failure"}],
    }
    get = Mock(side_effect=[response(payload=jobs), response(status=404)])
    monkeypatch.setattr(github_client.requests, "get", get)

    with pytest.raises(requests.HTTPError):
        github_client.fetch_github_run_event("shafin123-tech/testpilot", 123)


def test_rejects_partial_job_lists(monkeypatch):
    jobs = {
        "total_count": 101,
        "jobs": [{"id": 1, "status": "completed", "conclusion": "success"}],
    }
    get = Mock(return_value=response(payload=jobs))
    monkeypatch.setattr(github_client.requests, "get", get)

    with pytest.raises(ValueError, match="pagination"):
        github_client.fetch_github_run_event("shafin123-tech/testpilot", 123)
    assert get.call_count == 1
