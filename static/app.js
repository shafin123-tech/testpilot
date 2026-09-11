const analyzeButton = document.getElementById("analyze-button");
const resultsContainer = document.getElementById("results");

analyzeButton.addEventListener("click", async function () {
    const originalButtonText = analyzeButton.textContent;

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing...";

    resultsContainer.innerHTML = `
        <div class="request-status">
            <strong>Analysis in progress...</strong>
            <p>Sending pipeline event to POST /analyze</p>
        </div>
    `;

    const startTime = performance.now();

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                pipeline_id: 4812,
                repository: "payment-service",
                status: "failed",
                jobs: [
                    {
                        name: "unit-tests",
                        status: "passed",
                        duration_seconds: 48
                    },
                    {
                        name: "docker-build",
                        status: "failed",
                        duration_seconds: 32,
                        log: "COPY failed: requirements.txt not found"
                    },
                    {
                        name: "integration-tests",
                        status: "failed",
                        duration_seconds: 61,
                        log: "Connection refused: database:5432"
                    }
                ]
            })
        });

        const endTime = performance.now();
        const durationSeconds = ((endTime - startTime) / 1000).toFixed(1);

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        let resultHtml = `
            <div class="api-activity">
                <div>
                    <span>Request</span>
                    <strong>POST /analyze</strong>
                </div>

                <div>
                    <span>HTTP Status</span>
                    <strong class="success-text">
                        ${response.status} ${response.statusText}
                    </strong>
                </div>

                <div>
                    <span>Analysis Time</span>
                    <strong>${durationSeconds}s</strong>
                </div>

                <div>
                    <span>Failed Jobs</span>
                    <strong>${data.failed_job_count}</strong>
                </div>

                <div>
                    <span>Model</span>
                    <strong>qwen2.5-coder:7b</strong>
                </div>
            </div>
        `;

        for (const job of data.results) {
            let suggestionsHtml = "";

            for (const suggestion of job.analysis.suggestions) {
                suggestionsHtml += `<li>${suggestion}</li>`;
            }

            resultHtml += `
                <div class="result-card">

                    <div class="result-header">
                        <h3>${job.name}</h3>

                        <span class="category-badge">
                            ${job.category}
                        </span>
                    </div>

                    <div class="log-box">
                        ${job.log}
                    </div>

                    <h4>Summary</h4>
                    <p>${job.analysis.summary}</p>

                    <h4>Likely Root Cause</h4>
                    <p>${job.analysis.likely_root_cause}</p>

                    <h4>Recommended Actions</h4>

                    <ul>
                        ${suggestionsHtml}
                    </ul>

                </div>
            `;
        }

        resultHtml += `
            <div class="raw-response-section">

                <button
                    id="toggle-json-button"
                    class="secondary-button"
                >
                    View API Response
                </button>

                <pre
                    id="raw-json"
                    class="raw-json hidden"
                ></pre>

            </div>
        `;

        resultsContainer.innerHTML = resultHtml;

        const rawJson = document.getElementById("raw-json");
        const toggleJsonButton = document.getElementById("toggle-json-button");

        rawJson.textContent = JSON.stringify(data, null, 2);

        toggleJsonButton.addEventListener("click", function () {
            rawJson.classList.toggle("hidden");

            if (rawJson.classList.contains("hidden")) {
                toggleJsonButton.textContent = "View API Response";
            } else {
                toggleJsonButton.textContent = "Hide API Response";
            }
        });

    } catch (error) {
        console.error(error);

        resultsContainer.innerHTML = `
            <div class="error-message">
                <h3>Analysis failed</h3>

                <p>
                    Pipeline Doctor could not complete the request.
                </p>

                <p>
                    ${error.message}
                </p>
            </div>
        `;

    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = originalButtonText;
    }
});