import json
from pathlib import Path

from langchain_core.tools import tool


MOCK_JOBS_PATH = Path(__file__).with_name("mock_jobs.json")
with open(MOCK_JOBS_PATH, "r", encoding="utf-8") as handle:
    MOCK_JOBS = json.load(handle)


def search_jobs(query: str = "", min_hourly_rate: float = 0, limit: int = 10) -> list:
    q = (query or "").lower().strip()
    results = []
    for job in MOCK_JOBS:
        if min_hourly_rate and job["hourly_rate"] < min_hourly_rate:
            continue
        if q:
            haystack = " ".join(
                [job["title"], job["description"], " ".join(job["skills"])]
            ).lower()
            if q not in haystack:
                continue
        results.append(job)
    return results[:limit]


@tool(description="Search Upwork-style jobs by keyword and minimum hourly rate.")
def search_upwork_jobs(
    query: str = "",
    min_hourly_rate: float = 0,
    limit: int = 10,
) -> list:
    return search_jobs(query, min_hourly_rate, limit)
