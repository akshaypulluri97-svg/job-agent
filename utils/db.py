import os
import streamlit as st
from supabase import create_client

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def _uid() -> str:
    return st.session_state["user"].id

def get_profile() -> dict:
    if os.getenv("LOCAL_DEV") == "true":
        return st.session_state.get("_profile")
    try:
        res = get_supabase().table("resume_profiles").select("*").eq("user_id", _uid()).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def save_profile(resume_text: str, skills: list, experience_summary: str):
    if os.getenv("LOCAL_DEV") == "true":
        st.session_state["_profile"] = {
            "resume_text":        resume_text,
            "skills":             skills,
            "experience_summary": experience_summary,
        }
        return
    try:
        get_supabase().table("resume_profiles").upsert({
            "user_id":            _uid(),
            "resume_text":        resume_text,
            "skills":             skills,
            "experience_summary": experience_summary,
        }, on_conflict="user_id").execute()
    except Exception as e:
        st.error(f"Could not save profile: {e}")

def get_applications() -> list:
    try:
        res = (get_supabase().table("applications")
               .select("*")
               .eq("user_id", _uid())
               .order("created_at", desc=True)
               .execute())
        return res.data
    except Exception:
        return []

def save_application(job: dict):
    try:
        data = {
            "user_id":       _uid(),
            "job_title":     job.get("title") or job.get("job_title") or "",
            "company":       job.get("company") or "",
            "location":      job.get("location") or "",
            "job_url":       job.get("url") or job.get("job_url") or "",
            "adzuna_job_id": job.get("adzuna_job_id") or "",
            "match_score":   int(job.get("match_score") or 0),
            "strengths":     job.get("strengths") or [],
            "skill_gaps":    job.get("skill_gaps") or [],
            "cover_letter":  job.get("cover_letter") or "",
            "source":        job.get("source") or "adzuna",
        }
        res = get_supabase().table("applications").insert(data).execute()
        if res.data:
            return True
        return False
    except Exception as e:
        st.error(f"Could not save application: {e}")
        return False

def update_application(app_id: str, status: str, notes: str):
    try:
        get_supabase().table("applications").update({
            "status": status,
            "notes":  notes,
        }).eq("id", app_id).eq("user_id", _uid()).execute()
    except Exception as e:
        st.error(f"Could not update: {e}")

def get_seen_job_ids() -> set:
    try:
        res = (get_supabase().table("jobs_seen")
               .select("adzuna_job_id")
               .eq("user_id", _uid())
               .execute())
        return {row["adzuna_job_id"] for row in res.data}
    except Exception:
        return set()

def mark_jobs_seen(job_ids: list):
    if not job_ids:
        return
    try:
        rows = [{"user_id": _uid(), "adzuna_job_id": jid} for jid in job_ids]
        get_supabase().table("jobs_seen").upsert(
            rows, on_conflict="user_id,adzuna_job_id"
        ).execute()
    except Exception:
        pass

def save_tailored_resume(application_id, job_title, company,
                          original_text, tailored_text, suggestions):
    try:
        get_supabase().table("tailored_resumes").insert({
            "user_id":        _uid(),
            "application_id": application_id,
            "job_title":      job_title,
            "company":        company,
            "original_text":  original_text,
            "tailored_text":  tailored_text,
            "suggestions":    suggestions,
        }).execute()
    except Exception as e:
        st.error(f"Could not save tailored resume: {e}")
