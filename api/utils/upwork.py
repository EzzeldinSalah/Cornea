from langchain_core.tools import tool


MOCK_JOBS = [
    {
        "id": "u-001",
        "title": "Senior React + TypeScript developer for SaaS dashboard",
        "description": "Long-term role rebuilding the analytics dashboard for a B2B SaaS. Component library exists, you'd own the data-viz layer.",
        "hourly_rate": 75,
        "weekly_hours": 20,
        "duration": "3-6 months",
        "skills": ["React", "TypeScript", "Tailwind", "D3", "REST"],
        "client": {"rating": 4.9, "payment_verified": True, "spent_total_usd": 48200, "hire_rate_pct": 72},
        "posted_ago_days": 2,
    },
    {
        "id": "u-002",
        "title": "Svelte / SvelteKit developer for e-commerce migration",
        "description": "Porting a Next.js storefront to SvelteKit. Stripe and Shopify Storefront API already wired; you wire up the UI.",
        "hourly_rate": 60,
        "weekly_hours": 30,
        "duration": "1-3 months",
        "skills": ["Svelte", "SvelteKit", "TypeScript", "Stripe"],
        "client": {"rating": 4.8, "payment_verified": True, "spent_total_usd": 12300, "hire_rate_pct": 60},
        "posted_ago_days": 4,
    },
    {
        "id": "u-003",
        "title": "Cheap WordPress fixes — quick turnaround",
        "description": "Need someone to fix a broken plugin and update a theme. Small one-off job.",
        "hourly_rate": 15,
        "weekly_hours": 10,
        "duration": "Less than 1 month",
        "skills": ["WordPress", "PHP", "CSS"],
        "client": {"rating": 3.6, "payment_verified": False, "spent_total_usd": 320, "hire_rate_pct": 18},
        "posted_ago_days": 1,
    },
    {
        "id": "u-004",
        "title": "Python / FastAPI backend for fintech MVP",
        "description": "Greenfield API for a fintech MVP. Postgres, FastAPI, JWT auth. Founder is technical, specs are clear.",
        "hourly_rate": 85,
        "weekly_hours": 40,
        "duration": "3-6 months",
        "skills": ["Python", "FastAPI", "Postgres", "Docker", "AWS"],
        "client": {"rating": 5.0, "payment_verified": True, "spent_total_usd": 91000, "hire_rate_pct": 80},
        "posted_ago_days": 1,
    },
    {
        "id": "u-005",
        "title": "Mobile app — React Native — fitness tracker",
        "description": "Cross-platform fitness app. Designs done in Figma. Backend already live.",
        "hourly_rate": 55,
        "weekly_hours": 25,
        "duration": "1-3 months",
        "skills": ["React Native", "TypeScript", "Expo", "Redux"],
        "client": {"rating": 4.5, "payment_verified": True, "spent_total_usd": 7800, "hire_rate_pct": 55},
        "posted_ago_days": 6,
    },
    {
        "id": "u-006",
        "title": "Data analyst — clean and visualize sales data",
        "description": "Messy CSVs from 4 different sources. Need cleaned dataset + a few dashboards.",
        "hourly_rate": 40,
        "weekly_hours": 15,
        "duration": "Less than 1 month",
        "skills": ["Python", "Pandas", "SQL", "Tableau"],
        "client": {"rating": 4.7, "payment_verified": True, "spent_total_usd": 5400, "hire_rate_pct": 64},
        "posted_ago_days": 3,
    },
    {
        "id": "u-007",
        "title": "Looking for cheap full-stack dev — long term",
        "description": "Need a full-stack dev to maintain a Laravel + Vue app. Pays weekly. Lots of work.",
        "hourly_rate": 12,
        "weekly_hours": 40,
        "duration": "Ongoing",
        "skills": ["Laravel", "Vue", "MySQL", "PHP"],
        "client": {"rating": 3.2, "payment_verified": False, "spent_total_usd": 180, "hire_rate_pct": 9},
        "posted_ago_days": 7,
    },
    {
        "id": "u-008",
        "title": "Senior Next.js engineer — AI content tool",
        "description": "We're building an AI writing tool. Need someone strong with Next.js App Router, streaming, and OpenAI-compatible APIs.",
        "hourly_rate": 95,
        "weekly_hours": 30,
        "duration": "3-6 months",
        "skills": ["Next.js", "TypeScript", "OpenAI", "Vercel", "PostgreSQL"],
        "client": {"rating": 4.9, "payment_verified": True, "spent_total_usd": 132500, "hire_rate_pct": 85},
        "posted_ago_days": 0,
    },
    {
        "id": "u-009",
        "title": "Figma to HTML/CSS — landing page",
        "description": "Single landing page, pixel-perfect from Figma. No JS interactivity beyond a contact form.",
        "hourly_rate": 30,
        "weekly_hours": 10,
        "duration": "Less than 1 month",
        "skills": ["HTML", "CSS", "Tailwind", "Figma"],
        "client": {"rating": 4.6, "payment_verified": True, "spent_total_usd": 2100, "hire_rate_pct": 50},
        "posted_ago_days": 5,
    },
    {
        "id": "u-010",
        "title": "DevOps — set up CI/CD on AWS",
        "description": "Existing app, no pipeline. Need GitHub Actions → ECS deploy with staging + prod environments.",
        "hourly_rate": 70,
        "weekly_hours": 15,
        "duration": "Less than 1 month",
        "skills": ["AWS", "ECS", "Terraform", "GitHub Actions", "Docker"],
        "client": {"rating": 4.8, "payment_verified": True, "spent_total_usd": 23400, "hire_rate_pct": 70},
        "posted_ago_days": 2,
    },
    {
        "id": "u-011",
        "title": "Technical writer — API documentation",
        "description": "Need clear, developer-friendly docs for a REST API. ~30 endpoints. Markdown + OpenAPI.",
        "hourly_rate": 45,
        "weekly_hours": 20,
        "duration": "1-3 months",
        "skills": ["Technical writing", "OpenAPI", "Markdown", "REST"],
        "client": {"rating": 4.7, "payment_verified": True, "spent_total_usd": 8900, "hire_rate_pct": 67},
        "posted_ago_days": 4,
    },
    {
        "id": "u-012",
        "title": "Quick logo design — startup",
        "description": "Simple logo for a new startup. 2-3 concepts, then iterate on the chosen one.",
        "hourly_rate": 25,
        "weekly_hours": 5,
        "duration": "Less than 1 month",
        "skills": ["Illustrator", "Logo design", "Branding"],
        "client": {"rating": 4.4, "payment_verified": True, "spent_total_usd": 1300, "hire_rate_pct": 40},
        "posted_ago_days": 8,
    },
    {
        "id": "u-013",
        "title": "Senior Rust engineer — high-performance API",
        "description": "Replacing a Node service with Rust (Axum). Hot path is JSON-over-HTTP at 10k req/s.",
        "hourly_rate": 110,
        "weekly_hours": 25,
        "duration": "3-6 months",
        "skills": ["Rust", "Axum", "Tokio", "Postgres", "Redis"],
        "client": {"rating": 5.0, "payment_verified": True, "spent_total_usd": 210000, "hire_rate_pct": 90},
        "posted_ago_days": 1,
    },
    {
        "id": "u-014",
        "title": "Generic 'web developer' — vague brief",
        "description": "We need a website. Tell us what tech you'd use. Budget unclear.",
        "hourly_rate": 18,
        "weekly_hours": 20,
        "duration": "Ongoing",
        "skills": ["HTML", "JavaScript", "CSS"],
        "client": {"rating": 3.4, "payment_verified": False, "spent_total_usd": 0, "hire_rate_pct": 0},
        "posted_ago_days": 9,
    },
    {
        "id": "u-015",
        "title": "Frontend dev — Tailwind + Svelte component library",
        "description": "Build out an internal component library. Storybook setup exists. Mostly form components and data tables.",
        "hourly_rate": 65,
        "weekly_hours": 20,
        "duration": "1-3 months",
        "skills": ["Svelte", "Tailwind", "Storybook", "TypeScript"],
        "client": {"rating": 4.8, "payment_verified": True, "spent_total_usd": 36000, "hire_rate_pct": 75},
        "posted_ago_days": 3,
    },
]


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
