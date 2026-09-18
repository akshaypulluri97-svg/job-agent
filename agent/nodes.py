import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tools.resume_parser import extract_text_from_pdf
from tools.job_search import search_jobs
from utils.prompts import (
    EXTRACT_PROMPT, ANALYZE_PROMPT, TAILOR_PROMPT,
    ATS_EXTRACT_PROMPT, ATS_GAP_PROMPT,
    parse_llm_json
)
from agent.state import AgentState

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)


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


def _calculate_ats_score(gap: dict, ats_keywords: dict) -> int:
    """Calculate weighted ATS score from gap analysis results."""
    critical_matched  = len([k for k in gap.get("matched", [])
                             if k in ats_keywords.get("must_have", [])])
    preferred_matched = len([k for k in gap.get("matched", [])
                             if k in ats_keywords.get("preferred", [])])
    partial_matched   = len(gap.get("partial", []))
    total_critical    = len(ats_keywords.get("must_have", []))
    total_preferred   = len(ats_keywords.get("preferred", []))
    max_score         = (total_critical * 3) + (total_preferred * 1)

    if max_score > 0:
        raw_score = (critical_matched * 3) + (preferred_matched * 1) + (partial_matched * 1.5)
        return min(100, round((raw_score / max_score) * 100))
    else:
        total_keywords = (len(gap.get("matched", [])) +
                         len(gap.get("missing_critical", [])) +
                         len(gap.get("missing_preferred", [])))
        matched = len(gap.get("matched", []))
        return round((matched / total_keywords) * 100) if total_keywords > 0 else 0


def _run_gap_analysis(resume_text: str, ats_keywords: dict) -> dict:
    """Run ATS gap analysis on a given resume text."""
    try:
        gap_prompt = ATS_GAP_PROMPT.format(
            resume_text=resume_text[:2000],
            must_have=", ".join(ats_keywords.get("must_have", [])),
            preferred=", ".join(ats_keywords.get("preferred", [])),
            tools_platforms=", ".join(ats_keywords.get("tools_platforms", [])),
            job_functions=", ".join(ats_keywords.get("job_functions", [])),
        )
        gap_response = llm.invoke([HumanMessage(content=gap_prompt)])
        gap = parse_llm_json(gap_response.content)
    except Exception:
        gap = {
            "matched": [], "missing_critical": [],
            "missing_preferred": [], "partial": [],
            "ats_score": 0, "summary": ""
        }
    gap["ats_score"] = _calculate_ats_score(gap, ats_keywords)
    return gap


def tailor_node(state: AgentState) -> AgentState:
    """
    Full ATS-powered tailoring pipeline:
    1. Extract ATS keywords from JD
    2. Gap analysis on ORIGINAL resume → before_score
    3. Tailor resume using missing keywords + custom instructions
    4. Gap analysis on TAILORED resume → after_score
    5. Return before/after scores + suggestions
    """
    if not state.get("target_jd"):
        return {**state, "tailoring_suggestions": [], "ats_gap": {}, "ats_keywords": {}}

    jd_text = state["target_jd"]

    # ── Step 1: Extract ATS keywords from JD ────────────────────
    try:
        ats_prompt = ATS_EXTRACT_PROMPT.format(job_description=jd_text[:2000])
        ats_response = llm.invoke([HumanMessage(content=ats_prompt)])
        ats_keywords = parse_llm_json(ats_response.content)
    except Exception:
        ats_keywords = {
            "must_have": [], "preferred": [],
            "tools_platforms": [], "certifications": [], "job_functions": []
        }

    # ── Step 2: Gap analysis on ORIGINAL resume ──────────────────
    before_gap = _run_gap_analysis(state["resume_text"], ats_keywords)
    before_score = before_gap["ats_score"]

    # ── Step 3: Tailor resume ────────────────────────────────────
    try:
        missing_keywords = (
            before_gap.get("missing_critical", []) +
            before_gap.get("missing_preferred", [])
        )
        tailor_prompt = TAILOR_PROMPT.format(
            resume_text=state["resume_text"],
            job_description=jd_text[:2000],
            missing_keywords=", ".join(missing_keywords),
            custom_instructions=state.get("custom_instructions") or "None provided.",
        )
        tailor_response = llm.invoke([HumanMessage(content=tailor_prompt)])
        tailor_data = parse_llm_json(tailor_response.content)
        suggestions = tailor_data.get("suggestions", [])
        print("DEBUG first original:", suggestions[0]["original"][:100] if suggestions else "none")
        print("DEBUG resume start:", state["resume_text"][:200])
    except Exception:
        suggestions = []

    # ── Step 4: Apply suggestions and run gap analysis on tailored resume ──
    tailored_text = state["resume_text"]
    for s in suggestions:
        tailored_text = tailored_text.replace(s.get("original", ""), s.get("rewritten", ""))

    after_gap = _run_gap_analysis(tailored_text, ats_keywords)
    after_score = after_gap["ats_score"]

    # Merge after_gap with summary from before_gap
    after_gap["before_score"] = before_score
    after_gap["after_score"]  = after_score

    return {
        **state,
        "tailoring_suggestions": suggestions,
        "ats_keywords":          ats_keywords,
        "ats_gap":               after_gap,
    }