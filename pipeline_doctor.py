

import requests
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)




PIPELINE_URL = os.getenv(
    "PIPELINE_URL",
    "http://localhost:8000/pipeline_event.json",
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat",
)

MODEL = os.getenv(
    "MODEL",
    "qwen2.5-coder:7b",
)

OUTPUT_FILE = os.getenv(
    "OUTPUT_FILE",
    "pipeline_analysis.json",
)



def classify_failure(log):
    log_lower = log.lower()

    if "copy failed" in log_lower:
        return "docker_build"

    if "connection refused" in log_lower:
        return "connection"

    if "permission denied" in log_lower:
        return "permission"

    if "assertionerror" in log_lower:
        return "test_failure"

    return "unknown"

def fetch_pipeline_event_simple(url):
    response = requests.get(url)

    #print("response", response)

    response.raise_for_status()

    event = response.json()

    print("event type", type(event))

   # print("event", event["jobs"][0]["name"])

    return event

def fetch_pipeline_event(url):
    logger.info("Requesting pipeline event: url=%s", url)

    response = requests.get(url, timeout=5)

    logger.info(
        "Pipeline API responded: status_code=%s",
        response.status_code
    )

    response.raise_for_status()

    event = response.json()

    return event


def extract_failed_jobs(event):

    if not isinstance(event, dict):
        logger.error(
            "Invalid pipeline event type: actual_type=%s",
            type(event).__name__
        )
        raise TypeError("Pipeline event must be a dictionary")

    # jobs = event["jobs"]
    pipeline_id = event.get("pipeline_id", "unknown")
    jobs = event.get("jobs", [])
    
    if not isinstance(jobs, list):
        logger.error(
            "Invalid jobs field: pipeline_id=%s actual_type=%s",
            pipeline_id,
            type(jobs).__name__
    )
        raise TypeError("'jobs' must be a list")

    
    failed_jobs = []

    for job in jobs:
        if job.get("status") == "failed":
            failed_job = {
                "name": job.get("name", "unknown-job"),
                "log": job.get("log", "No log available")
            }

            failed_jobs.append(failed_job)

    return failed_jobs

def count_categories(analyzed_jobs):
    category_counts = {}

    for job in analyzed_jobs:
        category = job["category"]

        if category not in category_counts:
            category_counts[category] = 0

        category_counts[category] += 1

    return category_counts

def analyze_all_failed_jobs(failed_jobs):
    analyzed_jobs = []

    for job in failed_jobs:
        job_name = job["name"]
        job_log = job["log"]

        category = classify_failure(job_log)

        logger.info(
            "Analyzing failed job: job_name=%s category=%s",
            job_name,
            category,
        )

        llm_analysis = analyze_failure_with_llm(
            job_name,
            job_log,
            category,
        )

        analyzed_job = {
            "name": job_name,
            "log": job_log,
            "category": category,
            "analysis_status": "success",
            "analysis": llm_analysis,
        }

        analyzed_jobs.append(analyzed_job)
    for i in analyzed_jobs:
        print("analyze job i :", i)

    return analyzed_jobs


def write_analysis_report(report, output_file):
    with open(output_file, "w") as file:
        json.dump(report, file, indent=4)


def analyze_failure_with_llm(job_name, log, category):
    prompt = f"""
Analyze this CI pipeline failure.

Job name:
{job_name}

Detected failure category:
{category}

Failure log:
{log}

Return only valid JSON using exactly this structure:

{{
    "summary": "short explanation of what failed",
    "likely_root_cause": "most likely cause based on the available evidence",
    "suggestions": [
        "first troubleshooting step",
        "second troubleshooting step",
        "third troubleshooting step"
    ]
}}

Use the detected category only as supporting context.
Base the analysis primarily on the supplied failure log.
Do not include Markdown.
Do not include text before or after the JSON.
Do not claim certainty when the log does not prove the root cause.
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    response.raise_for_status()

    response_data = response.json()

    content = response_data["message"]["content"]

    analysis = json.loads(content)

    return analysis

def main():
    pipeline_url = "http://localhost:8000/pipeline_event.json"

    pipeline_event = fetch_pipeline_event(PIPELINE_URL)

    failed_jobs = extract_failed_jobs(pipeline_event)

    analyzed_jobs = analyze_all_failed_jobs(failed_jobs)
    category_counts = count_categories(analyzed_jobs)

    report = {
    "pipeline_id": pipeline_event["pipeline_id"],
    "repository": pipeline_event["repository"],
    "pipeline_status": pipeline_event["status"],
    "failed_job_count": len(analyzed_jobs),
    "category_counts": category_counts,
    "results": analyzed_jobs,
}
    write_analysis_report(report, OUTPUT_FILE)
   

    print("Analysis completed")
    print("report type", type(report))
    print("type(report[results]) ", type(report["results"]) )
 

    #print("Report written to pipeline_analysis.json")
    print(f"Report written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
#print("failed jobs", failed_jobs)
#result = extract_failed_jobs(url_failed_jobs)
#result = analyze_failed_jobs(failed_jobs)

#print("res", result)