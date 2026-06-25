import os
import requests

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRIES = {
    "ca": "Canada",
    "us": "USA",
    "in": "India",
    "gb": "UK",
    "au": "Australia",
    "de": "Germany",
    "sg": "Singapore",
}


def search_jobs(query: str, country_codes: list, results_per_country: int = 3) -> list:
    """Search Adzuna for jobs across multiple countries."""
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
                all_jobs.append({
                    "title":         job.get("title", ""),
                    "company":       job.get("company", {}).get("display_name", ""),
                    "location":      job.get("location", {}).get("display_name", ""),
                    "country":       COUNTRIES.get(code, code),
                    "country_code":  code,
                    "description":   job.get("description", "")[:1500],
                    "url":           job.get("redirect_url", ""),
                    "adzuna_job_id": str(job.get("id", "")),
                })
        except Exception:
            continue

    return all_jobs
