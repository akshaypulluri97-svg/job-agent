import os
import requests

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRIES = {
    "Canada":    "ca",
    "USA":       "us",
    "India":     "in",
    "UK":        "gb",
    "Australia": "au",
    "Germany":   "de",
    "Singapore": "sg",
}

COUNTRY_NAMES = {v: k for k, v in COUNTRIES.items()}

JOB_TYPES = {
    "Any":       {},
    "Full time": {"full_time": "1"},
    "Part time": {"part_time": "1"},
    "Contract":  {"contract": "1"},
    "Remote":    {},
}

FRESHNESS = {
    "Any time":      None,
    "Last 24 hours": 1,
    "Last 3 days":   3,
    "Last week":     7,
}


def search_jobs(query: str, country_codes: list, results_per_country: int = 3) -> list:
    """Search Adzuna for jobs across multiple countries (used by the LangGraph agent)."""
    all_jobs = []
    for code in country_codes:
        try:
            url = (
                f"https://api.adzuna.com/v1/api/jobs/{code}/search/1"
                f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
                f"&results_per_page={results_per_country}"
                f"&what={query.replace(' ', '+')}"
                f"&content-type=application/json"
            )
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            for job in resp.json().get("results", []):
                all_jobs.append(_parse_adzuna_job(job, code))
        except Exception:
            continue
    return all_jobs


def browse_jobs_adzuna(
    keyword: str,
    country_code: str,
    job_type: str = "Any",
    days_old: int = None,
    page: int = 1,
    results: int = 10,
) -> dict:
    """Browse Adzuna with keyword / job-type / freshness filters and pagination."""
    try:
        query = keyword.strip().replace(" ", "+") or "software"
        if job_type == "Remote":
            query += "+remote"

        params = (
            f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
            f"&results_per_page={results}"
            f"&what={query}"
            f"&content-type=application/json"
        )

        for k, v in JOB_TYPES.get(job_type, {}).items():
            params += f"&{k}={v}"

        if days_old:
            params += f"&max_days_old={days_old}"

        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page}{params}"
        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            return {"jobs": [], "total": 0, "error": f"Adzuna error {resp.status_code}"}

        data  = resp.json()
        jobs  = [_parse_adzuna_job(j, country_code) for j in data.get("results", [])]
        total = data.get("count", 0)
        return {"jobs": jobs, "total": total, "error": None}

    except Exception as e:
        return {"jobs": [], "total": 0, "error": str(e)}


def _safe_company_name(company_field) -> str:
    """Adzuna sometimes returns company as a dict, sometimes as a plain string."""
    if isinstance(company_field, dict):
        return company_field.get("display_name", "")
    if isinstance(company_field, str):
        return company_field
    return ""


def _safe_location_name(location_field) -> str:
    """Adzuna sometimes returns location as a dict, sometimes as a plain string."""
    if isinstance(location_field, dict):
        return location_field.get("display_name", "")
    if isinstance(location_field, str):
        return location_field
    return ""


def _safe_category_name(category_field) -> str:
    if isinstance(category_field, dict):
        return category_field.get("label", "")
    if isinstance(category_field, str):
        return category_field
    return ""


def _parse_adzuna_job(job: dict, country_code: str) -> dict:
    """Normalise a raw Adzuna job dict to a common shape."""
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    if salary_min and salary_max:
        salary = f"${int(salary_min):,} – ${int(salary_max):,}"
    elif salary_min:
        salary = f"From ${int(salary_min):,}"
    elif salary_max:
        salary = f"Up to ${int(salary_max):,}"
    else:
        salary = "Not specified"

    created = job.get("created", "")[:10] if job.get("created") else ""

    return {
        "title":         job.get("title", ""),
        "company":       _safe_company_name(job.get("company")),
        "location":      _safe_location_name(job.get("location")),
        "country":       COUNTRY_NAMES.get(country_code, country_code),
        "country_code":  country_code,
        "description":   job.get("description", "")[:1500],
        "url":           job.get("redirect_url", ""),
        "adzuna_job_id": str(job.get("id", "")),
        "salary":        salary,
        "created":       created,
        "category":      _safe_category_name(job.get("category")),
        "source":        "adzuna",
    }
