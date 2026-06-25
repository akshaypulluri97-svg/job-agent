import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tools.resume_parser import extract_text_from_pdf
from tools.job_search import search_jobs
from utils.prompts import EXTRACT_PROMPT, ANALYZE_PROMPT, TAILOR_PROMPT, parse_llm_json
from agent.state import AgentState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


def extract_node(state: AgentState) -> AgentState:
    """Extract skills and experience summary from resume text."""
    prompt = EXTRACT_PROMPT.format(resume_text=state["resume_text"])
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        data = parse_llm_json(response.content)
        return {
            **state,
            "skills": data.get("skills", []),
            "experience_summary": data.get("experience_summary", ""),
        }
    except Exception as e:
        return {**state, "error": f"Extract failed: {e}"}


def search_node(state: AgentState) -> AgentState:
    """Search for jobs across selected countries, filtering already seen ones."""
    try:
        query = " ".join(state["skills"][:5])
        country_codes = state.get("country_codes", ["ca", "us"])
        all_jobs = search_jobs(query, country_codes)

        # Import here to avoid circular imports
        from utils.db import get_seen_job_ids, mark_jobs_seen
        seen_ids = get_seen_job_ids()
        new_jobs = [j for j in all_jobs if j.get("adzuna_job_id") not in seen_ids]
        mark_jobs_seen([j["adzuna_job_id"] for j in all_jobs if j.get("adzuna_job_id")])

        return {**state, "jobs": new_jobs}
    except Exception as e:
        return {**state, "error": f"Search failed: {e}", "jobs": []}


def analyze_node(state: AgentState) -> AgentState:
    """Analyze each job against the candidate profile."""
    results = []

    # Use target JD if provided, otherwise use search results
    if state.get("target_jd"):
        jobs_to_analyze = [{
            "title":         "Target Role",
            "company":       "",
            "location":      "",
            "url":           "",
            "adzuna_job_id": "",
            "description":   state["target_jd"],
        }]
    else:
        jobs_to_analyze = state.get("jobs", [])

    for job in jobs_to_analyze:
        try:
            prompt = ANALYZE_PROMPT.format(
                skills=", ".join(state["skills"]),
                experience_summary=state["experience_summary"],
                job_title=job.get("title", ""),
                job_description=job.get("description", "")[:1500],
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            analysis = parse_llm_json(response.content)
            results.append({**job, **analysis})
        except Exception as e:
            results.append({**job, "error": str(e), "match_score": 0})

    return {**state, "analysis_results": results}


def tailor_node(state: AgentState) -> AgentState:
    """Generate resume tailoring suggestions for a target job."""
    if not state.get("target_jd"):
        return {**state, "tailoring_suggestions": []}

    try:
        prompt = TAILOR_PROMPT.format(
            resume_text=state["resume_text"],
            job_description=state["target_jd"],
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        data = parse_llm_json(response.content)
        return {**state, "tailoring_suggestions": data.get("suggestions", [])}
    except Exception as e:
        return {**state, "tailoring_suggestions": [], "error": f"Tailor failed: {e}"}
