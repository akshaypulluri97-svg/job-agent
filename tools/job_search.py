import os
import requests

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

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
    "Any time":     None,
    "Last 24 hours": 1,
    "Last 3 days":   3,
    "Last week":     7,
}

def search_jobs(query: str, country_codes: list, results_per_country: int = 3) -> list:
    """Search Adzuna for jobs across multiple countries (used by agent)."""
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

def browse_jobs_adzuna(keyword: str, country_code: str, job_type: str = "Any",
                        days_old: int = None, page: int = 1, results: int = 10) -> dict:
    """Browse Adzuna jobs with filters."""
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

        type_params = JOB_TYPES.get(job_type, {})
        for k, v in type_params.items():
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

def browse_jobs_jsearch(keyword: str, country_code: str, job_type: str = "Any",
                         days_old: int = None, page: int = 1) -> dict:
    """Browse JSearch jobs — pulls from LinkedIn, Indeed, Glassdoor in real-time."""
    try:
        if not JSEARCH_API_KEY:
            return {"jobs": [], "total": 0, "error": "JSearch API key not set"}

        query = keyword.strip() or "software engineer"
        if job_type == "Remote":
            query += " remote"

        country_name = COUNTRY_NAMES.get(country_code, "")
        if country_name:
            query += f" {country_name}"

        params = {
            "query":            query,
            "page":             str(page),
            "num_pages":        "1",
            "date_posted":      _jsearch_date_filter(days_old),
            "employment_types": _jsearch_job_type(job_type),
            "country":          country_code.upper() if country_code else "US",
        }

        headers = {
            "X-RapidAPI-Key":  JSEARCH_API_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        resp = requests.get(
            "https://jsearch.p.rapidapi.com/search-v2",
            headers=headers,
            params=params,
            timeout=15,
        )

        if resp.status_code != 200:
            return {"jobs": [], "total": 0, "error": f"JSearch error {resp.status_code}"}

        data = resp.json()
        jobs = [_parse_jsearch_job(j) for j in data.get("data", [])]
        return {"jobs": jobs, "total": len(jobs), "error": None}

    except Exception as e:
        return {"jobs": [], "total": 0, "error": str(e)}

def _jsearch_date_filter(days_old: int) -> str:
    if not days_old:
        return "all"
    if days_old <= 1:
        return "today"
    if days_old <= 3:
        return "3days"
    return "week"

def _jsearch_job_type(job_type: str) -> str:
    mapping = {
        "Full time": "FULLTIME",
        "Part time": "PARTTIME",
        "Contract":  "CONTRACTOR",
        "Remote":    "FULLTIME",
        "Any":       "",
    }
    return mapping.get(job_type, "")

def _parse_adzuna_job(job: dict, country_code: str) -> dict:
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
        "company":       job.get("company", {}).get("display_name", ""),
        "location":      job.get("location", {}).get("display_name", ""),
        "country":       COUNTRY_NAMES.get(country_code, country_code),
        "country_code":  country_code,
        "description":   job.get("description", "")[:1500],
        "url":           job.get("redirect_url", ""),
        "adzuna_job_id": str(job.get("id", "")),
        "salary":        salary,
        "created":       created,
        "category":      job.get("category", {}).get("label", ""),
        "source":        "adzuna",
    }

def _parse_jsearch_job(job: dict) -> dict:
    salary_min = job.get("job_min_salary")
    salary_max = job.get("job_max_salary")
    currency   = job.get("job_salary_currency", "USD")
    if salary_min and salary_max:
        salary = f"{currency} {int(salary_min):,} – {int(salary_max):,}"
    elif salary_min:
        salary = f"From {currency} {int(salary_min):,}"
    else:
        salary = "Not specified"

    posted = job.get("job_posted_at_datetime_utc", "")[:10] if job.get("job_posted_at_datetime_utc") else ""

    return {
        "title":         job.get("job_title", ""),
        "company":       job.get("employer_name", ""),
        "location":      f"{job.get('job_city', '')} {job.get('job_country', '')}".strip(),
        "country":       job.get("job_country", ""),
        "country_code":  "",
        "description":   job.get("job_description", "")[:1500],
        "url":           job.get("job_apply_link", ""),
        "adzuna_job_id": job.get("job_id", ""),
        "salary":        salary,
        "created":       posted,
        "category":      job.get("job_employment_type", ""),
        "source":        "jsearch",
    }
