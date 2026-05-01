import json
from pathlib import Path

from langchain_core.tools import tool


MOCK_JOBS_PATH = Path(__file__).with_name("mock_jobs.json")
with open(MOCK_JOBS_PATH, "r", encoding="utf-8") as handle:
    MOCK_JOBS = json.load(handle)
# Replace with real Upwork API post-auth.


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


@tool
def search_upwork_jobs(
    query: str = "",
    min_hourly_rate: float = 0,
    limit: int = 10,
) -> list:
    """Search Upwork for open jobs the user could apply to.

    Use this when the user asks for job suggestions, what to take next, where
    to apply, or whether better-paying clients are out there. To make a
    grounded recommendation, also call `get_client_blame` and compare the
    returned jobs against the user's current worst-paying or slowest-paying
    clients.

    Args:
        query: keyword matched case-insensitively against job titles,
            descriptions, and skills. Pass "" to browse everything.
        min_hourly_rate: filter out jobs below this hourly rate (USD).
            Pass 0 for no filter.
        limit: maximum number of jobs to return (default 10).

    Returns a list of jobs, each with: id, title, description, hourly_rate,
    weekly_hours, duration, skills, client (rating 0-5, payment_verified,
    spent_total_usd, hire_rate_pct), and posted_ago_days.
    """
    return search_jobs(query, min_hourly_rate, limit)
