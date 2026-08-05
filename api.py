import json
import os

from fastapi import FastAPI

from pipeline_doctor import (
    analyze_all_failed_jobs,
    count_categories,
    extract_failed_jobs,
    write_analysis_report,
)

OUTPUT_FILE = os.getenv(
    "OUTPUT_FILE",
    "output/pipeline_analysis.json",
)

app = FastAPI(
    title="Pipeline Doctor API",
    version="1.0.0",
)


@app.get("/health")
def health():
    print("\n========================================")
    print("[DEBUG] GET /health was called")
    print("========================================")

    response = {
        "status": "healthy",
    }

    print("[DEBUG] Health response:")
    print(response)

    return response


@app.post("/analyze")
def analyze_pipeline(pipeline_event: dict):
    print("\n========================================")
    print("[DEBUG] POST /analyze was called")
    print("========================================")

    print("[DEBUG] Type of pipeline_event:")
    print(type(pipeline_event))

    print("\n[DEBUG] Full pipeline event received:")
    print(json.dumps(pipeline_event, indent=2))

    print("\n[DEBUG] Reading important pipeline fields")

    pipeline_id = pipeline_event.get("pipeline_id")
    repository = pipeline_event.get("repository")
    pipeline_status = pipeline_event.get("status")

    print("[DEBUG] pipeline_id:", pipeline_id)
    print("[DEBUG] repository:", repository)
    print("[DEBUG] pipeline status:", pipeline_status)

    print("\n----------------------------------------")
    print("[DEBUG] Calling extract_failed_jobs()")
    print("----------------------------------------")

    failed_jobs = extract_failed_jobs(pipeline_event)

    print("[DEBUG] Type of failed_jobs:")
    print(type(failed_jobs))

    print("[DEBUG] Failed jobs returned:")
    print(json.dumps(failed_jobs, indent=2))

    print("[DEBUG] Number of failed jobs:")
    print(len(failed_jobs))

    if not failed_jobs:
        print("[DEBUG] No failed jobs were found")

    print("\n----------------------------------------")
    print("[DEBUG] Calling analyze_all_failed_jobs()")
    print("----------------------------------------")

    analyzed_jobs = analyze_all_failed_jobs(failed_jobs)

    print("[DEBUG] Type of analyzed_jobs:")
    print(type(analyzed_jobs))

    print("[DEBUG] Analyzed jobs returned:")
    print(json.dumps(analyzed_jobs, indent=2))

    print("[DEBUG] Number of analyzed jobs:")
    print(len(analyzed_jobs))

    print("\n----------------------------------------")
    print("[DEBUG] Calling count_categories()")
    print("----------------------------------------")

    category_counts = count_categories(analyzed_jobs)

    print("[DEBUG] Type of category_counts:")
    print(type(category_counts))

    print("[DEBUG] Category counts returned:")
    print(category_counts)

    print("\n----------------------------------------")
    print("[DEBUG] Building final report")
    print("----------------------------------------")

    report = {
        "pipeline_id": pipeline_id,
        "repository": repository,
        "pipeline_status": pipeline_status,
        "failed_job_count": len(analyzed_jobs),
        "category_counts": category_counts,
        "results": analyzed_jobs,
    }

    print("[DEBUG] Final report:")
    print(json.dumps(report, indent=2))

    print("\n[DEBUG] Returning report to API client")
    print("========================================\n")

    print("[DEBUG] Saving report to output/pipeline_analysis.json")

    print("[DEBUG] Saving report to", OUTPUT_FILE)

    write_analysis_report(
    report,
    OUTPUT_FILE,
)
    print("[DEBUG] Returning report to API client")
    

    return report


if __name__ == "__main__":
    print("[LOCAL DEBUG] Starting Pipeline Doctor API directly")

    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
